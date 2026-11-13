+++
title = "手搓 LLM 笔记 22：Qwen3 兼容性"
date = 2026-11-12
draft = false
slug = "llm-22-qwen3-compatibility"
tags = ["LLM", "I3番外", "Qwen3", "模型兼容性", "学习笔记"]
summary = "从 config 与 safetensors 审计出发，从零实现隔离的 V4 / Qwen3-0.6B，完成官方前向、cache decode、固定生成和本地对话验收，并复盘流式渲染、增量解码与 token 上限问题。"
[cover]
    image = "covers/llm-22-qwen3-compatibility.jpg"
    alt = "手搓 LLM 笔记 22：Qwen3 兼容性"
    hiddenInList = true
    hiddenInSingle = true
+++

这篇是 I3 的独立番外，起点不是“再写一个模型”，而是一个可复用的问题：**面对一个陌生模型，怎样判断当前代码能否加载、能否正确前向、还缺哪些能力？**

当前真实状态是：V3 继续作为 Qwen2.5-0.5B / 0.5B-Instruct 的稳定对照；独立实现的 V4 已承接 Qwen3-0.6B，并通过官方前向、连续 cache decode、固定生成和本地对话验收。本文保留从兼容性审计到流式对话排障的完整过程，不把单个模型与受控环境的结果扩大为全系列支持。

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

V4 最终没有复制或引用 V3 的模型实现，而是把 RMSNorm、SwiGLU、RoPE、Attention、TransformerBlock 和 GPTModel 重新写了一遍。这样每个版本都必须亲自过一遍，理解架构差异，而不是把“复用”误当成“掌握”；封板之后的工程复用是另一阶段的问题。RMSNorm 保留 FP32 累积、输入输出 dtype 一致的修复，避免重新引入 FP16 平方溢出。

公共 device、tokenizer 协议和报告工具可以复用；模型结构、权重映射和验收保持隔离。

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

## 六、前一晚的停止边界

前一晚先读懂 `config.json`、兼容性审计顺序和 V3 / V4 的隔离原则，没有立即开始 V4 实现。

不熬夜，不通宵。结构实现、权重键审计和官方数值对照留给后续学习日；后面的章节记录这些工作的实际完成情况。

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
bos  Beginning of Sequence 放在输入开头，告诉模型“文本从这里开始”
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
所以 rope_theta 越大 → 各维度频率越低 → 每步旋转角度越小 → 相邻位置的区分度更“细腻”，影响位置频率分布与长距离行为

`"tie_word_embeddings": true,`
输入 embedding（token → 向量）和输出 lm_head（向量 → vocab logits）共用同一个权重矩阵（互为转置）
对小模型来说可以节约参数。当前模型可以节约 vocab_size × hidden_size 151936 × 1024 大概 1.55亿参数量

`"torch_dtype":"bfloat16" `
torch加载权重使用的精度类型，看起来是BF16(BF16 指数位多，**尾数位少**，所以可表达的数据范围大，但精度低) 动态范围和 FP32 一样大

`"use_cache": true,`
开启kv cache的开关

`"vocab_size": 151936`
词表大小

## 七、权重审计：从“文件不可直接阅读”到可复用检查能力

Safetensors 是二进制格式，不能像 Markdown 或 JSON 一样直接阅读。但这个能力不应该只停留在某次 Qwen3 实验的临时命令里，因此新增：

```text
src/squid/checkpoints/inspect.py
```

`inspect_safetensors()` 使用 `safe_open()` 读取：

- 权重键名称；
- 张量形状；
- dtype；
- 元素数量；
- 文件字节数与权重键总数。

它只读取元数据，不加载完整模型权重，适用于后续其他模型的兼容性审计。用户已添加最小回归并实际运行，结果为 **1 passed**。

### 1. Qwen3-0.6B 的真实权重证据

当前本地 Qwen3-0.6B 文件：

```text
文件大小：1,503,300,328 bytes
权重键数量：311
文件中的总元素数：751,632,384
主要 dtype：BF16
```

第 0 层的真实形状为：

| 权重 | 形状 | 结构含义 |
| --- | --- | --- |
| `q_proj.weight` | `[2048, 1024]` | 16 个 Q heads × 128 head_dim |
| `k_proj.weight` | `[1024, 1024]` | 8 个 KV heads × 128 head_dim |
| `v_proj.weight` | `[1024, 1024]` | 与 K 对称 |
| `o_proj.weight` | `[1024, 2048]` | 将 2048 维 attention 结果降回 1024 维隐藏状态 |
| `q_norm.weight` | `[128]` | 每个 head 内部的 Q 归一化 |
| `k_norm.weight` | `[128]` | 每个 head 内部的 K 归一化 |
| `input_layernorm.weight` | `[1024]` | 隐藏状态归一化 |
| `post_attention_layernorm.weight` | `[1024]` | 隐藏状态归一化 |

这与 config 中 `hidden_size=1024`、`head_dim=128` 相互印证：**head_dim 不再由 hidden_size / heads 自动得到，Q/K/V 与输出投影的形状都围绕显式 head_dim 组织。**

### 2. 一个不能靠 config 猜测的 lm_head 细节

配置中写着：

```json
"tie_word_embeddings": true
```

第一版探针因此假设文件里不会有独立 `lm_head.weight`，结果实际检查为：

```text
no_independent_lm_head = false
```

也就是说，文件中同时存在：

```text
model.embed_tokens.weight
lm_head.weight
```

这时不能直接忽略 `lm_head.weight`。正确做法是先比较两份实际权重，再决定是否去重。

用户实际加载并比较后得到：

```text
embedding：shape=[151936, 1024]，dtype=BF16
lm_head：  shape=[151936, 1024]，dtype=BF16
torch.equal(...) = True
最大绝对差 = 0.0
```

因此可以确认：checkpoint 虽然重复保存了输出头，但两份权重完全相同。V4 在加载后使用一份共享参数是安全的。

去掉这份重复输出头后：

```text
751,632,384 - 155,582,464 = 596,049,920
```

约为 **5.96 亿元素**，与 0.6B 的模型命名数量级一致。这也说明模型名称、文件大小和实际加载后的独立参数量不能直接画等号。

### 3. 当前兼容性坐标

| 能力 | 当前判断 | 验收或边界 |
| --- | --- | --- |
| 配置字段映射 | V4 已独立实现 | 由官方前向与生成对照验收 |
| 显式 head_dim | V4 已新增 | `head_dim=128`，不再用 `hidden_size / heads` 推导 |
| QK RMSNorm | V4 已新增并映射权重 | 投影后、RoPE 前执行 |
| attention_bias=false | 已进入 V4 配置 | 不沿用 Qwen2.5 的 QKV bias |
| embedding / lm_head 共享 | 两份实际权重已证明相等 | 加载后只保留一份共享参数 |
| Sliding attention | 当前模型未启用 | 最小 V4 不实现 |
| BF16 | 已有支持 | 保留 RMSNorm FP32 累积修复 |
| 正确前向 / 对话 | 已在当前受控条件通过 | 见第八、九节；不扩大为全系列支持 |

早期总兼容性探针曾因独立 `lm_head` 的假设返回 `all_metadata_checks_passed=false`；随后的真实权重比较与 V4 官方对照已经关闭这个疑问，不把早期探针状态误写成当前失败状态。

这次最值得保留的经验是：

> **Config 描述的是模型的结构意图，checkpoint 则决定实际如何存储。两者出现表面不一致时，不直接忽略字段，也不立即判定模型异常，而是用真实权重形状和数值证明是否可以安全映射。**

## 八、V4 官方数值与生成验收通过

ModelV4 从零实现了 RMSNorm、SwiGLU FFN、RoPE、Qwen3Attention、TransformerBlock 和 GPTModelV4，没有复制或引用 V3 的模型实现。独立加载器使用 `checkpoints/qwen3.py`，测试位于 `tests/test_qwen3/`。

### 1. 真实权重前向对照

使用本地 Qwen3-0.6B、CPU、FP32、固定英文 prompt：

```text
V4 输出形状：     (1, 6, 151936)
官方输出形状：    (1, 6, 151936)
最大 logit 差异：4.1008e-05
平均 logit 差异：4.3524e-06
allclose(1e-4)： true
top-1 一致：     true
全部有限：       true
```

这验证了显式 head_dim、QK RMSNorm、GQA、RoPE、权重共享和独立映射在当前受控条件下成立。

### 2. 连续 cache decode

V4 与官方连续执行三次单 token cache decode：

| Step | V4 token | 官方 token | 是否一致 | allclose(1e-4) |
| --- | ---: | ---: | --- | --- |
| 1 | 264 | 264 | 是 | 是 |
| 2 | 8544 | 8544 | 是 | 是 |
| 3 | 429 | 429 | 是 | 是 |

### 3. 固定贪心生成

两边固定生成 8 个 token：

```text
V4：    264, 8544, 429, 702, 40444, 23839, 11004, 323
官方：  264, 8544, 429, 702, 40444, 23839, 11004, 323
```

生成长度、token IDs 和文本均完全一致：

```text
a topic that has sparked considerable debate and
```

因此当前最小目标可以正式验收：**V4 不只是能加载 Qwen3 权重，还能在 CPU / FP32 / eager 下完成正确的 prefill、连续 cache decode 和固定贪心生成。**

这组数值结论仍限定于当前输入、CPU / FP32 / eager，不扩大为所有设备、dtype 或 Qwen3 全系列均已通过；chat template 与 thinking 的本地对话验收另见第九节。MoE 与其他模型格式不在本次验收范围内。

## 九、Qwen3 对话服务：思考开关与思考区分离

V4 数值验收通过后，`chat_server` 与 Web UI 已从 V3 / Qwen2.5-0.5B 切换到 V4 / Qwen3-0.6B。当前使用的是 `Qwen/Qwen3-0.6B` 后训练对话模型，不是 `Qwen3-0.6B-Base`。

### 1. 思考模式真正进入模板

`build_qwen_chat_prompt()` 新增可选的 `enable_thinking` 参数，服务端将页面开关随请求传入：

```text
enable_thinking=true
→ 使用 Qwen3 默认的 thinking 生成路径

enable_thinking=false
→ chat template 加入空的 <think>...</think> 区域，引导模型直接回答
```

该参数是模板控制，不是 V4 新增了一套推理算法。V4 负责执行模型，模型负责是否生成思考内容。

模板 stub 测试与流式、会话相关测试合计 **13 passed**，JavaScript 语法检查通过。

### 2. 页面将思考与正式回答分离

新增 `<details>` 思考区：

- 标题为“思考过程”；
- 默认折叠，点击可展开；
- 流式过程中可以展开观察；
- 正式回答使用独立区域，不再把 `<think>` 当普通正文；
- 历史恢复与多会话切换继续使用同一套分离渲染；
- 页面底部新增“思考模式”复选框，生成时禁用切换，避免请求中途改变模板状态。

### 3. 真实浏览器验收

开启思考模式，输入 `2+2 等于几？`：

- 页面出现可折叠的“思考过程”；
- 思考区与正式回答分离；
- 正式答案为“2加2等于4。”；
- 折叠与展开均正常；
- SSE 流式状态、TURN 计数和会话列表正常。

关闭思考模式并新建会话，输入 `3+3 等于几？`：

- 没有思考区；
- 直接返回“3 + 3 等于 6。”；
- 新建会话与流式输出仍正常。

当时观察到回答中偶尔出现 ``，尚未完成归因。后续对照服务端历史与流式页面，才确认其中至少有一类来自增量解码，而不是模型真的输出了乱码；详细定位见第十节。

## 十、流式对话排障：顺序、增量解码与生成预算

对话页面接通以后，真正暴露的问题不再只是模型结构，而是**连续事件如何被转换成稳定的用户界面**。今天修复了三个不同层级的问题，它们表面上都像“页面显示不对”，实际根因完全不同。

### 1. 思考过程为什么跑到正文下面

流式渲染函数分别维护 `.thinking-details` 和 `.assistant-answer`。旧逻辑在思考节点不存在时直接 `appendChild(details)`：

```text
正文节点先创建
→ 思考节点随后出现
→ appendChild 把思考节点追加到正文后面
```

这解释了为什么思考结束后，正文开始生成，思考区反而位于正文下方。修复不是调整 CSS，而是明确 DOM 顺序：

```javascript
container.insertBefore(
  details,
  container.querySelector('.assistant-answer'),
);
```

即使正文节点先生成，思考区也始终插入正文之前。使用“你好，请介绍一下 LLM 中的注意力机制”做真实浏览器验收，确认**正文流式生成过程中和生成结束后**，思考区都位于上方；折叠、展开与最终 Markdown 渲染保持正常。

### 2. `` 不是页面编码问题，而是不稳定前缀被提前推送

当时页面出现：

```text
结：
```

但服务端 `/session/history` 中保存的最终回答是正常的：

```text
总结：
```

这组对照非常关键：如果最终历史正确、只有流式页面错误，就应优先检查增量链路，而不是怀疑模型权重或 HTML 的 UTF-8 声明。

`ChatSession.ask_stream()` 的策略是每得到一个 token，就重新解码全部 `generated_ids`，再按上一次文本长度截取 delta。旧逻辑隐含了一个不总成立的假设：**上次解码文本永远是这次解码文本的稳定前缀。**

当末尾汉字所需的字节或 token 尚未到齐时，中间解码可能临时以 `` 结尾：

```text
上一次：...
这一次：...总结

旧 delta = response[len(previous_response):]
结果只发出“结”，而之前的“”已经推送给页面，无法撤回
```

修复方式是在末尾仍为 `` 时暂缓推送，等待后续 token 将其补全；生成结束后再补发剩余文本：

```python
if response.endswith("\ufffd"):
    continue
```

新增的 `test_ask_stream_waits_for_incomplete_utf8_suffix` 用受控解码序列复现这个边界，要求最终 deltas 只有 `["总结"]`，不能包含 ``，也不能丢掉“总”。这是流式文本处理里值得长期保留的原则：

> **只能向只能追加的 UI 推送已经稳定的前缀；可能随后续输入改写的尾部，应当先留在缓冲区。**

### 3. 512 tokens 为什么会同时截断思考与正文

本地对话默认值经过两轮有依据的调整：

```text
context_size：  4096 → 8192
max_new_tokens： 256 → 512 → 1024
```

两个环境变量分别为 `LVCHAT_CONTEXT_SIZE` 与 `LVCHAT_MAX_NEW_TOKENS`，仍可在启动时覆盖。

第一次调到 512 后，`25 * 24 结果是多少` 已能完整输出思考与“25 乘以 24 等于 600”。但另一个问题“你好，介绍一下注意力机制”仍停在 `4. **优势**`。对服务端清理后的回答重新编码，结果是**正好 512 tokens**，说明它撞到了生成上限。

这里最容易误解的是：

```text
max_new_tokens = 思考 tokens + 正式回答 tokens + 结束标记
```

它不是正文独享的预算。把默认上限调整为 1024 后，同一个问题完整生成到“优势”和“总结”；清理后的历史回答重新编码为 **585 tokens**，不含已被清理的结束标记。这说明此前 512 的确不足，而这次调参有一致问题的数据依据，不是无目的翻倍。

上下文与生成预算也不是没有成本：因果掩码存在平方级开销，KV Cache 随 token 数增长，多会话还会继续累加。当前它们是本地实验配置，不代表已完成长上下文性能优化。

### 4. SSE done 不等于模型自然结束

旧页面只要收到 `done=true`，就显示“就绪 · SSE 流式返回”。但 `done` 原来只表示服务器的事件流结束，无法区分：

```text
stop：模型生成 EOS，自然结束
length：达到 max_new_tokens，被强制停止
```

现在 `ChatSession` 记录 `last_finish_reason` 与 `last_generated_tokens`，服务端在最后一个 SSE 事件中附加：

```text
finish_reason
generated_tokens
max_new_tokens
```

页面收到 `finish_reason=length` 时，会明确显示“已达生成上限 · 回答可能不完整”，并提示可以增大 `LVCHAT_MAX_NEW_TOKENS`，不再把硬截断伪装成正常完成。

真实验收分成两边：

- 默认 1024 下，同一注意力机制问题完整结束，页面保持正常完成状态；
- 临时将上限设为 16，页面实际出现“本次已达到 16 tokens 生成上限，回答可能不完整”的提示；验证后停止临时服务。

### 5. 模型能力问题与工程问题分开记录

小模型自身仍然存在不稳定。例如 `123 + 789` 的思考中，模型一度算出 912，随后陷入“8912？不对”的重复，直到耗尽预算，正式回答为空。这不是 DOM 或 UTF-8 修复能够解决的问题，继续增大预算也只会允许重复持续更久。

因此当前笔记把三类结论分开：

```text
架构正确性：由官方 logits、cache decode 和固定生成对照证明
工程链路：由 SSE、DOM 顺序、增量解码和结束原因验收
模型质量：单独观察，不用工程测试替模型能力背书
```

### 6. 今天的验证范围

本轮相关回归实际运行结果为 **10 passed**，覆盖 `test_chat_session.py`、Qwen logits chat 与 Qwen chat regression；其中包括新增的临时 `` 解码回归。JavaScript `node --check` 与本次变更文件的 `git diff --check` 均通过。

真实浏览器验收覆盖思考区顺序、乱码消失、1024 下长回答完整结束，以及 16 tokens 下的截断提示。这个数字只代表本轮指定回归集合，不累加历史测试数，也不冒充全量测试或 Qwen3 全系列验收。
