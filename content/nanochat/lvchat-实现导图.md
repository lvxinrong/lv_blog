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
