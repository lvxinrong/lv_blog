+++
title = "diy-llm 立项书：给作品线配一条理论线"
slug = "diy-llm-proposal"
aliases = ["/diy-llm/diy-llm-proposal/"]
date = 2026-10-24T12:00:00+08:00
draft = false
tags = ["LLM", "diy-llm", "CS336", "立项", "学习笔记"]
summary = "diy-llm 与 nanochat 并列：作品线负责做得出，理论线负责懂得深。按里程碑配章节，不顺序通读，选修区按需捡回。"
[cover]
    image = "covers/diy-llm-proposal.jpg"
    alt = "diy-llm 立项书"
    hiddenInSingle = true
    hiddenInList = true
+++

> 这不是课程笔记的开篇，是立项书。项目名：diy-llm 理论线走读。发起人、执行人：我自己。评委：Kimi。

## 为什么并列，而不是顺序

《从零构建大模型》给了我 GPT-2 时代的零件，nanochat（lvchat）要把零件装成整车。但装车的过程中一定会碰到书里没有的现代地形：RoPE、RMSNorm、KV cache、数据配比、Scaling Laws、DPO/GRPO。

[diy-llm](https://github.com/datawhalechina/diy-llm)（DataWhale 出品，斯坦福 CS336 中文本土化课程，16 章 + 6 作业）恰好覆盖这些地形。昨晚粗翻了一遍，不少概念已经有了初步认识——说明它不是另起炉灶的新课，而是已有知识的深水区。

所以定位并列：**nanochat 是作品线，diy-llm 是理论线。作品线负责“做得出”，理论线负责“懂得深”。**

## 用法：按里程碑配章节，不顺序通读

每个 lvchat 里程碑开工前，先读对应章节；交付后可选做对应作业当加试题。映射表维护在 [lvchat 实现导图](/nanochat/lvchat-roadmap/)。

| lvchat 里程碑 | diy-llm 配套章节 |
| --- | --- |
| M1 自训 BPE tokenizer | 第 2 章 分词器 + 作业 1 |
| M2 预训练 | 第 3 章 + 第 11 章 + 第 9 章 |
| M3 KV cache 推理引擎 | 第 10 章 推理 |
| M4 SFT | 第 13 章 训练流程 |
| M5 评估框架 | 第 12 章 评估与基准 + 作业 6 |
| 架构升级（GPT-2 → 现代） | 第 4 章 RoPE/RMSNorm/SwiGLU |

选修区（roadmap 里“明确砍掉”的装备，想捡回来时的教材）：MoE（第 5 章）、GPU/分布式（第 6-8 章）、GRPO/RLVR（第 14 章）、多模态（第 15 章）。

## 验收

理论线的验收不是“读完了”，是“用上了”：某个里程碑的实现决策能说出依据，或者某章的作业真的跑通。读不动的时候优先保作品线，理论线可以等。
