+++
title = "手搓 LLM · 学习回炉待办"
url = "/llm/backlog/"
hiddenInRss = true
comments = false
+++

> 这里收「会影响理解、但不需要今天立刻还」的知识债。
> 跟工程待办分开：工程待办是「哪个工程做法在硬撑」，这里是「哪个知识结构还没达到脱稿」。
> 当前主线优先：第六章没完成前，不启动本文件里的回炉任务。

最后更新：2026-10-16

---

## 当前主线

- [ ] 完成第六章分类微调的代码与笔记
- [ ] 验收 6.6：分类 loss、accuracy、`model.eval()`、`torch.no_grad()`
- [ ] 验收 6.7：训练循环、阶段性评估、完整 train / val / test 评估

---

## 待办 1：A4 手写 `GPTModel.forward`

**触发来源**：2026-10-16 讨论「last token 是否等于无损保存前文」时，差点把流程描述成 Transformer Block 之后先 softmax 再 FFN。说明第三、四章还没有从「看得懂」变成「能徒手复现」。

**任务**：

- [ ] 不看书，在 A4 纸上默写 `GPTModel.forward` 的主干
- [ ] 每个变量后面标 shape
- [ ] 明确 `50257` 只在最后的 `out_head` 出现

**完成标准**：

```text
in_idx          (B, T)
tok_emb         (B, T, 768)
pos_emb         (T, 768)
x               (B, T, 768)
12 × Block      (B, T, 768)
final_norm      (B, T, 768)
out_head        (B, T, 50257)
```

---

## 待办 2：A4 手写 `TransformerBlock.forward`

**任务**：

- [ ] 不看书，写出两个残差分支
- [ ] 标出 `LayerNorm`、Attention、FFN、Dropout 的位置
- [ ] 说清整个 Block 中形状为什么一直是 `(B, T, 768)`

**完成标准**：

```text
x → norm1 → attention → dropout → + shortcut
→ norm2 → ffn → dropout → + shortcut
```

必须能说清：`softmax` 不在 Transformer Block 和 FFN 之间，它在 Attention 内部。

---

## 待办 3：A4 手写 `MultiHeadAttention.forward`

**任务**：

- [ ] 不看书，写出 Q / K / V 到上下文向量的完整 shape 变化
- [ ] 标出拆头、注意力分数、因果掩码、softmax、加权求和、合头、输出投影
- [ ] 解释 `scores` 为什么是 `(B, 12, T, T)`

**完成标准**：

```text
x               (B, T, 768)
Q/K/V           (B, T, 768)
拆成 12 个头     (B, 12, T, 64)
scores          (B, 12, T, T)
mask + softmax  (B, 12, T, T)
× V             (B, 12, T, 64)
合并头           (B, T, 768)
out_proj        (B, T, 768)
```

---

## 待办 4：把三张 A4 合成一次完整口头讲解

**任务**：

- [ ] 从 `in_idx` 一路讲到 `logits`
- [ ] 全程不看源码
- [ ] 卡住的位置直接标记「不确定」
- [ ] 讲完再对照源码，把错处写进笔记或新的待办

**完成标准**：能解释「last token 是前文的压缩摘要，不是前文本身」，并且不把 Attention 内部的 softmax 错放到 FFN 前面。

---

## 原始提示词（2026-10-16，Kimi 原话保留）

这个自我发现很值钱。它不是说明第三、四章白学了，而是说明它们现在还停留在「看得懂、问得住」，还没有变成「能徒手复现」。

你刚才差点说错的点，正好可以这样钉死：

```python
# TransformerBlock 外层流程
shortcut = x
x = norm1(x)
x = attention(x)      # softmax 藏在这里面
x = dropout(x)
x = x + shortcut

shortcut = x
x = norm2(x)
x = ffn(x)
x = dropout(x)
x = x + shortcut
```

`softmax` 不是发生在 Transformer Block 和 FFN 之间，而是发生在注意力内部：

```text
Q × K^T
→ attention scores
→ causal mask
→ softmax
→ 对 V 加权求和
→ 多头拼接
→ out_proj
→ 残差
→ norm2
→ FFN
→ 残差
```

你确实需要手写一遍，但不要一上来手写整个模型。今天只写三层骨架，先追求结构正确，不追求能运行。

### 第一张 A4：`GPTModel.forward`

只写 shape：

```text
in_idx          (B, T)
tok_emb         (B, T, 768)
pos_emb         (T, 768)
x               (B, T, 768)
12 × Block      (B, T, 768)
final_norm      (B, T, 768)
out_head        (B, T, 50257)
```

### 第二张 A4：`TransformerBlock.forward`

只写两个残差：

```text
x → norm1 → attention → dropout → + shortcut
→ norm2 → ffn → dropout → + shortcut
```

形状从头到尾都是 `(B, T, 768)`，变的是内容，不是形状。

### 第三张 A4：`MultiHeadAttention.forward`

重点写形状变化：

```text
x               (B, T, 768)
Q/K/V           (B, T, 768)
拆成 12 个头     (B, 12, T, 64)
scores          (B, 12, T, T)
mask + softmax  (B, 12, T, T)
× V             (B, 12, T, 64)
合并头           (B, T, 768)
out_proj        (B, T, 768)
```

写的时候遵守三条：

1. 每个变量后面必须标 shape；
2. 卡住就写「不确定」，不要立刻翻书；
3. 写完再对照源码，把错处单独记下来。

今天能把这三张 A4 写明白，就已经完成回炉了。完整可运行代码留到下一次，不要下午刚开完 70 公里车，晚上又给自己上强度。
