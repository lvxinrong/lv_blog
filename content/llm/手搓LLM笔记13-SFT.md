+++
title = "手搓 LLM 笔记 13：SFT，从续写机到指令跟随"
date = 2026-10-30T15:00:00+08:00
draft = true
slug = "llm-13-sft-instruction-following"
tags = ["LLM", "SFT", "指令微调", "学习笔记", "草稿"]
summary = "355M 全参 SFT 冒烟与 base/SFT 行为对照：base 全是 0 分，SFT 开始按模板回答。从续写机到指令跟随，M4 的核心证据。"
[cover]
    image = "covers/llm-13-sft-instruction-following.jpg"
    alt = "手搓 LLM 笔记 13：SFT"
    hiddenInList = true
    hiddenInSingle = true
+++

> 草稿，待验收。

## M4 在做什么

**把模型从“会续写”变成“听得懂指令”**——用现成的 1100 条指令数据（85% 训练 / 10% 测试 / 5% 验证）对 355M base 模型做全参 SFT，然后用 base/SFT 对照看“指令跟随能力”的变化。

## 过程：先跑通，再对照

SFT 冒烟先把训练链路跑通：load 355M base → InstructDataset + instruct_collate → sft_train_model（warmup + cosine + clip）。train/val loss 健康下降，val 到 1.126 进入平台期——**loss 到平台期 = 该上期末考了**。

然后做 base/SFT 行为对照：同一批 test 问题，分别问 base 和 SFT 模型，再用 DeepSeek 评委分别打分。

## 结果：base 全 0，SFT 有分

**base 模型**：
- "Rewrite the sentence using a simile" → 续写出一堆 prompt 碎片（把 `### Instruction:` 都编出来了）
- "What type of cloud..." → 无限复读 "What is the cloud type?"
- **评委均分 0.0**（全 0 分）——完全不会按指令回答

**SFT 模型**：
- "Rewrite the sentence using a simile" → "The car is a fast car." 然后停止
- "What type of cloud..." → "A type of cloud is typically associated with thunderstorms." 然后停止
- **评委均分 4.0**（有一个 20 分）——开始按模板回答并停止

**这就是 SFT 的核心证据：从“听不懂指令的续写机”变成“按模板回答的指令跟随者”。** 分数还不高（小模型、935 条训练样本），但方向是对的：指令跟随能力被训出来了。

## 踩过的坑

- **没有 `if __name__ == '__main__':` 入口**：函数写了但没被调用，脚本秒退无输出
- **`cfg["n_epochs"]` 引用错**：n_epochs 在 train_cfg 不在 cfg，KeyError
- **collate 签名照抄书里的**：我们的 instruct_collate 是 `(batch, pad_token_id, ignore_index)`，没有 device/allowed_max_length 参数（data/ 不碰 device）
- **prompt 少了 `### Response:` 头**：SFT 直接只吐结束符——SFT 对模板格式是强依赖的
- **110 条 × 256 token × 2 模型生成量太大**：改成小批量冒烟，先跑通评委链路

## 待办与下一步

- 用 DeepSeek 生成蒸馏指令数据（数据量上去，回答质量才有空间）
- CoT 数据（推理步骤+答案）作为扩展
- RoPE 补位置溢出的坑（晚上有时间就做）
- 下午研究 instruct_collate 的签名与职责
