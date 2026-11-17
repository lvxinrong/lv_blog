+++
title = "手搓 LLM 笔记 26：I4 后训练收官"
date = 2026-11-17
draft = false
slug = "llm-26-i4-post-training-recap"
tags = ["LLM", "I4", "SFT", "DPO", "LoRA", "RLVR", "GRPO", "后训练", "学习笔记"]
summary = "I4 收官：完成多轮 SFT、CoT-SFT、DPO 批量训练、LoRA / 全参对照、RLVR / GRPO 单组更新、同题规则胜率与真实 Web UI 回归。保留所有未超越原始模型、局部回退和最小实验边界。"
[cover]
    image = "covers/llm-26-i4-post-training-recap.jpg"
    alt = "手搓 LLM 笔记 26：I4 后训练收官"
    hiddenInList = true
    hiddenInSingle = true
+++

这篇是 I4 的收官汇总，承接：

- [笔记 23：多轮对话 SFT](/llm/llm-23-i4-multiturn-sft/)
- [笔记 24：思维链 CoT-SFT](/llm/llm-24-i4-cot-sft/)
- [笔记 25：DPO 偏好优化起步](/llm/llm-25-i4-dpo-preference/)

I4 的主干已经走通：多轮数据契约、SFT、CoT-SFT、DPO、LoRA / 全参对照、RLVR / GRPO 最小更新、同题规则对照和真实 Web UI 回归。

但“里程碑收官”不等于“所有模型能力目标都已达成”。本轮最重要的结论仍然是：**后训练会重新分配模型行为，loss 下降与能力改善不是同一件事。**

## 一、I4 最终交付清单

已完成：

```text
I4-A：多轮 Assistant-only mask、模板编码、Dataset、Batch padding、行为基线
I4-B：多轮 SFT、能力回退分析、训练量干预、LoRA / 全参对照
I4-C：CoT 数据契约、历史 CoT 可见性修复、三组 peak_lr 对照、严格格式验收
I4-D：DPO 指标、单步更新、偏好数据、16 个 Batch 训练与行为评估
I4-E：RLVR 分层奖励、组内优势、一次序列级 GRPO 更新与行为回归
总验收：同一 CoT 评测集对照、规则 win / tie / loss、30 项相关测试、真实 Web UI 多轮回归
```

I5 的 LLM 评委校准、偏见检查和自动化 CI 尚未开始。

## 二、DPO 批量训练：优化目标实现，整体正确率未提升

### 1. 训练配置与过程

DPO 使用 32 条训练偏好对、8 条验证偏好对，四种 rejected 类型均衡分布：

```text
verbose_correct
verbose_wrong
repetition
malformed
```

正式训练配置：

```text
batch_size = 2
max_steps = 16
beta = 0.1
learning_rate = 1e-7
grad clip = 1.0
参考模型只预计算一次 logprob
policy 从原始 Qwen3-0.6B Instruct 开始
```

训练结果：

```text
val loss： 0.628564 → 0.155683
val score：1.3776 → 22.8115
checkpoint reload：passed
```

这说明 DPO 的偏好优化目标确实被实现了。

### 2. 行为结果

| 指标 | 原始模型 | DPO v1 |
| --- | ---: | ---: |
| 最终答案正确 | **30/32** | 29/32 |
| 完整 CoT | 32/32 | 32/32 |
| 数值更新 | **15/16** | 14/16 |
| 单轮算术 | 15/16 | 15/16 |
| 自然结束 | 32/32 | 32/32 |

输出长度与推理质量：

| 指标 | 原始模型 | DPO v1 |
| --- | ---: | ---: |
| 平均生成 tokens | 163.1 | 153.2 |
| 中位生成 tokens | 146 | 134.5 |
| 最大生成 tokens | 430 | 317 |
| 推理算式错误 | 2 | 1 |

所以 DPO v1 的输出有所缩短，推理算式错误减少，但最终答案正确率没有超过原始模型，数值更新还出现一处回退。

准确结论是：**DPO 的 score / loss 优化链路成立，但当前合成偏好数据与配置没有带来整体行为提升。**

## 三、LoRA vs 全参数：效率明显占优，绝对效果并非全面更好

LoRA 使用与非 CoT 全参数 v2 相同的 128 + 32 数据、32 steps、batch=4、peak_lr=1e-5。

```text
rank = 8
alpha = 16
```

核心对照：

| 指标 | 全参数 v2 | LoRA r8 / α16 |
| --- | ---: | ---: |
| 可训练参数 | 全部参数 | **6,269,952（约 1.05%）** |
| 存档大小 | 2,384,324,167 bytes | **25,204,363 bytes** |
| 最终 full val loss | **1.021104** | 1.997782 |
| 独立行为验证 | **30/32** | **29/32** |
| 名字记忆 | 7/8 | **8/8** |
| 偏好记忆 | 8/8 | **8/8** |
| 数值更新 | **7/8** | 6/8 |
| 单轮算术 | **8/8** | 7/8 |

adapter 约为全参数 checkpoint 的 1/95，行为只少通过一条，名字记忆还少一处回退。

因此：

- 追求当前评测集最高分，全参数 v2 略占优；
- 追求接近的行为表现与更低的训练、存档成本，LoRA 明显更有性价比；
- 不能推广成“LoRA 总是更好”或“rank=8 是最佳配置”。

LoRA 的 val loss 更高、行为却接近全参数，也再次说明 loss 不能直接替代行为验收。

## 四、RLVR + GRPO：从可验证奖励到一次组相对更新

### 1. 两个概念的位置

RLVR 与 GRPO 不在同一层：

- **RLVR** 决定奖励从哪里来；
- **GRPO** 决定拿到奖励以后怎样更新模型。

GRPO 对同一 Prompt 采样一组回答，用组内平均奖励与标准差构造相对优势，再进行策略优化。RLVR 则可以与 GRPO、PPO 或其他策略优化算法组合，不是 GRPO 的专属组件。

#### RLVR 的完整含义

RLVR 全称是 **Reinforcement Learning with Verifiable Rewards，可验证奖励的强化学习**。

它的核心不是“奖励数字长什么样”，而是：**回答是否正确，可以由明确、可执行的验证器判断。**

例如：

```text
数学：最终数值是否等于标准答案
代码：是否编译通过、单元测试是否通过
结构化输出：是否符合指定 JSON Schema
对话协议：思考标签是否完整、是否正常结束
```

在本轮算术任务里，验证器不需要人工打分，也不调用 LLM 评委，而是直接解析回答并比较最终数字。

#### 它与 SFT、DPO、传统 RLHF 的区别

| 方法 | 学习信号 |
| --- | --- |
| SFT | 模仿给定的标准答案 |
| DPO | 同一 Prompt 下，Chosen 相对 Rejected 更受偏好 |
| 传统 RLHF | 常由人工偏好训练奖励模型，再进行强化学习 |
| RLVR | 由程序规则、编译器、测试或其他可执行验证器直接给奖励 |

因此，RLVR 的优势是奖励口径明确、可重复执行，特别适合数学、代码和结构化输出任务。它并不要求先构造 chosen / rejected 偏好对，而是可以在采样后对当前模型的回答直接验收。

#### 为什么本轮需要分层奖励

第一版只使用二值奖励：完整 CoT、答案正确、纯数字格式同时满足才给 1，否则全部为 0。

实际采样中出现了：

- 有些回答已经算出正确数值，但最终写成了完整算式，而不是纯数字；
- 有些回答不断自我怀疑，直到长度上限也没有结束。

如果全部给 0，验证器就无法区分“完整但格式不完美”和“根本没有答完”，组内也没有学习差异。

因此本轮使用 shaped reward v2：

```text
1.0：完整 CoT + 数值正确 + 纯数字答案
0.7：完整 CoT + 数值正确，但最终格式不完美
0.1：完整 CoT，但答案错误
0.0：结构不完整、截断或无法验收
```

这个设计不是降低正确答案标准：纯数字且正确的回答仍然获得最高奖励。部分奖励只是为了让模型先学习“完成一个可验证的回答”，再逐步改善格式与正确性。

#### RLVR 的边界与风险

可验证不等于所有重要质量都能被验证：

- 数学最终答案正确，不代表中间推理一定正确；
- 代码通过部分测试，不代表没有隐藏缺陷；
- JSON 可以解析，不代表字段语义符合业务意图；
- 结构完整，不代表回答自然、简洁或没有无关内容。

奖励设计还可能产生 reward hacking：模型可能学会迎合验证器，而不是真正改善任务能力。例如只输出高频正确答案、牺牲推理过程，或利用验证器没有覆盖的格式漏洞。

因此 RLVR 实验必须同时保留：

```text
验证器本身的正确性测试
奖励组成与版本记录
独立行为评测
对推理过程和最终答案的分别检查
对 reward hacking 与意外行为的观察
```

本轮的 shaped reward v2 只适用于当前受控算术实验，不能当成通用奖励设计，也不能与之前二值奖励的结果混为同一口径。

### 2. 实际样本组与优势

从 CoT-SFT v2 采样得到：

```text
rewards    = [0.7, 0.0, 0.0, 0.7]
advantages = [1.0, -1.0, -1.0, 1.0]
mean reward = 0.35
std reward = 0.35
has_learning_signal = true
```

两条完整但格式不完美的回答获得正优势，两条截断回答获得负优势。

### 3. 最小序列级 GRPO 更新

配置：

```text
group_size = 4
optimization_steps = 1
epsilon = 0.2
learning_rate = 1e-7
grad clip = 1.0
reference KL = 未加入
```

更新结果：

```text
before loss = 0
before mean ratio = 1.0
after loss = -0.20000002
after mean ratio = 3.06
grad norm before clip = 2379.9329
checkpoint reload = passed
```

逐响应 ratio：

```text
正优势：9.248458、2.639478
负优势：0.224003、0.128063
```

方向符合预期，但多个 ratio 已超出 `[0.8, 1.2]`，说明更新仍然激进，不能把 loss 和 ratio 变化直接当成稳定训练的证据。

### 4. 更新后的行为回归

| 指标 | CoT-SFT v2 | GRPO 单组更新 |
| --- | ---: | ---: |
| 最终答案正确 | 29/32 | **30/32** |
| 完整 CoT | 32/32 | **32/32** |
| 数值更新 | 16/16 | **16/16** |
| 单轮算术 | 13/16 | **14/16** |
| 自然结束 | 32/32 | **32/32** |

本次更新没有造成即时行为崩溃，最终正确率与原始模型持平。但它只有一组、一次更新，且未加入参考模型 KL，不能据此宣称 GRPO 已稳定提升模型。

## 五、同一 CoT 评测集上的最终对照

以下结果均来自同一 32 条 CoT 样本，不跨数据集比较通过率：

| 模型         |   答案正确 | 完整 CoT |   综合通过 | 平均 tokens | 中位 tokens | 最大 tokens |
| ---------- | -----: | -----: | -----: | --------: | --------: | --------: |
| 原始模型       | **30** |     32 | **30** |     163.1 |       146 |       430 |
| CoT-SFT v2 |     29 |     32 |     29 | **139.4** |   **120** |   **278** |
| DPO v1     |     29 |     32 |     29 |     153.2 |     134.5 |       317 |
| GRPO 单组更新  | **30** |     32 | **30** |     141.7 |   **120** |       376 |

可以看到不同方法优化的是不同侧面：

- 原始模型最终正确率最高，但输出偏长；
- CoT-SFT v2 最短，但正确率没有超过原始模型；
- DPO 有适度缩短，整体正确率仍未提升；
- GRPO 本次恢复到 30/32，但实验规模不足以证明稳定收益。

## 六、同题规则 win / tie / loss

为避免只比较总通过率，又按同一题的 `passed` 做了规则评委对照：

| 对照 | 左侧胜 | 左侧负 | 平局 |
| --- | ---: | ---: | ---: |
| 原始 vs CoT-SFT | 2 | 1 | 29 |
| 原始 vs DPO | 1 | 0 | 31 |
| 原始 vs GRPO | 1 | 1 | 30 |
| CoT-SFT vs DPO | 2 | 2 | 28 |
| CoT-SFT vs GRPO | 0 | 1 | 31 |
| DPO vs GRPO | 1 | 2 | 29 |

报告同时记录：

```text
win_rate_all = wins / 全部题目数
decisive_win_rate = wins / (wins + losses)
```

这些只是当前 32 条样本上的规则评委胜率，不是经过 I5 校准的 LLM 评委结果，也不能扩大为通用模型排名。

## 七、真实 Web UI 多轮回归

最后给 `chat_server.py` 增加 `LVCHAT_CHECKPOINT`，在真实页面加载训练后的模型，关闭 thinking，连续输入：

```text
第一轮：我叫小吕。
第二轮：那我叫什么？
```

### 1. 非 CoT SFT v2

页面结果为：

```text
第一轮 Assistant：你叫小吕。
第二轮 Assistant：你叫小吕。
```

第二轮包含正确名字，但两轮 Assistant 完全同文。多轮记忆内容正确，**非同文复制验收未通过**。

### 2. GRPO 单组更新 checkpoint

页面结果为：

```text
第一轮 Assistant：你好，小吕！我是你的助手，有什么可以帮助你的吗？
第二轮 Assistant：我叫小吕，很高兴认识你！有什么我可以帮你的吗？
```

这次第二轮包含正确名字，且没有复制第一轮，TURN=02、SSE 状态正常。按预先设定的“历史信息正确 + 非精确复制”两项标准，可以记为通过。

但第二轮使用“我叫小吕”，存在说话视角混淆，表达自然性仍需改进。

因此当前 Web UI 结论是：

- 非 CoT SFT v2 暴露了同文复制；
- GRPO checkpoint 提供了一条记忆正确、非精确复制的可用路径；
- 多轮表达质量并未完美；
- 本次验收针对当前 V4 / Qwen3 Web UI，**不代表 M6 的旧 355M 模型已重新测试和修复**。

## 八、相关回归

实际运行：

```text
tests/test_chat_sft.py
tests/test_i4_behavior_baseline.py
tests/test_chat_session.py
tests/test_qwen3

30 passed in 1.81s
```

此外，DPO 偏好数据审计、CoT 数据审计、checkpoint / adapter reload、DPO 训练、LoRA 训练和 GRPO 更新均由真实命令执行。

## 九、I4 最终结论

### 1. SFT 很容易学会形式，但可能重新分配甚至破坏能力

格式、模板和局部行为可以快速改变；最终答案、旧能力和开放域表现不一定同步改善。

### 2. 数据质量与 eval 必须同时设计

数据质量决定能学到什么，eval 决定能否看见收益、退化和未被直接训练的行为。只强调任何一个都会出问题。

### 3. loss 只是训练目标的代理指标

SFT、DPO、GRPO 中都出现了 loss 或 score 改善，但行为没有同步提升的情况。必须保留独立行为基线与能力保持集。

### 4. 不同方法的价值不能只用一个分数判断

- CoT-SFT v2 输出更短；
- DPO 学到了偏好差值并适度缩短输出；
- LoRA 用约 1% 参数取得接近全参数的行为；
- GRPO 完成了可验证奖励驱动的最小更新；
- 原始模型在最终答案正确率上仍很强。

这不是一个“谁彻底打败谁”的故事，而是不同目标、成本和副作用之间的取舍。

## 十、I4 停止边界与 I5 衔接

I4 可以按学习里程碑收官，但必须保留：

- 所有实验都基于小模型与受控合成数据；
- DPO 偏好数据不是人工标注；
- GRPO 只有一组、一次更新，未加入参考 KL；
- LoRA 只测试 rank=8、alpha=16 和当前固定配置；
- Web UI 多轮表达仍存在视角混淆；
- M6 旧 355M 模型未重新回归；
- 规则胜率不是校准后的 LLM 评委胜率。

下一阶段 I5 将处理评估校准、位置与长度偏见、多评委一致性和自动化回归门禁。I4 已经证明：**没有可信 eval，就无法判断后训练到底是在提升，还是在更隐蔽地破坏。**

## 附：留给未来回顾的独立复现任务（非里程碑）

I4 的实验主干已经收官，但这不等于我已经熟练掌握后训练。

当前更真实的状态是：我建立了 SFT、CoT-SFT、DPO、LoRA、RLVR / GRPO 的基本概念坐标，亲手跑过训练、生成与评估链路，也看到了 loss、优化目标和真实行为之间的差异。但 I4 的大部分实现代码由 Kimi 提供，我主要通过复制、阅读、运行、排障和实验分析参与，独立实现能力尚未被充分验证。

复制代码本身不等于没有学习。基线设计、指标修正、失败样例分析、训练干预和回退定位都是真实参与，但它们不能替代独立实现能力。因此留下以下回顾任务，供未来检查自己是否真正留下了可以独立重建的主干。

这些任务：

- 不属于新的里程碑；
- 不改变 I4 已收官的状态；
- 不阻塞 I5；
- 不要求重新手敲整个 I4；
- 可以在后续任何阶段按需要回顾。

### 1. 多轮 SFT 掩码独立复现

- [ ] 不看现有实现，写出 inputs / targets 的错位关系；
- [ ] 独立实现 Assistant-only mask，保留每轮 Assistant 正文与结束标记；
- [ ] 解释为什么 User 不参与 loss，却仍然可以作为上下文影响回答；
- [ ] 跑通现有多轮 Dataset 与 Batch padding 测试；
- [ ] 说明 Full 区间与 target 下标为什么相差一位。

### 2. DPO 核心计算独立复现

- [ ] 独立实现 Assistant 输出的 sequence logprob；
- [ ] 分别计算 policy / reference 对 Chosen 与 Rejected 的 logprob；
- [ ] 写出 score，并确认顺序是“训练后偏好差 − 训练前偏好差”；
- [ ] 写出 DPO loss，并验证初始 policy = reference 时 loss 为 ln 2；
- [ ] 能解释 score 增大究竟来自 Chosen 提高、Rejected 降低，还是两者同时发生。

### 3. LoRA 旁路独立复现

- [ ] 独立写出 A / B 两个低秩矩阵及前向计算；
- [ ] 解释 rank 如何限制更新容量，alpha / rank 如何缩放旁路输出；
- [ ] 验证 B 零初始化时，加入 LoRA 前后的模型输出保持一致；
- [ ] 计算一个具体 Linear 层的原参数量、LoRA 参数量与节省比例；
- [ ] 说明为什么 LoRA 参数效率高，不代表所有行为指标都更好。

### 4. RLVR / GRPO 最小机制独立复现

- [ ] 为一个算术任务写出可执行验证器与奖励函数；
- [ ] 对同一 Prompt 的一组回答计算组内均值、标准差与 advantage；
- [ ] 解释组内全对、全错或全部无效时为什么缺乏学习信号；
- [ ] 写出带 epsilon 裁剪的 ratio objective；
- [ ] 能判断正负 advantage 分别希望提高还是降低对应回答的生成倾向。

### 5. 回顾时的统一验收方式

每个小主干都尽量做到：

```text
能手写一个最小版本
能解释关键张量形状与符号方向
能跑通已有测试或最小探针
能说明故意改错一处会出现什么现象
```

目标不是把代码背得一字不差，而是脱离现成实现后，仍然能恢复核心计算链路，并用实验证明自己的理解。

在完成这些回顾之前，对 I4 的准确表述仍然是：**实验里程碑已完成，概念与工程闭环初步建立，独立实现熟练度仍需后续验证。** 这不是欠下一条新的主线，而是给未来的自己留下一张复习清单。

## 主要实验产物

```text
data/reports/i4-dpo-v1-training.json
data/reports/i4-dpo-v1-cot-behavior.json
data/reports/i4-lora-sft-r8a16-training.json
data/reports/i4-lora-sft-r8a16-synthetic-val.json
data/reports/i4-grpo-sampled-group.json
data/reports/i4-grpo-one-update.json
data/reports/i4-grpo-one-group-cot-behavior.json
data/reports/i4-final-comparison.json

data/model_pth/qwen3/i4-dpo-v1.pth
data/model_pth/qwen3/i4-lora-sft-r8a16.pth
data/model_pth/qwen3/i4-grpo-one-group.pth

scripts/i4_dpo_train.py
scripts/i4_lora_sft_train.py
scripts/i4_grpo_group_probe.py
scripts/i4_grpo_sample.py
scripts/i4_grpo_one_update.py
scripts/i4_final_comparison.py
scripts/chat_server.py
```
