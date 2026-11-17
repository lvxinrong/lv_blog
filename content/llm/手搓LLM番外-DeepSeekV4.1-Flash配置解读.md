+++
title = "手搓 LLM 番外：DeepSeek V4.1 Flash text_config 配置解读"
date = 2026-11-18T01:50:00+08:00
draft = false
slug = "llm-extra-deepseek-v41-flash-text-config"
tags = ["DeepSeek", "MoE", "Engram", "DSpark", "RoPE", "模型配置", "学习笔记"]
summary = "逐字段阅读 DeepSeek V4.1 Flash 的 text_config：从 hidden_size、Attention、MoE、长上下文压缩到 Engram 与 DSpark。区分配置事实、结构直觉与必须回源码确认的实现细节，不展开 vision_config。"
[cover]
    image = "covers/llm-extra-deepseek-v41-flash-text-config.jpg"
    alt = "手搓 LLM 番外：DeepSeek V4.1 Flash text_config 配置解读"
    hiddenInList = true
    hiddenInSingle = true
+++

这份 `text_config` 的信息密度很高。它不是一个简单的“更大版 Qwen”，而是把 **MoE、低秩 Attention、长上下文压缩、稀疏索引、Engram 查表记忆和 DSpark 投机解码**放进了同一套架构。

本文只解读配置，不宣称已经下载、加载或跑通模型。部分字段可以直接确认含义，部分只能形成结构直觉，还有一些必须回到官方 modeling 源码确认。

## 一、先看整体：它由哪些主线组成

```text
主干：40 个 Transformer Block
注意力：64 Q heads / 1 KV head，配合低秩 Q / O 与压缩机制
MoE：384 个路由专家 + 1 个共享专家，每 token 选择 6 个路由专家
长上下文：YaRN + 逐层压缩 + 滑动窗口 + 稀疏索引
Engram：独立的 n-gram 查表记忆
DSpark：3 个草稿阶段 + 块生成 + Markov 顺序依赖 + 置信度调度
量化：主路径 FP8、专家路径 FP4、动态激活与分块缩放
```

所以读这份配置时，不能只沿 `hidden_size → n_heads × head_dim` 这一条公式走。它要求把模型当作一个完整系统来读。

## 二、词表、隐藏维度与层数

### `vocab_size: 129280`

这是 tokenizer 的词表大小，包括子词、特殊 token、标点等，不是自然语言里的单词数量。

和 Qwen3 的 `151936` 相比，它少 22656 个 token，约少 14.9%。但词表不同，token id 不能直接兼容，同一个汉字在两个模型里的 id 也可能不同。

Embedding 参数量为：

```text
129280 × 5120 = 661,913,600，约 6.62 亿
```

这只描述输入 embedding 的规模，不代表整个模型的参数量。

### `hidden_size: 5120`

对应我们代码里的 `emb_dim`，表示每个 token 在残差流中的隐藏向量宽度：

```text
(B, T) → embedding → (B, T, 5120)
```

后面的 Block、归一化、残差连接和输出头主要围绕这 5120 维计算。

### `num_hidden_layers: 40`

对应 40 个 Transformer Block。每个 Block 包含注意力、归一化、残差和 FFN / MoE 等结构，但从后续配置看，各层并不完全同构。

## 三、Attention：Q 头很多，KV 很少，Q 内部维度也很宽

### `num_attention_heads: 64`、`num_key_value_heads: 1`

按标准 GQA 的字段含义：

```text
64 个 Q heads
共享 1 个 K head 和 1 个 V head
```

KV 头数为 1，可以看作 MQA 这一极端形式。它有利于降低 KV 的头数与缓存成本，但不等于注意力总计算量也同比减少。

### `head_dim: 512`

如果按标准 Attention 形状理解：

```text
Q 总维度 = 64 × 512 = 32768
K / V 总维度 = 1 × 512 = 512
```

`32768` 与 `hidden_size=5120` 并不相等，这正是 `head_dim` 与 `hidden_size` 解耦：

```text
输入：(B, T, 5120)
Q：5120 → 32768
注意力输出：32768
O 投影：32768 → 5120
```

隐藏流宽度与 Attention 内部宽度不要求一致。

但配置里还有 `q_lora_rank`、`o_lora_rank`，所以 32768 更适合先理解为理论上的 Q 头总维度，不能直接按普通 Linear 推断实际投影矩阵。

### `q_lora_rank: 1280`、`o_lora_rank: 1024`、`o_groups: 8`

这里的 LoRA 不是后训练 adapter，而是**模型原生的低秩投影结构**：

- `q_lora_rank`：Q 投影的低秩中间维度；
- `o_lora_rank`：O 投影的低秩中间维度；
- `o_groups`：O 投影的分组数。

后训练 LoRA 是给已有权重增加低秩补丁；这里的低秩结构从预训练起就存在于模型中。

### `qk_rope_head_dim: 64`

它表示 Q / K 中用于 RoPE 的通道数为 64，而不是整个 `head_dim=512` 都施加旋转编码。

我们的 V4 当前对所有 head_dim 通道执行 RoPE；这份配置则是：

```text
Q / K 中只有 64 个通道参与位置旋转
```

这不是 64 个可训练参数，而是 64 个通道，对应 32 对旋转维度。具体哪些通道使用 RoPE、哪些通道主要承载内容，需要看实现。

## 四、MoE 与 Router：大量专家、少量激活、整体缩放

### `n_routed_experts: 384`

表示有 384 个可供 Router 选择的专家。

### `n_shared_experts: 1`

表示有 1 个共享专家，通常每个 token 都会经过它。

### `num_experts_per_tok: 6`

每个 token 从 384 个路由专家中选择 6 个：

```text
384 → Top-6 → 6 个路由专家 + 1 个共享专家
```

路由专家选择比例为 `6 / 384 ≈ 1.56%`。这描述的是专家数量上的稀疏性，不等于整个模型的激活参数比例。

### `moe_intermediate_size: 2304`

这是每个 MoE 专家内部 FFN 的中间维度，不是专家数量。

### `scoring_func: "sqrtsoftplus"`

这是 Router 给专家打分时使用的函数：

```text
softplus(x) = ln(1 + e^x)
sqrtsoftplus(x) = sqrt(softplus(x))
```

它输出平滑、非负的匹配分数，用于后续专家选择与权重计算。

### `topk_method: "noaux_tc"`

这是 Top-K 专家选择策略的名称。`noaux` 看起来与不使用辅助损失的负载均衡有关，`tc` 的具体含义需要源码确认，不能只靠缩写猜。

### `norm_topk_prob: true`

表示对 Top-K 选中的路由权重做归一化。例如：

```text
[2, 1, 1] → [0.5, 0.25, 0.25]
```

使选中专家的权重和为 1，便于后续加权合并。

### `routed_scaling_factor: 1.5`

这是路由分支整体贡献的缩放系数，不是 `scoring_func` 的输入参数：

```text
scoring_func：计算专家匹配分数
norm_topk_prob：归一化选中权重
routed_scaling_factor：再缩放路由分支的整体贡献
```

## 五、长上下文：YaRN、压缩、索引和窗口同时存在

### `max_position_embeddings: 1048576`

对应 1,048,576 tokens 的位置容量，不是 1 MB 内存，也不是 100 万字符。

结合：

```json
"rope_scaling": {
  "rope_type": "yarn",
  "factor": 16,
  "original_max_position_embeddings": 65536
}
```

恰好有：

```text
65536 × 16 = 1048576
```

所以它表示通过 YaRN 扩展后的配置上限，不能直接理解为稳定有效的 100 万 token 上下文能力。

### `beta_fast: 32`、`beta_slow: 1`

这两个参数用于调整 YaRN 不同频率通道的扩展强度：

- fast / 高频部分：调整更强；
- slow / 低频部分：调整更弱。

具体 beta 如何进入官方公式，需要看实现。YaRN 扩展位置表示范围，不等于长上下文质量自动得到保证。

### `rope_theta: 10000`

这是主路径的 RoPE 底数，影响各通道的旋转频率与位置角度。它不能简单由 `qk_rope_head_dim=64` 推出“更小就够用了”，theta 与通道维度、训练上下文和位置泛化需要一起看。

### `compress_rope_theta: 160000`

这是压缩路径专用的 RoPE 底数，与主路径的 `10000` 不同，说明不同计算路径可能使用不同的位置编码策略。它具体作用于 token 位置、块位置还是索引位置，需要源码确认。

### `compress_ratios`

数组恰好有 40 项，对应 40 层：

```text
第 0～1 层：0
第 2～17 层：2
第 18～37 层：1
第 38～39 层：0
```

这更像逐层 Attention / KV 压缩策略，而不是直接压缩 Block 输出 hidden state。

`0、1、2` 是比例还是模式编号，需要源码确认，不能仅凭字段名直接解释为输出尺寸缩小多少。

### `kv_source_layer_ids: [2, 8, 14, 20]`

表示第 2、8、14、20 层与 KV 来源有关，可能存在跨层 KV 复用或共享。

### `index_source_layer_ids: [2, 8, 14, 20, 24, 28, 32, 36]`

表示另外 8 层与索引来源有关，稀疏索引机制可能从这些层获取信息。

两组 ID 的层编号从 0 还是从 1 开始，必须看官方代码。

### `index_n_heads: 32`、`index_head_dim: 128`、`index_topk: 512`

这组更像稀疏索引模块自己的配置：

```text
32 个索引头
每头 128 维
每次选择 Top-512 候选位置或块
```

它不是主 Attention 的 64 个 Q heads 和 `head_dim=512`，而是用于计算“哪些历史信息值得被选中”。

### `candidate_source_layer_id: 20`

候选信息来自第 20 层，具体层编号含义仍要看实现。

### `candidate_topk_blocks: 2048`

候选池最多保留 2048 个 block。

### `candidate_block_size: 8`

每个 block 包含 8 个 token，说明筛选粒度可能是 token 块而不是单 token。

如果按同一套块体系理解：

```text
候选池：2048 blocks × 8 tokens = 16384 tokens
实际选择：Top-512 blocks，约为候选池的 1/4
```

这只是由配置形成的结构直觉，具体块生成方式仍需源码确认。

### `sliding_window: 128`

这是局部注意力窗口，当前 token 主要关注附近约 128 个 token，而不是完整历史。它与 `index_topk` 的动态筛选不同：

- sliding window：固定范围稀疏；
- index top-k：内容驱动的动态稀疏。

## 六、Hyper-Connections：多路残差流与 Sinkhorn 混合

```json
"hc_mult": 4,
"hc_sinkhorn_iters": 20,
"hc_eps": 1e-06
```

这里的 `hc` 指 Hyper-Connections，作用于残差流，而不是 Attention heads。

可以暂时理解为：

```text
隐藏状态
→ 扩展成 4 路残差流
→ 用可学习的系数组合这些分支
→ 用 Sinkhorn 迭代归一化组合系数
→ 得到稳定的混合表示
```

`hc_mult=4` 是残差流扩展因子，`hc_sinkhorn_iters=20` 是 Sinkhorn 归一化迭代次数，`hc_eps=1e-6` 用于归一化计算的数值稳定性。

公开实现把它描述为多路残差流及 doubly stochastic 混合矩阵：[参考](https://atlas.klimoza.dev/models/deepseek-v4.1/blocks/token-group/group-input)。

它不是“把 x 复制四份，每份完整执行一次 Attention / FFN，再拼接”，而更像在子层前后对多路残差流进行混合与分配。

## 七、Engram：模型内置的 n-gram 查表记忆

`Engram` 可以理解成一种**模型内置的 n-gram 向量记忆库**：

```text
最近几个 token 组成 n-gram
→ 在专用记忆表中取向量
→ 门控判断是否采用
→ 注入当前隐藏状态
```

它不是为了替代 Transformer 推理，而是让常见短语、固定搭配和静态知识可以直接查用，减少模型反复重算。[公开介绍](https://aki.io/blog/deepseek-v4-1-flash-engram-embeddings/)也将它描述为 n-gram 查表记忆。

### `engram_layer_ids: [1, 14]`

表示在第 1、14 层插入 Engram 模块。

### `engram_num_embeddings: [384006168, 384016682]`

两个 Engram 表各自的 embedding 条目或容量，约 3.84 亿个。具体如何分片、如何映射到物理表，需要看实现。

### `engram_max_ngram_size: 4`

最多使用 4 个 token 组成一个 n-gram，说明它主要处理短组合与局部模式。

### `engram_vocab_size: 16000000`

n-gram 的索引 / 词表空间为 1600 万，远大于主词表的 129280。

### `engram_n_heads: 8`

Engram 检索模块使用 8 个头，不是主 Attention 的 64 个头。

### `engram_head_dim: 256`

每个 Engram head 的向量维度为 256。

### `engram_pad_token_id: 2`

Engram 自己的 padding token id。

### `engram_compressed_vocab_size: 99092`

压缩后的 n-gram 词表大小，不是主模型词表大小。

`engram_num_embeddings` 与 `engram_vocab_size` 不是一回事：前者更像实际条目或参数容量，后者是 n-gram 索引空间，`engram_compressed_vocab_size` 则是压缩后的表示空间。

它和“把短句直接做成高阶 token”也不同：主 token 序列没有被替换，Engram 是额外提供查表向量，补充模型计算。

## 八、DSpark：内置投机解码草稿结构

DSpark 是内置的投机解码机制，核心不是让模型更聪明，而是尽量通过并行起草与目标模型验证降低逐 token 解码成本。[DSpark 论文](https://arxiv.org/html/2607.05147v1)描述了半自回归并行起草、Markov 顺序依赖和置信度调度。

### `num_nextn_predict_layers: 3`

表示有 3 个 DSpark 草稿阶段 / 预测层，不是一次生成 3 个 token。

### `dspark_block_size: 5`

每个草稿块最多提出 5 个 token，不是固定接受 5 个。

### `dspark_noise_token_id: 128799`

这是 DSpark 并行起草时使用的特殊噪声 / 占位 token，不是正常文本内容。

### `dspark_target_layer_ids: [37, 38, 39]`

草稿结构复用目标模型第 37、38、39 层的表示，即 40 层主干的最后三层。

### `dspark_markov_rank: 256`

Markov 头的低秩维度，用于补足并行起草时的顺序依赖和块内一致性。

### `dspark_n_routed_experts: 128`

DSpark 自己的 MoE 部分包含 128 个路由专家，与主模型的 384 个专家分开。

### `dspark_num_experts_per_tok: 3`

DSpark 的 MoE 部分每个 token 选择 3 个路由专家。

所以这里有两套 MoE 配置：

```text
主模型：384 个专家，每个 token 选 6 个，另有 1 个共享专家
DSpark：128 个专家，每个 token 选 3 个
```

## 九、量化与精度配置

### `quant_method: "fp8"`

主量化方法使用 FP8，即 8 位浮点格式。它不是 INT8，具体是 E4M3 还是 E5M2 需要看实现。

### `activation_scheme: "dynamic"`

激活值在运行时动态量化，根据本次计算的实际数值范围确定尺度，而不是提前用校准数据固定所有激活范围。

### `weight_block_size: [32, 32]`

表示权重按 32×32 小块量化，每块 1024 个元素。它比整张量共用一套尺度更细，有利于适应不同区域的数值分布，但会增加缩放因子与管理成本。

### `scale_fmt: "ue8m0"`

这是缩放因子的编码格式：无符号 8 位指数形式，缩放值以 2 的幂次表示，而不是任意小数。它服务于量化尺度和硬件实现，不是权重本身的 dtype。

### `expert_dtype: "fp4"`

专家权重使用 FP4，即 4 位浮点格式，进一步降低存储与带宽成本，但也更依赖激活截断、量化尺度和专用 kernel。

因此这份配置是：

```text
主路径 FP8
专家路径 FP4
激活值动态量化
缩放值 ue8m0
权重块 32 × 32
```

不能把模型简单理解成 BF16，也不能把 FP4 理解成所有计算都只用 4 位完成。

## 十、其他字段速记

### `hidden_act: "silu"`

FFN 的门控分支使用 SiLU，与我们当前实现一致：

```python
self.act(self.gate_proj(x)) * self.up_proj(x)
```

门控结构由 `gate_proj` 和 `up_proj` 的权重形成，不需要额外配置一个“门阀开关”。

### `swiglu_limit: 10.0`

这是 SwiGLU 的激活范围限制。公开实现示例大致是：

```python
gate = torch.clamp(gate, max=10.0)
up = torch.clamp(up, min=-10.0, max=10.0)
activation = F.silu(gate) * up
```

它用于控制异常激活值并提高低精度计算稳定性，[公开实现说明](https://idlemachines.co.uk/essays/deepseek-v4-efficiency-release)。

### `rms_norm_eps: 1e-20`

RMSNorm 分母中的 epsilon，用于防止除零和数值稳定。我们的 Qwen3-0.6B 是 `1e-6`，这里的 `1e-20` 小了 10¹⁴ 倍。

### `attention_bias: false`

Attention 投影不使用 bias。

### `attention_dropout: 0.0`

Attention weights 的 dropout 比例为 0，即关闭注意力权重 dropout。

### `initializer_range: 0.02`

从零初始化权重时使用的正态分布标准差，可近似理解为 `N(0, 0.02)`。从 checkpoint 加载已有权重时，它不参与前向计算。

### `use_cache: true`

启用或允许 KV Cache，实际调用仍可覆盖。

### `tie_word_embeddings: false`

输入 embedding 与输出头不共享权重。若为 true，才会共享。

### `architectures: ["DeepseekV41ForCausalLM"]`

告诉 Transformers 应实例化哪个模型类。

### `model_type: "deepseek_v41"`

模型家族的配置标识。

### `dtype: "bfloat16"`

默认精度声明，但实际主路径与专家路径还受量化配置影响。

### `transformers_version: "5.6.0"`

配置对应的 Transformers 版本，不是模型自身版本号。

### `bos_token_id: 0`

序列开始 token。

### `eos_token_id: 1`

序列结束 token。

### `pad_token_id: 2`

Batch 对齐时使用的 padding token。

### `image_token_id: 129264`

图像相关特殊 token，用于多模态输入，不属于普通文本生成逻辑。本文按当前学习选择，不展开 `vision_config`。

## 十一、仍需回源码确认的问题

这份配置很适合做“从配置到实现”的审计入口，但不能代替实现。当前留下的明确待查项包括：

- `q_lora_rank / o_lora_rank` 的实际矩阵拆分与 Q/K/V/O 形状；
- `o_groups` 的分组方式；
- `noaux_tc` 的路由与负载均衡细节；
- `compress_ratios` 中 0 / 1 / 2 的精确语义；
- `kv_source_layer_ids` 与 `index_source_layer_ids` 的层编号及跨层数据流；
- `index_topk` 与候选块的实际筛选单位；
- `engram_num_embeddings` 的精确物理含义、分片与查表方式；
- DSpark 的置信度头、验证路径和接受率。

后续最合理的阅读顺序是：

```text
官方 modeling
→ attention / MoE forward
→ 压缩与索引路径
→ Engram 查表路径
→ DSpark draft / verify / confidence 调度
```

这份 `text_config` 的真正价值，是让我看到了一种趋势：**模型能力不只来自更大的矩阵，也来自低秩分解、稀疏计算、分层信息组织、查表记忆和推理期协同。** 后续实现时，我会把这些字段继续转换成可验证的形状、数据流和测试，而不是只停留在名词解释上。

## 写在最后

只读 `config.json`，就已经可以感受到最前沿开源模型的架构复杂程度。

再回头看我们从 V1 到 V4 的迭代，这种感受会更具体：

```text
V1：从 GPT-2 开始，把最基本的模型、训练和生成跑通
V2：补上 RoPE，开始理解位置编码如何进入注意力
V3：引入 RMSNorm、SwiGLU、GQA 和权重绑定，承接 Qwen2.5
V4：显式 head_dim、QK RMSNorm，承接 Qwen3，并继续做推理、对话和后训练实验
```

以前我更多在想：一个矩阵怎么算、一个 Block 怎么对齐、一个权重形状为什么对不上。现在再往前看，会发现大模型的能力已经不只是由这些基本结构决定了。

Attention 可以压缩，KV 可以跨层组织，专家可以稀疏调用，记忆可以独立查表，生成也可以由草稿结构和置信度调度一起完成。它们解决的不是“如何把模型做得更大”，而是“怎样让计算、存储和推理真正配合起来”。

从 V1 到 V4，我是在把主干写明白；再往后，就是把这些高效机制一件件拆开来看。这个差距很明显，但也让我更清楚下一步该学什么。

不过，有一点很重要：**整体思路上，它并没有逃离 Transformer 的体系。**

无论是 MoE、低秩 Attention、Hyper-Connections、Engram，还是 DSpark，主干计算依然是围绕 token 序列、注意力、残差流和逐层表示展开的。个人理解，这更像是对 Transformer 体系的一次精细化架构考量：在保留主干的前提下，针对长上下文、显存、计算效率和推理速度，做更细的拆解和优化。

这样看下来，很多新名词也没有那么陌生了。先抓住 Transformer 的主干，再看它们分别优化了哪一环，就更容易理解这些变化究竟在解决什么问题。

