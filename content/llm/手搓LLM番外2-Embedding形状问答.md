+++
title = "手搓 LLM 番外：LayerNorm 与 Embedding 层的形状问答"
date = 2026-10-28T08:00:00+08:00
draft = true
slug = "llm-10-1-embedding-shapes-qa"
tags = ["LLM", "GPT", "Embedding", "LayerNorm", "学习笔记", "草稿"]
summary = "LayerNorm 是不是等比例缩放？pos_emb 为什么用 arange？T 是 token_id 吗？tok_embeds 和 pos_embeds 为什么能广播？"
[cover]
    image = "covers/llm-10-1-embedding-shapes-qa.jpg"
    alt = "LayerNorm 与 Embedding 层的形状问答"
    hiddenInList = true
    hiddenInSingle = true
+++

> 草稿。睡前重读 GPTModel 代码时的一串自问自答。这次的主题是“形状”——很多概念自以为懂了，一写到 shape 就露馅。

## 1. LayerNorm 是不是也可以理解为等比例缩放？

对了一半。LayerNorm 是**平移 + 等比例缩放**（仿射变换），不是单纯缩放：

```python
norm_x = (x - mean) / sqrt(var + eps)   # ① 减均值（平移）→ ② 除标准差（等比例缩放）
result = scale * norm_x + shift         # ③ 可学的缩放 + 平移
```

除标准差这一步确实是等比例缩放，**不改变元素间的相对比例**——原来大的还是大、小的还是小，只是整体收到方差 1 的尺度。但如果只有缩放没有减均值，中心还是偏的。

记法：**缩放保比例，平移定中心。**

## 2. pos_embeds 为什么用 arange 取，和 tok_embeds 的取法完全不一样？

`torch.arange(seq_len)` 就是生成一串从 0 开始的位置下标 `[0, 1, 2, ..., T-1]`。

取法不同是因为**位置不随样本变化，token 随样本变化**：

- tok_emb：输入是 (B, T) 的 token id，每个样本的 token 都不一样，查出来是 (B, T, C)——每个样本一份
- pos_emb：所有样本的第 0 个位置都是同一个位置，只需要查一份，出来是 (T, C)

然后靠广播把同一份位置向量加到每个样本上。**tok 按 id 查各查各的，pos 按下标查大家共用。**

## 3. pos_embeds 出来的是 (T, emb_dim)？这里的 T 和 tok 的 T 含义不同吧？

是同一个 T——**都是“当前序列的实际长度”（seq_len）**。

pos_emb 整张表是 `(context_length, emb_dim)`（位置库总容量，比如 1024），但每次前向只用前 T 个位置，所以查出来是 `(T, emb_dim)`。和 tok_embeds 的 T 完全一致，才能逐位置相加。如果 T 不一样，加都加不了。

## 4. (B, T, C) 里的 T 也是 seq_len？我之前以为 T 是 token_id

T 是**位置数**（这条序列有几个槽位），不是 token_id。token_id 是装在张量里面的**值**：

```python
in_idx = tensor([[15496, 11, 262]])   # shape (1, 3)
#                ↑ 这三个值才是 token_id
# B=1, T=3 —— T=3 只是说这条序列有 3 个位置
```

所以 (B, T, C) 的完整含义是：B 个样本，每个样本 T 个位置，每个位置一个 C 维向量。pos_emb 用 arange(T) 就能对上，是因为**位置编号和位置上放什么 token 无关**——座位号 vs 坐着的人。

## 5. tok_emb 是 (vocab, emb_dim)，取出来怎么就成了 (B, T, emb_dim)？

`nn.Embedding` 是查表：**保留输入的形状，把每个 id 替换成对应的那一行向量**。

```
tok_emb 表:  (vocab_size, emb_dim)   ← 整个词表，每个 token 一个向量
in_idx:      (B, T)                   ← 每个位置上是 token_id
tok_embeds:  (B, T, emb_dim)          ← 每个位置上的 id 被换成向量
```

T 这个轴原样保留，第 0 个位置还是第 0 个位置，只是“位置上的 id”变成了“位置上的向量”。再加上 pos_emb 的 (T, C)，每个位置就同时知道“我是谁（token）”和“我在哪（位置）”。

## 6. 所以 tok_embeds 和 pos_embeds 才能广播？

对。广播的规则是**从右往左逐维对齐：相同，或其中一个为 1（或缺失补 1）**：

```
tok_embeds: (B, T, C)
pos_embeds:     (T, C)     ← 右边两维 T、C 完全相同，左边缺的 B 自动复制
结果:        (B, T, C)
```

T 和 C 必须一致（所以 pos 查表用 arange(seq_len) 保证 T 对上），B 那一维 pos 没有，广播就自动复制到每个样本上，不用手动复制。**广播不是“随便加”，是“从右往左对得上才加”。**
