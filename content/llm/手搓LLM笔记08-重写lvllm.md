+++
title = "手搓 LLM 笔记 08：重写 lvllm，按工程结构再串一遍"
date = 2026-10-20T12:00:00+08:00
draft = false
slug = "llm-08-rewrite-lvllm"
tags = ["LLM", "工程化", "重写", "学习笔记"]
summary = "终极回炉：不按章节收拢，按工程结构重写全书代码。data 三任务、train 分工、LoRA 接线、eval 评委链，最后用 23.6 vs 23.9 的回归收官。"
[cover]
    image = "covers/llm-08-rewrite-lvllm.jpg"
    alt = "手搓 LLM 笔记 08：重写 lvllm"
    hiddenInList = true
    hiddenInSingle = true
+++

> 施工图是 [lvchat 实现导图](/nanochat/lvchat-roadmap/) 的 M0。10 月 20 日立项，10 月 26 日回归通过，本篇为收官正文。原始踩坑记录保留在文末「素材积累」。

## 为什么重写

书读完的时候，我手里有一整个仓库的代码，但它们是按章节长的：ch03 一份、ch05 一份、ch07 一份，互相复制，配置散落，device 满天飞。能跑，但不是工程。

更关键的问题：这些代码是“跟着书写出来的”，合上书，我能不能按自己的结构重新组织一遍？这就是 M0 的由来——**不按章节收拢，按工程结构重写**。目标不是拥有一个新的仓库，是拥有"能写出这个仓库"的能力。

新仓库叫 squid-llms。军规两条：能手写就手写，AI 只当导航；每一处偏离书的设计，都要说得出理由。

## 最后的结构

```
src/squid/
├── config.py        # 单一配置入口
├── device.py        # 单一 device 入口
├── tokenizer/       # SquidTokenizer 协议 + tiktoken 实现
├── model/           # layers / gpt / lora
├── data/            # pretrain / classify / instruct + common
├── train/           # common / pretrain / classify / sft
├── generate/        # 纯 id 引擎 + 文本壳
├── eval/            # 批量生成 + DeepSeek 评委
└── checkpoints/     # 进口 / 自用 / 附加 三层
```

两个“单一入口”是最先定的：配置和 device 只有一个出处。后面所有层都不许自己造词表知识、自己判断设备——比如 pad_id 一律从 `tokenizer.eos_id` 进，不许写死 50256（GPT-2 ≠ Qwen，07-2 已经踩过）。

## data：按任务分，不按格式分

三种任务的数据组织方式根本不同，所以分三个文件：

- **pretrain**：定长滑窗。`input = ids[i:i+max_len]`，`target = ids[i+1:i+max_len+1]`，+1 偏移在 dataset 里做完，默认 collate 直接 stack。stride 是“窗口每次滑动的步长”不是窗口大小，取 max_length 一半就是 50% 重叠，抗上下文割裂。
- **classify**：变长文本 + 类别标签。pad 到 **batch 内最长**，所以 pad 必须在 collate——dataset 阶段看不到邻居，不知道要补多长。书里是补到全集最长，一条离群长文会让所有短文本陪着补，这里有意改掉了。
- **instruct**：最重的一条流水线，五步手术：

```python
full = prompt_ids + response_ids + [eos_id]   # 1. 追加 EOS
padded = pad_to_length(full, max_len, eos_id) # 2. pad 到 batch 最长
inputs  = padded[:-1]                         # 3. +1 错位
targets = padded[1:].clone()                  #    （clone：切片是视图）
targets[:len(prompt_ids) - 1] = -100          # 4. prompt 位不计分
targets[eos_pos[1:]] = -100                   # 5. 除第一个 EOS 外全遮
```

掩码要分两笔账记：**pad 掩码是卫生**（不做就污染 loss），**prompt 掩码是战术**（只做指令跟随时用）。一句话版：prompt 是考场，response 是答卷，遮盖是“不计分”，不是“拆考场”——模型始终看得到完整 prompt，只是不为它的预测打分。

还有三个对齐可以当口诀：**pad 对齐形状，+1 对齐时间，-100 对齐计分范围。**

## train：common 提供能力，循环决定节奏

三个训练循环 80% 相同，所以公共件沉到 common（loss 三件套、评估、LR 调度），任务文件只留差异。

最大的一个认知点是 `cross_entropy` 的契约：logits `(N, C)`、targets `(N,)`，**N 是预测点个数**。pretrain/SFT 每个位置都预测，N=B×T，所以要 `logits.flatten(0, 1)`；classify 只在最后一个位置预测，`logits[:, -1, :]` 出来就是 (B, C)，天然对齐，不需要 flatten。所以 classify 有自己的 `calc_loss_batch`，同名不同身，各放各家，不搞参数开关。

第二条是**函数自足**：`calc_loss_loader` 自己包 `no_grad`，不依赖调用方记得规矩（Java 直觉的胜利）。但反过来，训练用的 `calc_loss_batch` 绝不能包 no_grad——我包过一次，backward 直接没有梯度可回传。

第三条是 **prepare 归调用前，循环归循环**。换分类头、冻结、包 LoRA 都是训练前的模型手术，训练循环闭着眼跑，给它什么模型它训什么。

`lr_at_step` 抽成纯函数的理由只有两个字：**可测**。warmup 公式出过一次 bug（多乘了 total_steps），抽出来之后三个锚点断言（起点 initial_lr、warmup 顶点 peak_lr、终点 min_lr）三秒钟验尸。如果不写测试，抽它就没有意义。

## LoRA：手术、合并、存档

给模型换 LoRA 层的递归手术有个必须记住的招式：**`named_modules` 用来遍历，`named_children` 用来手术**。替换要拿“爹”的句柄才能 `setattr`，而 named_modules 会 yield 模块自身，拿它递归就是原地套娃——我用 RecursionError 实测过。

另外两条硬规矩：

- forward 和 merge 的缩放必须同一把尺：都是 `α/r`（论文原版）。书里只用 α，换 rank 时两种写法的强度差一个 1/r，对比实验时别混。
- 生命周期：**训练并联省显存，部署 merge 省计算**。`merged_weight()` 把 ΔW 折回主权重，之后保存的就是普通 GPT 的 state_dict，加载方不需要知道 LoRA 存在过。存档因此有两条路线：adapter 小而专用（保留继续训练的灵活），merged 大而通用（部署零开销）。

## eval：生成和打分分开烧

`generate/` 是生成能力，`eval/generate.py` 是测试集传送带：格式化 prompt（与训练同模板）→ 调 generate_text → 裁掉 prompt → 落盘 json。`eval/judge.py` 拿这个 json 去请 DeepSeek 打分。拆开的原因很实际：生成烧 GPU，打分烧 API 额度，两边失败重跑的成本完全不同。

judge 这边几个工程决定：API key 走 `.env` / 环境变量（不进 git）；有 score 的条目跳过，断点续跑不重复烧额度；每 10 条落盘一次；统计（均值、分位、直方图）抽成独立函数。

## 回归：23.6 vs 23.9

M0 的收官动作：拿旧仓库训练好的 LoRA 权重（355M，rank=16 alpha=16，4 epoch 那版），squid 负责加载、生成、打分，和旧仓库同权重基线对比。同权重是为了隔离变量——差异只剩管线本身。

| | squid 回归 | 旧仓库基线 |
| --- | --- | --- |
| 均分 | **23.6** | 23.9 |
| 0 分条数 | 73 | 70 |
| 81-100 分条数 | 18 | 19 |

均分差 0.3，分布形态一致，在评委噪声范围内。加上 13 个单元测试全绿，M0 验收通过。

另一个好用的 sanity check 记在这：**初始 loss ≈ ln(vocab_size)**。50257 词表随机猜的 baseline 是 10.83，训练起点贴着它才正常，之后掉得动才说明学习是真的。

## 这一遍重写，我练到的是什么

代码只是产出之一，更重要的是三条工作法：

1. **手写优先，AI 当导航。** AI 五分钟能写完整个仓库，但那是 AI 写的。collate 那几个坑（list 思维切 tensor、视图污染、BPE 接缝），只有亲手踩过才算学分。纯机械的搬运可以交给 AI，概念密集的地方必须手写。
2. **验收标准是“每行能讲清楚”，不是“脱稿默写”。** 看懂和写出之间隔着正常的鸿沟，读是再认，写是回忆。第二遍学习，读流畅、写磕绊就是这个阶段的样子。
3. **错处入笔记。** 每天的翻车现场当天记进素材库（见文末），写正文的时候全成了弹药。

下一步是 M1：自己训一个 BPE tokenizer，不调用 tiktoken，配套读 diy-llm 第 2 章。作品线和理论线从这里开始双轨并行。

## 素材积累（原始记录）

**Day 1（10-20）**：
- MHA 重写：骨架对、细节丢四个（多头拆解、√d_k、logits/权重命名、out_proj）；抓到两个致命 bug（`foward` 拼写、mask 切片错写成 `[:T, T:]`，正确是 `[:T, :T]`）
- 「张量的第一维永远是 batch」幻觉拔除——generate 的一维切法 bug 全源于此
- LayerNorm vs BatchNorm：「BatchNorm 统计别人，LayerNorm 只管自己」
- pre-norm 的「干净通道」：残差主干恒等直通，warmup 与 pre-norm 是同一问题的两代武器
- checkpoints 三层设计：gpt2.py（进口）/ store.py（自用）/ lora.py（附加）；键名映射吸收旧格式
- LoRA merge 验收的双重计数坑：merge 是搬家不是复制
- 竖切终点：355M 权重加载，squid 第一次开口

**Day 2（10-23）**：
- data 层按任务分不按格式分：pretrain（定长滑窗，dataset 内偏移）/ classify（collate 补 batch 内最长）/ instruct（掩码五连）
- collate 职责钉死：「定长的活 dataset 干，变长的活 collate 干，pad 永远在偏移前面」
- instruct collate 五步手术：追加 EOS → pad → +1 错位 → prompt 位 -100 → 除第一个 EOS 外全 -100
- 掩码两笔账：pad 掩码是卫生（必做），prompt 掩码是战术（看目标）；「prompt 是考场，response 是答卷，遮盖是不计分不是拆考场」
- pad_id 不许写死 50256：词表知识只从 tokenizer.eos_id 一个口进（GPT-2 ≠ Qwen，07-2 的前科）
- list 思维切 tensor 三坑：tensor 没有 .index、切片是视图要 clone、标量广播代替 list 赋值
- cross_entropy 契约 (N,C)+(N,)：N=预测点数。pretrain 要 flatten（N=B×T），classify 取 last-token 天然对齐（N=B）——同名不同身，各放各家
- 函数自足原则：no_grad 内收进 calc_loss_loader，不依赖调用方记得规矩（Java 直觉的胜利）；但训练用 loss 函数绝不能包 no_grad
- 训练层分工：common 提供能力，循环决定节奏；prepare（模型手术）归调用前，循环闭着眼跑
- lr_at_step 抽纯函数的意义 = 可测性：给出过 bug 的 warmup 公式配三锚点断言当验尸官
- named_modules 遍历、named_children 手术：替换要拿爹的句柄；named_modules 会 yield 自身，递归即套娃（RecursionError 实锤）
- LoRA：α/r 缩放 forward 与 merge 必须同尺；merged_weight 生命周期 = 训练并联省显存 → 部署 merge 省计算；存档两路线（adapter 小而专用 / merged 大而通用）
- sanity check：初始 loss ≈ ln(vocab_size)，一眼辨训练真假
- stride 语义钉死：窗口滑动的步长，不是窗口大小；stride=max_length/2 → 50% 重叠抗上下文割裂
- Kimi 翻车帧：出考题忘了等长样本没有 pad 路径；「我的时间来自对话时间戳，不是真的钟」
