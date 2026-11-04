+++
title = "手搓 LLM 笔记 14：M5，让评估能够中断后继续"
date = 2026-11-02T14:34:38+08:00
draft = false
slug = "llm-14-eval-resume"
tags = ["LLM", "M5", "评估", "学习笔记"]
summary = "RoPE 独立模型、选择题偏差、完整答案似然与自由生成断点续跑；M5 已完成 110 条结构化报告及 17 项相关回归。"
[cover]
    image = "covers/llm-14-eval-resume.jpg"
    alt = "手搓 LLM 笔记 14：M5 评估框架"
    hiddenInList = true
    hiddenInSingle = true
+++

## 今天的路线

上午把 RoPE 从概念讨论推进到独立实现，下午开始 M5 评估框架。

两件事看起来不相关，其实共享同一个工程习惯：**不能只让代码跑一次成功，还要让它可验证、可恢复、可重复执行。**

## 上午：独立 RoPE 模型闭环

### 为什么独立一个 package

旧 `GPTModel` 保留 GPT2 的可学习绝对位置编码和现有 355M 权重路径，不在同一个类里不断增加位置分支。

新版放在独立的 `rope_gpt` package 中：

```text
rope_gpt/
├── rope.py     # 频率、cos/sin、Q/K 旋转
├── layers.py   # RoPE MHA + TransformerBlock
└── gpt.py      # GPTModelRoPE
```

FFN 和 LayerNorm 复用旧实现；位置相关的 attention 和模型主干独立出来。

### 三个数学函数

`compute_inv_freq` 构造固定频率表：

```text
θⱼ = base^(-2j / head_dim)
```

这里的 `head_dim` 是单个注意力头的维度，不是完整的 `emb_dim`。例如 768 维、12 个 head，每头 64 维，每头内部有 32 组二维向量。

`compute_cos_sin` 用外积计算每个位置、每组频率对应的角度：

```text
freqs[i][j] = position_ids[i] × inv_freq[j]
```

`apply_rope` 使用与 nanochat 相同的前后半配对方式，对 Q/K 的最后一维做旋转，再拼接回原来的形状。

需要记住的边界：

- 标准 RoPE 没有可学习的位置参数，频率固定；
- 每组频率不同是为了覆盖不同尺度，不是每组属于不同 batch 或 head；
- 旋转保持 shape 和向量长度，但会改变点积，使点积能够感知相对位置；
- 每个二维旋转仍有周期，能计算更长位置不等于模型一定能泛化到更长上下文。

### 接入 MHA 与 KV cache

执行顺序：

```text
W_query/W_key 计算当前 Q/K
→ 拆成注意力头
→ 根据 past_len 得到当前位置
→ 旋转当前 Q/K
→ 拼接历史 K/V
```

Q 是当前 forward 的局部变量，不需要持久化。当前 K 旋转后进入 `present_kv`；历史 K 已经按原位置旋转过，不能重复旋转。V 始终不做 RoPE。

Block 和 GPTModel 负责逐层透传 cache，generate 负责保存整组 cache 并在下一轮喂回去。

### 验收结果

- 位置 0 保持不变，旋转前后向量模长一致；
- 相同相对距离下点积一致，不同相对距离下点积会变化；
- 两层 RoPE 模型完整前向与逐 token cache 前向对齐，最大误差约 `2.38e-07`；
- RoPE、旧模型、生成和 checkpoint 联合回归：`9 passed`；
- 复用原有 124M 预训练测试，只替换模型声明，train/val loss 持续下降；训练冒烟最后 val loss 约 `8.915`，BPB 约 `3.354`。

这些结果证明 RoPE 模型能从零训练并正确接入现有工程，不证明它在当前小语料上已经优于绝对位置编码。

## 下午：M5 评估框架

### 现有代码已经有什么

`eval/generate.py` 中的 `generate_responses` 已经能批量生成并保存回答，但只在全部结束后写一次文件。

`eval/judge.py` 中的 `score_entries` 已经有初步的评分续跑能力：已有 `score` 的记录会跳过，并每隔若干条保存一次。

所以 M5 不是从零重写，而是补齐生成端、评分端和报告之间的完整契约。

### 为什么需要断点续跑

假设有 110 条测试数据，生成到第 100 条时进程中断。

如果只在全部完成后保存，磁盘上可能一条有效结果都没有，下次只能从第一条重新生成。

改为每条生成后立即保存：

```text
第 1 条完成 → 写入 JSON
第 2 条完成 → 写入 JSON
……
第 100 条中断 → 前 100 条仍然保留
下次启动 → 跳过已有回答，从缺失位置继续
```

这里的“断点续跑”不是训练 checkpoint，也不是下载文件的断点续传，而是**评估任务的中间结果可恢复**。

目的不是让一次完整运行更快，而是避免重复消耗 GPU 时间和评委 API 额度，并允许随时人工检查中间结果。

### 当前新增函数

新增 `generate_responses_resumable`，与旧函数并存，便于对照。

当前状态：**代码已编写，等待断点续跑测试，尚未标记为验收完成。**

设计中的四个核心动作：

```text
读取历史 JSON → 用 index 识别记录 → 跳过已有 model_response → 每条生成后立即保存
```

同一个输出文件必须对应同一模型和同一份测试数据，不能换模型后错误复用旧回答。

### 为什么继续使用 JSON 数组

当前评估只有百余条记录，继续使用带缩进的 JSON 数组：

- 人类打开即可阅读；
- 现有 `score_entries` 不需要迁移；
- 每条记录保存时全量重写，当前规模下开销可以忽略；
- 保留完整 instruction、input、参考答案和模型回答，方便抽查。

JSONL 的流式追加更适合更大的记录规模，暂时不把格式迁移变成 M5 的主线。

## Python 细节：entry、JSON 与字典展开

### entry 是 Python 字典，不是 JSON 文本

JSON 是文件中的文本格式。经过 `json.loads` 后，它变成 Python 的 list、dict 等对象。

循环中的：

```python
for index, entry in enumerate(test_data):
```

这里的 `entry` 就是当前一条样本字典，通常包含：

```python
{
    "instruction": "任务要求",
    "input": "可选输入",
    "output": "参考答案",
}
```

### `**entry` 不是指针

在字典字面量中，`**entry` 表示把原字典的键值对展开并合并：

```python
new_entry = {
    "index": index,
    **entry,
    "model_response": response,
}
```

它保留原样本字段，再添加编号和模型回答，与内存地址或指针无关。

简单记忆：

```text
*  → 展开列表、元组等可迭代对象
** → 展开字典的键值对
```

### `indent=4` 与 `ensure_ascii=False`

```python
json.dumps(responses, indent=4, ensure_ascii=False)
```

- `indent=4`：按每层 4 个空格缩进，让 JSON 更适合人类阅读；
- `ensure_ascii=False`：中文直接写入文件，而不是变成 `\uXXXX` 转义；
- 配合 `encoding="utf-8"`，文件中的中文可以直接阅读；
- 两者改变的是文件呈现，不改变 JSON 加载后的数据。

## 选择题评测：从字母标签到完整答案似然

下午后半段做了两种完全不同的选择题评估。20 道英文题由 DeepSeek 生成并人工检查，覆盖 3～5 个选项，A/B/C/D 的正确答案位置各出现 5 次。

### 第一种：比较 A/B/C/D 的 next-token logits

prompt 中包含完整选项：

```text
Question: What is the capital of France?
A. Berlin
B. Paris
C. Madrid
D. Rome
Answer:
```

模型不需要自由生成，只取最后一个 prompt 位置的 logits，分别读取 `" A"`、`" B"`、`" C"`、`" D"` 对应 token id 的分数。

这里不需要为四个选项额外训练分类头。候选数量可以随 options 动态变化，其他词表 token 不影响 A/B/C/D 之间的相对排名。

数据里的 `answer` 保存从 0 开始的正确选项下标，不放进 prompt；A/B/C/D 是格式化时根据 options 的顺序添加的。

### 第一次结果：很像在蒙，而且主要在蒙 A

| 模型 | 原始准确率 | 打乱选项后准确率 |
| --- | ---: | ---: |
| base | 30%（6/20） | 30%（6/20） |
| SFT | 25%（5/20） | 30%（6/20） |

原始测试中，base 有 19 次选择 A，SFT 也有 19 次选择 A。打乱选项、同步调整 answer 下标后，两者仍然各有 19 次选择 0 号选项。

打乱后正确答案位于 0 号的题目正好有 6 道，因此“永远选 A”本身就得到 6/20，即 30%。两个模型的总分都与这个位置基线一致。

这说明当前字母评估法主要测到的是第一个选项的偏好，不能直接把 25% 或 30% 解释成模型知识答题能力。base/SFT 相差一两道题，也不足以证明 SFT 损伤或提升了知识能力。

## 第二种：完整答案的条件对数似然

这次不再展示 A/B/C/D，prompt 只保留：

```text
Question: 问题
Answer:
```

然后分别把每个完整 option 放到 Answer 后面，计算：

```text
log P(候选答案 | 问题)
```

行业术语是 conditional log-likelihood scoring（条件对数似然评分），在固定候选的选择题中也可称 multiple-choice likelihood evaluation。

### 实验结果

| 模型 | 总 logprob 准确率 | 平均 logprob 准确率 |
| --- | ---: | ---: |
| base | 50%（10/20） | 40%（8/20） |
| SFT | 60%（12/20） | 55%（11/20） |

完整答案评估显著高于字母评估，说明字母标签法确实埋没了模型已有的部分能力。但 50%～60% 也说明 355M 模型仍不稳定，不能把全部问题都归因于评估方法。

SFT 比 base 多答对 2～3 题，只是一个值得观察的小样本信号，不能推广成普遍结论。

## 本次最纠结的几个问题

### 把 option 放进输入，不是提前告诉模型答案了吗？

确实告诉了，但这是候选排序，不是自由作答。

四次评分分别构造四个独立输入：

```text
Question + Answer: Berlin
Question + Answer: Paris
Question + Answer: Madrid
Question + Answer: Rome
```

模型没有被要求判断“这段话对不对”，也没有自由生成答案；我们只是比较它认为哪个候选更像自然续写。

因此这里的 60% 不能解释成“自由回答正确率 60%”，只能解释为“在固定候选中，有 60% 的题目把正确答案排到了最高似然”。

### 这是不是生成回答后查找答案关键词？

不是。关键词匹配需要先自由生成，再检查文本中是否出现答案，容易被否定句或无关提及误导。

本次使用 teacher forcing：把候选答案的真实 token 放进输入，读取模型对每个目标 token 的预测分数。整个过程不生成自由文本，也不做字符串包含匹配。

### 一个 token 的 logits 不是一个 next-token 分数吗？

不是。每个位置的 logits 是整个词表上的分数向量，形状为 `(vocab_size,)`。

以“吕炘嵘性别是”为 prompt、“男”为候选答案为例：

```text
行：prompt 最后一个 token“是”所在的位置
列：“男”对应的 vocab token id
值：log P(男 | 吕炘嵘性别是)
```

所以是拿“男”的 token id，回到“是”所在位置的 logits 向量中，取出“男”对应的那一项分数。

代码中的 `gather` 就是在批量完成“每个答案位置取目标 token 对应列”的动作。

### 为什么不能直接取完整输入的 `logits[:, -1, :]`？

候选答案已经拼进完整输入后，最后一个位置预测的是“候选答案之后”的 token，不是候选答案本身。

若 prompt 长度为 P、答案有 A 个 token，则需要从 `P - 1` 开始取 A 个位置：

```python
start = len(prompt_ids) - 1
answer_logits = logits[:, start:start + len(continuation_ids), :]
```

第一个位置预测答案首 token，后续位置依次预测后续答案 token。

### 多 token 答案怎样评分？

候选答案先被完整编码为任意数量的 token。一次模型前向后，读取每个答案 token 的条件 logprob，再求总和或平均值：

```text
sum_logprob  = 整段答案的 logprob 之和
mean_logprob = sum_logprob / token 数量
```

Paris 只有一个 token，所以它的 sum 和 mean 都是约 `-4.039`。base 对其他候选的分数约为 -9、-10，说明它其实明确倾向 Paris，只是不善于把这个倾向映射成字母 B。

### 总和与平均为什么给出不同答案？

总 logprob 容易偏向短答案；平均 logprob 会改变长度影响，但也可能给多 token 候选额外优势。

例如“非洲最长河流”：

```text
Zambezi：总约 -5.42，平均约 -1.81
Nile：    总约 -4.05，平均约 -4.05
```

平均法选择了多 token 的 Zambezi，但总 logprob 法选择了正确答案 Nile。日本首都题中，平均法也偏向了多 token 的 Hanoi，而总 logprob 法选择了 Tokyo。

因此两种指标都应保留，不能把任何一种当成绝对公正的长度归一化。

## 对 M5 的方法论更新

选择题准确率不能脱离以下信息单独解读：

- 预测标签分布，防止“永远选 A”被误认为能力；
- 选项顺序对照，识别位置偏好；
- 候选答案的总/平均 logprob，观察长度偏差；
- 自由生成、候选排序和外部评委，分别说明不同能力，不能混为一个分数。

M5 的价值不是尽快拿到高分，而是知道一个分数到底测量了什么，以及它在哪些情况下不可信。

## 自由生成闭环：从一次脚本到可恢复评估

M5 第二天补齐了自由生成评估的工程链路：

```text
加载 SFT 权重
→ 切分 held-out test
→ generate_response_resumable 生成回答并逐条落盘
→ score_entries 调用 DeepSeek 评分并跳过已有分数
→ build_score_summary 汇总统计
→ save_score_report 保存 summary + items 的 JSON 报告
```

生成端和评分端都可以中断后继续。第二次运行生成函数时，已有 `model_response` 的记录会全部跳过；测试中还通过 mock 禁止重复调用生成函数，确认续跑不是仅靠结果相同来判断。

同时修复了两个输出细节：entry 自带的旧 index 不再覆盖当前编号，回答末尾的 `<|endoftext|>` 文本也会被清理。

## M5 全量 110 条验收

最终使用同一批 110 条 held-out test 完成生成、DeepSeek 评分和结构化 JSON 报告。

汇总结果：

```text
total:        110
valid_scores: 110
mean:         30.9
median:       0
min / max:    0 / 100
p10 / p90:    0 / 100
```

分数分布：

| 分数区间 | 数量 |
| --- | ---: |
| 0 | 60 |
| 1～20 | 4 |
| 21～40 | 12 |
| 41～60 | 9 |
| 61～80 | 2 |
| 81～100 | 23 |

均分 30.9 与此前 31.2 基线接近；中位数为 0，说明回答仍然明显两极分化。这个分数用于记录当前 SFT 模型行为，不用于证明模型能力突然提升。

报告文件：`data/instruct/m5-report-sft-110.json`，包含完整汇总与逐题明细，不再只把统计打印到终端。

## 相关回归与 M5 收官

相关回归共 **17 passed**，覆盖：

- 旧 GPTModel 前向与生成；
- checkpoint 保存和恢复；
- RoPE 数学性质与 cache 对齐；
- 选择题、选项打乱和完整答案似然；
- 评分解析、统计及 JSON 报告。

110 条全量报告不需要为了回归重复调用 DeepSeek；代码回归与全量评估分别验收。

至此，M5 的选择题评估、自由生成评分、断点续跑、结构化报告和相关回归均已完成。后续权重空间编程实验独立记录在[笔记 15](/llm/llm-15-weight-space-arithmetic/)，不作为 M5 的阻塞项。
