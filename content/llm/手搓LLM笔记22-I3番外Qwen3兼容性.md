+++
title = "手搓 LLM 笔记 22：Qwen3 兼容性"
date = 2026-11-12
draft = true
slug = "llm-22-qwen3-compatibility"
tags = ["LLM", "I3番外", "Qwen3", "模型兼容性", "学习笔记"]
summary = "以 Qwen3-0.6B 为例学习模型兼容性审计：从 config.json、权重键和官方 forward 判断 v3 与目标模型的差距，并约定 V3 / V4 完全隔离。当前只建立学习现场，不宣称 ModelV4 或 Qwen3 已加载。"
[cover]
    image = "covers/llm-22-qwen3-compatibility.jpg"
    alt = "手搓 LLM 笔记 22：Qwen3 兼容性"
    hiddenInList = true
    hiddenInSingle = true
+++

这篇是 I3 的独立番外，起点不是“再写一个模型”，而是一个可复用的问题：**面对一个陌生模型，怎样判断当前代码能否加载、能否正确前向、还缺哪些能力？**

当前真实状态是：v3 已验证 Qwen2.5-0.5B / 0.5B-Instruct；ModelV4 尚不存在，Qwen3 的加载与数值验收尚未完成。本文只建立学习现场，不提前记录成果。

## 一、为什么先学兼容性审计

`config.json` 是了解模型的第一入口，但“有 config”不等于“可以直接加载”。完整的判断链路是：

```text
模型家族与 config
→ 权重键、形状和分片
→ 官方 forward 的计算语义
→ 配置与权重映射
→ 官方 logits 对照
→ cache decode 与固定生成验收
```

这套方法以后面对 Llama、Mistral 或其他模型也适用，不只服务 Qwen3。

## 二、Qwen3-0.6B 的配置地图

当前目标模型的关键配置是：

| 配置 | 当前值 | 对我们意味着什么 |
| --- | ---: | --- |
| `model_type` | `qwen3` | 不是当前已验证的 Qwen2.5 家族 |
| `vocab_size` | 151936 | 与当前 Qwen2.5 词表一致 |
| `hidden_size` | 1024 | 对应我们的 `emb_dim` |
| `intermediate_size` | 3072 | 对应我们的 `ffn_dim` |
| `num_hidden_layers` | 28 | 28 个 Transformer Block |
| `num_attention_heads` | 16 | 16 个 Q heads |
| `num_key_value_heads` | 8 | 8 个 KV heads，使用 GQA |
| `head_dim` | 128 | 每个 attention head 的维度 |
| `rope_theta` | 1000000 | 与当前 Qwen2.5 配置一致 |
| `rms_norm_eps` | 1e-6 | RMSNorm 的 epsilon |
| `attention_bias` | false | Q/K/V 等投影不使用 bias |
| `tie_word_embeddings` | true | embedding 与输出头共享权重 |
| `max_position_embeddings` | 40960 | 配置允许的位置范围，不等于本轮实际上下文 |
| `use_sliding_window` | false | 当前最小目标不需要 sliding attention |
| `hidden_act` | `silu` | FFN 的 gate 分支使用 SiLU，与当前实现一致 |

其中最容易被直接套公式误导的是：

```text
hidden_size = 1024
num_attention_heads = 16
head_dim = 128
```

当前 v3 使用 `emb_dim / n_heads`，会得到 64，而 Qwen3 真实配置要求 128。因此 V4 必须允许 `head_dim` 与 `emb_dim` 解耦，不能只改配置数字。

另外，官方 Qwen3 forward 中还存在 **QK RMSNorm**：Q/K 投影后、RoPE 前分别归一化。这个结构差异不能只靠 config 猜，需要同时阅读官方实现和实际权重键。

## 三、V3 与 V4 必须完全隔离

为了保留稳定的 Qwen2.5 对照实现，约定：

```text
src/squid/model/v3_modern/    保持现状
src/squid/model/v4_qwen3/     V4 独立结构、RoPE、归一化和 attention

src/squid/checkpoints/qwen.py   V3 / Qwen2.5 加载器
src/squid/checkpoints/qwen3.py  V4 / Qwen3 独立加载器

tests/test_qwen/   V3 回归
tests/test_qwen3/  V4 独立验收
```

V4 可以从 V3 复制一个已知可用起点，但复制后独立演进，不直接 import 或修改 V3 的模型实现。RMSNorm 的 FP32 累积修复必须一并带入，避免重新引入 FP16 平方溢出。

公共 device、tokenizer 协议和报告工具可以复用；模型结构、权重映射和验收必须隔离。

## 四、兼容性审计清单

面对一个新模型时，按以下顺序判断：

1. **模型家族**：`model_type`、`architectures` 是否属于当前支持范围；
2. **结构配置**：hidden size、层数、heads、KV heads、head_dim、RoPE、bias、权重绑定；
3. **权重键**：是否存在当前映射无法处理的键，是否有独立 `lm_head.weight`；
4. **张量形状**：权重形状是否与配置一致；
5. **checkpoint 形式**：单文件还是多分片，格式是否可读取；
6. **tokenizer**：词表、EOS / BOS、chat template 和特殊 token；
7. **官方语义**：norm、RoPE、掩码、残差与输出头是否一致；
8. **数值验收**：官方 logits、prefill、cache decode 和固定生成对照。

需要区分三个层级：

```text
能加载权重
≠ 能正确前向
≠ 能正确对话
```

## 五、ModelV4 的最小目标

第一版只做：

```text
显式 head_dim
+ QK RMSNorm
+ Qwen3 配置与权重映射
+ V3 / V4 完全隔离
```

最小验收模型为 **Qwen3-0.6B Dense**。暂不承诺：

- Qwen3 全系列；
- Qwen3 MoE；
- GGUF / NVFP4；
- 27B 模型加载；
- 尚未执行的下载、前向或硬件验证结果。

## 六、今晚的停止边界

今晚只读懂 `config.json`、兼容性审计顺序和 V3 / V4 的隔离原则，不开始 V4 实现。

不熬夜，不通宵。结构实现、权重键审计和官方数值对照留到后续学习日。

### 1.  Qwen3-0.6B config.json
```json
{  
  "architectures": [  
    "Qwen3ForCausalLM"  
  ],  
  "attention_bias": false,  
  "attention_dropout": 0.0,  
  "bos_token_id": 151643,  
  "eos_token_id": 151645,  
  "head_dim": 128,  
  "hidden_act": "silu",  
  "hidden_size": 1024,  
  "initializer_range": 0.02,  
  "intermediate_size": 3072,  
  "max_position_embeddings": 40960,  
  "max_window_layers": 28,  
  "model_type": "qwen3",  
  "num_attention_heads": 16,  
  "num_hidden_layers": 28,  
  "num_key_value_heads": 8,  
  "rms_norm_eps": 1e-06,  
  "rope_scaling": null,  
  "rope_theta": 1000000,  
  "sliding_window": null,  
  "tie_word_embeddings": true,  
  "torch_dtype": "bfloat16",  
  "transformers_version": "4.51.0",  
  "use_cache": true,  
  "use_sliding_window": false,  
  "vocab_size": 151936  
}
```

逐项解读

`"architectures": [ "Qwen3ForCausalLM" ]`
`architectures` 的作用是告诉 Hugging Face Transformers 库：加载这个模型时应该实例化哪个 Python 类。这里就是 `Qwen3ForCausalLM` 这个类。

`"attention_bias": false, `
注意力层QKV线性投影是否带偏置项 

`"attention_dropout": 0.0`
注意力att层中，用于控制 softmax(att_scores) 之后的dropout的比例。 `attn_weights = self.dropout(attn_weights)`

`"bos_token_id": 151643, "eos_token_id": 151645, `
bos  Beginning of Sequence 放在输入开头，告诉模型"文本从这里开始"
eos End of Sequence  模型生成到这个 token 时停止输出 

`"head_dim": 128,`
多头注意力机制下每个头的emb_dim 

`"hidden_act": "silu",`
FFN 前馈神经网络中 用到的激活函数 FFN中声明了act  `self.act = nn.SiLU()`
```python
"""  
y = down_proj( SiLU(gate_proj(x)) * up_proj(x) )  
gate_proj门控信号，SiLU 之后才形成实际的连续开度。  
up_proj 升维后的x (B, T, emb_dim) -> (B, T, hidden_dim)  hidden_dim 默认是emb_dim的3倍  
down_proj 降维回 (B, T, hidden_dim) -> (B, T, emb_dim)  
SwiGLUFFN 相比较之前的 FeedForward 核心是多了一个门阀矩阵。  
按照我的理解，这个门阀矩阵是类似一个电阻的装置，允许电流通过大小，也就是hidden_dim每个维度允许通过多少  
  
但是核心原理和FeedForward不变，依然是在token经过attention 输出后的每个 token 的隐藏表示 做逐位置变换  
再更高维度对自身的隐藏表示进行编辑。  
阀门也就是在维度升高之后，增加了一个可以由模型自行通过学习修改阀门流量的开关。可以决定这些信息哪些值得保留，放大或者压下去。  
SwiGLU FFN 在升维后，是用 gate_proj 单独生成一路门控信号，经 SiLU 变成每个 hidden 维度的连续开度，再与 up_proj 的内容逐元素相乘。这个开度可学习、可大于 1、可接近 0、也可为负，因此模型能逐维度决定信息保留、放大、压制甚至反向。  
"""  
def forward(self, x):  
    return self.down_proj(  
        self.act(self.gate_proj(x)) * self.up_proj(x)  
    )
```


`"hidden_size": 1024`
其实就是emb_dim 但是Qwen3的设计上，说是`让注意力头的维度独立于隐藏层大小，调参更灵活`
那原本16个头，每个头dim是128 一共是 2048。那我猜测输入可能是 2048 然后输出的时候，在out_proj的声明上，可以是 (2048, 1024) 就可以实现降维。


`"initializer_range": 0.02,`
权重初始化时用的**正态分布标准差**。模型创建时，所有线性层和 embedding 的权重按 `N(0, 0.02)` 随机初始化

`intermediate_size": 3072`
FFN中升维的维度，那Qwen3 看起来就是 1024 -> 3072 -> 1024了

`"max_position_embeddings": 40960,` 
这个不是指位置编码(RoPE是相对位置，没有max一说) 
`max_position_embeddings` 在 RoPE 模型里含义变了:  **模型支持的最大序列长度**(也就是经常看到的模型上下文大小) 所以这个模型上下文大小就是40K

`"max_window_layers": 28, `
滑动窗口注意力（Sliding Window Attention）目前还没有学到，相关的配置是 `"sliding_window": null,`  `use_sliding_window` 就是滑动窗口的总开关


`"num_attention_heads": 16,` 
多头注意力机制中头的数量，因为GQA的架构中 KV的头是少于Q的，所以这里也就特指Q_head_nums

`"num_hidden_layers": 28, "`
LLM中一共有多少层 trf_block (一个trf_block 包含1个att和一个ffn)

`"num_key_value_heads": 8, `
多头注意力机制中 KV的头数量，一般小于Q的头数量。等于 Q 头数时就是标准 MHA，等于 1 时是 MQA（Multi-Query Attention），介于两者之间就是 GQA。

`"rms_norm_eps": 1e-06,`
RMSNorm中防止除0用的，一般设置的会很小 `eps=1e-6` 防止分母为 0，纯数值稳定性用途，不影响模型表达能力。
```python
def forward(self, x):  
    input_dtype = x.dtype  
    x_float = x.float()  
    mean_square = x_float.pow(2).mean(dim = -1, keepdim = True)  
    # 就在这里使用
    y = x_float * torch.rsqrt(mean_square + self.eps) * self.scale.float()  
    return y.to(dtype=input_dtype)
```
torch.rsqrt(mean_square + self.eps)  等价于 1 / sqrt(mean(x²) + eps)

`"rope_theta": 1000000,`
`rope_theta` 是计算各维度旋转频率的**底数（base）** 
```
第 i 对维度的频率: θ_i = 1 / (rope_theta^(2i/d))
位置 m 的旋转角度: m × θ_i
```
所以 rope_theta 越大 → 各维度频率越低 → 每步旋转角度越小 → 相邻位置的区分度更"细腻"，影响位置频率分布与长距离行为

`"tie_word_embeddings": true,`
输入 embedding（token → 向量）和输出 lm_head（向量 → vocab logits）共用同一个权重矩阵（互为转置）
对小模型来说可以节约参数。当前模型可以节约 vocab_size × hidden_size 151936 × 1024 大概 1.55亿参数量

`"torch_dtype":"bfloat16" `
torch加载权重使用的精度类型，看起来是BF16(BF16 指数位多，**尾数位少**，所以可表达的数据范围大，但精度低) 动态范围和 FP32 一样大

`"use_cache": true,`
开启kv cache的开关

`"vocab_size": 151936`
词表大小 