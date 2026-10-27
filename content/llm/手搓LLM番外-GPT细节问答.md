+++
title = "手搓 LLM 番外：GPT 细节的七次自问自答"
date = 2026-10-27T08:00:00+08:00
draft = true
slug = "llm-08-1-gpt-details-qa"
tags = ["LLM", "GPT", "学习笔记", "草稿"]
summary = "脑内复盘 GPT 全流程时卡住的点：drop_shortcut 的位置、权重何时更新、softmax 出现几次、为什么除以√d_k、方差与归一化、softmax 和 LayerNorm 的分工。"
[cover]
    image = "covers/llm-08-1-gpt-details-qa.jpg"
    alt = "GPT 细节的七次自问自答"
    hiddenInList = true
    hiddenInSingle = true
+++

> 草稿。M0 收官后、M1 开工前的那个早上，躺在床上把 GPT 全流程在脑内过了一遍。大部分能默出来，卡住的几个点就成了这篇问答。问是我自己问的，答是讨论之后我自己能讲通的版本。

## 1. 脑内过流程时，卡在了 drop_shortcut

主干能默出来：token → embedding → N 个 trf block → final_norm → logits → 采样。卡壳的地方是 block 里 att 和 ffn 之后各有一次 `drop_shortcut`——总把它忘了。

正确顺序是：**norm → 子层计算 → drop → 加回主干**，每个子层来一次。

```python
shortcut = x
x = self.norm1(x)
x = self.att(x)
x = self.drop_shortcut(x)   # dropout 只作用在分支输出上
x = x + shortcut            # 主干永远原样通过
```

位置的讲究：dropout 只打分支、不打主干。分支的增量被随机丢弃，强迫模型不依赖单一路径；主干（shortcut）如果被 drop，残差的“干净通道”就漏了。

## 2. W_q / W_k / W_v 是 forward 全程固定，loss.backward() 时才更新？

前半句对，后半句不对。更新发生在 **optimizer.step()**，不是 backward。

```python
logits = model(x)   # forward：用当前权重算，权重不动
loss.backward()     # 只把梯度填进 .grad，权重还是不动
optimizer.step()    # 这一步才真的改权重：W = W - lr × grad
```

一句话：forward 用权重，backward 算方向，step 才动权重。梯度累积能成立，靠的就是“backward 只攒不改”。

## 3. softmax 在全流程里是不是只出现两次？

两处，但第二处有个“但是”。

第一处在注意力内部：`softmax(attn_scores / √d_k)`，训练推理都有，是模型结构的一部分。

第二处在输出 logits——**只有推理采样时才显式算**。训练时 cross_entropy 直接吃原始 logits，内部自带 log_softmax，不需要我手动加。greedy 解码甚至可以不算，因为 softmax 是单调变换，不改变 argmax。

所以精确版：注意力里的 softmax 属于模型结构；输出端的 softmax 只是把分数翻译成概率的展示层。

## 4. 为什么是除以 √head_dim？

缩放因子跟着“点积的维度”走，不跟着“多头”走。多头里每个头的 q·k 是 head_dim 维点积，所以除 √head_dim；单头就是 √d_out。代码写 `keys.shape[-1] ** 0.5` 两种情况自动都对。

根因：点积是 d_k 个随机分量求和，标准差随 √d_k 膨胀；不压回去，softmax 的输入被撑大、输出饱和、梯度趋零。除 √d_k 是为了让 softmax 的输入尺度不随维度失控，保住梯度。是单次点积的维度效应，不是跨层累积。

## 5. 标准差、方差、“均值 0 方差 1”

自己先讲了一遍，被纠正了三处：

- 标准差管“广度”（散多开），均值管“中心”（在哪）。别说成“趋势”。
- “均值 0 方差 1”是平移和缩放，**不是把数据框进有限区间**。不截断，离群值还在，正态的尾巴照样拖到无穷。准确说法是“典型波动范围在 ±1 附近”。
- 标准化后的方差就是 1，和数据量无关。数据量影响的是**估计的可靠性**（N 小则方差估计噪声大，N 与 N-1 之争也在这），不影响标准化后的数值。

## 6. 为什么要均值 0、方差 1？（除了防溢出）

防溢出其实是最不重要的理由。真正的原因在优化动力学：

1. **梯度不被大尺度特征绑架**：量级差太多的特征，在同一学习率下更新会互相盖掉；归一化让大家站在同一起跑线。
2. **激活函数待在有梯度的区间**：softmax/sigmoid 输入太大就饱和，梯度趋零。控制在单位尺度附近就是待在敏感区。
3. **阻断层间尺度滚雪球**：每层输出是下层输入，逐层放大一点，几十层就是指数膨胀。LayerNorm 每层重新校准。
4. **零均值不浪费容量学偏置补偿**：输入整体偏一侧，下一层得先学个偏置拉回来，纯浪费。

一句话：归一化不是为了数好看，是为了每层的优化都在可预期的尺度上进行。

## 7. 为什么 attention 用 softmax，trf block 用 LayerNorm？

虽然都叫归一化，干的是两件事：

- **softmax 是“造权重”**：注意力需要非负、和为 1 的权重，才能对 values 做加权平均（凸组合）。LayerNorm 输出有正有负、和不为 1，当不了权重。
- **LayerNorm 是“校准数值尺度”**：特征向量要保留正负和大小自由的信息。换成 softmax 会把特征强行压成概率分布，各维度互相竞争，表示能力直接毁掉。

口诀：**softmax 归一化注意力分数，产出权重；LayerNorm 归一化特征向量，产出稳定尺度。一个管“看谁”，一个管“别算炸”。**

配套的两对机制也清楚了：√d_k 缩放 + softmax 是一对（为了权重健康），pre-norm + 残差是一对（为了特征健康）。
