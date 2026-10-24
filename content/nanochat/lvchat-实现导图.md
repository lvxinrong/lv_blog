+++
title = "lvchat 实现导图：开工顺序即依赖顺序"
slug = "lvchat-roadmap"
date = 2026-10-19T19:10:00+08:00
draft = false
tags = ["LLM", "nanochat", "lvchat", "学习笔记"]
summary = "不照抄 nanochat，以它为标准答案，从书里的手搓代码出发，自己长一个 nanochat-lite。八个里程碑，按依赖排序。"
[cover]
    image = "covers/lvchat-roadmap.jpg"
    alt = "lvchat 实现导图"
    hiddenInSingle = true
    hiddenInList = true
+++

> 本图是 [nanochat 立项书](/nanochat/nanochat-proposal/) 的施工图。原则：nanochat 仓库当「标准答案」，不当教材；从《从零构建大模型》的手搓代码出发，自己长一个 nanochat-lite（暂名 lvchat）。里程碑按依赖排序——开工顺序就是这张表的行序。

## 已持有资产（书给的）

GPT 模型本体、训练循环、loss、`generate`（temperature / top-k）、SFT 数据管道（掩码、+1、-100）、`get_device()`。

**M0 升级说明（2026-10-20）**：原计划是把这些代码「收拢」成骨架，现升级为**按工程结构重写**——分层（tokenizer / model / data / train / generate / eval / checkpoints）、单一配置入口、单一 device 入口、checkpoint 标准化。重写过程不翻书优先，翻一次记一笔欠账注释，写完清单归零。这个过程本身即《手搓 LLM 笔记 08》。

## 里程碑

| 阶段 | 内容 | 天数 | 验收 | nanochat 对照 |
| --- | --- | --- | --- | --- |
| M0 | 重写 lvllm：不按章节收拢，按工程结构**重写**书里全部代码（终极回炉），写成读书笔记 08 | 3–5 | 三个回归测试（分类 / 指令微调 / 生成）与旧仓库结果一致；欠账注释清单归零 | — |
| M1 | 自己训 BPE tokenizer（Python 实现，不用 tiktoken） | 2–3 | 编解码往返无损 + 压缩率可测 | `tokenizer.py` |
| M2 | 预训练：token 流打包、dataloader、cosine LR、梯度累积、bpb 指标 | 3–5 | bpb 曲线真实下降 + 模型咿呀学语 + checkpoint 带 config | `base_train.py` `dataloader.py` |
| M3 | 推理引擎：给 generate 装 KV cache | 2 | 输出与朴素版逐字一致，提速可测量 | `engine.py` |
| M4 | SFT：第七章管道移植，打开 completion-only | 2 | 套模板回答 + 评估集分数 | `chat_sft.py` |
| M5 | 评估框架：基模选择题 + DeepSeek 评委 | 1–2 | 一键出 JSON 报告 | `core_eval.py` `chat_eval.py` |
| M6 | 对话界面：CLI + 简单 Web 页 | 1–2 | 祁总打开浏览器能跟它聊上 | `chat_cli.py` |
| M7 | 彩蛋（可选）：年终总结 + 有道云笔记做中间训练 | 待定 | 「吕炘嵘 GPT」第一次附体 | midtrain 思路 |

## 明确砍掉

分布式训练（单卡）、Muon 优化器（先 AdamW）、fp8、排行榜调优。竞技装备不是学习装备。

## 风险

主风险在 M2：预训练是全图最贵也最陌生的部分，数据打包和训练稳定性都是新东西。对策：先用极小配置（d4、小语料）把全链路跑通，再放大到 d12。砍 depth 不砍链路，军规不变。

## 配套教材：diy-llm（2026-10-24 增补）

[diy-llm](https://github.com/datawhalechina/diy-llm)（DataWhale 出品，斯坦福 CS336 中文本土化课程，16 章 + 6 作业）正式列为 M1 起的配套教材。定位：lvchat 是作品主线，diy-llm 是理论配套——每个里程碑先读对应章节再动手，交付后可选做对应作业当加试题。不另开顺序通读的新主线。

| 里程碑 | diy-llm 配套章节 |
| --- | --- |
| M1 自训 BPE tokenizer | 第 2 章 分词器 + 作业 1 |
| M2 预训练 | 第 3 章（梯度累积/资源核算）+ 第 11 章（数据工程）+ 第 9 章（Scaling Laws） |
| M3 KV cache 推理引擎 | 第 10 章 推理（KV Cache、投机解码、量化） |
| M4 SFT | 第 13 章（Pre-training/SFT/DPO 全流程） |
| M5 评估框架 | 第 12 章 评估与基准 + 作业 6 |
| 架构升级（GPT-2 → 现代） | 第 4 章 RoPE/RMSNorm/SwiGLU |

「明确砍掉」部分的捡回路径也留好了：MoE（第 5 章）、GPU/分布式（第 6-8 章）、GRPO/RLVR（第 14 章）、多模态（第 15 章）——以后想扩装备时有教材，不急着现在看。
