+++
title = "手搓 LLM 笔记 28：I6 领域后训练起步——Java 缺陷定位与最小修复"
date = 2026-11-23
draft = true
slug = "llm-28-i6-java-defect-repair"
tags = ["LLM", "I6", "Java", "Defects4J", "领域后训练", "学习笔记"]
summary = "I6 起步草稿：选择 Defects4J 作为第一块 Java 缺陷修复评估场，冻结定位与最小 Patch 契约，正在搭建 WSL2 / Java 11 环境。原始基线、训练数据和 LoRA 对照尚未开始。"
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

Defects4J 的依赖安装与初始化正在执行，尚未完成 Lang-1 的 buggy / fixed 行为验收。

### 一次网络排障插曲

更换路由器后，Windows 将当前以太网识别为 Public，而 OpenSSH 入站规则只允许 Private，导致 Mac 的 SSH 连接停在 TCP 建连之前。

确认双方处于同一 `192.168.3.x` 网段后，将可信家庭网络从 Public 改为 Private，SSH 恢复。

这只是实验环境插曲，不计入模型能力成果。

## 七、下一步：先验收 Lang-1，不训练模型

初始化完成后，第一组验收固定为 `Lang-1`：

```text
checkout Lang-1b
→ 编译并运行触发测试
→ 确认 buggy 版本行为

checkout Lang-1f
→ 编译并运行相同测试
→ 确认 fixed 版本行为

使用 defects4j export
→ 导出源码目录、测试、classpath、修改类等元数据
→ 整理第一份标准评估输入
```

只有 buggy / fixed 两侧都可复现，后续模型生成与修复评估才有可靠底座。

## 八、当前停止边界

这篇草稿当前只记录：

- 任务范围与评估契约；
- Benchmark 选型理由；
- 数据隔离原则；
- 环境安装进度。

尚未完成：

- Lang-1b / Lang-1f 的实际验收；
- 第一份标准评估样本；
- 原始 Qwen3 基线；
- 领域训练数据构造；
- LoRA / 全参数对照；
- 任何模型能力提升证明。

因此 I6 目前仍是刚开工的阶段。先把评估场跑通，再讨论训练。

## 当前相关来源与产物

```text
https://github.com/rjust/defects4j
https://github.com/multi-swe-bench/multi-swe-bench
https://huggingface.co/datasets/ByteDance-Seed/Multi-SWE-bench
```

待后续实际运行后再补充：

```text
Defects4J 固定 commit
Lang-1b / Lang-1f 验收日志
标准输入 JSON
原始模型基线报告
训练数据与领域后训练报告
```
