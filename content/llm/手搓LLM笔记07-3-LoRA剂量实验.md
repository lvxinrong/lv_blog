+++
title = "手搓 LLM 笔记 07-3：LoRA 剂量实验——从没训练的 32 分到平台期判决"
date = 2026-10-20T16:30:00+08:00
draft = false
slug = "llm-07-3-lora-dose"
tags = ["LLM", "LoRA", "SFT", "实验", "学习笔记"]
summary = "附录 D+E 联合作战：在 355M 上手写 LoRA。一份没训练就拿到 32 分的假结果、一条 warmup 平方的 bug、四轮剂量扫描、一次平台期判决，和最后 merge 验收时抓到的双重计数。"
[cover]
    image = "covers/llm-07-3-lora-dose.jpg"
    alt = "手搓 LLM 笔记 07-3：LoRA 剂量实验"
    hiddenInList = true
    hiddenInSingle = true
+++

> 目标本来是「把手写 LoRA 跑通」，结果跑成了一整天的实验课：先被一份没训练的假结果骗了，再扫出完整的剂量曲线，最后在 merge 验收里抓到双重计数。系列规则不变：写下来的必须是我自己搞懂的，翻车的地方如实写。

## 一、假 LoRA 事件：没训练也能拿 32 分

我先交代流水线：`ch07_5.py` 训练 → `ch07_7.py` 生成测试回答 → `generate_model_scores.py` 用 DeepSeek 打分。

我在 07 里加了 `replace_linear_with_lora`，跑出 32.3 分，和全参数的 33.5 几乎一样，当时还挺高兴：「LoRA 用 1/150 的参数打平全参数」。

Kimi 翻了代码之后发现：**07 里根本没有训练循环**——加载 checkpoint、冻结、包 LoRA、直接生成评估。而 LoRA 的 B 矩阵是零初始化，adapter 对模型行为的贡献严格为零。所以 32.3 就是原来那个 33.5 的模型穿了件马甲。

**三组分数一模一样，不是因为 LoRA 打平了全参数，是因为那一组实验压根没发生。**

这条教训钉死：**结果完美符合「无差异」时，先怀疑实验是否真的发生了**。仪器没坏，是实验没做。

## 二、顺带曝光的两个 bug

**1. warmup_steps 被平方了。**

```python
warmup_steps = int(0.2 * total_steps * total_steps)  # 错
warmup_steps = int(0.2 * total_steps)                # 对
```

warmup 步数变成天文数字，整个训练一直活在 warmup 里，cosine 衰减从未生效。所以之前那组「调度三件套在短跑里无效」的结论作废——那不是一次有效的调度实验，是一次「全程低 lr」实验。

**2. 基线 checkpoint 被覆盖。**

原始 SFT 权重和后续实验共用同一个路径 `gpt2_355M_instruct.pth`，基线被后续运行覆盖。教训：checkpoint 命名必须带语义，只增不删。

## 三、真·LoRA 首轮：5e-5 的欠训判决

把 LoRA 接进 05 的训练路径（`replace_linear_with_lora` 在 optimizer 之前；optimizer 只接 `requires_grad` 的参数）：

```
Total trainable parameters before: 406,286,336
Total trainable parameters after:    7,898,384   ← 1.9%
```

峰值 lr 5e-5、2 epoch 的结果：

- val loss 停在 0.935（全参数 0.62）
- 评委打分 **14.1，84 个 0 分**（全参数 33.5 / 58 个）
- 样例把原句复读一遍——格式学了半个，变换没学会

判决：欠训。LoRA 的可训练参数少、梯度信号稀疏，lr 惯例要比全参数大 1~2 个数量级，5e-5 太温柔。

## 四、剂量曲线：四轮扫描

一次只改一个变量，同评委、同 110 条测试集：

| 配置 | 均分 | 0 分 | val loss |
| --- | --- | --- | --- |
| LoRA 5e-5, 2ep | 14.1 | 84 | 0.935 |
| LoRA 1e-4, 2ep | 16.4 | 79 | 0.866 |
| LoRA 2e-4, 2ep | 21.9 | 72 | 0.811 |
| LoRA 2e-4, 4ep | 23.9 | 70 | 0.739（已走平） |
| 全参数, 2ep | **33.5** | **58** | **0.62** |

每一步都有效，但收益递减（+2.3 → +5.5 → +2.0），val loss 在 0.74 走平。继续推 rank 或 epoch 还能挤几分，改变不了格局。

插曲：第一轮 4 epoch 跑完发现 `num_epochs` 忘了改，白跑一次。实验纪律加一条：改完配置先确认再跑。这种重复劳动就是 sweep runner（配置表驱动、自动 train/generate/score）存在的理由，已记入工程债。

## 五、平台期判决：结局 B

开跑之前 Kimi 预告了两种结局：A 是 LoRA 追平全参数，B 是 LoRA 的平台期低于全参数。数据落在 B。

这不是 LoRA 的失败，是定位澄清：**LoRA 的价值是「让不可能变可能」，不是「让小局变更优」。** 355M 全参数本来就训得动，LoRA 没有非赢不可的理由；Qwen 实验里它打过真正的仗——1.5B 模型全参数训练在 12G 显存里塞不下优化器状态，LoRA 是唯一能开工的方式。

另一个量化感受：LoRA 训练 2.2 分钟，全参数 2.75 分钟，只快 20%。冻结只是不更新，前向反向照样穿过全部权重——**LoRA 省的是显存，不是计算**。

## 六、merge 验收：先抓双重计数，再证数学等价

最后一关：把训练好的 ΔW 折叠回 W，验证「并联小路」和「权重更新」严格等价。

```python
module.linear.weight += (alpha / rank) * (A @ B).T
```

第一跑：**最大差异 32.6**。原因：合并后 LoRA 路径还开着，`linear(x) + lora(x)` 把 ΔW 算了两遍。merge 是搬家不是复制——搬完必须给旧路径断电：

```python
module.lora.B.zero_()   # 搬家完毕，旧路径关闭
```

第二跑：**最大差异 9.16e-05**，浮点误差级。等价性亲手证完，附录 E 正式画句号。顺带一提：32.6 这个「失败」反而是 LoRA 真训练过的证据——没学出权重的话，双重计数也差不出这个量级。

## 七、工程债（M0 的动机清单）

今天改一行配置要懂三个文件（训练/评估/打分互相 import、路径写死、optimizer 藏在流程中间），「没有工程化，改起来好麻烦」——这些痛点全部转化为 lvllm 重写（笔记 08）的需求：

1. checkpoint 标准化：语义命名、只增不删、adapter 单独存
2. sweep runner：配置表驱动，train/generate/score 一条龙
3. 训练/评估/打分解耦，配置集中

## 一句话总结

**结果出来了和实验发生了，是两回事**——这是今天最贵的一句话，其余都是注脚。

---

*前一篇：[手搓 LLM 笔记 07-2：换底座，从 33.5 分的 GPT-2 到 86.5 分的 Qwen](/llm/llm-07-2-switch-base/)*
