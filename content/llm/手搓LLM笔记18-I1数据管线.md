+++
title = "手搓 LLM 笔记 18：I1，让语料从文本流向可训练数据"
date = 2026-11-10T12:25:26+08:00
draft = false
slug = "llm-18-i1-data-pipeline"
tags = ["LLM", "I1", "数据工程", "memmap", "BPB", "学习笔记"]
summary = "从博客源文档清单、最小清洗和 JSONL，到 uint32 token 文件、np.memmap、训练冒烟、BPB 与 Scaling 测算；重点不是训练大模型，而是把数据如何进入模型这条链路打通。"
+++

> 今天没有训练一个更强的大模型，而是回答另一个更基础的问题：一堆博客文章，怎样变成可以追溯、可以流式读取、可以参与训练和评估的数据？

## 一、I1 要解决什么？

第一阶段和 I0 的代码已经可以完成模型训练与推理，但数据侧仍然存在一个隐患：所有东西都会被提前装进内存。

旧的 `TokenStreamDataset` 大致是：

```python
ids = []

for text in texts:
    ids.extend(tokenizer.encode(text))

for i in range(0, len(ids) - max_length, stride):
    self.input_ids.append(ids[i:i + max_length])
    self.target_ids.append(ids[i + 1:i + max_length + 1])
```

这里有三层全量物化：

1. 全部文本被读入内存；
2. 全部 token IDs 被放进 Python list；
3. 所有 input/target 窗口又被提前保存成两个 list。

在当前个人博客规模下，它并不慢，也不构成明显内存压力。但如果未来语料扩大，这种写法会让内存随语料总量增长。

所以 I1 的目标不是“让今天的数据突然变快”，而是建立一条更可扩展的主干：

```text
源文档清单
→ 最小清洗
→ train / held-out 隔离
→ JSONL 文档流
→ uint32 token 文件
→ np.memmap 按需读取
→ 训练与 BPB 评估
```

## 二、先盘点：42 条文档不都是文章

第一步没有直接清洗，而是从 `lv_blog/content/**/*.md` 重新建立文档级清单。

`train.txt` 已经把多篇文章拼成了一个大字符串，无法单独追溯每一篇。新的清单直接读取原始 Markdown，并保留标题、路径、日期、正文大小和 SHA-256。

第一次汇总：

```text
included_documents = 42
excluded:
  index  = 9
  layout = 3
  draft  = 14
```

我一开始觉得数量对不上，因为印象里应该是“接近 40 篇”。继续检查后发现，42 条中还包含：

```text
content/about.md       → 关于页面
content/roadmap.md     → 学习路线图
content/llm-backlog.md → 学习回炉待办
```

于是增加了 `document_type`，得到：

```text
article  = 39
profile  = 1
roadmap  = 1
backlog  = 1
合计     = 42
```

这正好解释了数量差异。

这次盘点让我看到：**数据口径不一致时，先分类和追溯，不要急着删除或强行让数字相等。**

## 三、manifest 是数据档案，不是训练文本

今天生成了几种不同用途的文件，需要分清：

```text
source inventory / corpus manifest
记录文档来源、类型、划分、大小和 hash

train.jsonl / heldout.jsonl
保存一篇篇清洗后的实际文档内容

token store metadata
记录 tokenizer、dtype、EOS、文档 offset / length 和 hash

memmap Dataset
根据二进制 token 文件与训练窗口配置，按需产生样本
```

manifest 不是模型直接读取的正文，而是整批数据的档案。后续要证明两次实验使用的是同一批数据，不能只写“用了博客语料”，还要能对应到具体版本和内容指纹。

## 四、SHA-256 在这里做什么？

SHA-256 在当前管线里只是内容指纹，不是加密，也不会参与模型计算。

它主要有四个用途：

1. 检查完全重复的正文；
2. 防止同一篇内容同时进入 train 和 held-out；
3. 判断文件或正文是否发生变化；
4. 让训练、BPB 和评估报告能追溯到具体数据版本。

今天还区分了两种 hash：

```text
source_sha256
→ 清洗后正文

encoded_sha256
→ 实际送入 tokenizer 的“标题 + 正文”
```

这两个值需要分开，因为后续加入标题以后，正文 hash 已经不能代表完整的编码输入。

## 五、清洗只做到够用，不做通用平台

我的博客格式比较固定，部分文章存在图片链接。今天的决定是：不写通用 Markdown 解析器，只覆盖当前真实格式。

`src/squid/data/markdown.py` 只做：

- 普通链接保留显示文字；
- 图片保留 alt，无 alt 则删除；
- 合并多余空行；
- 按代码块分段，代码内部不应用清洗规则。

代码块需要单独保护，否则代码里的注释或字符串也可能被误当成 Markdown 链接和图片。

`tests/test_markdown.py` 验收了 5 个场景：

```text
普通链接保留文字
图片保留 alt
无 alt 图片删除
代码块保持不变
多余空行合并
```

结果：`5 passed`。

这里刻意没有继续做 OCR、通用质量评分、复杂清洗规则或完整 MinHash 管线。当前语料规模小、来源可信，清洗够用地服务主干即可。未来如果有大批量语料，再借助 AI 完成更系统的清洗与划分也来得及。

## 六、第一次接触 JSONL

清洗后的文档被写成：

```text
data/corpus/blog_v1/train.jsonl
data/corpus/blog_v1/heldout.jsonl
```

JSONL 是 JSON Lines，一行一个完整 JSON 对象：

```jsonl
{"title": "第一篇", "text": "第一篇正文"}
{"title": "第二篇", "text": "第二篇正文"}
```

它和 JSON 数组不同，不需要一次性读取整个文件，可以：

```python
with open(path, encoding="utf-8") as file:
    for line in file:
        document = json.loads(line)
```

正文中的换行会被转义为 `\n`，读取后再还原，因此仍能保持“一行一篇”。

JSONL 不适合用 `indent=2` 美化，否则一条记录会跨多行。`manifest.json` 可以美化，文档流则保持一行一条。

最终构建结果：

```text
train_documents   = 38
heldout_documents = 2
total_documents   = 40
```

即：

```text
39 篇文章 + 1 篇 profile = 40 个候选
40 - 2 篇固定 held-out = 38 条训练候选
```

原有 held-out 继续隔离，没有因为重新生成语料而混回训练集。

## 七、标题应该进入训练文本

最初 `write_tokens()` 只编码：

```python
document["text"]
```

我随后意识到：标题对我来说很重要，它不是单纯的文件名，也承载文章主题和表达结构。

因此实际编码文本改为：

```python
text = (
    f"# {document['title']}\n\n"
    f"{document['text']}"
)
```

也就是：

```text
# 文章标题

清洗后的正文……
```

metadata 中同时记录：

```json
{
  "include_title": true,
  "title_template": "# {title}\n\n{text}"
}
```

这样以后看到 token 文件，就能明确知道标题有没有参与训练，以及是怎样拼入的。

## 八、为什么 token 文件使用 uint32？

Qwen 的词表大小是 `151936`，而 `uint16` 最大只能表示 `65535`。

因此不能为了节省空间使用 uint16，当前统一使用：

```python
np.asarray(ids, dtype=np.uint32)
```

每个 token 固定占 4 bytes。

`build_token_store.py` 的主干是：

```text
逐行读取一篇 JSONL
→ 拼接标题与正文
→ 编码当前文档
→ 追加 EOS ID
→ 转成 uint32
→ 写入二进制文件
→ 记录 offset、length 和 hash
```

这里修正过一个属性错误：需要写入的是整数 `tokenizer.eos_id`，不是字符串 `eos_token`。

最终生成：

```text
data/token_store/blog_v1/
├── train.uint32.bin
├── heldout.uint32.bin
└── metadata.json
```

汇总结果：

```text
train_tokens   = 117890
heldout_tokens = 5485
```

metadata 还验证了：

```text
二进制文件 bytes = token_count × 4
```

## 九、memmap：从“保存所有窗口”改成“用时再切”

`np.memmap` 使用只读映射：

```python
tokens = np.memmap(
    token_path,
    dtype="uint32",
    mode="r",
)
```

第一次读取时，成功从首篇文档还原出：

```text
# 关于

## 我是谁

吕炘嵘，一个写了十一年多代码的人……
```

新的 `MemmapTokenDataset` 不再提前保存所有窗口，只保存映射、窗口长度、stride 和样本数量：

```python
start = idx * self.stride

input_ids = self.tokens[
    start:start + self.max_length
]
target_ids = self.tokens[
    start + 1:start + self.max_length + 1
]
```

交给模型前再转换成 `torch.long`，因为 Embedding 索引需要整数张量。

### 最后一个窗口会不会越界？

`sample_count` 使用与旧实现一致的窗口起点范围。设 token 总数为 `L`、窗口长度为 `M`，最后一个起点满足：

```text
start <= L - M - 1
```

因此 target 的切片结束位置最多为：

```text
start + M + 1 <= L
```

刚好不会超出末尾。

NumPy 切片越界时通常会静默返回较短数组，所以测试不能只比较新旧实现，还需要独立检查每个 input/target 的 shape 都是 `(128,)`。

## 十、先做内容对照，再谈内存优化

今天写了两层对照：

1. `test_token_store_matches_pack_tokens`：二进制 token 流与旧 `pack_tokens()` 逐元素一致，offset、length 和 EOS 也一致；
2. `test_memmap_dataset_matches_legacy_dataset`：在 stride 64 和 128 下，新旧 Dataset 的选中窗口内容一致。

全部通过。

第一次内存对照还暴露了一个实验设计错误：

```text
旧 Dataset 使用旧 train.txt：69316 tokens → 541 窗口
新 Dataset 使用新 token store：117890 tokens → 921 窗口
```

输入不同，内存数字就不能直接比较。

修正为两边都使用同一个 `train.uint32.bin` 后，得到：

| 实现 | source tokens | windows | Python 当前分配 | Python 峰值分配 |
| --- | ---: | ---: | ---: | ---: |
| 旧 TokenStreamDataset | 117890 | 921 | 2,004,496 bytes | 2,004,672 bytes |
| MemmapTokenDataset | 117890 | 921 | 1,766 bytes | 8,505 bytes |

这才是同输入对照。

减少的是“提前物化所有窗口”的 Python 分配，不是宣称操作系统映射页面完全不占内存。`tracemalloc` 也无法覆盖所有底层和 OS 内存。

两边的构建时间分别是约 `2.50 ms` 与 `8.25 ms`，单次毫秒级结果不能用来证明 memmap 更慢或更快。当前优化的目标是可扩展性，不是这几毫秒。

## 十一、让 memmap 数据真正进入训练

随后用一个小型 `GPTModelV3` 做了 5 步训练冒烟：

```text
emb_dim = 64
ffn_dim = 256
n_layers = 2
n_heads = 4
n_kv_heads = 2
context_length = 128
vocab_size = 151936
```

没有加载 Qwen 权重，不追求模型质量，只验证：

- memmap 样本能进入模型；
- loss 是有限值；
- backward 与 optimizer 能执行；
- checkpoint 能保存与重载；
- 重载前后同一批输入的 logits 完全一致。

实测 loss：

```text
12.1019 → 12.1559 → 12.0544 → 12.1084 → 12.0915
```

没有断言 loss 必须下降，因为 5 步随机批次训练不能支持这种要求。

作为数量级参照，词表均匀分布时交叉熵约为：

```text
ln(151936) ≈ 11.93
```

所以这里的 loss 只能说明训练链路可运行，不能说明模型已经学会博客内容。

## 十二、BPB：把 loss 归一到原始文本字节

BPB 是 Bits Per Byte，表示平均每个原始 UTF-8 字节对应多少 bits 的预测/编码成本。同一份评估文本、同一口径下，通常越低越好。

它需要模型 loss 参与，不是 tokenizer 单独能计算的指标：

```text
BPB = 总交叉熵 nats / ln(2) / 总评估 UTF-8 bytes
```

今天的 held-out 冒烟报告：

```text
evaluated_tokens      = 5376
evaluated_utf8_bytes  = 18932
mean_loss             = 12.081579798743839
BPB                   = 4.949496596618363
```

计算时按 target 数累计交叉熵，避免最后一个较小 batch 被赋予与完整 batch 相同的平均权重；EOS 不折算成自然文本字节。

这个数值只验证 BPB 计算链路，不代表 Qwen，也不代表个人 midtrain 效果。换数据集或评估口径后，不能直接拿 BPB 比较。

## 十三、parameters、numel 与 Scaling 测算

`parameter.numel()` 是 number of elements，计算参数张量中有多少个元素。

例如：

```text
形状 (10, 64) 的权重
numel = 10 × 64 = 640
```

`model.parameters()` 会遍历模型中注册的 Parameter，包括 Linear、Embedding、RMSNorm 等模块内部的底层可学习张量；mask 和 inv_freq 这类 buffer 不属于 Parameter。

当前冒烟模型实际参数量：

```text
19,571,264
```

其中：

```text
tok_emb.weight  = 9,723,904
out_head.weight = 9,723,904
```

两块合计 `19,447,808`，约占整个模型的 **99.37%**。

因为当前冒烟配置是 `tie_word_embeddings=False`，输入与输出是两套独立权重。如果改为共享，总参数约为 `9,847,360`，几乎减半。

这也重新解释了 Weight Tying：不是两个模块变成一个，而是 `out_head.weight` 与 `tok_emb.weight` 指向同一个底层 Parameter。

### Chinchilla：一个从零预训练的参考基线

Chinchilla 是 DeepMind 在 2022 年提出的模型及训练研究，论文是 [《Training Compute-Optimal Large Language Models》](https://arxiv.org/abs/2203.15556)。

它研究的核心问题是：

> 在训练算力有限的情况下，参数量和训练 token 数应该怎样搭配？

当时很多模型倾向于不断扩大参数量，但训练数据量没有同步增加。Chinchilla 指出：很多大模型其实处于训练不足的状态，不能只堆参数，还要同步增加数据。

Chinchilla 使用大约 70B 参数和 1.4T tokens，两者之比约为：

```text
1.4T tokens / 70B 参数 ≈ 20 tokens / 参数
```

因此，“约 20 tokens/参数”后来常被用作从零预训练的一个粗略参考。它不是严格的物理定律，也不是所有模型都必须满足的门槛。

### 为什么它叫“计算最优”参考？

常见的 Transformer 训练计算量可以粗略理解为：

```text
训练计算量 ≈ 6 × 参数量 × 训练 token 数
```

在算力固定时，参数变大和 token 变多会争夺同一份计算预算：

- 参数很大、数据太少，模型可能训练不足；
- 数据很多、模型太小，也可能无法充分利用数据中的规律；
- Chinchilla 研究的是怎样在这两者之间取得更合理的配比。

它不是在讨论“一个参数必须分到 20 个 token 才能训练”，而是在讨论**从零预训练时，怎样让算力配置更接近计算最优**。

### 用当前模型做一次数量级估算

今天用“约 20 tokens / 参数”做了参考计算：

```text
当前冒烟模型参数量：19,571,264
当前训练语料：117,890 tokens

参考 token 量：19,571,264 × 20 = 391,425,280
当前语料覆盖率：117,890 / 391,425,280 ≈ 0.000301 ≈ 0.0301%

Qwen 0.5B 名义参考 token 量：10,000,000,000
当前语料覆盖率：约 0.00118%
```

这说明：按这个经验参考粗略估算，当前博客语料远低于从零计算最优预训练的参考量级。

但它不能推出：

- 当前模型完全不能训练；
- 小语料训练没有任何效果；
- 所有模型都必须严格训练到 20 tokens/参数；
- 个人 midtrain 没有意义。

语料少时模型仍可能学到模式，只是更容易重复、记忆或过拟合。现代模型也会因为推理成本、数据质量和训练目标不同，采用不同的实际配比。

### 计算时还要统一两个口径

**第一，训练总 token 数不等于去重后的语料 token 数。**多轮 epoch 会重复处理同一批语料，不能把“训练时处理的总 token 数”和“唯一语料 token 数”混为一谈。

**第二，参数统计口径必须一致。**今天使用的是总参数量，而当前冒烟模型约 99% 参数集中在输入/输出词表矩阵中。这个计算适合建立数量级直觉，不等于完整复现 Chinchilla 论文的 Scaling 实验。

个人 midtrain 是从已有底座继续训练，不是从零学习语言。Chinchilla 在这里的价值是提供一个**参数、数据和算力配比的参考基线**，而不是成为个人语料训练的硬性准入条件。

## 十四、今天记录的后续选修实验

实验名称：

> **在 GPTModel 的多头注意力机制计算中引入门阀装置对比。**

初步想法是在 attention 合头之后、`out_proj` 之前增加按 token、按特征通道的 sigmoid 门控。

Attention 本身已经通过 softmax 权重决定“从哪些 token 读取信息”；新增门控可以进一步决定“这些 attention 输出在哪些通道上通过多少”。两者作用对象不同，不必然重复。

这个实验当前只记录想法，尚未开始，不阻塞 I1。若承接 Qwen 权重，需要单独处理新增参数与初始化，不能直接 strict 加载原权重。

## 十五、今天的边界与真实完成方式

今天完成的是数据管线和指标闭环：

```text
清单 → 最小清洗 → 划分 → JSONL → uint32 → memmap
→ 训练冒烟 → checkpoint → BPB → Scaling 参考测算
```

没有完成或没有展开：

- 个人中文 midtrain；
- 通用大数据清洗平台；
- MinHash 近似去重实现；
- 大模型训练；
- 分布式、MoE 和 DeepInfer 部署；
- 对任意语料规模与任意模型质量的证明。

今天的部分工程脚本由 Kimi 提供完整代码，我负责运行、阅读、提问和验收；这部分不写成“全部亲手实现”。核心概念仍需通过复盘和后续默写来确认是否真正掌握。

## 十六、阅读后的四个回答

这一节的主体回答由我在阅读草稿后手敲，Kimi 只做了少量结构整理，并修正了 DataLoader 中 shuffle 的一处表述。

### 1. 今天哪些概念只是暂时听懂，还需要重新复述？

概念上的内容基本都能理解。说到底，今天做的事情就是**按需加载**。

之前训练数据比较小，可以全部加载到内存中；当训练语料规模上升后，就需要实现流式加载。`np.memmap` 的核心作用是在磁盘文件与内存访问之间建立映射关系，只把当前需要的部分交给内存使用，而不是提前把整个文件和全部训练窗口都转成 Python 对象。

所以今天的主干不是“把语料做得多大”，而是“语料变大以后，数据访问方式是否需要改变”。

### 2. 哪些代码需要我重新手写一遍？

我理解目前的代码暂时不需要专门考虑重写和回炉。本质上它仍然属于数据处理部分，我需要先理解原理和本质，后续在实际调整和使用过程中还会继续学习。

这不等于宣称每段代码都能脱稿默写，而是当前没有必要为了默写再单独开一轮重复劳动。

### 3. 数据管线和模型训练之间，还有哪些关系没有真正打通？

我目前的理解是：

```text
原始文档
→ 清洗与 train / held-out 划分
→ token store
→ Dataset
→ input / target 的 +1 错位处理
→ DataLoader
→ 模型 forward 与 loss
```

其中：

```python
input_ids = tokens[start:start + max_length]
target_ids = tokens[start + 1:start + max_length + 1]
```

target 仍然是在同一 token 流上向后错开一位，让模型学习预测下一个 token。

DataLoader 本身不知道 train、val、test 的区别，是我们根据用途设置 shuffle：

```text
train：通常 shuffle=True，让训练样本顺序随机化
val：shuffle=False，保证验证顺序与结果可复现
test：shuffle=False，保证最终测试顺序与结果可复现
```

另外，val 用于调参和选择，test 用于最终评估；held-out 是“被隔离、不参与训练”的总称，不能把所有 held-out 都自动当成同一个用途。

### 4. 哪些疑问值得单独回炉，而不是继续往后赶？

目前没有感觉需要单独回炉的内容。今天的疑问已经在 JSONL、SHA-256、标题拼接、uint32、memmap、窗口边界、BPB、parameters 和 Scaling 测算的过程中逐项解决。

如果后面实际训练或调整数据管线时暴露出新的理解缺口，再针对那个具体问题回炉，不为了回炉而回炉。
