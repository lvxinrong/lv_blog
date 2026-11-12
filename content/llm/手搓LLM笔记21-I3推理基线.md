+++
title = "手搓 LLM 笔记 21：KV Cache 与量化"
date = 2026-11-11T13:53:19+08:00
draft = false
slug = "llm-21-i3-inference-baseline"
tags = ["LLM", "I3", "推理", "KV Cache", "量化", "RMSNorm", "学习笔记"]
summary = "从 Prefill / Decode 与 KV Cache 基线出发，完成会话复用、token 预算和滑动裁剪，再用真实 Qwen 对照 INT8 / INT4 的存储、PPL、内存与生成性能，并定位 FP16 的 RMSNorm 平方溢出。"
[cover]
    image = "covers/llm-21-i3-inference-baseline.jpg"
    alt = "手搓 LLM 笔记 21：KV Cache 与量化"
    hiddenInList = true
    hiddenInSingle = true
+++

I3 正式开始。和 I2 不同，这一段不再围绕训练吞吐、反向传播和参数更新展开，而是围绕一个已经训练好的模型：**输入一段 prompt 之后，它是怎样一步一步生成回答的，又该如何测量和优化这条链路。**

第一站不是量化，也不是投机解码，而是先把推理基线立起来。没有基线，后面的“变快了”和“更省显存”都没有可靠的对照对象。

> 阅读主线：第一至四节是 I3-0 推理基线；第五至七节是 I3-1 增量 prefill、会话复用与滑动窗口；第八至十四节是 I3-2 权重量化、16-bit 激活和 FP16 排障。第十一节保留修复前现场，第十三、十四节是修复后的正式复测；结尾第十五节统一汇总结论与边界。

## 一、推理其实分为两步

过去看生成代码时，容易把整个 `generate()` 当成一个黑盒：输入提示词，循环若干次，文字就一个 token 一个 token 地出来了。

这次把它拆开后，结构其实非常清楚：**Prefill（预填充）和 Decode（解码）**。

### 1. Prefill：一次性处理完整 prompt

```text
完整 prompt
    ↓ 一次性送入模型
计算每个 prompt token 在每层的 K / V
    ↓
得到 past_kv + 最后一个位置的 logits
    ↓
采出第一个新 token
```

Prompt 中的所有 token 会一起进入模型。因果掩码仍然保证每个位置不能偷看未来，但矩阵计算可以覆盖整段 prompt，不必等前一个 prompt token 生成完再处理下一个。

这一步除了得到用于采样的 logits，还会留下每一层、每一个 prompt token 的 K 和 V，也就是 `past_kv`。

### 2. Decode：每次只输入一个新 token

```text
新生成的 token + past_kv
    ↓
计算这个新 token 的 K / V，并追加到 cache
    ↓
结合历史 K / V 做注意力计算
    ↓
得到 logits，采出下一个 token
    ↓
重复
```

Decode 并不是不再需要模型计算。每个新 token 仍然要经过所有 Transformer 层，只是历史 token 的 K/V 不需要重新计算。

所以 KV Cache 缓存的不是“答案”，也不只是最后一层的隐藏状态，而是：

> **每一层、每一个历史 token 的 K 和 V。**

Prefill 主要影响首字延迟，Decode 则决定后续文字向外冒的速度。这就是 TTFT 和 decode tokens/s 要分开测的原因。

## 二、先建立一份不改生成行为的基线

本次新增：

- `src/squid/generate/benchmark.py`：计时、KV Cache 字节统计与固定长度生成测量；
- `scripts/i3_inference_baseline.py`：加载真实模型，执行 warmup 和正式测量，保存报告；
- `tests/test_inference_benchmark.py`：对照原有生成函数，验证输出与 KV Cache 字节数。

测量入口没有替换正式的 `generate()`，而是单独建立固定长度 benchmark。这样可以控制实验条件，也不急于改动生产链路。

### 测量条件

- 模型：Qwen2.5-0.5B-Instruct，真实本地权重；
- 设备：Mac / MPS；
- 精度：FP32；
- Prompt：36 tokens；
- 固定生成：32 tokens；
- 解码：temperature=0，即贪心解码；
- 不启用 EOS 提前停止，保证每轮都生成相同数量的 token；
- 每种模式先 warmup 一次；
- 独立运行三轮，报告中位数；
- 模型加载和 prompt 编码不计入生成耗时。

TTFT 从生成测量开始，到采出第一个新 token 为止。Decode 吞吐使用首字之后的 31 个 token 除以对应时间，不把首字重复算进 decode。

## 三、第一轮真实结果

| 模式 | TTFT 中位数 | Decode 吞吐中位数 |
| --- | ---: | ---: |
| KV Cache | 43.28 ms | 40.26 tokens/s |
| No Cache | 48.44 ms | 23.28 tokens/s |

在当前模型、prompt 长度和生成配置下：

- Cache 的 decode 吞吐约为 no-cache 的 **1.73 倍**；
- 两种模式的真实输出**逐 token 一致**；
- Cache 的 TTFT 中位数较低，但 prompt 只有 36 tokens，三轮首字时间也有波动，先不对这项差异做过度解释；
- 这个结果使用 Qwen2.5-0.5B 和 Mac / MPS，不与 M3 当时 GPT-2 355M 的 3.6 倍结果直接混比。

三轮 decode 吞吐分别为：

```text
Cache：   41.15 / 40.26 / 39.01 tokens/s
No Cache：23.35 / 22.97 / 23.28 tokens/s
```

三轮汇总保存在 `data/reports/i3-inference-baseline-mps-summary.json`。

## 四、KV Cache 的实际字节数是怎样算出来的

这次没有只写理论公式，而是直接遍历模型返回的 `past_kv`：

```python
sum(
    tensor.nelement() * tensor.element_size()
    for layer_kv in past_kv
    for tensor in layer_kv
)
```

这是两层循环。`past_kv` 的结构是：

```text
past_kv
├── 第 0 层：(K 张量, V 张量)
├── 第 1 层：(K 张量, V 张量)
├── ...
└── 第 23 层：(K 张量, V 张量)
```

第一层循环遍历 24 个 Transformer 层，第二层循环遍历每层的 K 和 V。

其中：

- `nelement()` 是张量中的标量元素总数，也就是各维度长度的乘积，等价于 `numel()`；
- `element_size()` 是单个元素占用的字节数，FP32 为 4 bytes，FP16 / BF16 为 2 bytes；
- 两者相乘，才是一个张量实际占用的字节数。

本次 prefill 后，每个 K 或 V 的形状是：

```text
[batch=1, kv_heads=2, tokens=36, head_dim=64]
```

所以一个张量包含：

```text
1 × 2 × 36 × 64 = 4608 个元素
```

FP32 下为：

```text
4608 × 4 = 18,432 bytes
```

24 层、每层 K/V 两个张量，总计：

```text
18,432 × 24 × 2 = 884,736 bytes = 864 KiB
```

换成每个 token 的 KV Cache 成本：

```text
2（K 和 V）× 24 层 × 2 KV heads × 64 head_dim × 4 bytes
= 24,576 bytes/token
= 24 KiB/token
```

实测结果和公式完全一致。按这个每 token 成本推算，一个会话达到 4096 tokens 时，仅 KV Cache 约为 **96 MiB**；这是基于实测单位成本的推算，不是一次 4096-token 设备峰值测量。

## 五、代码审查中确认的三个边界

### 1. 为什么使用 `max_new_tokens < 1`

规则是允许所有大于等于 1 的值，因此需要拒绝 0 和负数。`!= 1` 会把 32、64 等合法值也错误拒绝。

当只生成一个 token 时，可以测 TTFT，但没有后续 decode token，因此 decode 吞吐记为 `None`，不伪造一个速度。

### 2. 为什么同时检查维度和 batch

`idx` 的约定形状是 `(B, T)`：

- `idx.ndim != 2`：要求输入确实有 batch 和 token 两个维度；
- `idx.shape[0] != 1`：当前基线只测单请求，因此 B 必须为 1；
- `idx.shape[1] < 1`：拒绝空 prompt。

最终接受的是 `(1, T)`，且 `T >= 1`。

### 3. 固定长度测量与 EOS 提前停止

当前固定长度函数不接收 `eos_id`，也没有 EOS `break`，所以一定会生成指定数量的 token。即使采到 EOS，也只把它当作输出 token。

如果未来把它通用化为支持 EOS 的测量入口，最后一个 token 的计时必须同时覆盖“达到最大生成长度”和“EOS 提前结束”，实际生成 token 数也要按输出长度重新计算。不能只加一句 `break`，否则计时和吞吐统计都会留下边界问题。

这也是为什么当前函数明确叫 `measure_fixed_length_generation`，而没有冒充完整的通用生成器。

## 六、一个被新测试逼出来的增量 Prefill Bug

为了准备会话级 KV Cache，先让 `generate()` 支持传入和返回 `past_kv`，随后补了一条对照测试：

1. 第一轮从 3 个 prompt token 开始，生成 3 个 token，并返回 cache；
2. 第二轮新增 2 个 token；
3. 对照组把第一轮输出和新增 token 拼成完整 prompt，从头重算；
4. 实验组只输入新增的 2 个 token，复用第一轮 cache；
5. 两组新生成的 token 和最终 cache 长度必须一致。

这条测试第一次运行时失败了：

```text
RuntimeError: The size of tensor a (8) must match the size of tensor b (2)
at non-singleton dimension 3
```

### 1. 为什么是 2 和 8

第一轮结束后，cache 中已有 6 个 token。第二轮一次新增 2 个 token，因此：

```text
q_len = 2
k_len = 6 + 2 = 8
attn_scores.shape = (B, H, 2, 8)
```

但 v1 的旧代码仍然按本轮 query 数量切掩码：

```python
mask_bool = self.mask.bool()[:q_len, :q_len]
```

得到的是 `2 × 2`，无法应用到 `2 × 8` 的注意力分数上。

### 2. 为什么旧测试一直没有发现

此前的两条常见路径都恰好绕开了这个问题：

- 全新 prefill 没有历史 cache，`q_len == k_len`，方形掩码恰好适用；
- 单 token decode 时 `q_len == 1`，代码直接使用 `mask_bool = None`，因为唯一的新 token 可以看到全部历史。

只有“已有 cache，同时一次新增多个 token”时，才会同时出现 `q_len > 1` 和 `k_len > q_len`。这就是多 token 增量 prefill 与此前单 token decode 的本质差别。

### 3. 不能只把掩码扩成 2 × 8

还需要保证掩码的行对应新 token 的真实位置。本轮两个 token 的绝对位置是 6 和 7：

```text
位置 6：允许看到 0～6，必须屏蔽 7
位置 7：允许看到 0～7
```

如果从掩码的第 0 行开始切，即使形状对了，语义也会错。正确修法是：

```python
q_len = queries.shape[2]
k_len = keys.shape[2]

if q_len == 1:
    mask_bool = None
else:
    past_len = k_len - q_len
    mask_bool = self.mask.bool()[
        past_len:past_len + q_len,
        :k_len,
    ]
```

`past_len:past_len + q_len` 选中与本轮 token 真实位置对应的掩码行，`:k_len` 则保留从全部历史到本轮当前的列。

修复后，目标测试通过；连同前面的生成与基线测试，当前为 **9 passed**。

### 4. 掩码切片到底取出了什么

模型初始化时会预先生成一张覆盖最大上下文的因果掩码。如果 `context_length=1024`，`self.mask` 的形状就是 `(1024, 1024)`。

上三角掩码中，第 `i` 行的含义是：

- 第 `0～i` 列为 `0 / False`：允许看到历史和当前位置；
- 第 `i+1` 列及之后为 `1 / True`：屏蔽未来位置。

`.bool()` 只负责把 0 / 1 转成 False / True，不重新决定屏蔽位置。切片也只是取出已有掩码的一部分，不修改原始掩码，更不会在切片时把某些位置设置为 True。真正使用掩码的是后续的 `attn_scores.masked_fill_(mask_bool, -torch.inf)`，它就地修改的是注意力分数，不是掩码。

当前修复中的二维切片是：

```python
mask_bool = self.mask.bool()[
    past_len:past_len + q_len,
    :k_len,
]
```

逗号前负责行，逗号后负责列：

- 行：从第一个新 token 的绝对位置 `past_len` 开始，取 `q_len` 行；切片结束位置不包含在结果中；
- 列：从第 0 列开始，取 `k_len` 列，对应当前真实存在的全部 Key。

代入本次测试的 `past_len=6`、`q_len=2`、`k_len=8`：

```python
mask_bool = self.mask.bool()[6:8, :8]
```

这就是从完整掩码中取第 6、7 行和第 0～7 列，得到 `2 × 8`，正好对应 `2 × 8` 的注意力分数。

取这些行，是因为本轮新 token 的绝对位置为 6、7；只取这些列，是因为当前只有 8 个 Key。更后面的 Key 不存在，多取不仅没有意义，还会让掩码与注意力分数形状不一致。

当 `q_len=1` 时，唯一的新 token 已经位于序列末尾，所有现有 Key 都属于历史或当前位置，没有未来 Key 需要屏蔽，因此可以直接使用 `mask_bool=None`。

### 5. 三个模型版本不能一概而论

- v1：已修复，并通过多 token 增量对照测试；
- v2：起初保留相同的旧掩码逻辑，随后使用同样的 `past_len` 偏移切片修复；
- v3：原本就使用 `past_len = k_len - q_len` 和偏移切片，没有这个缺陷。

最后用 pytest 参数化，让同一条增量对照测试分别使用 v1 和 v2 运行，避免复制两份测试后逐渐失去同步。v1、v2 的新增 token 输出和最终 cache 长度均与完整重算一致。

这次最值得保留的经验是：**测试“单 token decode 能复用 cache”，并不等于测试了“任意新增 token 段都能复用 cache”**。正确性测试必须覆盖不同的 `q_len / past_len` 组合，而不是只跑一条最顺的路径。

## 七、让 KV Cache 活到下一轮对话

单次生成的 cache 复用已经跑通后，下一步是把 cache 交给 `ChatSession` 保存。这里需要同时维护两份状态：

- `past_kv`：模型内部每一层的 K/V 张量；
- `cached_token_ids`：这些 K/V 实际对应哪些文本 token。

只有新 prompt 的开头与 `cached_token_ids` 完全一致，才允许复用 `past_kv`。命中时只传入新增 token；历史被改写、模板变化或淘汰导致前缀不一致时，必须放弃旧 cache，重新 prefill。

### 1. EOS 后要以真实 cache 长度为准

生成输出中的 token 数不一定等于 KV Cache 中的 token 数。当前 `generate()` 遇到 EOS 时，先把 EOS 加入输出，再直接 break，不会继续把 EOS 送入模型。

因此保存会话状态时，使用：

```python
cache_length = present_kv[0][0].shape[2]
cached_token_ids = full_token_ids[:cache_length]
```

`present_kv[0][0]` 是第 0 层的 K 张量，其形状为 `(B, H_kv, T, D)`；`shape[2]` 是完整 cache 的序列长度 T。各层 K/V 的 T 在当前模型中一致，所以不需要取“最后一层”或“最后一个 token”。

### 2. 按 token 预算淘汰历史

进入模型前，先为输出预留空间：

```text
prompt_budget = context_size - max_new_tokens
```

如果 prompt 超出预算，就删除最早的一轮历史，重新构建并编码 prompt，直到进入预算。System prompt 和当前输入仍由 prompt builder 保留，优先淘汰普通历史。

如果已经没有历史，当前输入自身仍然超长，则明确报错，不静默截断用户输入。这一限制也避免了模型实际使用尾部 `idx[:, -context_size:]`，而会话却错误记录头部 token IDs 的错位问题。

当前实现会在每轮淘汰后重新构建并编码完整 prompt。历史只有少量轮次时，这优先保证正确性；如果未来支持长会话，可以升级为按 token 块维护账本，减少重复编码。

### 3. 真实 Qwen 两轮探针

测试使用同一个真实 Qwen2.5-0.5B-Instruct 模型和相同输入：

- 一条会话正常保存并复用 cache；
- 另一条保留相同文本历史，但在每轮前清掉 cache，强制完整重算。

| 轮次 | 路径 | 本轮输入 tokens | 使用旧 cache | 输出一致 |
| --- | --- | ---: | --- | --- |
| 第一轮 | 会话 cache | 30 | 否 | 是 |
| 第一轮 | 完整重算 | 30 | 否 | 是 |
| 第二轮 | 会话 cache | 15 | 是 | 是 |
| 第二轮 | 完整重算 | 61 | 否 | 是 |

第二轮 prefill 输入从 61 降为 15 个新增 token，减少约 **75.4%**。两条路径的两轮回答均一致，证明这次会话复用不只是状态对象被保存了，而是真实模型链路确实复用了旧 K/V。

该探针没有测量 TTFT 或总耗时，因此当前只声明输入规模和正确性收益，不提前宣称性能提升比例。报告保存在 `data/reports/i3-session-cache-probe.json`。

### 4. 当前验收与剩余边界

- 会话命中、历史淘汰后回退、当前输入超长拒绝均有测试；
- 生成、推理基线、RoPE、真实 Qwen cache 和会话相关测试合计 **15 passed**；
- 真实 Qwen 两轮 cache / 完整重算输出一致；
- MPS 仍只有 allocated / driver 快照，没有与 CUDA 相同的峰值接口；
- v1 / v2 在历史淘汰后使用完整重算；v3 已接通滑动窗口与部分 KV Cache 复用；
- 模型内部仍使用动态 `torch.cat` 追加 K/V，预分配 cache 尚未实现；
- 量化、投机解码、SSE 和 CUDA 复测尚未完成。

### 5. 滑动窗口已接通，细节留作后续专题

v3 已接入显式 `position_offset`，`ChatSession` 使用 `next_position` 保存会话的原始位置进度。`_slide_cache_to_prompt()` 已接入 `ask()`：前缀不一致时，寻找可保留的固定前缀和最近后缀，同步裁剪各层 K/V 与 `cached_token_ids`，再只对剩余新增 token 做增量 prefill。

裁剪 cache 不会减少 `next_position`；只有清空会话或完全重建时才从 0 开始。每次生成后，根据 cache 的实际增长量推进位置，因此 EOS 已输出但未进入模型时不会被多算。

验收覆盖：

- 带编号的虚拟 K/V：前缀、后缀和 token IDs 裁剪后逐项一致；
- v3 真实模型结构：历史淘汰后只传增量，prefill 使用原始位置，后续 decode 正确递增；
- 真实 Qwen 权重第三轮滑动：cache 从 66 裁剪到 34 tokens，淘汰后的 prompt 为 53 tokens，实际只输入 19 个新增 token；位置从 66 继续，生成后推进到 90，与 cache 增长一致；
- 历史被有意淘汰后，回答允许变化，因此滑动场景不拿“与完整重算回答完全一致”作为错误目标。

当前对位置编码、前缀 / 后缀匹配和 K/V 裁剪的细节理解仍不够扎实。按学习节奏，将这部分标记为**后续专项研究**；代码链路已经完成最小验收，但后续仍应补更多边界测试与原理复盘，而不是把“跑通”当成“已经吃透”。

I3 主线下一站转入 **INT8 / INT4 权重量化推理**。

## 八、权重量化：先理解标尺，再讨论 Linear 替换

I3 的量化主线是推理侧的 **PTQ（训练后量化）**：模型训练已经完成，不再做反向传播或参数更新，只把已有浮点权重转换成更低精度的表示。

量化的目标不是绝对“不损失能力”，而是在**质量损失可接受**的前提下，减少每个权重的存储空间，降低模型体积和运行时显存，并争取减少带宽开销。提速不是自动结果，仍取决于反量化成本和实际计算 kernel。

### 1. INT8 / INT4 减少的是每个参数的位数

FP32 每个参数占 4 bytes，INT8 占 1 byte，真正的 INT4 占 0.5 byte。参数量和模型结构没有改变，改变的是每个参数的表示精度。

INT4 如果只把 `-7～7` 的数值放入 `torch.int8`，仍然每个值占 1 byte，不是真正的 4-bit 存储；后续还需要 bit packing，把两个 4-bit 数打包进一个 byte。

权重量化与 KV Cache 量化也是两件事。W8A16 / W4A16 表示权重使用 8 / 4 bit、激活使用 16-bit 浮点；当前讨论的仅权重量化不会自动改变此前 KV Cache 的精度。

### 2. scale 是每行自己的标尺

逐行对称 INT8 量化使用：

```text
M = 当前行最大绝对值
scale = M / 127
量化值 = round(weight / scale)
```

将除法展开：

```text
weight / (M / 127)
= (weight / M) × 127
```

因为 `|weight| <= M`，所以缩放结果的绝对值不会超过 127。最大绝对值映射到 ±127，其他元素按照自己占最大值的比例映射到中间位置，0 仍然映射到 0。

`clamp(-127, 127)` 是最后的范围保护，正常情况下 absmax 与 scale 已经保证不会越界。`.round()` 后数值虽然已是整数形式，dtype 仍是浮点；最后 `.to(torch.int8)` 才改变实际存储类型。

零行没有最大值可作为非零标尺，因此将 scale 安全替换为 1。`torch.where(scale == 0, torch.ones_like(scale), scale)` 是逐元素选择：scale 为 0 的位置取 1，其余位置保留原值。零行经过 `0 / 1` 后仍然全部是 0。

小矩阵实测中：

```text
原始权重：[0.0, 0.5, -1.0, 1.0]
INT8：   [0, 64, -127, 127]
反量化： [0.0, 0.5039, -1.0, 1.0]
```

`0.5` 到 `0.5039` 的差异就是量化误差。用户已亲自运行该探针，并完成两项数学测试，结果为 **2 passed**。

这份小矩阵还显示了 scale 的存储成本：12 个 FP32 权重原本占 48 bytes；12 个 INT8 权重占 12 bytes，但 3 个 FP32 行 scale 另占 12 bytes，总计 24 bytes。因此实际压缩倍率要包含 scale 等元数据，不能只看理论位数。

### 3. PTQ 与 LoRA 不是一回事

LoRA 主要通过训练低秩适配参数来微调能力；权重量化改变的是已有权重的数值表示，不训练新能力。工程上两者都可能涉及 Linear 模块处理，但训练语义不同。

如果训练中使用量化，需要进入 QAT、浮点主权重、梯度近似或低精度训练 kernel 等问题。当前的 INT8 buffer 实现只用于训练后的推理，不支持直接训练 INT8 权重。

### 4. 替换的是 GQA 内部的 Linear，不是整个 GQA

本次讨论中具体要替换的是这类线性投影：

```python
self.W_query = nn.Linear(emb_dim, emb_dim)
```

同理还包括 GQA 内部的 K/V 投影和输出投影等 Linear。这里不是替换整个 `GroupedQueryAttention`，更不是替换整个 `TransformerBlock`。

原调用链：

```text
TransformerBlock.forward()
→ GroupedQueryAttention.forward()
→ self.W_query(x)（nn.Linear）
→ F.linear(x, FP32 weight, bias)
```

替换后：

```text
TransformerBlock.forward()          不变
→ GroupedQueryAttention.forward()   不变
→ self.W_query(x)（QuantizedLinearInt8）
→ INT8 weight × scale，得到反量化浮点权重
→ F.linear(x, 反量化 weight, bias)
```

`nn.Linear.forward()` 的核心本来就是 `F.linear(x, weight, bias)`，即 `x @ weight.T + bias`。量化 Linear 重新调用 `F.linear`，不是漏掉了原层逻辑，而是只替换最底端线性计算的权重来源。

如果包装层同时保存原始 FP32 Linear 和 INT8 副本，原始权重仍占空间，就失去了量化节省存储的意义。因此这里是从原层取出权重并量化，再用不保存 FP32 主权重的新模块替换它。

当前反量化后仍通过 `F.linear` 做浮点计算，这是教学参考路径，不代表已经获得 INT8 硬件加速；每次 forward 产生的临时浮点权重也需要纳入后续内存测量。

此后已完成小型 v3 与真实 Qwen 的 INT8 / INT4 替换验收；具体过程、测试范围和实测边界见后续章节。

## 九、INT8 / INT4 实测：把每一个“没看懂”变成理解

今天学习量化时，并不是先理解再写代码，而是很多地方先产生疑问，再通过公式、形状和真实输出逐一对齐。比起最终的测试数字，这条理解路径更值得保留。

### 1. 从“缩放缺少数学直觉”到理解 scale
最初知道 `scale = max / 127`，但对为什么缩放后一定落入 `-127～127` 缺少直觉。
后来将公式展开：
```text
weight / scale

= weight / (M / 127)

= (weight / M) × 127
```


其中 `M` 是当前行最大绝对值。当前元素的绝对值除以 `M`，结果一定在 0～1；再乘 127，就不会超出 INT8 对称量化的标尺。

同时纠正了“归一化做得好，权重就一定在 -1～1”的误解。RMSNorm 主要规范化激活，weight decay 也不是硬性限制权重范围；量化正是通过每行自己的 absmax 和 scale 适应不同权重范围。

### 2. 从“不理解 where”到理解零行保护
最初没有看懂：
```
scale = torch.where(
    scale == 0,
    torch.ones_like(scale),
    scale,
)
```
后来明确它是逐元素三元选择：
- `scale == 0` 的位置，从全 1 张量中取 1；
- 其他位置保留原 scale；
- `ones_like()` 会保持相同的形状、dtype 和设备；
- 零行使用 scale=1 后，量化与反量化仍然都是 0，不会除零。

### 3. 从两行链式代码到理解量化顺序
```
quantized = torch.round(weight / scale)
quantized = quantized.clamp(-127, 127).to(torch.int8)
```

```
weight / scale 每行按自己的标尺缩放

torch.round() 四舍五入到整数位置

clamp(-127, 127) 范围保护

to(torch.int8) 最后才改变实际存储 dtype
```

### 4. 从“替换整个层？”到只替换 Linear 投影
最初疑惑：TransformerBlock 的 forward 明明做了很多事情，为什么 QuantizedLinear 里只有一句 `F.linear()`？
后来确认，替换的是 GQA 内部这类线性投影：
```
self.W_query = nn.Linear(emb_dim, emb_dim)
```
不是替换整个 GQA，也不是替换 TransformerBlock。外层的 RoPE、掩码、softmax、残差等逻辑都不变。
`nn.Linear.forward()` 的核心本来就是 `F.linear(x, weight, bias)`。量化层只改变权重来源：INT8 / INT4 存储先反量化，再完成相同的线性计算。

### 5. bias、detach、clone 与 Parameter / buffer
最初担心原 Linear 的 `bias=cfg["qkv_bias"]` 在替换后丢失。
后来明确：配置只在创建原 Linear 时使用；替换时直接检查 `linear.bias`，有就复制，没有就保留 None。因此 Q/K/V 有 bias、`out_proj` 无 bias 的差异可以逐层保留。
复制 bias 时：
```
linear.bias.detach().clone()
```
- `detach()`：断开自动求导关系；
- `clone()`：复制独立的数据存储，不与旧模块共用；
- 权重只需 detach，是因为量化计算本身会生成新的 INT8 张量和 scale。
也理解了为什么量化权重与 scale 使用 `register_buffer()`：PTQ 是训练后转换，推理不需要通过梯度学习它们。buffer 仍会跟随设备迁移并进入持久状态。
`nn.Parameter` 本身不会自动导致梯度下降；是否更新仍取决于 backward 和 optimizer。原始 FP32 权重在推理时也可以仍是 Parameter。

### 6. 从 parameters 与 state_dict 的模糊到发现统计 Bug
最初不清楚二者区别：
- `model.parameters()`：遍历需要训练的 `nn.Parameter`，主要交给优化器；
- `model.state_dict()`：返回名称到持久张量的字典，包含 Parameter 和持久 buffer，主要用于保存与恢复。
量化后，INT8 权重与 scale 都是 buffer，只用 `parameters()` 会漏掉它们。

第一版真实 Qwen 探针还暴露了共享权重去重问题：默认 `state_dict()` 返回的张量表示可能具有不同 Python `id`，即使模型里的 embedding 与 `out_head` 仍共享权重，也可能被重复统计。
修正为：
```
model.state_dict(keep_vars=True)
```
保留原 Parameter 对象身份后再去重，才得到可信的持久张量规模。这个修正只影响统计，不改变模型计算。

### 7. 理解 PPL 与 A32
PPL 就是 Perplexity，即困惑度：
```
PPL = exp(cross_entropy_loss)
```
它衡量相同数据、相同 tokenizer 下的 next-token 预测，越低通常越好，但不能代替所有任务能力评测。
也理解了量化标记：
```
W8A32 = INT8 权重 + FP32 激活
W4A32 = INT4 权重 + FP32 激活
W8A16 = INT8 权重 + FP16 / BF16 激活
W4A16 = INT4 权重 + FP16 / BF16 激活
```
A 是前向中的中间激活张量，不是激活函数。

### 8. INT8 真实 Qwen 对照
在真实 Qwen2.5-0.5B-Instruct 上，共替换 168 个 Transformer 内部 Linear，保留 `out_head` 和 embedding 权重绑定。

| 指标 | FP32 → INT8 |
| --- | ---: |
| 持久张量规模 | 1976.13 MB → 903.87 MB |
| 存储减少 | 54.26% |
| 压缩倍率 | 约 2.19 倍 |
| Heldout PPL | 69.294 → 69.540 |
| PPL 变化 | 上升约 0.354% |
| TTFT 中位数 | 32.62 ms → 61.29 ms |
| Decode 吞吐中位数 | 53.61 → 20.33 tokens/s |

本次输入的 top-1 token 保持一致，但生成文本存在少量差异。
INT8 减少了存储与当前分配内存，却因每次前向都反量化并使用 FP32 `F.linear` 而明显变慢。decode 吞吐只剩当前 FP32 对照的约 37.92%。
PPL 使用 `blog_v1` heldout 的 5120 个 token；质量结论只限这份数据。性能数字与此前 I3-0 使用不同 prompt 和运行批次，不跨批次混用。

### 9. 从“不知道一个 byte 存了什么”到理解 INT4 packing
最初的盲点是：把一个 INT8 拆成两个 INT4 后，分别存了什么？
后来确认，不是拆分一个已有的 INT8 权重，而是：
```text
两个不同的 FP32 权重
→ 分别量化成两个 INT4 量化码
→ 一个放低 4 位，另一个放高 4 位
→ 合并进一个 byte
```
合并与拆分分别是：
```python
packed = low | (high << 4)

low = packed & 0x0F
high = (packed >> 4) & 0x0F

```
`torch.stack([low, high], dim=-1)` 再 reshape，是为了把“所有低位值”和“所有高位值”恢复成原来的交替顺序。
4-bit 补码中的 `8～15` 表示 `-8～-1`，所以解包后对大于等于 8 的值减 16。
奇数列会补一个约定的 0。最后一个真实值放在最后一个 byte 的低 4 位，高 4 位为补齐码。原始 `in_features` 必须额外保存，因为仅凭 packed byte 数无法区分原始 5 列还是 6 列；解包后用它去掉补齐码。

由此也理解了：
- `in_features`：原始权重每行有多少列，也是输入特征数；
- `out_features`：权重有多少行，也是输出特征数；
- INT8 可以从量化矩阵形状直接得到 `in_features`；
- INT4 打包后必须从原 Linear 显式保存 `linear.in_features`。
当前对 pack / unpack 的原理已经大致理解，具体位运算实现仍标记为后续复盘，不把“大概看懂”写成完全掌握。

### 10. INT4 真实 Qwen 对照

| 指标           |            FP32 → INT4 |
| ------------ | ---------------------: |
| 持久张量规模       | 1976.13 MB → 724.95 MB |
| 存储减少         |                 63.31% |
| 压缩倍率         |               约 2.73 倍 |
| Heldout PPL  |       69.294 → 159.215 |
| PPL 变化       |            上升约 129.77% |
| TTFT 中位数     |   29.41 ms → 114.70 ms |
| Decode 吞吐中位数 |  53.03 → 9.83 tokens/s |
INT4 的最大 logit 差异达到 12.036，平均差异 2.331；本次 prompt 的 top-1 token 已改变。真实生成中出现偏离问题、语义重复的文本，与 PPL 的明显上升相互印证。

当前 INT4 的 decode 吞吐只剩 FP32 对照的约 18.53%。进一步节约存储的同时，质量损失与解包、反量化成本都显著增加。

这不是“INT4 技术不可用”的普遍结论，而是当前朴素逐行 INT4 实现的真实边界。Group-wise 量化、校准、异常通道处理、QAT 与融合 kernel 均未实现。

## 十、FP16 PPL 异常排查

在 W8A16 实验中，FP16 参考组的 heldout PPL 为 497.58，而 FP32 参考组为 69.29；加入 INT8 权重后，FP16 路径 PPL 为 506.21。

随后发现 BF16 参考组 PPL 为 69.23，与 FP32 接近；W8A16（BF16）为 69.89。说明当前异常与 FP16 特定路径相关，而不是所有 16-bit 激活都会发生。

曾尝试在 `model.half()` 后将每层 `inv_freq` 恢复为 FP32，但评估结果逐项不变，因此“仅恢复 inv_freq”不能解释或修复当前异常。

随后使用同一小批数据完成了 CPU / MPS 的 FP32、FP16、BF16 对照，并继续定位到 RMSNorm 的 FP16 平方溢出。完整证据、修复和复测结果见第十二节。

## 十一、16-bit 激活对照：区分 FP16、BF16 与量化开销

完成 W8A32 / W4A32 后，继续将激活切换到 16 bit。`model.half()` 的含义是把浮点参数和浮点 buffer 从 FP32 转成 FP16，不是减少参数数量或改变张量形状；整数与布尔张量保持原类型。`model.bfloat16()` 则切换到 BF16。

为避免同时改变两个变量，W8A16 / W4A16 的参考组也必须使用相同的 16-bit 激活，而不能继续拿 FP32 作为唯一对照。

### 1. 同一份 heldout 上的 PPL

所有路径仍使用 `blog_v1` heldout 的 5120 个 token、context=128、batch=4、10 个批次。

| 路径 | 16-bit 参考组 PPL | 量化后 PPL | 相对参考组变化 |
| --- | ---: | ---: | ---: |
| W8A16（FP16） | 497.585 | 506.211 | +1.733% |
| W8A16（BF16） | 69.235 | 69.887 | +0.942% |
| W4A16（BF16） | 69.235 | 161.227 | +132.871% |

BF16 参考组与 FP32 的 69.294 很接近，说明当前 BF16 链路没有出现 FP16 那种大幅偏移。

W4A16（BF16）与 W4A32 的 159.215 很接近，说明当前 INT4 的显著质量损失主要来自低精度权重本身，切换 BF16 激活不能修复。

### 2. W8A16（BF16）真实生成

| 指标 | BF16 参考组 → W8A16 |
| --- | ---: |
| TTFT 中位数 | 25.41 ms → 55.17 ms |
| Decode 吞吐中位数 | 66.25 → 22.89 tokens/s |
| 总耗时中位数 | 0.509 s → 1.455 s |
| 当前分配内存 | 1413.37 MB → 1045.14 MB |

Decode 吞吐只剩参考组的约 34.55%，TTFT 耗时约为参考组的 2.17 倍。BF16 基线本身较快，但当前逐层反量化路径仍然明显变慢。

### 3. W4A16（BF16）真实生成

| 指标 | BF16 参考组 → W4A16 |
| --- | ---: |
| TTFT 中位数 | 25.68 ms → 107.95 ms |
| Decode 吞吐中位数 | 68.29 → 10.60 tokens/s |
| 总耗时中位数 | 0.496 s → 3.131 s |
| 当前分配内存 | 1413.37 MB → 907.25 MB |

Decode 吞吐只剩参考组的约 15.52%，TTFT 耗时约为参考组的 4.20 倍。生成文本仍出现偏离原问题与语义重复，和 PPL 的显著上升一致。

### 4. 当前结论与未完成边界

- 当前教学实现中，权重量化降低了持久存储与当前分配内存，但没有带来推理提速；分解式解包、反量化和浮点 `F.linear` 产生了明显开销。
- INT8 在当前 heldout 上质量损失较小；INT4 在两种激活精度下都出现显著质量损失。
- 本节 16-bit 结果记录的是 RMSNorm 修复前的实验现场；共享修复合入后，相关 BF16 / FP16 结果需要用当前代码重新复测。
- FP16 的 RMSNorm 平方溢出已定位并修复，完整过程见第十二节，不能用此前的 BF16 结果掩盖 FP16 问题。
- 当前报告中的模型规模是去重后的持久张量字节数，不是实际 `.pth` 文件大小。
- CUDA 复测、多任务质量评测、group-wise INT4、校准、QAT 与融合 kernel 仍未完成。
- 投机解码尚未开始；先完成共享修复后的量化复测。

## 十二、FP16 PPL 异常闭环：RMSNorm 的平方溢出

### 1. 先区分设备与 dtype

同一批 128 tokens 的设备 / dtype 探针显示：

- MPS FP32 loss 为 3.73094，MPS BF16 为 3.73438，均正常；
- CPU FP32 为 3.73086，CPU BF16 为 3.73438，与 MPS 接近；
- CPU 与 MPS 的 FP16 logits 绝对值统计一致：`absmax=29.21875`、`mean_abs=2.19140625`，说明 FP16 模型前向偏移不是 MPS 独有；
- CPU FP16 的 cross-entropy loss 为 Infinity，但 logits 全部有限，说明 loss 的 FP16 归约溢出与模型 logits 非有限是两件事。

单批诊断只用于探针内部对照，不与十批评估的 PPL 数字混用。

### 2. 继续检查 RMSNorm 中间值

当前 RMSNorm 原实现使用输入自身 dtype 计算：

```python
mean_square = x.pow(2).mean(dim=-1, keepdim=True)
y = x * torch.rsqrt(mean_square + self.eps) * self.scale
```

逐层 forward hook 发现：FP16 从 `trf_block.3.norm1` 开始，后续各层 norm 与 `final_norm` 的 `mean_square` 持续出现非有限值；FP32 与 BF16 均没有。

第一处异常层的输入绝对值最大值为 619：

```text
619² = 383,161
FP16 最大有限值约为 65,504
```

因此平方在 FP16 下溢出为 `inf`。随后 `rsqrt(inf)=0`，有限输入乘 0 后输出仍可能是有限的 0，所以最终 logits 不一定出现 NaN，但隐藏状态已经失真。这解释了为什么 PPL 大幅上升，却没有直接以模型报错的形式暴露。

### 3. 使用 FP32 累积修复

修复后的 RMSNorm 只在内部转换为 FP32 完成平方、均值和归一化，输出再转回输入 dtype：

```python
def forward(self, x):
    input_dtype = x.dtype

    x_float = x.float()
    mean_square = x_float.pow(2).mean(
        dim=-1,
        keepdim=True,
    )
    y = (
        x_float
        * torch.rsqrt(mean_square + self.eps)
        * self.scale.float()
    )

    return y.to(dtype=input_dtype)
```

这样不会把整个模型转回 FP32，后续 Linear 的输入与权重仍保持相同的 FP16 / BF16 类型。

新增回归使用 `619.0` 的 FP16 输入：旧实现会溢出并输出 0，修复后输出有限且为 1，同时保持 FP16 dtype。用户运行该回归及相关 RoPE、推理基线、量化模块和真实 Qwen cache 测试，结果为 **10 passed**。

### 4. 复测证明根因与修复一致

修复后重新运行原始 W8A16（FP16）PPL：

```text
FP16 参考组：
loss = 4.23828
PPL  = 69.2887

FP16 + INT8 权重：
loss = 4.24160
PPL  = 69.5191
相对参考组上升约 0.333%
```

FP16 参考组已从修复前的 497.585 降回 69.289，与 FP32 的 69.294 基本一致。由此形成完整闭环：

```text
FP16 中间激活平方溢出
→ RMSNorm 输出失真
→ PPL 大幅上升
→ RMSNorm 改为 FP32 累积
→ FP16 PPL 恢复正常
```

这次排障的重要经验是：**最终输出有限，不代表中间过程没有溢出；某一层输出仍有限，也不代表它的数值语义仍然正确。**

共享 RMSNorm 修复会影响其他 dtype 路径，因此既有 BF16 / FP16 性能与质量结果需要按当前代码重新复测，不能自动沿用到修复后的最终报告。

## 十三、RMSNorm 修复后的 BF16 正式复测

共享 RMSNorm 改为 FP32 累积后，重新运行 BF16 的 PPL 与真实生成，以下结果替代此前修复前数据，作为当前代码的正式对照。

### 1. PPL 复测

| 路径 | BF16 参考组 PPL | 量化后 PPL | 相对参考组变化 |
| --- | ---: | ---: | ---: |
| W8A16（BF16） | 69.560 | 69.887 | +0.470% |
| W4A16（BF16） | 69.560 | 159.224 | +128.902% |

FP32 累积改变了 BF16 参考组的少量数值，但没有改变主要结论：INT8 在当前 heldout 上损失较小，INT4 仍有显著损失。

### 2. W8A16（BF16）生成复测

| 指标 | BF16 参考组 → W8A16 |
| --- | ---: |
| TTFT 中位数 | 26.29 ms → 56.07 ms |
| Decode 吞吐中位数 | 63.97 → 22.46 tokens/s |
| 总耗时中位数 | 0.526 s → 1.481 s |
| 当前分配内存 | 1413.37 MB → 1045.14 MB |

TTFT 耗时约为参考组的 2.13 倍，decode 吞吐约为参考组的 35.11%。当前实现仍因逐层反量化而明显变慢。

### 3. W4A16（BF16）生成复测

| 指标 | BF16 参考组 → W4A16 |
| --- | ---: |
| TTFT 中位数 | 26.30 ms → 109.09 ms |
| Decode 吞吐中位数 | 63.72 → 10.57 tokens/s |
| 总耗时中位数 | 0.529 s → 3.140 s |
| 当前分配内存 | 1413.37 MB → 907.25 MB |

TTFT 耗时约为参考组的 4.15 倍，decode 吞吐约为参考组的 16.59%。INT4 生成文本仍存在明显语义偏移，与 PPL 大幅上升一致。

这些数字来自用户在同一 Mac / MPS、同一 prompt、1 次 warmup、3 次正式测量下的实际运行。不同实验批次的中位数不与其他日期或其他 prompt 的结果混用。

## 十四、修复后的 FP16 生成对照

RMSNorm 修复后，继续补测 W8A16（FP16）的真实生成，确认不仅 PPL 恢复，生成路径也不再受平方溢出影响。

| 指标 | FP16 参考组 → W8A16（FP16） |
| --- | ---: |
| TTFT 中位数 | 26.19 ms → 56.44 ms |
| Decode 吞吐中位数 | 63.28 → 22.64 tokens/s |
| 总耗时中位数 | 0.533 s → 1.471 s |
| 当前分配内存 | 1413.37 MB → 1045.14 MB |

TTFT 耗时约为参考组的 2.16 倍，decode 吞吐约为参考组的 35.77%。结果与 BF16 量化路径相近：存储与当前分配内存下降，但当前分解式反量化实现仍然明显变慢。

FP16 参考组已恢复正常流畅生成；量化组仍有数值和文本差异，但不再出现修复前由 RMSNorm 溢出造成的异常质量路径。

至此，Mac 上已完成 W8A32、W4A32、W8A16 / W4A16（BF16）以及 W8A16（FP16）的当前实验闭环。实际 `.pth` 文件大小、CUDA 复测、多任务质量评测、group-wise INT4 与融合 kernel 仍保留为后续边界。

## 十五、阶段总结：速度、空间、质量与理解是四本账

这篇笔记从一条简单的生成调用出发，最后覆盖了 KV Cache、会话状态、权重量化和数值排障。为了避免细节淹没结论，这里统一收拢实验口径与最终结果。

### 1. 实验口径

- 推理基线使用真实 Qwen2.5-0.5B-Instruct、Mac / MPS、FP32、36 个 prompt tokens、固定生成 32 tokens；cache / no-cache 独立运行三轮并取中位数。
- 会话探针使用相同真实模型和固定多轮输入，分别检查完整重算、会话复用和滑动淘汰；没有测量其 TTFT 收益，不把输入 token 减少比例当作提速比例。
- 量化存储探针替换 168 个 Transformer 内部 Linear，保留 `out_head` 与 embedding 的权重绑定；持久张量通过 `state_dict(keep_vars=True)` 去重统计，不等同于实际 `.pth` 文件大小。
- PPL 使用 `blog_v1` heldout 的 5120 个 token，context=128、batch=4、10 批；PPL 只代表当前语料的 next-token 预测变化。
- 量化生成使用同一 prompt、固定 32 tokens、贪心解码、1 次 warmup、3 次正式测量并取中位数。固定长度测量有意不启用 EOS 提前停止，不将输出中的后续标记解释为正式服务异常。
- MPS 使用 current allocated / driver allocated 快照；没有与 CUDA 相同的峰值接口，不伪造跨设备峰值对照。

### 2. KV Cache 与会话复用的核心结果

- 单次生成中，cache 的 decode 吞吐中位数为 40.26 tokens/s，no-cache 为 23.28 tokens/s，约 **1.73 倍**；两种路径逐 token 输出一致。
- Qwen 当前 FP32 配置的 KV Cache 实测为 **24 KiB/token**；36 个 prompt tokens 对应 864 KiB。4096 tokens 的 96 MiB 是按单位成本推算，不是实测设备峰值。
- 第二轮完整重算需要输入 61 tokens，会话复用后只输入 15 个新增 token，输入减少约 **75.4%**，回答保持一致。
- 真实第三轮滑动中，cache 从 66 裁剪到 34 tokens，淘汰后的 prompt 为 53 tokens，实际只输入 19 个新增 token；位置从 66 继续，生成后推进到 90。
- 会话复用与滑动窗口证明了状态和位置链路的正确性，但没有单独测量性能收益；滑动位置与裁剪细节仍需要后续复盘。

### 3. 量化结果汇总

下表中的参考组随实验路径变化：W32 使用 FP32，A16 使用相同 16-bit 激活参考组。不同批次的 FP32 / BF16 性能中位数不跨实验混用。

| 路径 | 持久张量规模 | PPL：参考 → 量化 | TTFT：参考 → 量化 | Decode：参考 → 量化 |
| --- | ---: | ---: | ---: | ---: |
| W8A32 | 1976.13 → 903.87 MB | 69.294 → 69.540 | 32.62 → 61.29 ms | 53.61 → 20.33 tokens/s |
| W4A32 | 1976.13 → 724.95 MB | 69.294 → 159.215 | 29.41 → 114.70 ms | 53.03 → 9.83 tokens/s |
| W8A16（BF16） | 本轮未重复测量 | 69.560 → 69.887 | 26.29 → 56.07 ms | 63.97 → 22.46 tokens/s |
| W4A16（BF16） | 本轮未重复测量 | 69.560 → 159.224 | 26.30 → 109.09 ms | 63.72 → 10.57 tokens/s |
| W8A16（FP16，修复后） | 本轮未重复测量 | 69.289 → 69.519 | 26.19 → 56.44 ms | 63.28 → 22.64 tokens/s |

由此得到几个有边界的结论：

1. **INT8 在当前 heldout 上质量损失较小**。W8A32 / W8A16 的 PPL 相对各自参考组只有约 0.3%～0.5% 的上升；这不等于所有任务都无损。
2. **当前逐行 INT4 的质量损失显著**。PPL 接近翻倍，top-1 与真实文本均发生变化；不能推广为所有 INT4 方法都如此，因为 group-wise、校准、异常通道处理和 QAT 均未使用。
3. **当前教学实现没有因量化而提速**。每次前向都需要反量化，INT4 还需要解包和符号恢复，随后仍执行浮点 `F.linear`。没有融合低精度 kernel 时，额外开销超过了存储与带宽收益。
4. **持久张量压缩不等于运行时内存按相同比例下降**。设备分配器、激活、临时反量化权重和 KV Cache 都有独立开销。

### 4. FP16 异常给出的额外答案

FP16 参考组最初 PPL 高达 497.585，并不是量化导致，也不是所有 16-bit 激活的普遍现象。

逐层排查最终确认：第 3 层 RMSNorm 输入 absmax 达到 619，平方为 383161，超过 FP16 最大有限值 65504；`mean_square` 溢出为 `inf`，随后 `rsqrt(inf)=0`，隐藏状态被压成有限的 0，因此最终 logits 有限却早已失真。

RMSNorm 改为 FP32 累积、输出再转回原 dtype 后，FP16 参考组 PPL 恢复为 69.289，W8A16 为 69.519；10 项相关回归由用户运行通过，生成路径也恢复正常。

这次排障说明：**最终输出有限，不代表中间过程没有溢出；测试某一层是否能运行，也不等于它的数值语义正确。**

### 5. 当前完成与尚未完成

当前完成的是 I3 前半段的 Mac 学习闭环：

- 推理基线与 KV Cache 实测；
- 多 token 增量 prefill 的 v1 / v2 掩码修复；
- 会话级 cache、token 预算和 v3 滑动链路；
- INT8 / INT4 权重量化、存储、PPL、内存和生成对照；
- FP16 RMSNorm 平方溢出的定位、修复与复测。

仍未完成：

- 投机解码与 SSE / 多会话隔离；
- CUDA 同口径复测；
- 实际量化模型文件大小、多任务质量评测；
- 预分配 KV Cache、group-wise INT4、校准、QAT 与融合 kernel；
- 滑动窗口细节和 INT4 pack / unpack 实现的独立复盘。

测试数字均对应当时明确列出的测试文件与范围，不把不同阶段的 `passed` 数量累加成一次全量回归。功能进度与学习理解也继续保持两本账：跑通的功能可以记录为已验证，尚未吃透的部分仍明确留给后续。
