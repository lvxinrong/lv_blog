+++
title = "手搓 LLM 笔记 23：I4 多轮对话 SFT"
date = 2026-11-16T09:00:00+08:00
draft = false
slug = "llm-23-i4-multiturn-sft"
tags = ["LLM", "I4", "SFT", "多轮对话", "后训练", "学习笔记"]
summary = "从 Assistant-only loss mask、Qwen 多轮模板和 128 条合成样本开始，完成全参数 SFT、独立行为评测与训练量干预。记录 v1 能力回退、v2 恢复，以及 loss 与行为表现不一致的真实证据。"
[cover]
    image = "covers/llm-23-i4-multiturn-sft.jpg"
    alt = "手搓 LLM 笔记 23：I4 多轮对话 SFT"
    hiddenInList = true
    hiddenInSingle = true
+++

这篇记录的是 **I4-B：多轮对话 SFT 的最小完整闭环**，不是整个 I4 的收官。CoT-SFT、DPO、GRPO、LoRA 与全参对照尚未开始。

这一轮最有价值的地方，不只是最后得到了一个当前最佳 checkpoint，而是第一次完整看见：

```text
多轮数据如何变成训练目标
→ SFT 如何改变模型行为
→ 新能力习得为什么会伤害旧能力
→ 为什么不能只看训练 loss 判断后训练效果
```

## 一、实验目标与边界

本轮使用 **Qwen3-0.6B Instruct**，从我们独立实现的 V4 加载、训练和生成。实验设备为 MacBook M4 Pro，实际运行后端为 MPS，权重和训练使用 FP32。

第一版只研究非 CoT 的多轮行为：

- 名字与偏好记忆；
- 根据新信息更新旧数值；
- 简单算术；
- 按指定格式输出；
- 自然结束，不复制上一轮回答。

这不是开放域对话训练。训练数据是受控合成数据，行为评测也只有 6 条固定基线和 32 条独立验证样本。所有结论都限定在这个范围内。

## 二、先弄清楚：多轮样本到底监督什么

### 1. `-100` 与 `-torch.inf` 不是一回事

M4 的单轮 SFT 已经使用过 `ignore_index=-100`，但这次重新读代码时，我发现自己仍然容易把它和注意力中的 `-torch.inf` 混在一起。

```text
target = -100
→ 这个位置的预测不计入 loss
→ 输入 token 仍然存在，仍可被后续位置读取

attn_score = -torch.inf
→ 经 softmax 后注意力概率为 0
→ 这条注意力连接被切断
```

所以，User 不参与 loss，不代表模型看不到 User。模型仍然读取完整问题和历史，只是我们不要求它学习生成 User 的提问。

### 2. 为什么 `targets[:P - 1]` 而不是 `targets[:P]`

假设：

```text
full:    [p0, p1, p2, r0, r1, EOS]
inputs:  [p0, p1, p2, r0, r1]
targets: [p1, p2, r0, r1, EOS]
```

`targets[i] = full[i + 1]`。当 prompt 长度 `P=3` 时，必须保留 `targets[2] = r0`，否则第一个回答 token 就没有监督。

这也解释了为什么 Full 中的 Assistant 区间不能直接当作 target 下标：

```text
full[29:35]  → targets[28:34]
full[53:59]  → targets[52:58]
```

### 3. 多轮 Assistant 都应该监督，User 只提供上下文

本轮使用 Assistant-only SFT：

```text
System：上下文，不计 loss
User：上下文，不计 loss
Assistant 角色头：上下文，不计 loss
Assistant 正文：计 loss
Assistant 的 <|im_end|>：计 loss
```

`<|im_start|>assistant` 是模板提供的答题区，不需要模型自己生成；`<|im_end|>` 是模型回答结束后需要生成的动作，必须参与训练。

多轮样本里会出现多个 `<|im_end|>`。System 和 User 的结束标记与 Assistant 的结束标记虽然 token id 相同，但职责不同，不能只保留整个序列中的第一个 EOS。

## 三、把真实 Qwen 模板变成 Dataset

### 1. 模板探针

我们首先用两轮对话检查真实渲染结果，而不是凭感觉拼字符串。固定样例渲染后共有 60 个 token，两轮 Assistant 的 Full 区间为：

```text
第一轮：full[29:35]
第二轮：full[53:59]
```

第二轮还包含一个空的 `<think>...</think>` 区域。当前非 CoT 数据契约中，空 think 区域只作为上下文，不参与 loss；两轮 Assistant 正文及各自的 `<|im_end|>` 参与 loss。

### 2. 核心掩码构造函数

`src/squid/data/chat_sft.py` 中，区间统一使用 Full 下标、右端不取：

```python
def build_assistant_targets(full_ids, assistant_spans, ignore_index=-100):
    if not full_ids:
        raise ValueError("full_ids 不能为空")

    targets = [ignore_index] * (len(full_ids) - 1)

    for start, end in assistant_spans:
        if start < 1 or end > len(full_ids) or start >= end:
            raise ValueError(
                f"非法 Assistant 区间：[{start}, {end})"
            )

        targets[start - 1:end - 1] = full_ids[start:end]

    return targets
```

### 3. 不写死区间，用前缀编码定位

`find_assistant_spans()` 在渲染文本中顺序定位每轮 Assistant 正文及 `<|im_end|>`，再分别编码正文前和结束标记后的前缀，得到 token 下标，并断言前缀编码与 `full_ids` 完全一致。

```python
start_ids = tokenizer.encode(
    full_text[:content_start],
    add_special_tokens=False,
)
end_ids = tokenizer.encode(
    full_text[:end_char],
    add_special_tokens=False,
)

assert start_ids == full_ids[:len(start_ids)]
assert end_ids == full_ids[:len(end_ids)]
```

这样避免把某组固定样例的下标硬编码进 Dataset，也避免简单搜索 token id 时误切正文。

`encode_qwen_multiturn()` 将真实模板、区间定位和 target 构造接起来：

```python
def encode_qwen_multiturn(tokenizer, messages):
    full_text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=False,
    )
    encoded = tokenizer.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=False,
    )

    full_ids = encoded["input_ids"]
    if full_ids and isinstance(full_ids[0], list):
        full_ids = full_ids[0]

    spans = find_assistant_spans(
        tokenizer, messages, full_text, full_ids
    )
    targets = build_assistant_targets(full_ids, spans)

    return full_ids[:-1], targets
```

### 4. Batch padding

inputs 使用 EOS/pad id 补齐，targets 使用 `-100` 补齐，不额外追加 EOS，因为每轮 Assistant 已经包含自己的 `<|im_end|>`：

```python
def qwen_multiturn_collate(batch, pad_token_id, ignore_index=-100):
    max_len = max(len(inputs) for inputs, _ in batch)
    input_batch = []
    target_batch = []

    for inputs, targets in batch:
        input_ids = torch.tensor(inputs, dtype=torch.long)
        target_ids = torch.tensor(targets, dtype=torch.long)

        input_batch.append(
            pad_to_length(input_ids, max_len, pad_token_id)
        )
        target_batch.append(
            pad_to_length(target_ids, max_len, ignore_index)
        )

    return torch.stack(input_batch), torch.stack(target_batch)
```

对应测试按阶段实际运行为 **1 passed、2 passed、3 passed**，分别覆盖掩码错位、真实模板 Dataset 和 Batch padding。这些数字不是一次全量回归。

## 四、冻结行为基线，也修正评测器自己

### 1. 固定基线配置

行为基线使用：

```text
模型：Qwen3-0.6B Instruct
device：mps
dtype：FP32
context_size：8192
max_new_tokens：512
temperature：0.0
enable_thinking：false
```

六条样例覆盖多轮记忆、连续数值更新、算术和格式遵循。

### 2. `expected_contains` 为什么不能判断数值答案

第一版规则只检查回答是否包含 `912`。但：

```python
"912" in "8912"  # True
"912" in "7192"  # True
```

所以数值题改为精确匹配，并单独拆出两个指标：

```text
answer_correct：内容或数值是否正确
format_compliant：是否遵守输出格式
```

例如：

```text
24            → 格式正确，答案错误（期望 30）
123+789=912   → 格式错误，答案正确
912           → 格式和答案都正确
```

评分器新增独立测试，实际运行 **4 passed**；加入复制检测后为 **7 passed**。

### 3. 一个列表共享引用造成的全量误报

32 条评估第一次全部显示 `copy=True`。根因不是模型全都复制，而是：

```text
case["history"] 与 session.history 指向同一个列表
→ session.ask() 把当前回答追加进 history
→ 复制检测读取到刚生成的回答
→ 再与 response 比较，永远相等
```

修复为：

```python
session.history = history.copy()
```

这次错误提醒我：**训练前先验证评测器，训练后也不要把评测器的异常直接归因于模型。**

### 4. 训练前的真实行为

原始模型的六条基线结果为：

```text
passed = 2/6
answer_correct = 4/6
format_compliant = 4/6
copied_previous_assistant = 1
natural_stop = 6/6
```

典型现象包括：

- 苹果已有 24 个，再买 6 个，仍回答 `24`；
- `25 * 24` 错答为 `240`；
- `123 + 789 = 912` 结果正确，但违反“只回答数字”；
- 颜色题直接复制上一轮 Assistant。

## 五、4-step 冒烟：先证明链路，不证明能力

正式数据之前，用 4 条训练样本、2 条验证样本做了 4 个优化步骤：

```text
initial train loss：3.390143
initial val loss：  2.800545
final train loss：  1.958147
final val loss：    1.819232
optimization steps：4
checkpoint reload：passed
```

恢复 checkpoint 后生成两条验证回答：

```text
期望 28 → 生成 28，正常 stop
期望 15 → 生成 6，正常 stop
```

所以冒烟只证明了数据、loss、反向传播、checkpoint 和生成链路可用。第二条答错说明它没有证明模型能力。

## 六、128 + 32 合成数据与隔离审计

正式数据由 GPT 辅助生成，再经过本地审计：

| 类别 | Train | Val |
| --- | ---: | ---: |
| 单轮算术 | 32 | 8 |
| 多轮数值更新 | 32 | 8 |
| 名字记忆 | 32 | 8 |
| 偏好记忆 | 32 | 8 |
| 合计 | **128** | **32** |

隔离要求包括：

- train / val 没有完全重复的对话；
- 同一算术表达式不跨集合；
- 排除行为基线中的小吕、蓝色、3×8+6、25×24、123+789、17+5；
- 避免复用已有 smoke 样例；
- Assistant 不携带 think 或角色标记；
- 每条样本都能通过真实模板编码，并且存在有效监督 token。

分类审计最初把“叫我”“首选爱好”“昵称”等表达误归为数值任务。修正审计规则后，四类数量恢复平衡，全部模板编码通过，train / val 精确重复为 0，排除项检查通过。

这组数据仍然只是受控任务数据，不代表真实多轮语料分布。

## 七、v1：64 steps，loss 很漂亮，行为却出现回退

### 1. 训练配置与 loss

```text
全参数 SFT
batch_size = 4
n_epochs = 2
optimization steps = 64
peak_lr = 1e-5
initial_lr = 1e-6
min_lr = 1e-7
weight_decay = 0
warmup_steps = 6
seed = 123
context_size = 1024
```

结果：

```text
initial train loss：3.797954
initial val loss：  3.745439
final train loss：  0.616244
final full val loss：0.859470
checkpoint reload：passed
```

### 2. 六条基线：从 2/6 到 4/6

v1 的六条基线变为：

```text
passed = 4/6
answer_correct = 4/6
format_compliant = 6/6
copied_previous_assistant = 0
natural_stop = 6/6
```

改善包括：

- 苹果题从 `24` 更新为 `30`；
- `17 + 5` 从完整算式变为只输出 `22`；
- 名字回答变为“你叫小吕”。

但也出现：

```text
25 * 24：240 → 60，仍然错误
123 + 789：结果正确的算式 → 909，数值回退
```

### 3. 32 条独立验证：总通过率提升，名字却明显退化

| 类别 | 原始模型 | SFT v1 |
| --- | ---: | ---: |
| 名字记忆 | 8/8 | **3/8** |
| 数值更新 | 2/8 | **7/8** |
| 偏好记忆 | 7/8 | 7/8 |
| 单轮算术 | 2/8 | **7/8** |
| 总计 | 19/32 | **24/32** |

v1 的格式合规从 24 提升到 31，但内容正确从 25 降为 24。名字类出现“你”“你。”“你记住了”等无效回答。

### 4. 同一训练集上的对照，确认训练引入的回退

为了区分“原本不会”与“训练后改坏”，又比较了原始模型与 v1 在同一 128 条样本上的 `passed`：

| 类别 | 原始模型 | SFT v1 | 净变化 |
| --- | ---: | ---: | --- |
| 名字记忆 | 32/32 | 21/32 | **-11** |
| 偏好记忆 | 32/32 | 28/32 | **-4** |
| 数值更新 | 12/32 | 27/32 | **+15** |
| 单轮算术 | 8/32 | 21/32 | **+13** |
| 总体 | 84/128 | 97/128 | +13 |

原始模型在名字和偏好样本上全部正确，v1 却在相同输入上退化。这不能简单解释为验证集分布不同，而是全参数训练在获得新行为时干扰了旧行为，符合局部灾难性遗忘的表现。

另一个重要事实是：**v1 的最终 train loss 已降到 0.616，但训练集逐条生成仍只有 97/128 综合通过。** 平均 token loss 与行为成功不是同一个指标。

## 八、v2：减少训练量，恢复新旧能力的平衡

### 1. 干预方式与训练结果

在数据、Batch、学习率峰值、随机种子等保持不变的前提下，将 `n_epochs` 从 2 改为 1：

```text
optimization steps = 32
warmup_steps = 3
final train loss = 1.104157
final full val loss = 1.021104
checkpoint reload = passed
```

严格来说，修改 `n_epochs` 后，总步数、warmup 步数和学习率衰减过程都发生了变化。因此这是一组训练量与调度对照，不能把全部差异只归因于 epoch 数。

### 2. 原始模型、v1、v2 的独立验证对照

| 指标 | 原始模型 | v1：2 epochs | v2：1 epoch |
| --- | ---: | ---: | ---: |
| 综合通过 | 19/32 | 24/32 | **30/32** |
| 内容正确 | 25/32 | 24/32 | **30/32** |
| 格式合规 | 24/32 | 31/32 | **31/32** |
| 名字记忆 | 8/8 | 3/8 | **7/8** |
| 数值更新 | 2/8 | 7/8 | **7/8** |
| 偏好记忆 | 7/8 | 7/8 | **8/8** |
| 单轮算术 | 2/8 | 7/8 | **8/8** |

最重要的现象是：**v2 的 val loss 比 v1 更高，行为表现却显著更好。** 这直接说明，不能只凭平均 token loss 判断后训练是否更好。

### 3. 六条冻结基线全部通过

v2 在最初六条基线上的结果为：

```text
passed = 6/6
answer_correct = 6/6
format_compliant = 6/6
copied_previous_assistant = 0
natural_stop = 6/6
empty = 0
```

真实回答为：

```text
名字：小吕。
颜色：蓝色。
苹果更新：30
25 * 24：600
123 + 789：912
17 + 5：22
```

全部自然结束，没有精确复制旧回答。

### 4. v2 仍有两个失败样例

32 条独立验证中仍有两条失败：

- 数值更新第 01 条：期望 `7`，模型只生成 1 个 token 就 EOS，形成空回答；
- 名字记忆第 29 条：期望“小棉”，模型回答“你。”，生成 3 个 token 后停止。

所以 v2 是当前最佳，不是全样本正确，也不是所有行为问题都已解决。

## 九、这一轮得到的结论

### 1. 多轮 SFT 首先是数据契约问题

不是把多轮文本拼起来就算完成。必须明确每轮角色、正文、结束标记和错位 target 的关系，否则模型可能在错误的文本上接受训练。

### 2. 格式行为通常比数值能力更容易学到

v1、v2 都很快提升了“只输出数字”的格式遵循，但算术正确性并未同步提升，部分题目还发生回退。loss 下降不能直接解释为推理能力增强。

### 3. 全参数训练会同时产生收益与干扰

v1 在数值更新和格式上明显收益，却损害了原本稳定的名字与偏好回答。后训练需要同时评估新任务收益和旧能力保持。

### 4. 行为评测必须独立于训练 loss

本轮最关键的证据是：v2 的 val loss 更高，行为却更好。只优化 loss，无法发现这种新旧能力冲突。

### 5. 评测器本身也需要回归测试

contains 误判、格式与正确性混淆、history 共享引用，都曾制造假结论。训练实验必须保留原始回答、评分规则和报告版本，不能只保存一个最终分数。

## 十、当前停止边界

当前只完成 I4-B 的受控多轮 SFT 闭环：

- v2 是本轮最佳 checkpoint；
- 不能据此宣称开放域多轮对话能力；
- 不能据此宣称 1 epoch 普遍优于 2 epochs；
- 尚未完成真实多轮语料、LoRA / 全参对照、CoT-SFT、DPO 或 GRPO；
- 名字和偏好类的核心实体包含规则仍是弱语义评测，后续需要更可靠的评估校准。

下一步进入 I4-C 时，需要先想清楚：

```text
<think> 中的推理过程是否参与 loss？
如何分别定位思考区间与正式回答区间？
thinking 与正文的 token 预算如何计算？
如何判断思考质量，而不只是判断输出格式？
```

这一轮的主干已经搭起来了：**数据契约、训练、checkpoint、独立行为评测、回退分析和干预对照。** 后面新增 CoT、DPO 或其他方法，都应该在这套基线上继续做局部进化。

## 主要实验产物

```text
src/squid/data/chat_sft.py
scripts/i4_qwen_multiturn_template_probe.py
scripts/i4_qwen_multiturn_span_probe.py
scripts/i4_behavior_baseline.py
scripts/i4_synthetic_data_audit.py
scripts/i4_multiturn_sft_train.py
scripts/i4_synthetic_behavior_eval.py

data/reports/i4-qwen3-0_6b-behavior-baseline-v3.json
data/reports/i4-multiturn-sft-v1-training.json
data/reports/i4-multiturn-sft-v2-1epoch-training.json
data/reports/i4-synthetic-val-original.json
data/reports/i4-multiturn-sft-v1-synthetic-val.json
data/reports/i4-multiturn-sft-v2-1epoch-synthetic-val.json
data/reports/i4-multiturn-sft-v2-1epoch-behavior-v3.json

data/model_pth/qwen3/i4-multiturn-sft-v1.pth
data/model_pth/qwen3/i4-multiturn-sft-v2-1epoch.pth
```
