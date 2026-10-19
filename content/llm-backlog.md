+++
title = "手搓 LLM · 学习回炉待办"
url = "/llm/backlog/"
hiddenInRss = true
comments = false
+++

> 这里收「会影响理解、但不需要今天立刻还」的知识债。
> 跟工程待办分开：工程待办是「哪个工程做法在硬撑」，这里是「哪个知识结构还没达到脱稿」。
> 当前主线优先：第六章没完成前，不启动本文件里的回炉任务。

最后更新：2026-10-17

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

## 待办 5：修正笔记04「方差累加」那段的数学

**触发来源**：2026-10-17 从第一章重新回炉，重推 LayerNorm 到底在干什么，发现 [笔记04](llm/手搓LLM笔记04-GPT架构拼装.md) 第七节第 131 行那段 `1.25^24` 的粗算站不住。

**原文（要改的就是这句）**：

> 真正需要两个的原因在残差。如果 x 已经归一化（方差 1），子层输出的方差是 0.25，那 `x + f` 之后方差变成 1.25。均值没问题（0 加 0 还是 0），**但方差会累加**。一个 block 加两次，十二层就是 24 次，粗算是 1.25 的 24 次方——两百多倍。不重新归一化，尺度早就飞了。

**四个认知错误，逐条钉死**：

- [ ] `0.25` 是**方差**（std = 0.5），不是加在数值上的增量；`x + f` 是逐分量相加，方差是加完后**重新统计**出来的结果
- [ ] 方差可加有前提：`Var(X+Y) = Var(X) + Var(Y) + 2Cov(X,Y)`，只在**不相关**时相加。正相关时是**标准差**相加——`f = 0.5x` 时 `var(x+f) = 2.25`，不是 1.25
- [ ] std 涨的是 `√var`：`var 1 → 1.25` 只是 std `1 → 1.118`，谈不上"膨胀"
- [ ] `1.25^24` 把「绝对 0.25」和「比例 0.25」混成了一个：`var ← var + 0.25` 是**线性**（24 次 = 7），`var ← 1.25·var` 才是指数（212）。**pre-LN 的输入每次都被归一化，所以子层输出是固定绝对尺度，落到的是前者**

**替换成三句话**：

1. 残差让方差累加——但数值不累加
2. pre-LN 下是**线性**累加，12 层约 1.6～2 倍，不是几百倍
3. `1.25^24` 隐含「子层输出方差 ∝ 输入方差」，而 **LayerNorm 存在的意义正是取消这个比例**

**顺带要拧的两个归因**：

- [ ] 不是"防点积膨胀"：**点积是传感器，不是肇事者**。治点积膨胀的是 attention 里的 `1/√d_k`，管层间尺度的是权重初始化（GPT-2 用 `std=0.02`）
- [ ] 真正的问题是**各层尺度不一致**（lr、fp16 数值范围、GELU 与 softmax 的工作区间都只有一套），外加均值漂移；不是"数值大"
- [ ] `LayerNorm` 的 `scale`/`shift` 可学，输出方差并不被锁死为 1——它不是防爆阀，也不负责梯度爆炸（那是 warmup / 梯度裁剪）

**可复现实测**（2026-10-17 在 `~/lv_repo/lv_llms/.venv` 跑过，12 层、768 维、`std=0.02` 初始化，每 block 一条支路）：

```python
import torch, torch.nn as nn
torch.manual_seed(0); torch.set_grad_enabled(False)
d, B, T, L = 768, 4, 64, 12

def make(norm):
    layers = []
    for _ in range(L):
        mods = [nn.LayerNorm(d)] if norm else []
        w1, w2 = nn.Linear(d, 4*d), nn.Linear(4*d, d)
        for m in (w1, w2):
            nn.init.normal_(m.weight, std=0.02); nn.init.zeros_(m.bias)
        layers.append(nn.Sequential(*mods, w1, nn.GELU(), w2))
    return layers

for tag, norm in [("pre-LN", True), ("no norm", False)]:
    layers, x = make(norm), torch.randn(B, T, d)
    print(f"\n== {tag} ==")
    for i, f in enumerate(layers, 1):
        h = f(x); x = x + h
        if i in (1, 6, 12):
            print(f"  block {i:2d}  子层输出 std {h.std():.3f}  残差流 std {x.std():.3f}")
```

实测结果：

| | 第 1 层 | 第 6 层 | 第 12 层 |
|---|---|---|---|
| pre-LN：子层输出 std | 0.361 | 0.361 | 0.361 |
| pre-LN：残差流 std | 1.061 | 1.335 | **1.596** |
| 无 norm：子层输出 std | 0.364 | 0.522 | 0.882 |
| 无 norm：残差流 std | 1.066 | 1.478 | **2.306** |

左半边子层输出 std 从头到尾恒定，所以残差流方差是 `1 + L×0.13` 这种**线性**叠加（12 层 `√(1+12×0.13) = 1.6`，与实测吻合）。右半边增量跟着干道长，才变成几何式（每块方差约乘 `1+g²`, `g≈0.36`）。

**注意**：上表每 block 只挂了一条支路，GPT-2 实际有 attention + FFN 两条，方差贡献翻倍，12 层约 `√(1+24×0.13) ≈ 2.0`。

**完成标准**：不看笔记能说清「为什么 pre-LN 下是 `√L` 而不是指数增长」，并由此解释 `final_norm` 那一刀的来历。跟上面「待办 2」里"标出 LayerNorm 位置"那一条一起还。

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
