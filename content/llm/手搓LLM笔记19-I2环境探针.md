+++
title = "手搓 LLM 笔记 19：I2 环境探针，先确认设备到底支持什么"
date = 2026-11-10T14:55:19+08:00
draft = true
slug = "llm-19-i2-environment-probe"
tags = ["LLM", "I2", "PyTorch", "AMP", "SDPA", "torch.compile", "学习笔记"]
summary = "I2 先做环境探针：在真实训练之前，确认 FP16、BF16、autocast、SDPA 与 torch.compile 在当前 Mac/MPS 环境中的支持情况，并讲清高阶函数、lambda、参数展开和延迟执行。"
+++

> I2 不直接从修改训练代码开始。优化之前先确认当前设备究竟支持什么，避免把 CUDA 教程里的能力直接套到 Mac/MPS 上。

## 一、I2-0 的目标是什么？

当前目标是建立训练加速的环境与基线，不是马上让模型提速。

本次环境探针覆盖：

```text
FP16 / BF16 原生矩阵乘法
→ FP16 / BF16 autocast
→ SDPA
→ torch.compile
```

源码：`scripts/i2_environment_probe.py`。

输出报告：`data/reports/i2-environment.json`。

这一步只回答“当前环境能否运行这些能力”，不证明完整模型训练稳定，也不证明任何优化已经产生收益。

## 二、run_probe：统一管理执行与异常

环境探针使用了一个统一入口：

```python
def run_probe(function):
    try:
        result = function()
        return {
            "supported": True,
            "result": str(result),
        }
    except Exception as exc:
        return {
            "supported": False,
            "error": f"{type(exc).__name__}: {exc}",
        }
```

它接收一个可调用对象，在内部真正执行，并统一整理成功或失败结果。

这是一种**高阶函数（Higher-order Function）**的用法：函数接收另一个函数作为参数。也可以把它看成一个手写 wrapper（包装器），有点类似 Java/AOP 里的环绕通知，但这里不需要引入框架。

它解决了两个问题：

1. 把实际执行统一放进 `try/except`，一个探针失败不会阻止其他探针执行；
2. 所有探针使用相同的结果结构，方便汇总成 JSON。

但它只证明“没有抛异常”，不等于结果正确。具体正确性仍由探针内部的断言或结果检查负责。

在正式测试中不能随意吞掉所有异常；这里适合使用，是因为环境盘点的目标是完整收集支持与不支持项。

## 三、位置参数与关键字参数

`*args` 和 `**kwargs` 的区别：

```text
*args   → 接收位置参数，只传值，收集成 tuple
**kwargs → 接收 key=value 参数，收集成 dict
```

例如：

```python
def example(a, b, device=None):
    ...
```

调用：

```python
example(1, 2, device="mps")
```

在一个通用包装器里：

```python
def run_probe(function, *args, **kwargs):
    return function(*args, **kwargs)
```

再这样调用：

```python
run_probe(example, 1, 2, device="mps")
```

就等价于原调用。

`args` 和 `kwargs` 只是约定俗成的变量名，真正让收集与展开生效的是 `*` 和 `**`。

## 四、lambda：把调用包装成稍后再执行的函数

当前代码里：

```python
run_probe(lambda: dtype_probe(torch.float16))
```

等价于：

```python
def temporary_function():
    return dtype_probe(torch.float16)

run_probe(temporary_function)
```

`lambda` 是创建匿名函数的关键字，基本格式为：

```python
lambda 参数: 返回值表达式
```

例如：

```python
lambda x: x * 2
```

等价于：

```python
def double(x):
    return x * 2
```

当前 lambda 冒号前没有参数，所以它是一个无参数函数。

### 为什么不直接调用？

如果写成：

```python
run_probe(dtype_probe(torch.float16))
```

Python 会先执行 `dtype_probe(torch.float16)`，再把结果传给 `run_probe()`。如果探针出错，异常发生在进入 `run_probe()` 之前，内部的 `try/except` 就接不住。

使用 lambda 后：

```text
创建 lambda，但不执行探针
→ 把 lambda 传给 run_probe
→ run_probe 内部执行 function()
→ 这时才执行 dtype_probe(torch.float16)
→ 异常由 run_probe 统一捕获
```

这里的“延迟执行”不是异步、定时或懒加载，也不是等到保存 report 时才执行。它只是**相对于直接调用，推迟到包装器内部执行**。

### 为什么 SDPA 和 compile 不使用 lambda？

因为它们本身已经是没有参数的函数：

```python
run_probe(sdpa_probe)
run_probe(compile_probe)
```

传函数名而没有括号，就还没有执行。`run_probe()` 内部的 `function()` 才会真正调用它们。

需要记住：

```python
run_probe(sdpa_probe)   # 传函数对象，尚未执行
run_probe(sdpa_probe()) # 先执行，再把结果传进去
```

所以规则是：

> 无参数函数直接传函数名；需要参数的函数，可以用 lambda 或 partial 提前绑定参数，再交给统一执行器。

## 五、闭包：内部函数使用外层的 device

几个探针定义在 `main()` 内部，并直接使用：

```python
device=device
```

这里没有显式给 `sdpa_probe()` 传 `device`，是因为内部函数可以读取外层函数作用域中的变量。这属于**闭包（closure）**的使用。

它不是 Python 自动推断参数，也不是自动注入；只是函数沿作用域找到了外层已经定义的 `device`。

## 六、item()：把单元素 Tensor 转成 Python 数字

原生精度探针使用：

```python
result = (x @ x).sum().item()
```

拆开是：

```text
x @ x       → 得到一个矩阵
.sum()      → 对所有元素求和，得到单元素 Tensor
.item()     → 转成普通 Python float
```

`item()` 是 number of elements 为 1 时才能使用的取值方式：

```python
torch.tensor(2.0).item()        # 可以
torch.tensor([1.0]).item()      # 可以
torch.tensor([1.0, 2.0]).item() # 报错
```

它常用于打印 loss、写 JSON 或取单个数值。

但需要注意：

- `loss.item()` 后得到的是普通数字，不能再参与反向传播；
- 在 GPU/MPS 上，`item()` 会把结果同步回 CPU，频繁调用可能影响性能测量。

## 七、autocast：在指定作用域内自动选择部分算子的精度

代码：

```python
with torch.autocast(
    device_type=device.type,
    dtype=dtype,
):
    result = x @ x
```

`autocast` 是自动混合精度/自动类型转换，不是参数匹配。

其中：

- `device_type`：设备类型，例如当前 `"mps"`；
- `dtype`：目标计算精度，例如 FP16 或 BF16；
- `with`：只在这个代码块作用域内启用。

它不会把所有模型参数永久转换，也不会无差别转换所有运算。符合规则的算子会按 autocast 策略选择计算精度，离开 `with` 后恢复默认行为。

探针中还检查了：

```python
assert result.dtype == dtype
```

防止“语法上写了 autocast，实际输出 dtype 却完全没变化”的空操作被误判为支持。

### FP32、FP16 与 BF16 的位分配

| 格式 | 总位数 | 指数位 | 尾数位 |
|---|---:|---:|---:|
| FP32 | 32 | 8 | 23 |
| FP16 | 16 | 5 | 10 |
| BF16 | 16 | 8 | 7 |

三种格式都由符号位、指数位和尾数位组成。指数位决定数值范围，尾数位决定有效数字的精度：

- FP16 指数位较少，范围较小；尾数位比 BF16 多，精度细节更多；
- BF16 指数位与 FP32 相同，范围接近 FP32；尾数位较少，精度更粗；
- FP32 同时具备更多有效数字和足够大的数值范围，适合作为数值基线。

这不是通过“小数点靠前或靠后”实现的。浮点数都可以近似理解为“有效数字 × 2^指数”，指数决定数量级，尾数决定保留多少有效数字。

## 八、SDPA：统一注意力入口，不是单一后端算法

SDPA 全称 Scaled Dot-Product Attention，缩放点积注意力。

调用：

```python
result = F.scaled_dot_product_attention(q, q, q)
```

这里的 `F` 是 `torch.nn.functional` 的别名，不是 function 的缩写。

三个 `q` 分别作为 Q、K、V。真实模型中它们通常来自不同 Linear 投影；探针里复用同一个随机张量，只是为了验证调用链路。

随机张量形状：

```text
(1, 2, 8, 16)
= (B=1, H=2, T=8, D=16)
```

输出形状仍为 `(1, 2, 8, 16)`。

SDPA 完成的数学过程仍然是：

```text
Q × Kᵀ
→ 除以 √head_dim
→ 按需添加 mask
→ softmax
→ × V
```

与手写 eager 的区别是：

```text
eager：逐步生成 scores、weights 和输出
SDPA：交给 PyTorch 统一算子，由后端选择具体实现
```

PyTorch 可能根据版本、设备、dtype、形状和 mask 等条件，选择普通 math、memory-efficient 或其他优化路径。SDPA 不等于 FlashAttention，后者只是可能的后端之一。

这也解释了之前官方对照中的数值差异：数学公式相同，但不同后端的运算顺序、融合与舍入路径可能不同。

## 九、torch.compile：优化计算执行方式

当前探针：

```python
def function(x):
    return x * 2 + 1

compiled = torch.compile(function)
result = compiled(torch.tensor([1.0, 2.0], device=device))
```

`torch.compile(function)` 不会立即执行函数，而是返回一个新的可编译优化对象。传入输入后，由它完成实际计算。

本例中：

```text
1 × 2 + 1 = 3
2 × 2 + 1 = 5
```

输出为 `[3.0, 5.0]`。

compile 的目标是把逐步执行的 PyTorch 代码转换成更适合优化的计算图，再由后端生成更高效的执行路径。它不改变数学公式或模型权重。

首次调用通常有编译成本，后续稳态执行才可能体现收益。微小函数通过探针，不等于完整 model_v3 编译后一定更快。

### 与 Java JIT 的类比

Java HotSpot JVM 中，热点代码会经过 JIT（Just-In-Time，即时编译）优化：

```text
Java 源码
→ javac 生成字节码
→ JVM 执行并收集运行时信息
→ JIT 将热点字节码编译成优化后的原生机器码
```

这里不是修改或重新实现原字节码，而是把热点代码编译成当前 CPU 可直接执行的原生机器码。

常见名词包括 HotSpot、热点代码、分层编译、C1/C2 编译器和去优化。

与 PyTorch 的对应关系：

```text
Java JIT：热点字节码 → 优化后的 CPU 机器码
torch.compile：张量计算图 → 优化后的设备内核
```

一个重要区别是：Java JIT 会依据运行时热点自动优化，而 `torch.compile()` 是我们显式选择要编译的函数或模型。

两者都不是改变程序语义，而是在保持逻辑的前提下优化执行方式。

## 十、当前真实环境结果

当前环境：

```text
Python 3.12.12
PyTorch 2.14.1
macOS arm64
device = MPS
CUDA 不可用
```

探针结果：

| 能力 | 结果 | 实际输出 |
| --- | --- | --- |
| FP16 原生矩阵乘法 | 通过 | sum=4096.0 |
| BF16 原生矩阵乘法 | 通过 | sum=4096.0 |
| FP16 autocast | 通过 | 输出 dtype 为 FP16 |
| BF16 autocast | 通过 | 输出 dtype 为 BF16 |
| SDPA | 通过 | 输出形状 `(1, 2, 8, 16)` |
| torch.compile | 通过 | 输出 `[3.0, 5.0]` |

这些结果证明的是**当前微探针可执行**，不是完整训练优化已经通过。

尚未证明：

- 完整 model_v3 在 FP16/BF16 下训练稳定；
- 长训练的 loss 与 checkpoint 行为正确；
- compile 后的完整模型获得真实吞吐收益；
- 当前 Mac 支持 FlashAttention；
- 任何速度、显存或 MFU 改善。

下一步才是建立固定输入、固定模型、固定步数的 FP32 训练基线，然后逐项引入混合精度、SDPA/compile 和 Activation Checkpointing，并同时记录正确性与资源指标。

## 十一、思考：大模型时代还需要 Dropout 吗？

在环境探针之外，我还注意到了另一个问题：当前 GPTModel 里似乎在多个位置都放了 Dropout，Embedding、Attention 权重和残差分支都有。但现代大模型又经常直接使用 `drop_rate=0.0`，这些传统正则化手段是否已经过时？

我的原始直觉是：大模型是在用海量数据拟合世界，训练样本一直增加，过去为了解决小样本过拟合而设计的 Dropout，放在今天可能显得有些生硬。

这个直觉有一部分是对的。大模型从零预训练时，数据规模很大，很多语料只训练一次或少数几次，算力本身就是主要瓶颈，模型甚至还没有充分拟合训练集。此时主要矛盾往往是训练不足、算力和数据效率，而不是过拟合。Dropout 的正则化收益可能不明显，还会增加额外计算与训练噪声。

但“过拟合的本质就是样本不足”并不完整。更准确的定义是：

> 过拟合是模型在训练数据上的表现，明显好于它在同分布未见数据上的表现。

样本数量只是其中一个因素。数据重复程度、多样性、模型容量、训练步数、epoch、学习率，以及训练分布与真实使用分布是否一致，都会影响过拟合。

即使数据总量很大，也可能因为重复、污染或分布差异而过拟合；小数据也不一定必然过拟合，需要看 train 与 held-out 的真实差距。

放到当前个人博客语料上，结论又会变化。当前训练 token store 只有约 117,890 tokens，如果后续 midtrain 时反复进行多轮 epoch，模型容量较大、训练步数较多，Dropout、学习率、训练步数、数据混合和 early stopping 都可能重新变得重要。

因此，不是“过去的方法在大模型时代失效”，而是：

> 大规模预训练常常不需要 Dropout；小语料微调、midtrain 和反复训练时，它仍然可能有用。是否启用，应由训练场景和 train/held-out 表现决定，而不是仅凭“这是大模型”。

另外，Dropout 也不是一个单纯的性能开关。关闭后即使更快，也可能改变训练行为与正则化强度，不能直接写成 I2 的“免费性能优化”。如果以后做对照，需要固定模型、数据、初始化和训练预算，同时比较训练吞吐、train/held-out loss、BPB 与行为表现。

## 十二、思考：val loss 下降能否直接解决泛化问题？

顺着 Dropout 的讨论，我又产生了一个想法：既然目标是泛化，是否应该准备一个小样本 val 数据集，通过 val loss 下降来解决，而不是通过 Dropout 这种随机方式？

这里需要把训练手段与评估证据分开。

> val loss 下降是评估结果，不是训练手段。验证集可以测量和选择模型，但本身不会直接让模型学会泛化。

Validation 的作用是：

- 测量模型在未参与训练的数据上的表现；
- 帮助选择 checkpoint、学习率、Dropout 和训练步数；
- 在 val loss 开始恶化时考虑 early stopping；
- 检查某种训练方法是否可能改善了泛化。

如果“用 val loss 选择最佳 checkpoint 或 early stopping”，这是合理的；但它只是从已有训练结果中做选择，不是直接提升模型的泛化能力。

Dropout 与验证集工作在两个阶段：

```text
Dropout：
训练时随机屏蔽部分激活
→ 减少对特定神经通路的依赖
→ 尝试改善训练后的泛化表现

Validation：
测量 held-out loss / BPB
→ 判断这种训练方式是否有效
```

所以它们不是互相替代的两种方案，而是训练方法与评估方法的关系。

### loss 下降也不能直接等于“学会了”

即使是 val loss 下降，也只是泛化改善的证据之一：

- 小验证集可能有较大的偶然性；
- 平均 loss 可能被少数样本主导；
- 模型可能只学到表面模式，行为测试仍然失败；
- 反复根据 val 结果调参，也可能产生对验证集的适应性过拟合。

因此更稳妥的划分是：

```text
train：用于梯度更新
val：用于调参、选 checkpoint 和 early stopping
test：保持隔离，用于最终验收
```

同时再配合固定行为测试、BPB 和生成样例，而不是只盯着一个 loss 数字。

如果未来比较 `dropout=0.0 / 0.05 / 0.1`，应该同时观察 train loss、val loss、train/val 差距、固定行为表现以及最终 test 结果。只有当这些证据共同支持时，才能说某种配置在这次实验中可能改善了泛化。

这两个思考最后收敛成同一句话：

> **Dropout 是可能改善泛化的训练手段，val/test 是检验泛化的证据；loss 下降本身不会直接解决泛化问题。真正需要建立的是可复现的训练对照和独立的评估证据。**

## 十三、数学回炉：从 logits、Softmax 到交叉熵的 -ln(p)

在 Activation Checkpointing 的正确性测试中，我又回炉了一个看似早就理解、其实一直说得不够准确的地方：交叉熵到底怎样从模型输出变成 loss？

### 1. logits 与 target 分别是什么？

假设一次有 `N` 个位置需要预测，词表大小为 `V`：

```text
logits：(N, V)
targets：(N,)
```

`logits` 中每一行都是当前位置对整个词表的预测分数；`targets` 中每个值则是该位置的正确 token ID。

例如 `N=1、V=6`：

```python
logits = torch.tensor([[1., 2., 3., 4., 5., 6.]])
target = torch.tensor([4])
```

这里 `target=4` 表示正确类别的下标是 4，不是“target 的概率就是 1”。如果要写成理想的 one-hot 目标分布，才是 `[0, 0, 0, 0, 1, 0]`。

### 2. Softmax 不会减少维度，也不会替训练取 argmax

经过 `log_softmax` 后，形状仍然是 `(N, V)`。它只是把每个位置上的一组 logits 转换成概率分布。

训练时不会取“概率最大的 token”，而是使用 target 中已知的正确 token ID，取出它对应的对数概率：

```python
log_probs = F.log_softmax(logits, dim=-1)  # (N, V)

loss_per_token = -log_probs[
    torch.arange(N),
    targets,
]  # (N,)

loss = loss_per_token.mean()  # 标量
```

所以交叉熵不是 `(N, V)` 与 `(N,)` 的直接逐元素比较，而是“根据正确类别下标取概率，再计算负对数”。

取概率最大的 token 属于生成/预测阶段的 argmax，不是交叉熵训练。

### 3. 为什么 flatten 后就能计算 loss？

语言模型输出是 `(B, T, V)`，target 是 `(B, T)`：

```python
logits.flatten(0, 1)  # 合并 B 和 T，保留 V，得到 (B*T, V)
targets.flatten()     # 展开所有维度，得到 (B*T,)
```

`flatten(0, 1)` 中的 0 和 1 是维度编号，不是取第 0 个和第 1 个元素。

logits 不能直接使用 `flatten()`，否则会把词表维度也展开，破坏每个位置的类别分布。

### 4. -ln(p) 到底在计算什么？

当正确 token 经过 Softmax 后的概率为 `p`，它的交叉熵损失是：

```text
loss = -ln(p)
```

这不是 `100 - 百分比概率`，而是正确 token 概率的负自然对数：

```text
p = 0.40 → loss = -ln(0.40) ≈ 0.9163
p = 0.99 → loss = -ln(0.99) ≈ 0.01005
p = 1.00 → loss = 0
```

正确 token 的概率越高，loss 越小；概率越接近 0，loss 越大。

这里的“值越大 loss 越小”，指的是**正确 token 的概率 p 越大**，不是任意错误 token 的 logit 越大。

### 5. ln(p) 的数学含义

`ln(p)` 是以自然常数 `e` 为底的对数：

```text
ln(p) = logₑ(p)
e ≈ 2.71828
```

它可以理解为指数函数的反函数：

```text
y = ln(p)  ⇔  eʸ = p
```

也就是：e 的多少次方等于 p，这个次数就是 ln(p)。

例如：

```text
ln(1) = 0，因为 e⁰ = 1
ln(e) = 1，因为 e¹ = e
ln(0.5) ≈ -0.6931
```

`ln` 是自然对数，不是 `log10`，并且要求 `p > 0`，所以 `ln(0)` 没有定义。

当 `0 < p < 1` 时，`ln(p)` 是负数；交叉熵前面的负号再把它变成非负的损失值。

### 6. 与 BPB 的连接

PyTorch 交叉熵默认使用自然对数，单位是 nats。之前计算 BPB 时除以 `ln(2)`，就是把 nats 转成 bits，再按实际评估文本的 UTF-8 bytes 归一化。

因此，从模型输入到评估指标可以这样串起来：

```text
token IDs
→ 模型输出 logits
→ log_softmax
→ 取正确 token 的对数概率
→ -ln(p) 得到交叉熵 loss
→ nats 转 bits
→ 按原始文本 bytes 归一化得到 BPB
```

这次回炉让我再次意识到：能写出 `F.cross_entropy()` 不等于已经讲清它。高数和数学直觉丢了很久也不需要逃避，但暂时不需要另开一门庞大的数学主线；先把当前公式与代码、数值例子和实际指标对应起来，就是有效的补充。

