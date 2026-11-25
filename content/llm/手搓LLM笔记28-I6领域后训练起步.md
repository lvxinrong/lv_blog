+++
title = "手搓 LLM 笔记 28：I6 领域后训练起步——Java 缺陷定位与最小修复"
date = 2026-11-23
draft = true
slug = "llm-28-i6-java-defect-repair"
tags = ["LLM", "I6", "Java", "Defects4J", "领域后训练", "学习笔记"]
summary = "I6 完成结构化局部编辑、8/16/32 样本学习曲线与 rank 16 对照：数据扩展和 rank 翻倍均未带来 validation 修复通过；Time 上可应用编辑从 0/4 提升到 4/4、编译从 0/4 到 1/4，但触发测试仍为 0/4。当前只证明契约学习，不证明修复泛化。"
[cover]
    image = "covers/llm-28-i6-java-defect-repair.jpg"
    alt = "手搓 LLM 笔记 28：I6 领域后训练起步"
    hiddenInList = true
    hiddenInSingle = true
+++

这篇是 I6 的起步草稿，承接 [笔记 27：I5 评估校准与回归基准自动化](/llm/llm-27-i5-judge-calibration-regression/)。

I5 结束以后，我对后训练多了一条更明确的约束：不能等训练完成以后，才找一个指标说明模型变好了。评估应该和任务、数据一起设计。

所以 I6 不从训练脚本开始，而从这三个问题开始：

```text
想让模型学会什么具体能力？
怎样证明它真的学会了？
训练数据与最终评估数据怎样隔离？
```

## 一、I6 的目标：不是泛化地“更会写 Java”

I6 的第一版领域限定为：**Java 缺陷定位与最小修复。**

不扩展到所有 Java 开发工作，也不把目标写成“训练一个精通后端开发的模型”。

任务范围暂时固定为：

```text
输入：
- buggy 版本的 Java 方法 / 相关类源码
- 触发测试或失败信息
- 必要的文件路径与项目元数据

输出：
1. 缺陷定位结果：文件、类、方法或关键行
2. 最小 unified diff Patch
```

最小验收不是回答看起来合理，而是：

```text
定位正确
Patch 可以应用
项目编译成功
触发测试从失败变为通过
相关回归测试保持通过
```

这些指标把“模型说了一段修复建议”和“模型实际修复了一个缺陷”分开。

## 二、为什么选择 Defects4J 作为第一块评估场

候选调研阶段对照了 Defects4J 与 Multi-SWE-bench。

| 维度 | Defects4J | Multi-SWE-bench |
| --- | --- | --- |
| 核心任务 | 已知缺陷复现、定位与程序修复 | 真实 GitHub Issue 的仓库级修复 |
| Java 规模 | 854 个 active bugs、17 个项目 | 128 个 Java 实例 |
| 修复边界 | 修复提交经过最小化，去除无关重构和功能新增 | 保留真实 Issue / PR 的仓库级上下文 |
| 验证方式 | 编译、触发测试、相关测试与元数据导出 | Docker 中应用 Patch，并检查测试状态变化 |
| 环境复杂度 | Java 11 + CLI，链路较短 | Docker、仓库镜像与评估配置，变量更多 |
| 当前定位 | 第一版本地可验证评估场 | 后续真实 Issue / 仓库级泛化对照 |

Defects4J 的关键优势是：每个 active bug 都有触发测试，在 buggy 版本失败，在 fixed 版本通过。

这正好对应 I6 的可验证目标。模型是否正确，不需要由另一个 LLM 评委凭文本风格判断，而可以由编译器和测试直接回答。

Multi-SWE-bench 仍然很有价值，但当前不直接上仓库级 Issue 修复。变量太多时，一旦失败，很难区分问题来自模型、Prompt、上下文、Agent 还是环境。

## 三、评估协议先于训练

第一版使用固定 Prompt、贪心生成、单次 Pass@1，不做反复重试，也不挑最好的一次结果。

需要分别记录：

```text
定位正确率
Patch 应用成功率
编译成功率
触发测试通过率
相关回归测试通过率
空输出 / 非法格式 / 超长截断比例
```

失败分类不能全部写成“未解决”：

```text
empty_response
invalid_patch_format
patch_apply_failed
compile_failed
triggering_test_still_failed
regression_test_failed
wrong_localization
length_limited
```

只有这些失败类型被保留下来，后续 LoRA 才能帮助判断训练究竟改善了哪一类问题。

## 四、数据隔离需要从第一天开始

评估集不能先拿去训练，再把训练后的分数当成能力提升。

后续 Java 修复数据需要按以下维度去重与隔离：

```text
仓库 / 项目
Issue / PR
commit
缺陷族
```

Defects4J 与 Multi-SWE-bench 中存在相同项目，例如 Mockito。不能只看实例 ID 就默认不存在重叠。

如果未来使用 Defects4J 内部划分训练与测试，也优先考虑按项目隔离，而不是把同一项目的代码片段随机拆开。否则训练数据很容易记住项目特有的实现模式，测试分数无法代表对陌生项目的泛化能力。

## 五、模型与训练方法暂时没有定死

当前优先候选仍然是已有 V4 / Qwen3-0.6B 与 LoRA。

但这只是候选方案，不是已经确认的最佳方法。需要先建立原始模型基线，观察它主要失败在哪里：

- 不理解任务契约；
- 找不到缺陷位置；
- 生成 Patch 格式错误；
- 定位正确但修复错误；
- 上下文不足；
- 缺乏必要的项目或工具信息。

不同失败原因不一定都靠训练解决。有些问题可能需要检索、工具调用或更好的上下文组织，而不是直接改权重。

如果从零训练或使用大规模全参数训练，还需要另做资源评估。I6 不把这种扩张当作当前前置条件。

## 六、当前环境进度

本轮选择直接在 Windows + WSL2 中搭评估与训练闭环，不再先在 Mac 上重复搭建一套。

当前已经实际完成：

```text
WSL2 发行版：Ubuntu 24.04.3 LTS
Java / javac：11.0.33.1
Git：2.43.0
Subversion：1.14.3
Perl：5.38.2
cpanm：1.7047
WSL 文件系统剩余空间：约 944G
```

其中：

- Java 11 用于编译和运行 Defects4J 项目；
- Git / SVN 用于读取不同项目的历史版本；
- Perl 是 Defects4J 框架的重要组成部分；
- cpanm 用于安装仓库声明的 Perl 依赖。

Defects4J 的依赖安装与初始化已经完成。44 个 Perl distributions 安装成功，官方初始化脚本正常结束，框架入口 `defects4j info -p Lang` 已验证。

### 一次网络排障插曲

更换路由器后，Windows 将当前以太网识别为 Public，而 OpenSSH 入站规则只允许 Private，导致 Mac 的 SSH 连接停在 TCP 建连之前。

确认双方处于同一 `192.168.3.x` 网段后，将可信家庭网络从 Public 改为 Private，SSH 恢复。

这只是实验环境插曲，不计入模型能力成果。

### 工作目录持久化

最初的部分工作区位于 `/tmp`。WSL 停止或系统清理后，临时目录消失，需要重新 checkout。后续 I6 工作目录统一放到：

```text
~/experiments/i6/workdirs
```

`defects4j` 的 PATH、时区和用户级 Perl 环境整理到：

```text
~/experiments/defects4j-env.sh
```

重连后通过 `source` 恢复，不再依赖上一次 SSH 会话中的临时变量。

## 七、原始模型基线：先把失败类型分清

### 1. Lang-1：raw unified diff 不可应用

buggy / fixed 行为已经实际验证：

```text
Lang-1b：编译成功，TestLang747 失败
Lang-1f：编译成功，Failing tests: 0
```

元数据：

```text
buggy commit：396afc3e4693cfee182efe582455f2d97058c068
fixed commit：d1a45e9738de5b3e299bb51e987565dcce55fee6
修改类：org.apache.commons.lang3.math.NumberUtils
触发测试：NumberUtilsTest::TestLang747
```

原始模型返回的 diff 包含 Markdown 代码围栏、伪造 index hash、错误的 hunk 行数，并且只有删除原方法，没有实际修复新增行。

真实只读校验：

```text
git apply --check
→ error: corrupt patch at line 33
```

因此分类为：

```text
invalid_patch_format
```

它没有进入编译和触发测试阶段，不能记成“修复方案被测试否定”。

### 2. Lang-3：从输出格式问题走向真实修复失败

buggy / fixed 行为：

```text
Lang-3b：编译成功，testStringCreateNumberEnsureNoPrecisionLoss 失败
Lang-3f：编译成功，Failing tests: 0
```

元数据：

```text
buggy commit：64cfee77e333d0c31a0fde0abe6dac3d97b0f078
fixed commit：8a1042959df80c06dbfa83896594caa8e20ff9d6
修改类：org.apache.commons.lang3.math.NumberUtils
```

原始 raw diff 输出在 1024 tokens 处截断，且出现 `100%` 等异常内容，`git apply --check` 失败。

增加一个与缺陷无关的合法 diff 格式示例后，模型开始以 `diff --git` 开头，也不再整段删除方法，但仍然没有产生合法的新增修复行，没有补上精度限制。格式引导只改变表面形式，没有解决修复语义。

### 3. 完整方法输出：局部修改合理，但主缺陷仍未修复

随后把输出契约从 unified diff 改为“修复后的完整方法”，由我们负责后续方法替换与评估。

模型输出中出现了：

```diff
- d.floatValue()
+ d.doubleValue()
```

这个局部修改保留了 Double 当前的精度，是合理的。但它没有增加 Lang-3 需要的：

```text
numDecimals <= 7  → Float
numDecimals <= 16 → Double
```

将候选方法替换到独立工作区后，真实验收结果为：

```text
方法替换：passed
编译：成功
触发测试：失败
evaluation_status：trigger_test_failed
```

所以当前基线不是简单的“模型只会复制”。它能做局部语义修改，但没有识别并修复测试真正要求的精度分支。

## 八、单样本 LoRA 冒烟：训练样本修复成功，迁移未发生

### 1. Lang-5 训练数据

选择 Lang-5 的 LocaleUtils.toLocale 作为第一份训练候选。真实修复只涉及单文件、单方法，符合当前训练契约。

样本审计结果：

```text
full_tokens：1424
supervised_tokens：561
fixed_method_characters：2628
```

输入为 buggy 方法与触发测试，训练目标为 fixed 方法。Lang-5 标记为 `train_candidate`，Lang-1 / Lang-3 不进入这条训练样本。

### 2. 一次更新与 32 次更新

LoRA 配置：

```text
rank = 8
alpha = 16
context_size = 2048
batch_size = 1
activation_checkpointing = true
可训练参数：6,269,952（约 1.0519%）
```

一次更新：

```text
train loss：0.119955 → 0.113637
optimization_steps：1
adapter：25,210,667 bytes
严格重载：passed
```

但生成结果仍基本保留 buggy 方法，没有学会下划线 Locale 修复分支。

32 次更新：

```text
train loss：0.119955 → 0.000183
optimization_steps：32
adapter：25,211,467 bytes
严格重载：passed
```

此时模型生成了完整的 `_GB` / `_GB_POSIX` 等下划线处理分支。

真实方法替换、编译和测试：

```text
method_replacement：passed
compile_returncode：0
trigger_test_passed：true
evaluation_status：trigger_test_passed
```

这证明 LoRA 能拟合训练样本，并通过 Defects4J 的可执行验收。它只证明训练样本过拟合成功，不是未见缺陷或未见项目的泛化证据。

### 3. Lang-3 的迁移对照

将同一个 Lang-5 adapter 用于 Lang-3，输出没有补上 `numDecimals` 精度限制。

独立工作区验收结果：

```text
方法替换：passed
编译：成功
触发测试：失败
evaluation_status：trigger_test_failed
```

所以当前结论是：**单样本 LoRA 能学会 Lang-5，但没有给 Lang-3 带来可测的修复提升。**

## 九、小批量完整方法训练：样本增加没有直接转化为修复能力

### 1. 批量审计与数据隔离

单样本闭环完成后，下午开始批量审计 Defects4J 缺陷，不再逐个人工摸排。

Lang-16 至 Lang-25 这一批共审计 10 个 ID，结果为：

```text
single_method_candidate：7
inactive_or_unknown：2
class_level_only：1
```

单方法候选为 Lang-16、17、19、20、21、22、24。Lang-20 因 `method:join` 无法唯一确定方法签名而进入 `needs_review`，没有为了凑样本强行生成。

完整方法 v3 数据最终按以下角色隔离：

```text
train：Lang-5、6、9、14、16、17、19、21、22、24
validation：Lang-10
held-out：Lang-1、Lang-3
```

Lang-1、Lang-3 没有进入训练。数据构造脚本同时检查训练角色、`excluded_from_training` 和实例 ID 重叠，避免无意中把评估样本拿去训练。

### 2. 10 train + 1 validation 的完整方法 LoRA

训练配置保持为：

```text
模型：Qwen3-0.6B
epochs：5
batch_size：1
learning_rate：1e-5
rank：8
alpha：16
context_size：8192
optimization_steps：50
```

真实训练结果：

```text
initial train loss：0.215521
initial validation loss：0.162649
final train loss：0.112916
final validation loss：0.089339
best validation loss：0.080126（step 13）
trainable parameters：6,269,952
adapter reload：passed
```

但真实修复结果没有同步变好：

- Lang-10 使用 best adapter 后，方法替换和编译成功，触发测试仍失败；
- Lang-3 的输出自然结束，但大括号数量为 45 / 44，分类为 `malformed_method`；
- 训练样本 Lang-16 无论使用 best 还是 final adapter，均为编译成功、触发测试失败。

所以不能说“0.6B 学不会”，也不能说“LoRA 已提升领域能力”。loss 下降只说明目标 token 的预测损失下降，不等于可执行修复成功。

### 3. Lang-16 暴露出的监督稀释

Lang-16 的参考修复实际上只有一行：让十六进制前缀判断同时支持大写 `0X` 和 `-0X`。

```diff
-        if (str.startsWith("0x") || str.startsWith("-0x")) {
+        if (str.startsWith("0x") || str.startsWith("-0x") || str.startsWith("0X") || str.startsWith("-0X")) {
```

但完整方法训练目标有 6079 个字符、1212 个监督 token。模型把绝大部分训练容量用在复制原本就正确的方法体上，真正需要学习的一行修改被大量复制 loss 稀释。

这不是简单的“数据太少”，而是**输出契约让学习信号落在了错误的位置**。

## 十、结构化局部编辑：让模型提议修改，让评估器执行修改

### 1. 新的输出契约

完整方法输出改为结构化局部编辑：

```json
{
  "action": "replace",
  "target_method": "createNumber",
  "old_text": "需要修改的精确且唯一原文",
  "new_text": "用于替换原文的最小修复代码"
}
```

模型只负责提出编辑。评估器负责检查字段、目标方法、原文唯一匹配，只替换一次，然后在独立副本中编译和运行测试。

这不是让模型做全局查找替换，也不会自动补括号、修复 JSON 或把接近的输出“救活”。匹配为零或大于一次都应保守失败。

### 2. 原始模型与 Lang-16 单样本结构化冒烟

原始 Qwen3-0.6B 在 Lang-16 上输出过 `old_text == new_text`，分类为 `no_op_edit`。这说明只改 Prompt 不会自动得到正确修复。

随后只使用 Lang-16 构造一份结构化样本：

```text
full_tokens：2496
supervised_tokens：80
```

监督目标从完整方法的 1212 token 缩短到约 80 token。训练与验证在这里使用同一份冒烟样本，因此 validation loss 也只反映拟合程度，不代表泛化。

32 epochs、32 次更新后的结果：

```text
initial train loss：0.392564
final train loss：0.040485
best validation loss：0.041319（step 29）
adapter reload：passed
```

模型精确生成了包含 `0X` / `-0X` 的单行替换。真实评估为：

```text
validation：ready_to_apply
match_count：1
compile_returncode：0
trigger_test_passed：true
evaluation_status：trigger_test_passed
```

这再次证明训练链路能够记住一个训练样本，而且结构化契约可以进入真实编译测试闭环。

但把同一个 adapter 用于 held-out Lang-3 时，模型错误地把整数分支改成 Float / Double / BigDecimal 分支。虽然唯一匹配并编译成功，触发测试仍然失败，分类为 `wrong_repair`。

因此，**结构化格式学会、训练样本记住、未见缺陷会修复，是三个不同结论。**

## 十一、批量结构化转换：困难在锚点，而不是 JSON

### 1. 前两版转换都没有达标

第一版只截取修改行，结果为 5 train、0 validation、6 个转换失败：

- Lang-14、17、10：`match_not_found`；
- Lang-9：`ambiguous_match`，同一锚点出现 5 次；
- Lang-19、Lang-5：包含多个不连续 hunk，当前契约不支持。

第二版改为保留完整 hunk 上下文，但仍然是 5 train、0 validation、6 个失败。Lang-9 的重复匹配被上下文消除，Lang-22 却加入了新的匹配失败。

逐例打印参考 Patch、`old_text` 和 buggy 方法后，根因得到确认：

- Lang-10、Lang-22 把方法前的 Javadoc 带入了 `old_text`；
- Lang-14 把方法后的 `/**` 带入了 `old_text`；
- Lang-17 带入了方法结束后的空行，末尾多出一个 `\n`，而提取的方法源码没有末尾换行；
- Lang-5、Lang-19 仍是真实的多 hunk，不应拼成一份错误的连续编辑。

### 2. 最小修改核心加必要的唯一上下文

最终转换算法不再保留整个 hunk，也不退回完整方法：

1. 先取包含全部实际修改的最小连续核心；
2. 如果原文在目标方法中唯一，直接生成编辑；
3. 如果出现重复，逐行向左右扩展 hunk 中已有的上下文；
4. 只接受在 buggy 方法中精确出现一次的候选；
5. 匹配不到、无法唯一匹配或存在多个 hunk 时继续保守失败。

这一版结果为：

```text
train samples：8
validation samples：1
conversion failures：2
```

剩下的两个失败就是明确超出当前单 hunk 契约的 Lang-5 和 Lang-19。Lang-1、Lang-3 继续只作为 held-out，不进入训练。

Mac 上相关单测实际结果为 **11 passed**。Mac 提交与 WSL 拉取版本均为 `8a2638d`；代码和单测在 Mac，数据转换、训练和 Defects4J 评估在 WSL。

同时修正了两处审计元数据：结构化样本的 `data_role` 不再全部写成 smoke，训练报告中的 train / validation 数量也改为实际值。

## 十二、8 样本结构化 LoRA：仍未跨过训练拟合门槛

### 1. 5 epochs 训练结果

为了与完整方法小批量实验尽量保持可比，仍使用 5 epochs、相同学习率、LoRA rank / alpha 和 8192 context。

```text
train samples：8
validation samples：1
optimization_steps：40
initial train loss：0.694831
initial validation loss：0.391292
final train loss：0.357563
final validation loss：0.357516
best validation loss：0.347862（step 5）
trainable parameters：6,269,952
adapter bytes：25,212,731
best / final adapter reload：passed
```

这里的 `0.347862` 不能和完整方法实验的 `0.080126` 直接比较。两次监督文本、目标长度和 token 分布不同，loss 不是同一标尺。

### 2. best adapter 的真实生成结果

| 实例 | 数据角色 | 生成侧结果 |
| --- | --- | --- |
| Lang-16 | train | 不断重复十六进制判断，JSON 不完整，`invalid_json` |
| Lang-10 | validation | `no_op_edit` |
| Lang-1 | held-out | `no_op_edit` |
| Lang-3 | held-out | `no_op_edit` |

这一轮还发现了评估脚本 `apply_structured_edit.py` 第 50 行的独立缩进错误。因此上述结果都停留在生成侧，没有进入编译和测试，不能记成 `trigger_test_failed`。

缩进修正后，`py_compile` 已通过。这是评估基础设施修复，不计入模型能力结果。

### 3. final adapter 对照

已有的 5 epochs final adapter 也完成了同一批生成检查：

| 实例 | 生成侧结果 | 生成 token | 结束原因 |
| --- | --- | ---: | --- |
| Lang-16 | `match_not_found` | 394 | stop |
| Lang-10 | `no_op_edit` | 207 | stop |
| Lang-1 | `match_not_found` | 113 | stop |
| Lang-3 | `no_op_edit` | 527 | stop |

final adapter 同样是 **0/4 `ready_to_apply`**，所以没有候选进入编译和触发测试。

最重要的负结果不是 held-out 又失败了，而是：**连已经参与训练的 Lang-16 都没有生成可应用修复。**

这意味着当前 5 epochs 模型连“训练集拟合良好”都没有证明，更谈不上过拟合。过拟合应当是训练样本表现很好、未见样本表现差，而不是训练与评估都失败。

目前只实际检查了 Lang-16 这一个训练样本，不能扩张成“全部 8 个训练样本都失败”。但 Lang-16 已足以让训练拟合 sanity check 不通过。

## 十三、32 epochs：训练样本终于学会，但未见样本仍未修复

### 1. 为什么补做优化充分性对照

5 epochs 的 final adapter 连训练样本 Lang-16 都没有学会，因此不能直接把失败归因于泛化不足。

此前 Lang-16 单样本成功实验看过同一样本 32 次，而 8 样本、5 epochs 实验中，每个样本只学习了 5 次。为对齐单个样本的曝光次数，补做 32 epochs 对照。

除 epochs 外，数据、学习率、batch size、LoRA rank / alpha 和 8192 context 均保持不变。实验预期并实际产生了 256 次更新。

### 2. loss 曲线出现明确的阶段性

```text
initial train loss：0.694831
initial validation loss：0.391292
best validation loss：0.270363（step 45）
final train loss：0.101296
final validation loss：0.372016
optimization_steps：256
adapter bytes：25,213,131
best / final adapter reload：passed
```

validation loss 在 step 45 到达最低点，随后整体持续回升；train loss 则继续下降，不少抽样 batch 已降到 `0.001～0.03`。

这说明 loss 上出现了过拟合趋势，但此时仍不能直接写成“修复能力已经过拟合”。是否记住训练样本，必须由真实生成、编译和测试回答。

### 3. e32 final 首先通过 Lang-16 训练拟合检查

e32 final adapter 对 Lang-16 精确生成了训练目标中的单行替换：

```diff
-        if (str.startsWith("0x") || str.startsWith("-0x")) {
+        if (str.startsWith("0x") || str.startsWith("-0x") || str.startsWith("0X") || str.startsWith("-0X")) {
```

真实评估结果：

```text
validation：ready_to_apply
match_count：1
unique_match：true
compile_returncode：0
trigger_test_passed：true
evaluation_status：trigger_test_passed
```

这证明在 8 样本混合训练下，模型仍然能够记住 Lang-16。5 epochs 确实存在训练不足，结构化输出契约和 LoRA 训练链路本身可以工作。

但这只是 8 个训练样本中的一个，不能扩张为“全部训练样本都已拟合”。

### 4. step-45 best 与 e32 final 的完整对照

best adapter 是按 validation loss 预先选出的主对照。两个已有 adapter 都保留评估，不根据 held-out 成绩重新挑模型。

| 实例 | 数据角色 | e32 best（step 45） | e32 final |
| --- | --- | --- | --- |
| Lang-16 | train | 编译成功，触发测试通过 | 编译成功，触发测试通过 |
| Lang-10 | validation | 唯一匹配，但 `compile_failed` | `match_not_found` |
| Lang-1 | held-out | `match_not_found` | `match_not_found` |
| Lang-3 | held-out | `match_not_found` | `ambiguous_match` |

Lang-10 的 best 候选试图修改正则转义分支，生成了：

```java
regex.append('\');
```

这不是合法的 Java 字符字面量。编译器在 `FastDateParser.java:325` 报 `unclosed character literal`，因此分类为 `compile_failed`，没有进入触发测试。

不能人工把反斜杠补成合法代码后再记为模型成功。即使这样做让编译通过，也不会自动修复 Lang-10 的空白处理缺陷。编译门在这里拦住了一个无效候选，说明可执行评估确实必要。

e32 final 在 Lang-10、Lang-1、Lang-3 上都没有产生可应用编辑，因而没有进入编译和测试。更多训练没有改变“未见样本没有成功修复”的结果。

## 十四、本轮停止边界

到这里，可以把这轮“输出契约与优化充分性”对照定格为：

- 完整方法输出会让极小修复被大量复制 token 稀释；
- 结构化局部编辑能把监督集中到实际修改，并支持严格、可执行的评估；
- 单样本结构化 LoRA 能记住 Lang-16，但没有证明 held-out 修复能力；
- 8 样本、5 epochs 的结构化 LoRA 未通过 Lang-16 训练拟合检查；
- 32 epochs 后，best 和 final 都能修复训练样本 Lang-16，训练不足问题得到改善；
- step-45 best 至少能为 validation Lang-10 生成可应用候选，但该候选编译失败；
- e32 final 的三个未见样本全部停在生成侧，没有表现出比 best 更好的修复能力；
- 当前没有任何已验证的 validation 或 held-out 修复成功，更没有未见项目的泛化证据。

这些结果不能用来推断 Qwen3-0.6B 的能力上限。数据规模、缺陷多样性、上下文信息和基座能力仍然混在一起，不能单独归因。

当前不再继续增加 epochs，也不急着扩大数据或引入新方案。先保留所有 adapter、模型响应、评估报告和负结果，后续方向另行决定。

本轮主要新增产物包括：

```text
data/instruct/i6_repair_v3_train.json
data/instruct/i6_repair_v3_val.json
data/instruct/i6_structured_v3_train.json
data/instruct/i6_structured_v3_val.json

data/model_pth/qwen3/i6-repair-lora-v3-best.pth
data/model_pth/qwen3/i6-lang16-structured-lora.pth
data/model_pth/qwen3/i6-structured-lora-v3-best.pth
data/model_pth/qwen3/i6-structured-lora-v3-e5.pth
data/model_pth/qwen3/i6-structured-lora-v3-e32-best.pth
data/model_pth/qwen3/i6-structured-lora-v3-e32.pth

data/reports/i6-repair-lora-v3-training.json
data/reports/i6-lang16-structured-lora-training.json
data/reports/i6-structured-lora-v3-training.json
data/reports/i6-structured-lora-v3-e32-training.json

~/experiments/i6/reports/lang16-structured-v3-e32-final-eval.json
~/experiments/i6/reports/lang16-structured-v3-e32-best-eval.json
~/experiments/i6/reports/lang10-structured-v3-e32-best-eval.json
```

## 十五、重新冻结协议：数据量与 rank 分开验证

上一阶段停止后，新一轮实验仍然只使用 Qwen3-0.6B，但把数据量和 LoRA rank 拆成两个对照。

主配置为：

```text
输出：结构化局部编辑
初始 rank：8
初始 alpha：16
learning rate：1e-5
batch size：1
epochs：32
正式训练 context：4096
CUDA allocator：expandable_segments
```

数据角色重新冻结为：

```text
train：8 / 16 / 32 个严格嵌套的 Lang + Math 实例
validation：Lang-10、Lang-26、Lang-28、Math-2
开发诊断：Lang-1、Lang-3
最终项目级 held-out：Time-4、Time-5、Time-7、Time-8
```

Time 实例全部标记为 `eval_holdout`，`excluded_from_training=true`。三份实际训练 JSON 均确认不包含 Time。Time 的私密参考转换检查只用于确认评估契约可用，没有调用训练或更新权重。

checkpoint 的可执行选择顺序固定为：

```text
触发测试通过数
→ 编译通过数
→ ready_to_apply 数
→ validation loss
```

这轮固定的是 32 epochs，而不是固定总更新数。因此：

```text
8 samples  × 32 epochs = 256 steps
16 samples × 32 epochs = 512 steps
32 samples × 32 epochs = 1024 steps
```

它衡量的是相同单样本曝光次数下的数据与计算量共同扩展，不是严格的等算力对照。样本数、更新步数和 tokens seen 必须一起报告。

## 十六、工程排障：路径、Prompt、显存与评估口径

### 1. 历史源码布局不再写死

Lang-36 的真实源码位于 `src/java`，而不是 `src/main/java`。原批量审计因此在 FileNotFoundError 后中断，后续 Math / Time 完全没有开始。

修复后，单样本构造、批量审计和批量样本构造共用 `find_java_file()`，支持多个源码与测试根目录，并要求唯一匹配。批量审计增加 `audit_error` 和 `checkout_error`，单个实例失败后保留错误并继续。

相关单测最终覆盖源码与测试的旧式目录布局、checkout 异常分支和方法选择；三批真实审计均完整写出报告，没有遗留审计错误。

### 2. 训练和推理共用同一份 Prompt

训练脚本与推理脚本原本各写了一份结构化编辑 Prompt，措辞存在差异。后续将推理侧 Prompt 固化为 `build_structured_task()`，训练数据也调用同一函数。

相关结构化测试为 **13 passed**，其中也覆盖从 adapter 存档自动读取 rank / alpha，避免 rank 16 被按 rank 8 加载。

### 3. 4096 是运行可行性修正，不是模型调优

16 样本在 8192 context 下曾出现 CUDA OOM。检查时没有残留计算进程，8 与 16 样本的最长输入又完全相同，都是 Lang-24 的 3413 tokens，因此不能归因于新增样本更长。

另一次运行长期停在 step 12，GPU 利用率接近 100%、显存接近 12 GB。终止该进程后，改为：

```text
context_size = 4096
PYTORCH_CUDA_ALLOC_CONF = expandable_segments:True
```

1 epoch、16 次更新的冒烟完整通过，后续正式 8 / 16 / 32 与 rank 16 训练均沿用该配置。

当前模型为每层预分配 `context_length × context_length` 的布尔 mask。28 层从 8192 降到 4096，理论上少占约 1.3 GiB。实际运行也明显更顺畅，但没有做严格 wall-time 对照，因此不报告加速倍数。

4096 与 8192 的 8 样本训练 loss 数字完全一致，符合当前样本均未超过 3413 tokens 的事实。降低预分配 context 没有改变有效训练内容。

### 4. 周期 validation 有一个必须保留的口径限制

训练脚本调用周期评估时使用 `eval_iter=1`。当前 validation 有 4 个样本、batch size 为 1，所以：

- 周期打印与 best adapter 保存只看第一条 validation；
- final full validation loss 才计算全部 4 条。

因此 best probe loss 与 final full validation loss 不是同一统计范围，不能用二者差值精确量化过拟合。周期曲线仍可反映固定探针样本的趋势，最终 best / final 选择则使用 4 条 validation 的真实编译与测试结果。

这一限制不追溯美化前面的训练曲线；若继续训练，应先把周期 validation 改为全量计算。

## 十七、8 / 16 / 32 样本学习曲线：loss 改善，修复率没有改善

### 1. 训练指标

| 训练样本数 | steps | best probe loss | best step | final train loss | final full validation loss |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 8 | 256 | 0.281917 | 45 | 0.096723 | 0.401462 |
| 16 | 512 | 0.244578 | 41 | 0.068224 | 0.451176 |
| 32 | 1024 | 0.235986 | 73 | 0.076630 | 0.581424 |

best probe loss 随样本增加而下降，但 16 → 32 的改善已经变小。final train loss 与 final full validation loss 的统计范围不同，且 final 表现并未随样本量增加而改善。

### 2. 同一组 4 个 validation 的可执行结果

下表依次记录 `ready_to_apply / 编译通过 / 触发测试通过`：

| 样本数 | best | final | 按冻结规则选择的诊断 checkpoint |
| ---: | --- | --- | --- |
| 8 | 3 / 2 / 0 | 1 / 0 / 0 | best |
| 16 | 2 / 1 / 0 | 3 / 1 / 0 | final |
| 32 | 1 / 1 / 0 | 3 / 0 / 0 | best |

所有配置的 validation 触发测试通过数都是 **0/4**。

因此，增加样本和更新步数没有带来已验证的 validation 修复收益。token loss 的改善不能替代程序修复结果。

失败候选也显示问题已经超出 JSON 和锚点：Lang-28 会随意修改实体值，Math-2 会把超几何均值的分母改成错误表达式，部分 final 候选还会引入未定义的 `n`、`m`。即使候选能唯一匹配，修复内容仍然可能完全错误。

## 十八、rank 16：拟合能力增强，但 validation 修复仍为零

在冻结的 32 样本、32 epochs、4096 context 上，将 rank 从 8 增到 16。当前实现使用 `alpha / rank` 缩放，因此 alpha 同步从 16 增到 32，保持比例为 2。

```text
trainable parameters：6,269,952 → 12,539,904
adapter bytes：25,214,795 → 50,295,003
optimization steps：1024（两者一致）
```

训练结果：

| 指标 | rank 8 | rank 16 |
| --- | ---: | ---: |
| best probe loss | 0.235986 | 0.235595 |
| best step | 73 | 41 |
| final train loss | 0.076630 | 0.024013 |
| final full validation loss | 0.581424 | 0.923282 |

rank 16 的 final train loss 明显更低，说明增加的容量确实增强了拟合能力。但 best probe loss 几乎没有变化。

同一组 validation 的可执行结果为：

| rank | adapter | ready | 编译通过 | 触发测试通过 |
| ---: | --- | ---: | ---: | ---: |
| 8 | best | 1/4 | 1/4 | 0/4 |
| 8 | final | 3/4 | 0/4 | 0/4 |
| 16 | best | 1/4 | 1/4 | 0/4 |
| 16 | final | 3/4 | 1/4 | 0/4 |

rank 16 best 在四个实例上的分类与 rank 8 best 一致。rank 16 final 产生了更多可应用候选，但仍有非法 JSON、编译失败和错误修复，没有任何触发测试通过。

因此本轮结论是：**rank 翻倍增强了训练集拟合，没有转化为 validation 修复收益，并伴随更强的过拟合。** 当前没有依据继续增加 rank 32。

## 十九、Time 最终验收：契约学会，不等于缺陷修好

### 1. 最终配置在查看 Time 前冻结

按 validation 的可执行选择规则，8 样本 rank 8 best 的编译通过数为 2/4，高于其他配置。因此最终使用：

```text
8 train
rank 8，alpha 16
32 epochs
step-45 best adapter
4096 训练 context
```

Time-4、5、7、8 的参考修复均先通过结构化转换检查。最终验收只比较原始 Qwen3-0.6B 与这个预先选出的 adapter，不在 Time 上重新选择样本数、rank 或 checkpoint。

### 2. 原始模型与训练后模型

| 指标 | 原始模型 | 选定的 8 样本 rank-8 adapter |
| --- | ---: | ---: |
| ready_to_apply | 0/4 | 4/4 |
| 编译通过 | 0/4 | 1/4 |
| 触发测试通过 | 0/4 | 0/4 |

原始模型的输出为：

```text
Time-4：invalid_json
Time-5：no_op_edit
Time-7：invalid_json
Time-8：invalid_json
```

训练后的输出为：

```text
Time-4：compile_failed
Time-5：compile_failed
Time-7：compile_failed
Time-8：trigger_test_failed
```

这是一条真实但边界很窄的正结果：在未见项目上，后训练让模型从无法遵守结构化编辑契约，提升到四个实例都能生成唯一匹配并可应用的编辑，其中一个还能编译。

但最终修复仍是 **0/4**。4/4 `ready_to_apply` 不能写成 4/4 修复成功，也不能据此声称获得未见项目的程序修复泛化能力。

## 二十、当前阶段边界：I6 尚未完成

**I6 今天不能标记为完成。** 它的目标是 Java 缺陷定位与最小修复，而当前 validation 和 Time 的触发测试通过数仍为零。结束的只是这一批数据量与 rank 对照实验，不是 I6 的目标本身。

这一轮实验分别回答了：

- 结构化局部编辑能否训练并进入真实编译测试：可以；
- 增加 epochs 是否能改善训练样本拟合：可以，Lang-16 已验证；
- 8 → 16 → 32 是否提高 validation 修复率：没有；
- rank 8 → 16 是否提高 validation 修复率：没有；
- 后训练是否改善未见项目上的结构化输出与可应用性：在 4 个 Time 实例上有明显改善；
- 是否已经学会修复未见缺陷或未见项目：没有证据，所有最终 trigger 通过数仍为零。

这些结果不能单独证明数据规模、rank 或 0.6B 基座的理论上限。它们只说明当前数据、任务契约和训练配置下，收益停在了结构化可应用性，而没有到达正确修复。

下一阶段暂不继续增加样本、epochs 或 rank。先保留所有 adapter、响应和评估报告，再考虑用开发样本做“给定正确位置”诊断，区分定位与修复内容；候选覆盖、span ID 和约束解码都属于后续独立实验，尚未执行或验收。

本轮后续主要产物包括：

```text
data/instruct/i6_structured_08_train.json
data/instruct/i6_structured_16_train.json
data/instruct/i6_structured_16_val.json
data/instruct/i6_structured_32_train.json
data/instruct/i6_structured_32_val.json

data/model_pth/qwen3/i6-structured-08-r8-e32-c4096-best.pth
data/model_pth/qwen3/i6-structured-16-r8-e32-c4096-best.pth
data/model_pth/qwen3/i6-structured-16-r8-e32-c4096.pth
data/model_pth/qwen3/i6-structured-32-r8-e32-c4096-best.pth
data/model_pth/qwen3/i6-structured-32-r16-e32-c4096-best.pth
data/model_pth/qwen3/i6-structured-32-r16-e32-c4096.pth

data/reports/i6-structured-08-r8-e32-c4096-training.json
data/reports/i6-structured-16-r8-e32-c4096-training.json
data/reports/i6-structured-32-r8-e32-c4096-training.json
data/reports/i6-structured-32-r16-e32-c4096-training.json

~/experiments/i6/holdout_checks/time-4.json
~/experiments/i6/holdout_checks/time-5.json
~/experiments/i6/holdout_checks/time-7.json
~/experiments/i6/holdout_checks/time-8.json
```

## 二十一、方法论复盘：从向 AI 要答案，到自己设计实验

近期的微调实验让我深刻意识到：**控制变量不是科研写作里的装饰，而是机器学习实验能够归因、复现和落地的工程纪律。**

过去遇到模型不拟合或表现差时，很容易陷入乱试：同时调整样本量、学习率、rank 和 Prompt，看到一个稍好的 loss 就继续加码。即使最后结果变好，也无法回答究竟是哪一个改动起了作用；如果结果变差，更不知道该回退哪一步。

现在必须先把顺序固定下来：**先定实验框架，再分离变量；先准备对照，再开始训练。**

每次实验都要明确唯一主动改变的变量。例如观察 8、16、32 样本时，模型、rank、学习率、Prompt、解码方式和评估集都应保持不变，并准备同类对照组与横向对比数据。不能拿某次实验的 best 和另一次实验的 final 随意拼接，也不能把不同数据口径下的 loss 当成同一标尺。

### 单一变量不等于只改一个命令行参数

本轮 8 / 16 / 32 实验固定了 epochs，但样本增加时，总更新步数同时从 256 增至 512、1024。样本量是我主动改变的变量，总计算量则是连带变化的变量。

如果不记录这个连带变化，就可能把“更多数据与更多计算共同带来的变化”错误归因于数据量本身。因此，控制变量不仅是说一句“其他都一样”，还要主动寻找那些没有被固定、甚至会随主动变量一起变化的因素。

以后的实验卡至少要写清：

```text
研究问题：这次究竟想验证什么？
主动变量：只允许哪一个因素变化？
固定变量：模型、数据、Prompt、seed、解码、训练预算中哪些不变？
连带变量：steps、tokens seen、耗时和显存是否随主动变量变化？
对照组：纵向历史对照与横向同条件对照分别是什么？
数据隔离：train / validation / held-out 是否真正分离？
真实验收：谁来判断成功，编译器、测试还是人工阅读？
停止条件：出现什么结果后不再继续加码？
```

如果实验卡写不清这些问题，就先不启动训练。

### AI 做红队，而不是替人决定真相

AI 可以极大地辅助批量审计、数据转换、日志归类和失败聚类，也可以检查 Prompt 漂移、指标口径和数据泄漏，节省大量重复劳动。但 AI 给出的解释仍然只是待验证假设，不是实验事实。

多模型审核的价值也不在于“多数模型同意就是答案”。更合理的分工是：

```text
人先提出研究问题并设计实验框架
→ 主 AI 协助补全流程与实现细节
→ 另一个 AI 做独立红队审查
→ 人处理分歧并冻结配置
→ 执行实验，保留全部原始结果
→ 用真实执行结果而不是模型投票裁决
```

红队审查至少要追问：

- 是否还有第二个变量同时变化？
- validation 与 held-out 是否被反复用于调参？
- 不同实验的指标是否同口径？
- 是否存在数据泄漏或近重复样本？
- 负结果是否被“loss 下降”掩盖？
- 当前证据是否还有同样合理的其他解释？

不同 AI 之间的分歧应该保留下来，作为需要验证的问题，而不是选择一个听起来更自信的说法。编译器、测试和原始日志比任何模型的口头判断都更有裁决权。

对我来说，接下来的核心目标，是完成从“向 AI 要答案的执行者”到“自己先设计实验框架，再让 AI 做红队审查”的转变。AI 可以放大执行效率，但人必须保留底层的工程直觉、问题意识和探索精神，并对实验边界与最终结论负责。

这才是小鱿鱼知识体系真正需要沉淀的能力：**不是记住某一次训练用了多少样本，而是能够独立设计一组严谨、可归因、可复核的实验。**

## 当前相关来源与产物

```text
https://github.com/rjust/defects4j
https://github.com/multi-swe-bench/multi-swe-bench
https://huggingface.co/datasets/ByteDance-Seed/Multi-SWE-bench

~/experiments/i6/cases/lang-1-case.json
~/experiments/i6/cases/lang-1-key.json
~/experiments/i6/cases/lang-3-case.json
~/experiments/i6/cases/lang-3-key.json
~/experiments/i6/cases/lang-5-case.json
~/experiments/i6/cases/lang-5-key.json

data/instruct/i6_lang5_smoke.json
data/model_pth/qwen3/i6-lang5-lora-smoke.pth
data/model_pth/qwen3/i6-lang5-lora-32steps.pth

data/reports/i6-lang-1-baseline.json
data/reports/i6-lang-3-baseline.json
data/reports/i6-lang-3-format-guide.json
data/reports/i6-lang-3-full-method.json
data/reports/i6-lang5-lora-smoke.json
data/reports/i6-lang5-lora-32steps.json
data/reports/i6-lang5-lora-smoke-response.json
data/reports/i6-lang5-lora-32steps-response.json
data/reports/i6-lang3-lora-32steps-response.json

~/experiments/i6/reports/lang-3-full-method-eval.json
~/experiments/i6/reports/lang3-lora-32steps-eval.json
~/experiments/i6/reports/lang5-lora-32steps-eval.json
```

Lang-4 的真实 Patch 涉及字段、构造器和方法，属于多位置修复，暂不进入当前单方法训练契约。后续需要扩展输出与评估契约时再使用，不能为了凑样本数而丢弃必要修改。
