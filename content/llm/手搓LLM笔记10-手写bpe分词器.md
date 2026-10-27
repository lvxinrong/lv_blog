+++
title = "手搓 LLM 笔记 10：手写 BPE，从写不出来到甜点区"
date = 2026-10-27T18:00:00+08:00
draft = false
slug = "llm-10-handwritten-bpe"
tags = ["LLM", "diy-llm", "BPE", "tokenizer", "学习笔记"]
summary = "纯 Python 手写 BPE 训练与编解码，封装成 SquidTokenizer；再用压缩率曲线和小模型 BPB 实验，找到博客语料的甜点区 4000 次合并。"
[cover]
    image = "covers/llm-10-handwritten-bpe.jpg"
    alt = "手搓 LLM 笔记 10：手写 BPE"
    hiddenInList = true
    hiddenInSingle = true
+++

上一章遗留的作业：在 `squid/tokenizer/bpe.py` 里实现三个函数：`train_bpe`（学合并表）、`encode`（按表切分）、`decode`（还原）。先小语料跑通往返，再上博客语料测压缩率。

说实话，开工前我觉得自己写不出来。但拆成小函数之后，一个一个都拿下了。

## 三个零件

**count_pairs**：用滑动窗口把 i 和 i+1 的 id 配成 key，统计每个 key 出现的次数。

```python
def count_pairs(ids: list[int]) -> dict[tuple[int, int], int]:
    counts = {}
    for a, b in zip(ids, ids[1:]):
        key = (a, b)
        if key not in counts:
            counts[key] = 1
        else:
            counts[key] += 1
    return counts
```

**merge**：把 ids 里所有出现过的 pair 替换成新 id。比如 pair=(1,2)、ids=[1,2,1,2,3,4,5]、new_id=9，结果就是 `[9, 9, 3, 4, 5]`。

```python
def merge(ids: list[int], pair: tuple[int, int], new_id: int) -> list[int]:
    new_idx = []
    i = 0
    while i < len(ids):
        if i < len(ids) - 1 and (ids[i], ids[i + 1]) == pair:
            new_idx.append(new_id)
            i = i + 2
        else:
            new_idx.append(ids[i])
            i = i + 1
    return new_idx
```

这里有个容易写错的点：统计是滑动窗口（允许重叠），替换是贪心扫描（命中消费两格，不匹配消费一格）。所以用 while 手动控制步长，for i in range 里修改 i 下一轮会被覆盖。

**train_bpe**：vocab 初始 256 项（所有单字节），每轮取 count_pairs 里 value 最大的 key 合并，新 id 从 256 开始累加。

```python
def train_bpe(text: str, num_merges: int):
    ids = list(text.encode("utf-8"))
    vocab = {i: bytes([i]) for i in range(256)}
    merges = {}

    for _ in range(num_merges):
        counts = count_pairs(ids)
        if not counts:
            break
        best = max(counts, key=counts.get)
        new_id = 256 + len(merges)
        ids = merge(ids, best, new_id)
        merges[best] = new_id
        vocab[new_id] = vocab[best[0]] + vocab[best[1]]

    return vocab, merges
```

注意最后一行：best 里装的是 id 不是字符，要先查 vocab 取出 bytes 再拼接，不能直接 `best[0] + best[1]`（那是两个整数相加）。

## encode / decode 与往返无损

```python
def decode(ids: list[int], vocab) -> str:
    return b"".join(vocab[i] for i in ids).decode("utf-8")

def encode(text: str, merges) -> list[int]:
    ids = list(text.encode("utf-8"))
    for pair, new_id in merges.items():
        ids = merge(ids, pair, new_id)
    return ids
```

decode 是查词表把 ids 还原成文本，必须先在 bytes 世界拼完整再 decode，不然中文多字节字符会被切碎。encode 是把训练学到的合并规则**按学习顺序**在新文本上重放一遍——merges 存的是规则不是结果，不重放，新 token 不会出现。

往返验收过了：`decode(encode(text, merges), vocab) == text`。

Python 里 bytes 和 str 的转换我目前还不熟，记入欠账，后面找机会补。

## 封装成 SquidTokenizer

```python
class MyBPETokenizer(SquidTokenizer):
    def __init__(self, vocab, merges, eos_id=None):
        self.vocab = vocab
        self.merges = merges
        self._eos_id = eos_id if eos_id is not None else len(vocab)
        self.vocab.setdefault(self._eos_id, b"<|endoftext|>")

    def encode(self, text: str) -> list[int]:
        return bpe.encode(text, self.merges)

    def decode(self, idx: list[int]) -> str:
        return bpe.decode(idx, self.vocab)

    @classmethod
    def from_directory(cls, path):
        vocab, merges = bpe.load_bpe(path)
        return cls(vocab, merges)

    @property
    def eos_id(self) -> int:
        return self._eos_id
```

这段学到的 Python 点：

1. 三元表达式是 `值A if 条件 else 值B`，所以 eos_id 那行就是“传了用传入的，没传用词表大小”
2. `@classmethod` 是挂在类上的方法，类似 Java 静态工厂。`cls(vocab, merges)` 就是调用 `__init__`，但比 Java static 多一层：cls 是类本身，子类调用返回子类实例
3. `@property` 把方法伪装成属性，访问不用加括号
4. `self._*` 下划线只是约定，不是 private，依然能访问

## 实验一：压缩率曲线与甜点区

分别训练了 [64, 128, 256, 512, 1024, 2000, 4000, 8000, 16000] 次的词表，在 held-out 文本上测压缩率（`len(text.encode("utf-8")) / len(tokenizer.encode(text))`，即 bytes/token，越高越省）：

```
merges=   64  tokens=10588  bytes/token=1.29
merges=  128  tokens= 9631  bytes/token=1.42
merges=  256  tokens= 8346  bytes/token=1.64
merges=  512  tokens= 7009  bytes/token=1.95
merges= 1024  tokens= 5944  bytes/token=2.30
merges= 2000  tokens= 5043  bytes/token=2.71
merges= 4000  tokens= 4287  bytes/token=3.19
merges= 8000  tokens= 3869  bytes/token=3.54
merges=16000  tokens= 3704  bytes/token=3.69
```

token 数一直在降，bytes/token 一直在涨，但**看每次翻倍的收益**：前期稳定 +17% 左右，4000→8000 掉到 +11%，8000→16000 只剩 +4%。**甜点区在 4000-8000**，再往后基本是在背语料。

直观例子：手机号最好学成 3-4-4 的片段，merges 一直增大就会学成整个 11 位号码——每个号码独一无二，embedding 永远学不到，模型也无法对号码内部做推理。所以并不是 merges 越多越好，每个 token 携带的信息越大，模型训练时也需要更强的能力去掌握它。

另一个好玩的发现：512 次合并时“大模型”还排不上号（语料里只出现 31 次），2000 次之后它终于“拥有姓名”，被切成了一个完整 token。**词表大小决定了多低频的词才配拥有姓名。**

## 实验二：BPB，把模型拉上一起评

和 DeepSeek 讨论后确认：评估分词器不能只看 bytes/token，那只是在评分词器本身，还得看“模型+词表”的整体效果。这个指标叫 **BPB（Bits Per Byte）**：

```
BPB = (val_loss / ln2) ÷ bytes/token
```

含义：**给这段文本编码，平均每个字节要花多少比特**。val_loss 是模型每预测一个 token 的代价（nats），除以 ln2 换成比特；再除以 bytes/token，就把“每个 token 的成本”折算成“每个字节的成本”。**越低越好**——它同时惩罚两种情况：词表太碎（bytes/token 小）和模型没学好（val_loss 高）。

### 实验设计

四组：512 / 2000 / 4000 / 8000，同一个微型模型配置（emb_dim=64、n_layers=2、context=128），同一份 train/held-out 文本，只换分词器。

**一个关键的控制变量：统一步数，不是统一 epoch。** 因为词表越大，同样文本的 ids 越短，定长窗口切出的窗口数越少，每 epoch 的训练步数也越少：

```
窗口数 = (len(ids) - max_length) / stride
每 epoch 步数 = 窗口数 / batch_size
```

如果只统一 epoch，大词表模型等于“饿着肚子考试”。所以给 `pretrain_model` 加了 `max_steps` 参数，四组都固定走 500 步。

### 结果

```
m512 : val_loss=4.819  bytes/token=1.99  BPB=3.494
m2000: val_loss=6.551  bytes/token=2.80  BPB=3.373
m4000: val_loss=7.584  bytes/token=3.30  BPB=3.315
m8000: val_loss=8.378  bytes/token=3.66  BPB=3.300
```

**为什么 val_loss 一路涨？** val_loss 是“每个 token 的预测难度”，词表变大之后，大量 token 在 117KB 语料里只出现几次，embedding 学不充分，预测它们接近靠蒙，困惑度自然上升。这不是词表变差，是“大 token 更难预测”的固有代价。

**但 BPB 在降**——因为每个 token 装的字节更多了，折算回每字节成本反而便宜。而且看边际收益：512→2000 降 0.121，2000→4000 降 0.058，4000→8000 只降 0.015。**BPB 的甜点同样在 4000 附近**，和压缩率实验互相印证。

结论：**val_loss 上升不等于词表不好，BPB 才是整体账；但 BPB 的边际收益也会递减，4000 之后再合并基本没红利。**

## BPE 的三个哲学点

实验做完再回头看，BPE 的底层逻辑其实就三句话：

1. **原子由数据决定。** 什么是“思考的最小单位”，不是人预先规定的，是语料的统计分布决定的。代码语料出 `def`、`();`，中文博客语料出“模型”、“训练”——**词表是语料的指纹**，换语料就要重新训词表。
2. **频率决定谁先成为原子。** BPE 每轮只合并最高频的相邻对，它只认频率，不认语义重要性。“大模型”再重要，出现 31 次也得往后排。
3. **预算决定多低频才配拥有姓名。** 词表大小（合并次数）就是预算：高频组合早早拿到独立 token_id，低频组合要等预算够了才有机会。512 次时“大模型”没姓名，2000 次才有了。

## 工程收获

- 训练产物（vocab/merges）用 JSON 存成中间文件（`save_bpe` / `load_bpe`），实验和训练可以分开重跑
- 不同配置分目录存（`data/blog/m512/`、`m2000/`……），不然实验产物互相覆盖，回头根本对不上号
- 路径用 `Path(__file__).resolve().parents[N]` 锚定，不再受 IDE 工作目录的摆布

## 欠账与下一步

- Python 的 bytes/str、pathlib 这些基础用法还不熟，找时间补
- M2 预训练：token 流打包、梯度累积、bpb 指标，这次 BPB 实验就是预习

**一句话总结 M1：BPE 的目标不是把文本压到最短，是在压缩率、词表规模、可学习性、组合泛化之间找平衡。**
