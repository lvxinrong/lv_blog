+++
title = "手搓 LLM 笔记 24：I4 思维链 CoT-SFT"
date = 2026-11-16
draft = false
slug = "llm-24-i4-cot-sft"
tags = ["LLM", "I4", "CoT", "SFT", "思维链", "后训练", "学习笔记"]
summary = "从 CoT 数据契约、Qwen 历史思考剥离和严格格式验收出发，完成 128 + 32 条 CoT 数据审计与三组 peak_lr 对照。记录 CoT 丢失、低学习率恢复、输出长度与推理算式变化，以及最终答案未超过原始模型的边界。"
+++

这篇记录 **I4-C：思维链 CoT-SFT 的受控实验与阶段收官**。它不是“CoT 能力已经解决”的证明，而是一次从数据协议、模板行为、训练干预到行为验收的完整排障。

最后得到的结论并不只是“哪个学习率最好”，而是：

```text
原始模型已经会生成 CoT
→ 全参数 SFT 在不同 peak_lr 下产生不同程度的行为破坏
→ 低学习率版本保留并改善了一部分行为
→ 但最终答案正确率仍没有整体超过原始模型
```

## 一、实验目标与基线

本轮继续使用 **Qwen3-0.6B Instruct**，从原始权重开始。实际运行环境为 MacBook M4 Pro、MPS、FP32。

实验问题不是“模型能不能显示 `<think>`”，而是：

- 简短、正确的 CoT 数据能否改善推理表达；
- 最终答案与思考结构能否同时保持；
- 不同 peak_lr 会如何影响原生 CoT 行为；
- 训练后是否变得更短、更可靠，还是只是 loss 更低。

第一版 CoT 行为基线使用 32 条独立验证样本，分别统计：

```text
answer_correct：最终数字是否正确
format_compliant：是否以 <think> 开始，恰好一对标签、非空推理、纯数字答案，且推理不是答案复读
finish_reason：自然结束还是长度截断
```

原始模型的基线结果为：

```text
answer_correct = 30/32
format_compliant = 32/32
passed = 30/32
empty = 0
natural_stop = 32/32
```

原始模型已经具备完整 CoT 输出能力，主要问题是思考偏长、存在自我怀疑，以及少量算术和推理错误。

## 二、CoT 数据契约：监督完整 Assistant 输出

### 1. 思考标签也属于训练目标

本轮选择监督完整 Assistant 输出，而不是只监督最终答案：

```text
<think>
简短、正确的推理
</think>
最终答案
<|im_end|>
```

在固定探针中，Full 下标为：

```text
31～33：Assistant 角色头
34：    <think>
36～87：推理正文
88：    </think>
90～92：最终答案 600
93：    <|im_end|>
```

因此：

```text
full[34:94] → targets[33:93]
```

Assistant 角色头、System 和 User 不计 loss；思考标签、推理正文、最终答案和 `<|im_end|>` 都参与 loss。

这样训练的是完整输出协议：开始思考、进行推理、结束思考、给出答案、正常结束，而不是只学习答案格式。

### 2. 多轮 CoT 的一个真实兼容问题

GPT 辅助生成数据后，发现了一个系统性问题：**Qwen 模板会剥离历史 Assistant 的思考过程，只保留最终答案。**

例如原始数据是：

```text
Assistant 1：<think>12 × 16 = 192。</think>192
User 2：补货后变为 3 倍
Assistant 2：<think>192 × 3 = 576。</think>576
```

模板实际保留的是：

```text
历史 Assistant：192
最后一轮 Assistant：完整 CoT + 576
```

第一版 `find_assistant_spans()` 直接拿原始完整 CoT 去渲染文本中查找，必然找不到。受影响的正好是 64 条 train + 16 条 val，共 80 条多轮样本。

最终没有修改数据，也没有强行改变 Qwen 模板，而是遵循“模板实际显示什么，就监督什么”：

```python
def get_assistant_visible_content(messages, index):
    content = messages[index]["content"].lstrip("\n")

    if index == len(messages) - 1 or "</think>" not in content:
        return content

    return content.split("</think>")[-1].lstrip("\n")
```

这样历史 Assistant 只监督最终答案和 `<|im_end|>`，最后一轮继续监督完整 CoT。新增回归后达到 **5 passed**，同时覆盖原有非 CoT 行为与多轮 CoT 可见性。

这也是训练与推理保持一致的重要原则：不为了保留思考而制造一套与真实调用不同的模板。

## 三、128 + 32 条 CoT 数据审计

正式数据分为两类：

| 类别 | Train | Val |
| --- | ---: | ---: |
| 单轮算术 | 64 | 16 |
| 多轮数值更新 | 64 | 16 |
| 合计 | **128** | **32** |

每条 Assistant 使用 1～3 行简短推理，最终答案为纯数字。数据审计实际覆盖：

- JSON、角色顺序和类别比例；
- 每个 Assistant 恰好一对 think 标签；
- 推理与最终答案非空，答案为纯数字；
- train / val 无完全重复对话；
- train / val 无重复显式算式；
- 与 smoke、非 CoT 数据无重复显式算式；
- 排除行为基线中的名字、颜色和指定表达式；
- **272 条显式算式重新核算**；
- 全部 160 条样本通过真实模板编码，修复后的历史 CoT 与最后一轮 CoT 均可定位。

本地 `i4_cot_data_audit.py` 最终输出：

```text
train equations checked: 218
val equations checked: 54
total equations checked: 272
train / val exact overlap: 0
train / val expression overlap: 0
existing-data expression overlap: 0
全部 CoT 数据审计通过
```

算式解析只能覆盖明确写成“数字 + 运算符 + 数字”的部分，不能代替全部自然语言推理质量评估。

## 四、训练前的两个关键对照

### 1. 原始模型与上一轮非 CoT v2

在开启 thinking 后，上一轮非 CoT SFT 的最佳版本出现了明显的行为变化：

| 指标 | 原始模型 | 非 CoT v2 |
| --- | ---: | ---: |
| 最终答案正确 | 30/32 | 10/32 |
| 完整 CoT 格式 | 32/32 | 0/32 |
| 综合通过 | 30/32 | 0/32 |

这说明非 CoT SFT 对 thinking 行为存在明显干扰。因此，本轮从原始权重开始，不把“恢复被破坏的 thinking”和“学习短 CoT”混成同一个实验。

### 2. 评分脚本也需要先修正

第一次评估时，`expected` 是完整的 `<think>...</think>` 加答案，却拿去与模型的纯数字答案做 `expected_exact` 比较，导致所有样本被误判为答案错误。

修正为：

```python
expected_answer = split_cot_response(expected)[1]
```

并分别保存完整期望输出与最终期望数字。修正后，原始模型的 30 条正确答案才被正确计入。

这再次说明：**先验收评测器，再比较模型。**

## 五、三组训练与行为结果

三组都使用原始权重、128 条训练样本、32 条验证样本、`batch_size=4`、`n_epochs=1`、32 steps、seed=123。

报告核对后，三版的 `initial_lr` 与 `min_lr` 实际均为 `1e-6` 和 `1e-7`，并非整体按比例缩放。因此，本实验应理解为 **peak_lr 与后续调度路径的对照**，不声称其他调度参数完全相同。

| 版本 | peak_lr | final full val loss | 答案正确 | 完整 CoT | 综合通过 |
| --- | ---: | ---: | ---: | ---: | ---: |
| v1 | 1e-5 | **0.807683** | 6/32 | 0/32 | 0/32 |
| v2 | 1e-6 | 1.159451 | **29/32** | **32/32** | **29/32** |
| v3 | 3e-6 | 1.037620 | 18/32 | **1/32** | **1/32** |

### 1. v1：低 loss，但 CoT 直接丢失

v1 的训练结果很漂亮：

```text
initial train loss = 2.670255
final train loss = 0.822201
final full val loss = 0.807683
```

但行为上：

- 32 条样本全部没有完整 CoT；
- 最终答案只剩 6 条正确；
- 两组回答重复到长度上限；
- 训练原题上，原始模型 4/4 正确且完整 CoT，v1 只剩 1/4 正确、0/4 完整 CoT。

所以它不是简单的验证集泛化失败，而是训练直接引入了 CoT 行为干扰。

### 2. v2：降低 peak_lr 后，CoT 恢复并出现局部收益

将 `peak_lr` 降到 `1e-6` 后：

```text
final train loss = 1.140148
final full val loss = 1.159451
```

行为结果为：

```text
answer_correct = 29/32
format_compliant = 32/32
passed = 29/32
natural_stop = 32/32
```

分类表现：

| 类别 | 原始模型 | v2 |
| --- | ---: | ---: |
| 数值更新 | 15/16 | **16/16** |
| 单轮算术 | 15/16 | 13/16 |

v2 的数值更新超过原始模型，但单轮算术和总体正确率仍未超过原始模型。因此它是**当前 SFT 干预中破坏最小、存在局部收益的 checkpoint**，不是全面优于原始模型的 checkpoint。

### 3. v3：中间学习率再次出现结构性退化

将 `peak_lr` 调到 `3e-6` 后，最终答案为 18/32，严格有效 CoT 只剩 1/32。

主要问题包括：

- 前置乱码或无关数字；
- 空思考；
- 思考标签与答案交错；
- 最终答案与中间结果不一致；
- 数值更新行为明显失稳。

v3 的 `format_compliant=1` 使用收紧后的格式定义重新计算，不能把早期宽松检查中的 28 条标签出现当作有效 CoT。

## 六、严格格式验收：出现标签不等于有效 CoT

早期格式检查只要求有一对标签、非空推理和最终答案，导致“前置垃圾数字”和“答案复读”也被判为合格。

最终收紧为：

```python
def has_complete_cot_format(response):
    stripped = response.strip()
    if not stripped.startswith("<think>"):
        return False

    reasoning, final_answer = split_cot_response(stripped)

    return (
        response.count("<think>") == 1
        and response.count("</think>") == 1
        and bool(reasoning)
        and bool(final_answer)
        and reasoning != final_answer
    )
```

这要求：

- 必须以 `<think>` 开始；
- 恰好一对标签；
- 推理与答案都非空；
- 推理不能只是答案复读；
- 最终答案仍需通过纯数字格式检查。

原始模型与 v2 在新定义下仍为 32/32；v3 从宽松的 28 条降为严格的 1 条。这说明**短输出和出现标签都不能代替有效结构验收**。

## 七、输出长度与推理算式变化

进一步比较原始模型与 v2：

| 指标 | 原始模型 | v2：peak_lr=1e-6 | 变化 |
| --- | ---: | ---: | ---: |
| 平均生成 tokens | 163.1 | 139.4 | **缩短约 14.5%** |
| 中位生成 tokens | 146 | 120 | **缩短约 17.8%** |
| 最大生成 tokens | 430 | 278 | **缩短约 35.3%** |
| 推理算式错误 | 2 条 | **0 条** | 当前检查中消除 |

v2 的确不只是“保住原模型”，它确实带来了输出变短和显式推理算式改善。

但 `reasoning equation errors=0` 只说明正则识别出的算式计算正确，不代表整段推理逻辑和最终答案一定正确。v2 仍有 3 条最终答案错误，仍存在自我怀疑、过程混乱和前后不一致。

## 八、loss 与行为表现再次不一致

v1 的 val loss 最低，却只有 6/32 正确答案且完全丢失 CoT；v2 的 val loss 更高，却有 29/32 正确答案和完整 CoT。

这与 I4-B 的结论一致：

> **平均 token loss 下降，不等于目标行为变好；训练拟合程度更强，也不等于旧能力保留得更好。**

后训练必须同时评估：

```text
训练与验证 loss
最终答案正确性
输出结构完整性
推理过程质量
旧能力保持情况
```

## 九、阶段结论

本轮可以确认：

- CoT 的标签、推理正文和最终答案都能进入训练目标；
- Qwen 历史 Assistant 的 CoT 会被模板剥离，Dataset 必须按可见内容定位；
- peak_lr 对 CoT 行为有显著影响，高学习率下可能出现格式丢失和结构性退化；
- LR=1e-6 的版本保留了完整 CoT，并改善数值更新、输出长度和显式推理算式；
- 但最终答案正确率没有整体超过原始模型，不能宣称 CoT-SFT 已全面提升能力。

因此，如果优先追求最终答案正确率，**原始模型仍然更合适**；如果研究如何以较小破坏获得局部行为收益，v2 才具有对照价值。

## 十、阶段收官与下一步

I4-C 按受控实验阶段收官，保留以下未解决问题：

- 最终答案准确率尚未整体超过原始模型；
- 推理仍然偏长，自我怀疑并未完全消失；
- 推理算式检查不能覆盖完整语义质量；
- 尚未评估更大数据集、真实任务或其他模型规模；
- 尚未开始 DPO / GRPO。

下一步进入 I4-D 时，将重点研究偏好数据：

```text
Chosen：简短、正确、结构完整的 CoT
Rejected：冗长、自我怀疑、算式错误、结构混乱或重复的回答
```

DPO 的目标是学习偏好差异，而不是简单模仿标准答案。它是否能在保留最终答案能力的同时改善表达，需要重新建立基线和能力保持评测，不能当成自动修复工具。

## 主要实验产物

```text
src/squid/data/chat_sft.py
scripts/i4_cot_template_probe.py
scripts/i4_cot_data_audit.py
scripts/i4_cot_target_probe.py
scripts/i4_cot_sft_train.py
scripts/i4_cot_behavior_eval.py

data/reports/i4-cot-original-baseline.json
data/reports/i4-cot-v2-baseline.json
data/reports/i4-cot-sft-v1-training.json
data/reports/i4-cot-sft-v2-lr1e-6-training.json
data/reports/i4-cot-sft-v3-lr3e-6-training.json
data/reports/i4-cot-sft-v1-behavior.json
data/reports/i4-cot-sft-v2-lr1e-6-behavior.json
data/reports/i4-cot-sft-v3-lr3e-6-behavior.json

data/model_pth/qwen3/i4-cot-sft-v1.pth
data/model_pth/qwen3/i4-cot-sft-v2-lr1e-6.pth
data/model_pth/qwen3/i4-cot-sft-v3-lr3e-6.pth
```
