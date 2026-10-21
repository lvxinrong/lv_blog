+++
title = "手搓 LLM 笔记 08：重写 lvllm，按工程结构再串一遍"
date = 2026-10-20T12:00:00+08:00
draft = false
slug = "llm-08-rewrite-lvllm"
tags = ["LLM", "工程化", "重写", "学习笔记"]
summary = "终极回炉：不按章节收拢，按工程结构重写全书代码——分层、单一配置、单一 device 入口、checkpoint 标准化。重写完成时发布。"
[cover]
    image = "covers/llm-08-rewrite-lvllm.jpg"
    alt = "手搓 LLM 笔记 08：重写 lvllm"
    hiddenInList = true
    hiddenInSingle = true
+++

> 预告：本篇目前只有计划，重写 lvllm 完成后正式撰写正文。施工图见 [lvchat 实现导图](/nanochat/lvchat-roadmap/) 的 M0。

## 计划

- 分层：tokenizer / model / data / train / generate / eval / checkpoints
- 单一配置入口（config）、单一 device 入口（get_device）、checkpoint 标准化（权重 + config + val_loss）
- 军规：能不翻书就不翻，翻一次记一笔欠账注释，写完清单归零
- 验收：分类、指令微调、生成三个回归测试与旧仓库结果一致

## 素材积累（M0 进行中）

**Day 1（10-20）**：
- MHA 重写：骨架对、细节丢四个（多头拆解、√d_k、logits/权重命名、out_proj）；抓到两个致命 bug（`foward` 拼写、mask 切片错写成 `[:T, T:]`，正确是 `[:T, :T]`）
- 「张量的第一维永远是 batch」幻觉拔除——generate 的一维切法 bug 全源于此
- LayerNorm vs BatchNorm：「BatchNorm 统计别人，LayerNorm 只管自己」
- pre-norm 的「干净通道」：残差主干恒等直通，warmup 与 pre-norm 是同一问题的两代武器
- checkpoints 三层设计：gpt2.py（进口）/ store.py（自用）/ lora.py（附加）；键名映射吸收旧格式
- LoRA merge 验收的双重计数坑：merge 是搬家不是复制
- 竖切终点：355M 权重加载，squid 第一次开口
