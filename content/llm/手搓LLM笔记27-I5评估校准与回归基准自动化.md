+++
title = "手搓 LLM 笔记 27：I5 评估校准与回归基准自动化"
date = 2026-11-18
draft = false
slug = "llm-27-i5-judge-calibration-regression"
tags = ["LLM", "I5", "Evaluation", "LLM-as-Judge", "Bootstrap", "回归测试", "学习笔记"]
summary = "I5 收官：完成人工盲评、AB/BA 位置校准、长度控制、多评委对照、独立 held-out、paired bootstrap 和 I0～I4 注册范围的一键回归报告。工程链路已跑通，但小样本、独立实现熟练度和完整评估能力仍需继续探索。"
[cover]
    image = "covers/llm-27-i5-judge-calibration-regression.jpg"
    alt = "手搓 LLM 笔记 27：I5 评估校准与回归基准自动化"
    hiddenInList = true
    hiddenInSingle = true
+++

这篇是 I5 的收官汇总，承接 [笔记 26：I4 后训练收官](/llm/llm-26-i4-post-training-recap/)。

I4 做完了多轮 SFT、CoT-SFT、DPO、LoRA、RLVR / GRPO，但行为对照没有证明任何方法全面优于原始模型。DPO 的 val loss 从 0.628564 降到 0.155683，score 从 1.3776 升到 22.8115，行为正确数却仍是 29/32，没有超过原始模型的 30/32。

这让我更确定一件事：**训练曲线只能说明优化目标正在下降，不能单独说明模型能力正在变好。**

I5 要补的就是这条证据链。

我对评估的第一性原理理解是：全面、科学、可对照、可对比、可解释地评估一个模型。现在再补一句：全面不是测完所有能力，而是知道自己测了什么、没测什么；科学也不是公式复杂，而是结论有边界，并且允许被新证据推翻。

## 一、I5 最终交付清单

本轮完成：

```text
I5-A：人工评价协议、8 对匿名盲评样本、私密映射、标签写保护
I5-B：成对评委、AB/BA 位置交换、结果坐标还原、断点续跑
I5-C：无效填充与有效信息的长度控制实验
I5-D：DeepSeek + Qwen4 Max 双评委、10 对独立 held-out、v2 评价规则
I5-E：paired bootstrap、带 CI 的胜率矩阵、I4 门禁、I0～I4 注册范围总报告
总验收：项目全量 173 passed，统一缓存报告与 I0/I4 受控刷新报告
```

这里有两个范围必须写清楚：

- 人工样本仍然很小，8 对用于开发校准，10 对用于独立描述性验证；
- 一键报告覆盖的是当前注册产物，不是 I0～I4 所有历史实验的全量实时重跑。

## 二、从单条打分到成对评估

M5 的评委主要给单条回答打 0～100 分，适合生成评分分布，但不适合直接研究位置偏见。

位置偏见需要一个对照结构：同一个评委面对同一对回答，只交换 A/B 的展示位置，观察它是否仍然选择同一条内容。

因此 I5 新增成对评估链路，没有重写 M5：

```text
同一任务
→ 回答 A / 回答 B
→ 原始 AB 顺序评一次
→ 交换 BA 顺序再评一次
→ 还原到原始回答身份
→ 判断一致、位置敏感或明确胜负翻转
```

A/B 只是座位号，不是回答的身份证。

假设甲是正确回答，乙是错误回答：

```text
第一次：A=甲，B=乙，评委选 A
第二次：A=乙，B=甲，评委选 B
```

两次原始字母不同，但都是在选甲，所以内容判断一致。

如果两次都选当前 A，则还原后一次选甲、一次选乙，才是明确的胜负翻转。

核心还原逻辑是：

```text
swapped=False：A/B 原样保留
swapped=True ：A ↔ B，tie 保持 tie
```

`position_sensitive` 表示交换后结论发生变化；`decisive_flip` 则要求还原后确实发生 A/B 双方互换。`tie → A` 属于位置敏感，但不属于明确胜负翻转。

如果两次没有形成共同结论，就记录 `consensus_winner=null`。不能擅自改成平局，也不能只挑其中一次有利的结果。

## 三、人工评价协议：结果、推理质量、信息密度

### 1. 四个原因编码

人工标签使用：

```text
correctness：最终答案与历史状态是否正确
instruction：是否遵循明确的任务和输出指令
reasoning ：推理是否可靠，是否有有效独立验算
clarity   ：有效信息密度、重复和表达质量
```

双方最终都答对时，不能仅因为正确性重要就填 correctness；它没有造成双方差异。非平局至少记录一个原因，平局可以为空。

### 2. 三层递进，而不是加权平均

标注过程中，我逐渐把自己的判断整理成三层字典序：

```text
第一层：任务结果
       最终答案、历史状态、明确指令遵循

第二层：推理质量
       推理可靠性、历史解释、有效独立验算

第三层：信息密度
       有效信息、重复、空话、简洁程度
```

前一层能够分出明确高下，就不让后一层翻盘：

- 简洁但错误，不能靠表达战胜正确回答；
- 数值正确但违反“只输出数字”，会在第一层落后；
- 双方都正确且合规时，正确独立验算可以提高推理质量；
- 推理质量也相同时，才比较谁更简洁有效。

这套标准是我的个人评价口径，不是所有人都必须同意的 universal 答案。评估系统首先要明确目标偏好，再讨论 AI 评委是否对齐。

## 四、8 对开发盲评：稳定不等于与人工一致

首批从 I4 四模型的现有报告中抽取 8 对：

```text
3 对规则结果有分歧
3 对双方规则通过
2 对双方规则未通过
```

公开文件只有 A/B、任务、参考答案和人工标注栏；模型身份、规则结果和 token 数保存在私密 key 中。

抽样过程中发现同一道题被重复抽进不同 pair，于是增加了 `case_index` 跨分层去重。完成标注后又增加写保护：只要检测到人工标签，导出器就拒绝覆盖。

真实双评委结果：

| 8 对开发样本 | DeepSeek | Qwen4 Max |
| --- | ---: | ---: |
| 双顺序一致 | 6 | 7 |
| 位置敏感 | 2 | 1 |
| 明确胜负翻转 | 0 | 0 |
| 与人工一致 | 4 | 6 |
| 与人工分歧 | 2 | 1 |
| 无共识、未参与人工比较 | 2 | 1 |

双方都有共识的 5 对，结论全部相同。16 次同顺序比较中，13 次相同，3 次不同。

这里的重点不是选出一个更好的评委，而是看到两类问题：

- DeepSeek 在两对双方都未通过的样本上，从平局变成了有赢家；
- 两位评委都在一些双方答对的样本上稳定给 tie，而我会根据推理和表达选出赢家。

所以，**双顺序稳定只说明结果稳定，不说明评价标准已经与人工一致。**

## 五、长度控制：变长不等于变更好

为了隔离长度影响，又构造了 4 个受控条件：

| 条件 | DeepSeek | Qwen4 Max |
| --- | --- | --- |
| 完全重复 | 稳定 tie | 稳定 tie |
| 无效填充变长 | 简洁版获胜 → tie，未决 | 稳定选择简洁版 |
| 有效验算变长 | 稳定 tie | 稳定 tie |
| 错误且冗长 | 稳定选择正确简洁版 | 稳定选择正确简洁版 |

在这 4 个条件中，没有任何双顺序共识选择更长回答。

因此本轮没有观察到“越冗长越容易赢”的证据，但也不能推广成两个评委在所有任务上都没有长度偏见。

更有价值的发现是：两位评委都把有效独立验算判成了平局。Qwen 的原始推理明确承认验算正确，却认为它不足以构成实质差异。

这说明问题不只在长度，还在“有效信息什么时候足以打破平局”。于是 v2 prompt 明确加入：

```text
正确、非重复、与任务相关的独立验算或推理，可以构成实质优势。
重复用户要求、复述格式、重复同一种计算，不属于有效增量。
额外验算不是强制要求，没有有意义增量时不处罚简洁回答。
```

## 六、10 对独立 held-out：不再看答案调评委

随后创建了 10 对全新样本，每类两对：

```text
正确性门槛
有效独立验算
无效填充
实质等价
指令遵循
```

这些题与前面的开发材料不重复。先完成人工标注，再运行冻结的 v2 prompt。

解盲后，设计假设与人工判断有 4 对不一致：

- 两条设计为无效填充的样本，我都选择了显式阐述指令理解的版本；
- 两条设计为实质等价的样本，我分别根据简洁性和历史回顾选出了赢家。

这些 winner 没有被改成设计假设。它们反而帮助我进一步确认了上面的三层评价标准。

### 1. held-out 总体结果

| 10 对 held-out | DeepSeek | Qwen4 Max |
| --- | ---: | ---: |
| 双顺序一致 | 6 | 10 |
| 位置敏感 | 4 | 0 |
| 明确胜负翻转 | 2 | 0 |
| 与人工一致 | 4 | 6 |
| 与人工稳定分歧 | 2 | 4 |
| 无共识、未决 | 4 | 0 |

双方都有共识的 6 对全部结论相同。20 次同顺序比较中，16 次相同，4 次不同。

### 2. 按条件看结果

| 条件，每类 2 对 | DeepSeek | Qwen4 Max |
| --- | --- | --- |
| 正确性门槛 | 1 对一致，1 对未决 | 2 对一致 |
| 指令遵循 | 1 对一致，1 对未决 | 2 对一致 |
| 有效独立验算 | 2 对一致 | 2 对一致 |
| 格式复述 / 填充 | 1 对稳定分歧，1 对未决 | 2 对稳定分歧 |
| 实质等价的细微差异 | 1 对稳定分歧，1 对未决 | 2 对稳定分歧 |

Qwen 的 6 对人工一致，全部集中在正确性、指令遵循和有效独立验算；4 对分歧全部是稳定给出 tie。

也就是说，Qwen 在当前样本上更稳定，但并没有完全对齐我的信息密度与历史解释偏好。

DeepSeek 的两次明确胜负翻转分别落在正确性和指令遵循样本上，这类不稳定比一般的表达偏好更需要进入回归报告。

当前没有同一 held-out 上的 v1 对照，因此只能说 v2 在这批新样本上的表现已经测量，不能把差异全部归因于 prompt 改进。

## 七、Qwen 接入：输出预算也属于评估配置

Qwen4 Max 使用 Token Plan 的 OpenAI 兼容接口，复用同一套双顺序和断点续跑逻辑。

实际接入时遇到了空内容：

```text
max_tokens=16
finish_reason=length
content=""
```

提高预算后可以正常输出。v2 held-out 中，256 tokens 也曾出现全部用于 reasoning、正式答案尚未产生的情况，因此该轮改用 512，并把配置写入报告身份。

Qwen 报告保留：

```text
content
reasoning_content
finish_reason
prompt / completion / reasoning tokens
```

这说明输出预算不是无关紧要的工程参数。预算过小会把“尚未给出判断”变成空内容；不同评委的推理模式和 token 配置也必须记录，不能把所有行为差异都解释成模型本身的能力差异。

解析失败时，原始响应会先落盘再抛错；有效顺序在续跑时不重复请求。

## 八、paired bootstrap：给 I4 胜率补上不确定性

I4 原本只有同一 32 题上的 win / loss / tie。I5 增加 paired bootstrap，重采样单位是 case，而不是分别抽左右模型的回答。

每次抽中一道题，就同时保留所有模型在这道题上的结果，再重新计算指标。

```text
win_rate_all   = wins / 全部 case
net_win_rate   = (wins - losses) / 全部 case
tie_rate       = ties / 全部 case
```

取 2000 次重采样的 2.5% 与 97.5% 分位数，得到 95% 区间。

真实结果：

| 对照 | W/L/T | net | 95% CI | 判定 |
| --- | --- | ---: | --- | --- |
| original vs CoT-SFT v2 | 2/1/29 | +0.03125 | [-0.0625, +0.15625] | inconclusive |
| original vs DPO v1 | 1/0/31 | +0.03125 | [0, +0.09375] | inconclusive |
| original vs GRPO 单组更新 | 1/1/30 | 0 | [-0.09375, +0.09375] | inconclusive |
| CoT-SFT v2 vs DPO v1 | 2/2/28 | 0 | [-0.125, +0.125] | inconclusive |
| CoT-SFT v2 vs GRPO | 0/1/31 | -0.03125 | [-0.09375, 0] | inconclusive |
| DPO v1 vs GRPO | 1/2/29 | -0.03125 | [-0.15625, +0.0625] | inconclusive |

六组全部为 `inconclusive`。

`original vs DPO` 的下界虽然等于 0，仍按严格规则判为证据不足。点估计为 0 也不代表等效，只表示当前样本没有检测到净差异。

32 道题中，每变化一道题就是 3.125 个百分点。bootstrap 展示了这种不确定性，但没有把小样本变成大样本。

## 九、从报告到门禁：产物有效不等于能力通过

I4 门禁将三类状态分开：

```text
artifact_status=pass
  报告可读、源哈希一致、case 完整且对齐

regression_detected
  是否有候选相对 original 出现明确的净胜率回退

evidence_status
  improvement_detected / regression_detected / inconclusive
```

真实 I4 结果：

```text
artifact_status=pass
models=4
cases_per_model=32
pairwise_comparisons=6
regression_detected=False
evidence_status=inconclusive
```

退出码为 0 只表示产物有效且没有检测到明确回退，不表示候选模型已经通过能力验收，更不证明模型等效。

## 十、I0～I4 注册范围的一键总报告

### 1. 补齐 I0 机读对齐报告

I0 原先主要依赖测试和历史日志。本轮新增独立报告导出器，使用固定输入、CPU、FP32、官方 eager 和本地 Qwen2.5-0.5B-Instruct 权重：

```text
完整 logits：4/4 通过
cache prefill：通过
首层与末层 KV：通过
连续 cache decode：3/3 通过
上述受控张量 max_abs_difference：全部为 0.0
```

结论只适用于当前固定条件，不推广到任意输入、设备、dtype、SDPA 或生成质量。

### 2. 统一覆盖与总报告

覆盖清单把产物分为：

```text
controlled_alignment
single_observation
repeated_measurement
single_workload
paired_gate
```

最终注册范围为 8 组产物，字段全部有效：

```text
coverage_status=complete_for_registered_scope
registered_scope_only=true
```

统一入口：

```bash
uv run python scripts/i5_regression.py

uv run python scripts/i5_regression.py \
  --refresh-controlled \
  --resamples 2000 \
  --seed 20261119
```

两种模式都已实际运行。第二种只实时刷新 I0/I4，I1～I3 始终读取历史测量：

```text
refresh_scope=[I0, I4]
full_live_refresh=False
```

历史性能摘要：

```text
I2 Compile 相对吞吐：约 +7.27%，三次运行，不提供性能 CI
I3 KV Cache decode：约 1.73x，贪心输出一致
I3 投机解码 k=2：token 一致，speedup=0.515，当前未提速
```

最终总状态：

```text
artifacts_valid_capability_inconclusive
```

这个状态很准确地表达了当前结果：注册的数值与工程检查有效，但 I4 后训练能力差异仍然证据不足。

## 十一、全量项目回归

收官前实际运行：

```bash
uv run pytest -q
```

结果：

```text
173 passed in 594.64s (0:09:54)
```

同时执行：

```bash
git diff --check
```

检查通过。

这次不是只跑 I5 新增的纯函数测试，而是项目当前完整测试集合。全绿表示当前测试覆盖范围通过，不替代开放能力评估，也不改变 I4 的 `inconclusive`。

## 十二、现成框架与本次手搓的位置

评估并不缺少现成框架：

- EleutherAI lm-evaluation-harness：标准 Benchmark、loglikelihood、生成任务和模型适配；
- Inspect AI：Dataset、Solver、Scorer、多轮、工具与模型评分；
- OpenCompass：大量模型与数据集，以及 Generic LLM Judge；
- Promptfoo：模型 × Prompt 矩阵、断言、回归和 CI。

I5 的手搓实现让我看见了这些框架背后的基本问题，但如果目标是长期维护通用评估平台，没有必要全部自己重写。

后续可以用同数据、同模型、同解码参数做框架对照，重点检查请求构造、样本日志、评分接口、tie / unresolved 和统计口径，而不是默认框架的每个定义都与我们相同。

## 十三、I5 停止边界

I5 可以按学习里程碑收官，但必须保留：

- 评估主要基于小模型、算术与多轮数值更新的受控合成样本；
- 8 对开发样本与 10 对 held-out 都不足以支持普遍评委排名；
- 当前没有进行有统计意义的人机相关系数分析；
- Qwen 与 DeepSeek 的推理方式和输出预算不同；
- 没有同批 v1 / v2 对照，不宣称 prompt 改进的因果收益；
- 人工标签来自单一标注者，代表当前个人评价口径；
- I1～I3 在总报告中仍是历史缓存，不是完整 live 回归；
- 注册范围覆盖不等于所有历史实验已经统一接入；
- 工程链路完成不等于我已经独立掌握评估工程。

## 附：留给未来的独立回顾任务（非里程碑）

第一次从零手搓 LLM 时，我也只是懵懵懂懂。评估现在处于类似阶段：已经有概念、直觉和一些诊断经验，但大部分实现代码由 Kimi 提供，独立复现和迁移设计尚未充分验证。

评估可以被看作完全独立于某个 LLM 的一等工程体系。它包括任务构造、实验设计、人工标注、统计、数据隔离、报告和回归门禁。后续需要多评估几次，而不是把 I5 当成评估学习的终点。

以下任务不属于新里程碑，不阻塞 I6：

- [ ] 不看现有代码，独立复现 `canonicalize_winner` 与位置交换结果还原；
- [ ] 独立实现 `build_paired_outcomes`，解释为什么必须按 case 配对；
- [ ] 用一个小例子手算 wins、losses、ties 和 net_win_rate；
- [ ] 解释为什么 tie、unresolved 和 decisive_flip 不能混为一谈；
- [ ] 面对一个新任务，先写能力定义、数据隔离、基线和验收协议，再写训练代码；
- [ ] 使用一个现成 eval 框架复现小组实验，并比较双方报告口径；
- [ ] 在 I6 Java 缺陷修复中，把编译率、测试通过率、定位准确率和通用能力保持纳入同一评估协议。

回顾目标不是背代码，而是离开现成实现后，仍能恢复最小主干，并知道每个结论能证明什么、不能证明什么。

## 十四、收官不是结束

I5 更像是在地图上探索了一块迷雾，打下了一个标记。

现在我知道这里有哪些路：人工协议、双顺序、多评委、长度控制、配对统计和回归门禁；也知道哪里有悬崖：小样本、评价偏好、数据泄漏、未决分母和把 loss 当能力。

但这块区域还远没有深度探索。

所以今天的准确结论是：**I5 工程里程碑完成，评估学习刚刚开始**。后面还会在标准 Benchmark、Java 缺陷修复、Agent 轨迹和其他真实任务上继续把这块地图补完整。

## 主要实验产物

```text
data/eval/i5-human-calibration-blind.json
data/eval/i5-human-calibration-key.json
data/eval/i5-length-control.json
data/eval/i5-holdout-blind.json
data/eval/i5-holdout-key.json

data/reports/i5-pairwise-deepseek-chat-pilot.json
data/reports/i5-pairwise-qwen4-max-pilot.json
data/reports/i5-judge-comparison-pilot.json
data/reports/i5-length-deepseek-deepseek-chat.json
data/reports/i5-length-qwen-qwen4-max.json
data/reports/i5-holdout-v2-deepseek-chat.json
data/reports/i5-holdout-v2-qwen4-max-maxtokens512.json
data/reports/i5-holdout-v2-comparison.json
data/reports/i4-final-comparison-ci.json
data/reports/i5-i4-gate.json
data/reports/i0-numerical-alignment.json
data/reports/i5-regression-coverage.json
data/reports/i5-regression-summary.json

src/squid/eval/pairwise.py
src/squid/eval/qwen_judge.py
src/squid/eval/bootstrap.py

scripts/i5_calibration_export.py
scripts/i5_pairwise_judge.py
scripts/i5_judge_comparison.py
scripts/i5_length_control.py
scripts/i5_length_judge.py
scripts/i5_holdout_export.py
scripts/i5_i4_bootstrap_report.py
scripts/i5_i4_gate.py
scripts/i0_numerical_alignment_report.py
scripts/i5_regression_coverage.py
scripts/i5_regression.py
```
