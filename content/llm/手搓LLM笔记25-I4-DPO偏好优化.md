+++
title = "手搓 LLM 笔记 25：I4 DPO 偏好优化"
date = 2026-11-16T15:00:00+08:00
draft = false
slug = "llm-25-i4-dpo-preference"
tags = ["LLM", "I4", "DPO", "偏好优化", "CoT", "后训练", "学习笔记"]
summary = "DPO 起步实录：理解 chosen / rejected、序列 logprob、参考模型、score 与 loss，完成偏好数据、模板编码审计和单步更新。记录梯度裁剪对 Adam 整体缩放不敏感，以及 LR=1e-7 的温和更新；批量 DPO 训练尚未开始。"
[cover]
    image = "covers/llm-25-i4-dpo-preference.jpg"
    alt = "手搓 LLM 笔记 25：I4 DPO 偏好优化"
    hiddenInList = true
    hiddenInSingle = true
+++

今天先停在 **DPO 小批量训练之前**。

这一阶段没有把 DPO 当成一个需要马上跑通的训练脚本，而是先拆开它最基本的概念和计算链路：什么是 chosen / rejected，怎样计算一段输出的 logprob，参考模型起什么作用，score 和 loss 如何产生，以及一次真实更新为什么会过于激进。

当前状态是：**DPO 概念、偏好数据、模板编码和单步验证已完成；批量训练、checkpoint 和训练后的行为评估尚未开始。**

## 一、SFT 与 DPO：模仿答案，还是学习偏好

SFT 的目标比较直接：给模型一个标准回答，让它学习怎样生成。

DPO（Direct Preference Optimization）关注的是同一个 Prompt 下两个回答的相对关系：

```text
Chosen：希望模型更倾向的回答
Rejected：希望模型少倾向的回答
```

Rejected 不一定是绝对错误，也可能只是没有 Chosen 好。例如两个答案都正确，但一个简洁、一个啰嗦。DPO 不是给所有场景规定两个绝对方向，而是学习**同一个 Prompt 下的相对偏好**。

本轮的起点和参考模型都使用原始 Qwen3-0.6B Instruct。这样可以从原生 CoT 能力出发，研究“简短、正确、结构完整”的回答偏好，而不是先修复上一轮 SFT 造成的行为退化。

## 二、偏好数据长什么样

第一版偏好探针使用：

```json
{
  "messages": [
    {"role": "system", "content": "你是一个乐于助人的 AI 助手。"},
    {"role": "user", "content": "37 × 6 等于多少？请简短推理并给出最终数字。"}
  ],
  "chosen": "<think>\n30 × 6 = 180，7 × 6 = 42。\n180 + 42 = 222。\n</think>\n\n222",
  "rejected": "<think>\n让我先想一下……</think>\n\n226"
}
```

`messages` 负责提供上下文，chosen / rejected 是候选 Assistant 输出。计算序列概率时，只累计候选输出中目标 token 的 logprob，不把 Prompt 当作需要生成的答案。

## 三、序列 logprob：模型怎样给一段回答打分

对一段 Assistant 输出：

```text
log p(token₁, token₂, ..., tokenₙ)
= 每个目标 token 的 log 概率之和
```

logprob 越接近 0，模型分配的序列概率越高；越负，概率越低。长回答通常也会累积更大的负值，因此不能只凭总 logprob 判断回答质量。

本轮原始探针得到：

| 输出 | 序列 logprob | Token 数 | 平均每 token logprob |
| --- | ---: | ---: | ---: |
| Chosen | -46.830143 | 41 | -1.142199 |
| Rejected | -152.992218 | 74 | -2.067462 |

差值为：

```text
-46.830143 - (-152.992218) = +106.162075
```

这表示原始模型给 Chosen 的序列概率更高，不是“好 106%”。同时，这个探针里原始模型本来就很偏好 Chosen，因此它适合演示计算，但未必能提供很强的训练信号。

核心计算使用：

```python
with torch.set_grad_enabled(require_grad):
    logits = model(inputs)
    log_probs = torch.log_softmax(logits, dim=-1)
    token_logprobs = log_probs.gather(
        -1,
        safe_targets.unsqueeze(-1),
    ).squeeze(-1)

    mask = targets != -100
    total = (token_logprobs * mask).sum()
```

`targets` 必须和 `inputs` 一样保留 Batch 维度，否则 gather 时会出现维度错误。

## 四、参考模型与 DPO loss

DPO 真正优化的不是简单的 `chosen - rejected`，而是当前模型相对参考模型的偏好变化：

```text
score =
  (policy_chosen_logprob - reference_chosen_logprob)
  -
  (policy_rejected_logprob - reference_rejected_logprob)
```

损失形式为：

```text
loss = -log sigmoid(β × score)
```

训练刚开始时，policy 和 reference 使用同一份权重：

```text
score = 0
loss = -log sigmoid(0) = ln 2 ≈ 0.693147
```

本轮 `beta=0.1` 时，探针实际得到：

```json
{
  "score": 0.0,
  "loss": 0.6931471824645996
}
```

这验证了 DPO 初始计算链路。参考模型的作用是提供一个锚点，避免只追求偏好差值而把模型推得太远。

### 指标复盘：我的理解与需要保留的边界

在真正开始批量训练前，我又把 DPO 中几个容易混淆的指标从头过了一遍。这里同时记录最初的直觉和修正后的理解，避免只保留最后一句定义。

#### 1. token 概率不是 logits，sequence_logprob 也不是字符串距离

模型在每个位置先返回整个词表的 logits。它们是原始打分，有正有负，也不要求总和为 1：

```text
logits
→ softmax：整个词表的概率分布
→ log：整个词表的 log 概率分布
→ gather：取目标 token 对应的 logprob
```

如果目标序列是 `a b c`，序列概率不是三个独立概率的乘积，而是：

```text
p(a | prompt)
× p(b | prompt, a)
× p(c | prompt, a, b)
```

取自然对数后，连乘变成连加：

```text
log p(a,b,c)
= ln p(a | prompt)
+ ln p(b | prompt, a)
+ ln p(c | prompt, a, b)
```

我一开始把 sequence_logprob 理解成“生成序列与目标序列的距离”，认为越接近 0 就越接近正确答案。这个理解需要修正：

> **sequence_logprob 是模型给目标序列分配的条件概率的 log 值，不是编辑距离，也不是正确率。**

越接近 0，说明模型越倾向于生成这条目标序列。如果目标本身是错误答案，模型也可能非常自信地错误。只有目标确实是正确回答时，才能进一步解释为对正确答案的倾向增强。

`mean_logprob_per_token` 只是长度归一化后的观察指标，不是 DPO 的优化目标。

#### 2. chosen_minus_rejected 是当前模型的原始偏好差

```text
chosen_minus_rejected
= sequence_logprob(chosen) - sequence_logprob(rejected)
```

也可以写成：

```text
log [p(chosen) / p(rejected)]
```

我的理解是：

- 大于 0：当前模型更倾向 Chosen；
- 小于 0：当前模型更倾向 Rejected；
- 等于 0：两者的序列概率相同；
- 差值的绝对值越大，说明当前模型对两者的概率倾向差异越大。

但它仍然不是质量分：一方面它不代表哪个回答客观上更正确，另一方面序列 logprob 会受回答长度影响，不能把它当成跨样本公平比较的指标。

#### 3. score 是两个模型的偏好差之差

设 A 为训练前的参考模型，B 为训练后的 policy：

```text
policy_chosen = B 给 Chosen 的 sequence_logprob
policy_rejected = B 给 Rejected 的 sequence_logprob
reference_chosen = A 给 Chosen 的 sequence_logprob
reference_rejected = A 给 Rejected 的 sequence_logprob
```

`policy_chosen` 不是 chosen_minus_rejected，而是单独对 Chosen 的序列 logprob 计算。

先分别计算两个模型的原始偏好差：

```text
diff_A = A_chosen - A_rejected
diff_B = B_chosen - B_rejected
```

DPO 的 score 是：

```text
score = diff_B - diff_A
```

展开就是：

```text
(B_chosen - A_chosen)
-
(B_rejected - A_rejected)
```

我最初写成了 `diff_A - diff_B`，虽然“拆开比较两个模型”的思路是对的，但顺序反了，整个符号也会相反。正确方向是**训练后减训练前**。

`score > 0` 表示训练后模型对 Chosen 相对于 Rejected 的偏好优势增强了；`score < 0` 表示这个相对优势减弱了。

但 score 仍不是整体能力分：

- 它不能说明最终答案一定更正确；
- 它不能说明 CoT 格式一定更好；
- 它不能说明其他能力没有被破坏；
- 它也不能单独区分是 Chosen 提高、Rejected 降低，还是两者同时变化。

所以必须继续查看两个候选各自的 logprob 分量。

#### 4. loss 是偏好关系的 logistic loss

```text
loss = -log sigmoid(β × score)
```

在 β 固定时，score 增大，loss 降低；score 减小，loss 升高。

它与 SFT 的 token 级交叉熵不同，优化的是偏好关系。loss 下降说明偏好优化方向符合目标，不代表模型整体能力一定提升。

#### 5. β 是偏好压力旋钮，不是学习率或百分比

我暂时把 β 理解为偏好压力旋钮：

```text
β 较小：偏好压力通常更温和
β 较大：偏好压力通常更强
```

但 β 不是“采用多少比例的更新”，也不是直接乘在参数更新上的 LR。它先把 score 缩放，再进入 sigmoid，影响 loss 的非线性变化和偏好约束强度。

实际更新幅度由 β、score、LR、优化器和梯度裁剪共同决定。

#### 6. grad norm 是梯度向量长度，不是平均梯度

```text
grad norm = sqrt(所有梯度值的平方和)
```

它通常是一次反向传播后，所有可训练参数梯度拼成的长向量的 L2 范数，用来观察整体梯度规模。

流程是：

```text
loss.backward()
→ 计算 grad norm
→ 可选：梯度裁剪
→ optimizer.step()
```

因此要把几个概念分开：

- loss：优化目标；
- β：偏好压力；
- grad norm：梯度规模；
- LR：实际更新步长；
- optimizer：决定梯度如何转换为参数更新。

昨天的实验还说明，整体裁剪梯度不一定能显著改变 Adam 的单步更新；直接降低 LR 才真正缩小了 score 和 logprob 的变化幅度。

#### 7. 现在对整组指标的理解

```text
sequence_logprob：模型给某段输出的序列概率
chosen_minus_rejected：当前模型对两个候选的原始偏好差
score：当前模型相对参考模型的偏好变化
loss：把 score 转成可优化目标
β：偏好压力旋钮
grad norm：反向传播得到的整体梯度规模
```

这些指标都不能单独回答“模型能力是否提升”。最后仍要回到 answer_correct、CoT 格式、输出长度、自然结束和旧能力保持。

## 五、一次真实单步更新：loss 下降不等于能力提升

使用冻结的参考模型和可训练的 policy，执行一次真实的 `loss.backward()` 与 `optimizer.step()`。

在 `peak_lr=1e-6` 时：

```text
before score = 0
before loss = 0.693147
grad norm = 268.085846

after score = 35.349922
after loss = 0.028742
```

更新前后两个候选的序列 logprob 为：

```text
Chosen：  -46.830143 → -44.240398
Rejected：-152.992218 → -185.752396
```

这意味着：

- Chosen 提高了约 2.59；
- Rejected 被压低约 32.76；
- score 的大幅提升主要来自 Rejected 被压低，而不是 Chosen 变好了多少。

因此，**DPO loss 下降不自动等于模型能力提升**。如果更新过猛，仍可能破坏其他正常输出。

## 六、梯度裁剪生效，为什么输出却几乎不变

加入：

```python
torch.nn.utils.clip_grad_norm_(
    policy_model.parameters(),
    max_norm=1.0,
)
```

裁剪后实际梯度范数为 1，但 score 和 logprob 几乎不变。

原因是梯度裁剪对所有梯度做同比例缩放，而 Adam 的更新会进行一阶、二阶动量归一化。整体缩放后，方向与归一化结果可能非常接近，尤其在单步、无 weight decay 的情况下。

所以这次得到的工程结论是：

> **梯度裁剪可以限制梯度规模，但不能代替降低学习率来控制 Adam 的实际更新幅度。**

## 七、LR=1e-7：更温和的单步变化

将学习率从 `1e-6` 降到 `1e-7`，保留 `beta=0.1` 和 `grad clip=1.0`：

| 指标 | LR=1e-6 | LR=1e-7 |
| --- | ---: | ---: |
| score change | 35.333 | **3.698** |
| 更新后 loss | 0.0288 | **0.5252** |
| Chosen 变化 | +2.588 | **+0.339** |
| Rejected 变化 | -32.745 | **-3.359** |

学习率缩小 10 倍后，score 变化也大约缩小 10 倍，更新方向没有改变，但明显温和得多。

因此当前候选起点是：

```text
LR = 1e-7
beta = 0.1
grad clip = 1.0
```

它只是一个偏好探针得出的候选配置，不能据此宣称是正式训练的最佳配置。

## 八、DPO 编码：Prompt 与候选输出必须分开处理

本次还实际遇到了一个模板问题：如果把 chosen / rejected 也交给 Chat Template 重新渲染，模板可能拆分、清理甚至重写思考标签，导致 malformed 的原始输出被“修正”。

最后的正确分工是：

```python
prefix_text = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True,
    enable_thinking=True,
)
full_text = prefix_text + response + "<|im_end|>\n"
```

也就是：

- Prompt 使用官方 Chat Template；
- chosen / rejected 作为原始候选输出直接追加；
- 不让模板二次修改候选回答；
- 再从 prefix / full 的 token 长度计算目标区间。

这样正常 CoT 与空思考、缺失标签、标签交错等 malformed 输出都能保留原始形式进入 logprob 计算。

## 九、32 + 8 条偏好数据与审计

本轮合成偏好数据分为四种 rejected 类型：

| pair_type | Train | Val |
| --- | ---: | ---: |
| verbose_correct | 8 | 2 |
| verbose_wrong | 8 | 2 |
| repetition | 8 | 2 |
| malformed | 8 | 2 |
| 合计 | **32** | **8** |

每类内部，单轮算术与多轮数值更新各占一半。

数据要求：

- Chosen 必须是简短、正确、结构完整的 CoT；
- verbose_correct 的 Rejected 答案正确但明显啰嗦；
- verbose_wrong 的 Rejected 含明确计算或最终答案错误；
- repetition 包含重复或自我怀疑；
- malformed 包含空思考、缺失标签、前置乱码或结构混乱。

`i4_dpo_data_audit.py` 实际验证：

- 样本数量、任务比例和四种 pair_type 数量；
- Chosen 的 CoT 格式、最终答案和中间算式；
- Rejected 是否符合对应类型；
- train / val 无重复 Prompt；
- 与已有 smoke、非 CoT、CoT 数据无重复显式算式；
- 行为基线排除项未命中；
- 全部 chosen / rejected 均通过偏好编码。

审计输出为：

```text
train chosen equations checked: 37
val chosen equations checked: 8
preference encoding: passed
train / val prompt overlap: 0
existing-data expression overlap: 0
exclusion checks: passed
全部 DPO 数据审计通过
```

这些是合成偏好数据，不代表人工标注，也不代表通用能力结论。

## 十、今晚的停止边界

今天完成的是：

- DPO 基本概念与数据契约；
- 序列 logprob、score 和初始 loss；
- 单步更新、梯度范数与 Adam 缩放现象；
- LR=1e-7 的温和更新；
- 偏好数据与完整编码审计。

尚未完成：

- 小批量 DPO 训练；
- DPO checkpoint；
- 训练后的答案正确率、CoT 格式、输出长度和能力保持评估；
- LoRA / 全参对照；
- RLVR / GRPO。

所以当前不能写成“DPO 已提升模型”。准确状态是：**DPO 的数据、计算和单步工程验证已经准备完成，下一步才是小批量训练与行为对照。**

今晚先到这里，保留已有 checkpoint、报告、偏好数据和编码实现，明天从批量 DPO 开始即可。

## 附：参数规模、垂直领域与能力权衡

在后训练实验之外，我又梳理了一次自己对“为什么做垂直领域微调”的认知。这不是一个已经证明的结论，而是后续选择模型、数据和评测目标时的一套假设。

### 1. 我目前的三个判断

第一，参数规模决定模型的能力上限。大厂在固定参数下训练出的通用模型，大概率希望成为六边形战士；但垂直领域并不一定需要六边形战士。

例如做架构设计时，我可以接受模型在数学、科研等领域不那么突出，把有限的容量和训练预算集中到架构领域，换取这一领域内的大幅度提升。

第二，一个 27B 模型经过合适的领域微调，如果能在架构设计这一明确任务范围内，与 100B+ 的通用模型打得有来有回，就已经足够有价值。这里追求的不是全面替代更大的模型，而是在垂直场景中形成实际优势。

第三，大厂基础模型已经做了大量通用优化。对具体使用者来说，微调、SFT、DPO 等方法更像是在做权衡和有的放矢，而不是继续追求全面提升。微调前需要明确要突出哪一方面，也要接受这更像系统架构中的 trade-off。

### 2. 需要补充的第一条边界：参数规模不是唯一变量

参数规模影响模型容量、知识承载和复杂推理上限，但同样规模的模型，实际能力还可能受这些因素影响：

- 训练数据质量与覆盖；
- 训练 token 量和计算量；
- 架构与训练方法；
- 后训练方式；
- 推理时的上下文、工具、检索和思考预算。

因此，27B 模型在垂直领域挑战更大的通用模型是合理目标，尤其是在任务边界清楚、领域数据质量高、评价标准明确的情况下。

但这不代表它获得了大模型的全部能力，更可能是把有限容量集中到了一个更窄、更有价值的任务分布内。

### 3. 需要补充的第二条边界：领域提升不必然牺牲其他能力，但一定存在权衡风险

微调并不是每次都必须“数学下降，架构上升”。如果数据混合合理、训练强度适当，也可能在保留通用能力的同时提升领域表现。

但 I4 的实验已经给出了真实例子：

```text
格式能力提升
→ 名字记忆出现回退

数值更新提升
→ 部分算术正确率回退

偏好 loss 降低
→ 最终行为没有同步改善
```

所以真正需要管理的是：

> **我愿意接受哪些能力损失，以及怎样通过 eval 及时发现实际发生的损失。**

有些损失是主动接受的，有些是不小心造成的。只有设置能力保持评测，才能区分这两者。

### 4. 需要补充的第三条边界：领域优势必须限定任务分布

“27B 架构模型和 100B+ 通用模型有来有回”还需要继续追问是在什么任务上：

- 编写常规架构文档；
- 根据明确需求做技术选型；
- 发现复杂系统中的依赖与故障风险；
- 面对陌生业务做开放式架构权衡；
- 审查真实代码、数据和运行证据，还是只根据提示词给建议。

越靠近固定流程、明确格式和常见案例，小模型领域化越容易取得优势；越接近开放问题、跨领域推理和复杂长链路决策，大模型的通用能力仍然可能很重要。

因此，领域模型超过大模型必须限定在明确的任务分布与评价口径内，不能从一组领域测试直接推广成全面超越。

### 5. 把训练目标写成一份架构 trade-off 说明

如果后续真的训练架构领域模型，可以把目标写成：

```text
目标：架构领域能力显著提升

约束：
- 通用代码能力最多允许下降多少
- 数学能力是否可以不保留
- 多轮指令遵循不能退化
- 输出结构与工具调用必须稳定

验收：
- 架构领域测试集
- 未见项目与跨域测试
- 通用能力保持集
- 失败与回退案例
```

这和系统架构设计很像：不是追求所有指标无限上升，而是在明确目标、约束和成本的前提下做选择，并用评测验证选择是否成立。

### 6. 架构领域尤其需要区分权重与上下文

架构知识并不都适合固化进权重：

```text
架构原则、设计方法、评审方式
→ 可以通过训练内化

当前系统结构、依赖、容量、故障现场
→ 更适合由代码图谱、知识库和运行时上下文提供
```

如果训练的是会背架构答案的模型，它可能只能在熟悉模板里表现良好；真正有价值的是在明确任务分布内，基于真实证据做出可评审的设计决策，同时保留必要的代码分析和系统推理能力。

### 7. 当前结论

垂直微调的目标不是培养一个更小的六边形战士，而是在明确任务分布内，把有限参数用到最有价值的地方，并且清楚知道自己付出了什么代价。

这套认知与 I4 的实验结论是一致的：**后训练不是无成本的全面增强，而是能力分布的重新塑造。目标、约束和 eval 必须同时设计。**

## 主要实验产物

```text
data/instruct/i4_dpo_preference_probe.json
data/instruct/i4_dpo_synthetic_train.json
data/instruct/i4_dpo_synthetic_val.json

scripts/i4_dpo_logprob_probe.py
scripts/i4_dpo_one_step.py
scripts/i4_dpo_data_audit.py
scripts/i4_cot_behavior_eval.py
scripts/i4_behavior_baseline.py
```
