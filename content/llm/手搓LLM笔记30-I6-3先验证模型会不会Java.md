+++
title = "手搓 LLM 笔记 30：I6-3 先验证模型会不会 Java"
date = 2026-11-26
draft = false
slug = "llm-30-i6-3-java-basics"
tags = ["LLM", "I6", "Java", "基础能力评估", "控制变量", "学习笔记"]
summary = "I6-3 已冻结 100 条训练样本与 20 条独立验证题，完成 4/8 epochs LoRA 对照：4 epochs 有局部概念改善，8 epochs 出现回落且整体未超过前者，决定停止加 epochs。下一步只针对 static 增训 30 个新场景，保持其余配置不变，重点验证直接访问、显式对象引用和 static 字段共享是否真正改善。"
+++

这篇承接 [笔记 29：I6-2 能力分层——Loss 下降究竟证明了什么？](/llm/llm-29-i6-capability-layers-loss-boundary/)。

前两篇 I6 记录了许多失败：模型会复读、会改格式、会生成合法 JSON，也会偶尔修复训练样本，但一直没有证明它能稳定修复未见缺陷。

今天决定不再从真实缺陷倒推能力，而是先验证一个更基础的假设：

> **0.6B 到底会不会 Java？**

## 一、为什么要先建立第一层

之前的实验默认了基础模型已经具备 Java 能力，只需要通过后训练学会缺陷修复。但这个前提从未被系统验证。

模型能复述方法、保持签名、输出结构化字段，甚至生成可编译的方法，都不能证明它掌握了基本的类型、边界和逻辑语义。

因此，I6-3 先不继续讨论训练数据、rank、span 或 Agent，而是回到最小任务：

```text
给模型明确的方法签名和规格
→ 让它生成一个短方法
→ 严格校验结构
→ javac 编译
→ 用独立断言验证行为
```

这一步不验证“会不会修真实缺陷”，只验证“能不能写出基本可运行的 Java”。

## 二、第一层实验卡：I6-J0

### 固定条件

```text
模型：Qwen3-0.6B 官方原始权重
adapter：不加载
dtype：bf16
thinking：关闭
解码：贪心，单轮 Pass@1
context：4096
max_new_tokens：256
```

输出契约：

```text
只输出一个完整 Java 方法
方法签名必须与输入一致
不要完整类、测试、Markdown 或解释
```

每题只渲染和分词一次，保留 input IDs、原始响应和生成 token 数。输出只移除实际命中的末尾 EOS，不自动裁剪方法、补括号或修复代码。

### 首批六道题

| ID | 方法签名 | 规格与公开示例 | 私有断言 |
| --- | --- | --- | --- |
| J0-01 | `public static int add(int a, int b)` | 两数之和，`2 + 3 = 5` | `add(-2, 3) == 1`、`add(0, 0) == 0` |
| J0-02 | `public static int maxOfTwo(int a, int b)` | 返回较大值，`maxOfTwo(2, 7) == 7` | 相等时返回该值、负数比较 |
| J0-03 | `public static int sumArray(int[] values)` | 数组求和，`[1,2,3] → 6` | 空数组为 0、含负数数组 |
| J0-04 | `public static int countEven(int[] values)` | 统计偶数个数，`[1,2,4,5] → 2` | `[-2,0,3] → 2`、奇数数组为 0 |
| J0-05 | `public static String toUpperCase(String text)` | 转大写，null 返回 null，`"abc" → "ABC"` | `null`、空字符串、混合大小写 |
| J0-06 | `public static double divideAsDouble(int numerator, int denominator)` | 返回 double 除法，`1 / 2 → 0.5` | `1 / 4 → 0.25`、负数除法 |

任务约束：

- 数组参数不传入 null；
- 除数保证不为 0；
- 公开示例放入 Prompt；
- 私有断言只存在评估器中，不进入 Prompt；
- 参考实现只用于正控，不进入模型输入。

这些题覆盖基本运算、条件、循环、数组、null、String API 和类型转换。它们不是训练集，也不承担证明通用 Java 能力的任务，只是第一层最小探针。

## 三、应用与验收链路

候选方法与测试类相互独立，应用器负责：

```text
严格校验恰好一个签名匹配的目标方法
→ 原样插入独立测试类
→ javac 编译
→ java -ea 执行公开与私有断言
```

评估不依赖 Defects4J，也不引入 JUnit，避免把真实项目环境混入基础能力测试。

每题分别记录：

```text
structure_pass：结构合法
compile_pass：javac 返回 0
behavior_pass：公开与私有断言全部通过
```

失败分类固定为：

```text
malformed_method：结构或签名不合格
compile_failed：编译失败
assertion_failed：编译成功但行为断言失败
length_limited：输出预算耗尽
evaluation_error：应用器、测试或环境异常
```

编译通过本身不能证明会 Java。一个只会 `return 0;` 的方法也可能编译，但语义完全错误。因此，**结构、编译和行为必须分别记录。**

## 四、正控先于模型评估

六份参考实现必须经过同一插入、编译和断言链路，并要求 **6/6 通过**。

任何正控失败，先检查测试、方法签名或应用器，不把它算成模型问题。正控全部通过后，才允许运行原始模型。

## 五、结果怎么解释

第一层不因为一道题失败就宣布模型“完全不会 Java”，而是看是否出现系统性基础失败：

```text
add / maxOfTwo / sumArray 三个最基础题
全部无法生成可编译且断言正确的方法
→ 第一层不通过，暂停人工 D1 修复题
```

如果编译大多通过、但断言错误较多，只能说明模型具有一定 Java 形式表征，但基本逻辑语义薄弱。可以进入 D1，但必须把这个缺口明确写入能力画像。

因此，第一层的目标不是得到一个“会 / 不会”的粗暴标签，而是形成一张基础能力表：

| 能力类别 | 需要观察的结果 |
| --- | --- |
| 方法与签名结构 | 是否恰好一个目标方法，签名是否一致 |
| Java 语法与编译 | 是否能通过 javac |
| 基本运算与条件 | 是否正确处理比较、边界和返回值 |
| 数组与循环 | 是否正确遍历、求和和计数 |
| null 与常见 API | 是否按规格处理 null 和字符串 |
| 类型转换 | 是否避免整数除法等类型错误 |

## 六、后续四步路线

第一层完成后，再按相同原则逐层推进：

```text
J0：Java 语法与常识
J1：人工构造 20 道单行 D1 局部修复题
J2：真实 Defects4J 局部缺陷
J3：Defects4J D2 / D3 领域语义与更多上下文
```

有限轮次反馈和 Agent 属于系统能力对照，不与纯模型单轮能力混算。SPAN-L1 继续暂停，直到定位重新被证明是当前主要瓶颈。

## 七、J0 实测结果：有基本能力，但输出完整性很不稳定

六道参考实现先后在 WSL 和 Mac 上均通过同一 runner：

```text
reference controls: 6/6 passed
```

这证明任务 JSON、方法插入、javac 和独立断言链路可用。随后使用原始 Qwen3-0.6B、不加载 adapter、固定贪心 Pass@1 进行对照。

以下结果全部使用**修正后的候选评估器**。评估器先校验候选结构，再将候选本身插入独立 Java 类，执行 javac 和公开 / 私有断言。

| 对照 | 行为通过数 | 真实结果 |
| --- | ---: | --- |
| instruction v1 | 2/6 | add、maxOfTwo 通过，另外四题在方法签名后立即 EOS |
| fp32 对照 | 2/6 | 六题的 generated_ids、response、评估状态和 input hash 均与 bf16 完全一致 |
| 完整性 Prompt v2 | 1/6 | 只有 add 通过；J0-02 空方法编译失败，J0-04 断言失败 |
| assistant prefill | 1/6 | add 通过；J0-02 空方法编译失败，另外三题直接只生成 EOS |
| raw 代码续写 | 0/6 | 全部耗尽 256 tokens，主要是占位符、重复注释和重复任务描述 |
| 极简自然语言 | 0/6 | 全部耗尽 256 tokens，出现注意事项、超长数字和重复格式说明 |
| 继续删除输出约束 | 0/6 | 输出更加发散，开始补充 Calculator、测试类、问题描述与提示 |

初版曾出现“2/6 → 3/6”的表面变化，但复查发现当时 runner 在编译和断言阶段仍写入 `reference_method`，因此参考实现被错误地用于代替模型候选。修正为写入 `method` 并增加“错误候选必须失败”的回归测试后，真实结果是 **v1 为 2/6，v2 为 1/6**。初版结果不用于能力结论。

## 八、逐次实验变更记录

### E1：基础指令版

Prompt 的核心要求为：

```text
只输出一个完整 Java 方法，方法签名必须与输入一致。
不要输出类、测试、Markdown 或解释。

[方法签名]
{signature}

[任务规格]
{specification}

[公开示例]
{public_example}
```

结果为 **2/6**：

- J0-01：`return a + b;`，通过；
- J0-02：`return a > b ? a : b;`，通过；
- J0-03～J0-06：只生成方法签名和 `{`，随后立即 EOS，没有进入语义评估。

这组结果只能证明：模型在部分基本任务上有完整 Java 生成能力，不能证明其具备稳定的 Java 修复能力。

### E2：bf16 与 fp32 对照

其他变量保持不变，只将模型加载精度从 bf16 改为 fp32。

逐题核对结果为：

```text
generated_ids 完全相同：6/6
response 文本完全相同：6/6
评估状态完全相同：6/6
prompt_tokens 完全相同：6/6
input_ids_sha256 完全相同：6/6
```

因此，在当前 Mac MPS、该权重、这些 Prompt 和贪心设置下，**dtype 没有造成可观察的输出差异**。提前 EOS 和各题结果不能归因于 bf16。

这里只比较生成与评估结果，没有测量速度或显存，不据此推断两种精度的性能相同。

### E3：增加完整性要求

在 v1 的基础上，只新增：

```text
[完整性要求]
方法体必须非空，并以 } 结束。
不要在方法体完成之前结束生成。
```

结果为 **1/6**，不是初版误报的 3/6。

#### J0-02：正确方法变成空方法

v1 中的正确输出：

```java
public static int maxOfTwo(int a, int b) { return a > b ? a : b; }
```

v2 中的输出：

```java
public static int maxOfTwo(int a, int b) { }
```

编译器报“缺少返回语句”。这说明增加完整性文字后，模型反而改变了原本正确的生成路径。

#### J0-04：结构失败变为断言失败

v1 中只有：

```java
public static int countEven(int[] values) {
```

v2 中变成：

```java
public static int countEven(int[] values) { return values.length; }
```

它从“方法不完整”变为“可以编译”，这是结构上的进展。但 `values.length` 只是数组长度，不是偶数个数，公开和私有断言共失败 4 次，因此仍不能记为修复成功。

另外三道题仍然在 `{` 后立即 EOS。可见，**同一句完整性要求在不同题目上的作用不同，既可能帮助结构完成，也可能造成空方法或错误语义。**

### E4：assistant prefill

在 assistant 生成区末尾直接预置：

```python
prompt += task["signature"] + " {"
```

模型不再自行决定方法开头，而是续写方法体，评估时再拼回完整方法。

结果为 **1/6**：

- J0-01 续写 ` return a + b; }`，得到正确方法；
- J0-02 只续写 ` }`，得到空方法并编译失败；
- 另外三题只生成 `[151645]`，即一个 EOS，`completion_response` 为空。

这说明 prefill 可以让某些简单方法完成，但不是通用的完整性解决方案，甚至可能让原本已经生成的开头直接结束。

### E5：raw 纯文本代码续写

不使用 Chat 标记，改为：

```java
// Task
// {specification}
// Public example
// {public_example}
{signature} {
```

结果为 **0/6**，全部耗尽 256 tokens。

代表性输出包括：

- J0-01 不断重复 `// Task` 和 `{ ... }`；
- J0-03 不断重复 `// Solution` 与 `// Write your code here.`；
- J0-05 前半段有 `null` 判断和大写转换，后半段继续追加无关 Stream API 注释，仍不是合法单一方法。

raw 模式不是“少写提示就更自然”，它同样会出现占位、重复和任务漂移。

### E6：极简自然语言 Prompt

进一步去掉公开示例、完整签名代码块、Chat 角色描述和额外契约，只保留自然语言规格，例如：

```text
请使用 Java 实现一个名为 add 的静态方法，参数为 int a 和 int b，返回它们的和。
只输出方法本身，不要解释或示例。
```

结果为 **0/6**，全部耗尽 256 tokens。

值得注意的是，J0-01 中其实出现了正确的 `add` 实现，但它被包在 `Calculator` 和 `CalculatorTest` 中，还重复输出类，违反“只输出方法本身”的边界，不能被提取后算作成功。

其他输出还包括超长数字、重复“注意：不要使用任何空格/注释/换行符”和重复问题说明。极简 Prompt 并没有让任务更集中。

### E7：继续删除输出约束

继续删除：

```text
只输出方法本身，不要解释或示例。
```

结果仍为 **0/6**，而且输出更加发散：

- J0-01 开始要求创建 `Calculator` 和带 `main` 的测试类；
- J0-02 不断重复“问题描述 / 问题要求 / 问题提示”；
- J0-03 反复罗列“问题限制 / 问题示例 / 问题测试用例 / 问题说明”。

这说明**简洁不等于删得越少越好**。示例和冗余信息可以删，但“只输出目标方法、不要额外类和解释”这种评估边界不能轻易删除。

## 九、评估结果的可信度说明

本轮还暴露了一个评估器问题：早期版本在结构校验时读取模型候选，却在编译和断言阶段写死 `reference_method`，因此参考实现会被错误地用于代替模型输出。

后来已做两项修正：

```text
编译与断言阶段改为写入 method
增加错误候选必须返回 assertion_failed 的回归测试
```

参考正控恢复为 **6/6**，回归测试也确认错误候选不会再被参考实现“救活”。旧报告只作为历史问题记录，不用于能力结论。

这次修正也改变了实验解释：J0-04 不能再因为输出 `values.length` 而被记为通过。后续实验日志必须同时记录候选原文、结构校验、编译结果和真实断言结果。

## 十、当前能力边界与下一步

目前可以确认：

- 原始 0.6B 确实能完成部分基本 Java 方法；
- 但输出完整性、指令遵循和任务保持很不稳定；
- Prompt 对输出有实际影响，但效果按题目变化，不能认为增加约束必然提升整体成功率；
- bf16 与 fp32 的输出严格一致，当前不需要再把精度作为这些输出差异的解释；
- `passed` 只有在候选本身被插入、编译并执行后才具有意义。

因此，暂不直接进入真实 Defects4J 修复，也不继续无限调整 Prompt。下一步先构造 **J0-K 概念与代码阅读数据**：

```text
static / final / void / return / this / new
== / equals
int / double 与整数除法
array.length / String.length()
overload / override
```

概念题要求简短回答，必要时给出正确示例或反例，评分点提前写入参考答案，先由人核对，不让另一个模型代替裁判。

代码阅读题则要求模型判断：能否编译、输出什么、哪一行有问题、为什么。这样可以区分：

```text
不理解 Java 概念或 API
vs
知道一些概念，但无法稳定组织成完整代码
```

## 十一、概念理解实测：问题不只在代码生成

完成 6 道概念题后，按题目附带的 scoring_points 人工复核，结果如下：

| 题目                  | 模型表现                                                                          | 结论                    |
| ------------------- | ----------------------------------------------------------------------------- | --------------------- |
| static              | 知道 static 属于类，但错误声称 static 方法可以直接访问非 static 成员                                | 部分正确，但 static 上下文理解错误 |
| final               | 判断 `final int x = 1; x = 2;` 可以编译，并认为重新赋值合法                                   | 概念错误                  |
| 整数除法                | 认为 `1 / 2 = 0.5`，没有说明整数除法；改为 `1.0 / 2` 在 double 接收时可以得到 0.5                   | 原结果错误，修改思路部分可用        |
| `== / equals`       | 将 `new String("a") == new String("a")` 判为 true；`equals` 判为 true，但又说两者“进行相同操作” | 引用相等与内容相等混淆           |
| length              | 没有给出结果 3，并把数组的 `length` 称为方法                                                  | 字段与方法区分错误             |
| overload / override | overload 基本正确；override 错写成“同一个类中不同实现”，且回答被截断                                  | override 理解错误且回答不完整   |

这说明模型不仅无法稳定组织完整代码，**对 final、整数除法、引用相等、字段与方法、override 等基础概念也存在明显混淆**。

不过，add、maxOfTwo、String.equals 和 overload 的部分回答也说明，模型并非完全没有 Java 知识。更准确的状态是：知识点零散、表层化，无法稳定支撑精确执行。

## 十二、代码阅读实测：异常与边界也没有被识别

随后使用 3 道短代码阅读题，结果全部出现关键语义错误：

| 题目 | 正确行为 | 模型回答 |
| --- | --- | --- |
| static 方法访问实例字段 | 不能编译，static 方法不能直接访问非 static 的 `count` | 认为可以编译，并说 static 方法可以访问非 static 成员 |
| null 元素调用 `toUpperCase()` | 先输出 A，随后抛出 `NullPointerException`，不输出 C | 输出 `A, C, C`，并认为 null 的 `toUpperCase()` 返回 null |
| `i <= values.length` 遍历数组 | 输出 1、2、3 后，在 `i == 3` 时数组越界，应改为 `<` | 认为循环只执行 3 次并正常结束，没有识别越界 |

R01 对应编译器错误：

```text
non-static variable count cannot be referenced from a static context
```

R02 和 R03 则说明模型把本应由编译器或运行时发现的异常直接“想没了”。

因此，目前不适合直接进入真实 D1 修复。继续扩大验证题量，大概率只是重复这些错误，不能带来更多路线信息。

## 十三、后续设想：从“先教 Java”开始分层微调

基于当前结果，我倾向于停止继续摸底，把下一步改成一个小规模、可回归的分层教学实验：

> **通过 LoRA 等参数高效微调方式，先让 0.6B 掌握基础概念与代码行为，再逐步过渡到单行修复和完整函数生成。**

这不是已经证明有效的方案，而是一条需要通过实验验证的课程假设。

### 建议的课程顺序

```text
L0：概念问答
  static / final / this / null / == / equals / int / double / 数组边界

L1：代码行为判断
  能否编译、输出什么、哪里报错、异常类型是什么

L2：单行与表达式修复
  修正错误比较符、错误返回值、类型转换、null 处理、循环边界

L3：完整短函数生成
  从明确规格生成一个结构完整且通过断言的方法

L4：真实局部缺陷
  再进入 Defects4J D1 / D2 / D3
```

### 每一层都要有独立验收

```text
概念题：答案是否满足评分点
代码阅读：编译、输出和异常类型是否对应
单行修复：替换后是否通过指定断言
完整函数：结构、编译和行为是否同时通过
真实缺陷：编译与触发测试是否通过
```

不能只因为某一层 loss 下降，就直接进入下一层。也不能把旧层成绩丢掉，只在最后看一个总分。

### LoRA 的角色

LoRA 可以先沿用小 rank 和小批量高质量样本，验证它是否能让模型形成稳定的局部模式，而不必一开始就追求全参数训练。

但需要提前承认两个风险：

- 模型可能只记住题目和答案格式，而没有获得可迁移的 Java 语义；
- 后续阶段可能破坏前面已经学会的概念或输出契约。

因此，每一层都应设置：

```text
基础模型基线
→ 微调后同题回归
→ 未见模板或未见任务验收
→ 旧能力回归检查
```

如果训练后只是原题答对、换题型就失败，应记录为“记忆或格式拟合”，而不是“Java 能力形成”。如果基础概念都没有改善，再考虑数据质量、任务拆分或更换模型，而不是直接增加 rank、样本量或训练轮数。

这条路线真正想验证的是：**能否把 Java 教学拆成一条从概念、行为、单行修复到完整函数的可验证学习路径，而不是继续要求模型一次性学会真实缺陷修复。**

## 十四、L0 数据集与独立验证集冻结

为避免把验证题背下来，数据分为两套：

```text
训练集：data/instruct/i6_l0_concept_train_v1.json
独立验证集：data/instruct/i6_l0_concept_eval_v1.json
```

训练集由 DeepSeek 生成，共 100 条，四个主题各 25 条：

- `L0-STATIC-*`：static 与实例成员；
- `L0-FINAL-*`：final 变量、字段和引用；
- `L0-DIV-*`：整数除法与类型转换；
- `L0-EQ-*`：`==`、`equals` 和 null。

验收时发现 `L0-EQ-011` 与验证集 `L0-TRAIN-10` 高度近似，已替换为编译期常量折叠的新场景。最终检查：

```text
100 条 train
主题分布：25 / 25 / 25 / 25
无完全重复 ID、问题或答案
无训练集内部相似度 >= 0.80 的重复对
无与验证集相似度 >= 0.75 的重复对
```

独立验证集共 20 条，明确全部改为 `eval_holdout`，不进入 LoRA 训练。人工基线核验结果为：

```text
完整正确：0 条
基本正确但不完整：1 条（L0-VAL-04）
部分正确：8 条
关键错误：11 条
```

## 十五、SFT 转换与 LoRA 配置

训练前完成消息转换与隔离：

```text
data/instruct/i6_l0_concept_sft_train.json：92 条
data/instruct/i6_l0_concept_sft_val.json：8 条
data/instruct/i6_l0_concept_sft_holdout.json：20 条
```

所有样本都包含 `system / user / assistant` 三段消息，120 个 ID 在三个角色之间唯一。token 验收结果：

```text
train max_full_tokens = 226
validation max_full_tokens = 178
holdout max_full_tokens = 291
全部 <= 4096
```

训练配置固定为：

```text
模型：Qwen3-0.6B
方法：LoRA + SFT
rank：8
alpha：16
learning rate：1e-5
batch size：1
context：4096
trainable parameters：6,269,952
adapter：约 25.2 MB
运行环境：Windows + Ubuntu WSL + CUDA
```

训练集和 validation 用于训练与选模，eval_holdout 只用于最终验收，不用于调参。

## 十六、4 epochs 与 8 epochs 的真实结果

### 4 epochs：出现局部概念改善

训练记录：

```text
optimization steps：368
initial train loss：3.205156
initial validation loss：3.031298
final train loss：1.964655
final full validation loss：2.127206
best probe loss：2.333778（step 365）
best adapter reload：passed
```

按 scoring_points 人工比较，4 epochs 的明确变化包括：

- `TRAIN-04`：从“结果正确但初始化解释错误”变为基本正确；
- `TRAIN-06`：从引用概念不完整变为能正确说明 final 锁住的是引用，但未补充 `append()` 合法；
- `TRAIN-10`：从 `==` 与 `equals` 结果完全答反，变为 `false`、`true` 结果与解释基本正确；
- `HOLDOUT-03`：从错误输出 25 变为正确输出 0，但运算顺序解释仍错误；
- `VAL-04`：结果仍正确，且提到了重写后的比较逻辑，但对象关系解释仍有混淆。

这说明 **LoRA 确实有局部概念塑形能力，但不能据此说已经学会 Java**。

### 8 epochs：结果更混合，不能称为整体提升

训练记录：

```text
optimization steps：736
initial train loss：3.205156
initial validation loss：3.031298
final train loss：1.721135
final full validation loss：2.026600
best probe loss：2.142791（step 133）
best adapter reload：passed
```

8 epochs 的变化不是简单进步：

- `TRAIN-04`：从基本正确回落为“方法体外未初始化”的错误解释；
- `TRAIN-06`：从正确理解 final 引用，回落为错误声称 `sb.append("B")` 编译失败；
- `VAL-02`：从能判断编译错误，变为错判“能编译”，忽略 capacity 未初始化就读取；
- `VAL-04`：从 `false`、`true` 正确结果，回落为 `true`、`false`；
- `TRAIN-07`：从错误改法变为 `23 / 5.0`，能够得到 4.6；
- `TRAIN-09`：从一种正确改法变为两种正确改法，但仍未解释原式为何是 10.0；
- `TRAIN-10`：基本正确的结果与解释得以保持；
- `HOLDOUT-03`：输出仍为正确的 0，但改法仍得不到预期的整数 37。

其余大量错误仍未解决，包括 static 访问、final 初始化、`Object.equals` 默认引用比较、数组边界和 null 上调用实例方法。

### 当前判断

```text
4 epochs：少量明确改善，但整体仍很不稳定
8 epochs：部分改善与明显回落并存，没有超过 4 epochs 的整体表现
```

因此，**不再继续增加 epochs 到 16 或 32**。4 → 8 已经证明“多训练”不能自动解决问题，且存在记忆与泛化不稳定。

## 十七、下一步：只针对 static 增训，不直接背验证题

下一步不再加训练轮数，而是先针对 static 这一高频错误类型补充数据：

```text
原训练集：92 train
新增数据：30 条 static，ID 为 L0-STATIC-101 ～ L0-STATIC-130
训练集合计：122 条
```

新增样本只覆盖：

- static 方法没有 this，不能直接访问实例字段或实例方法；
- 通过显式对象引用访问实例成员是合法的；
- static 字段被所有实例共享，实例字段各对象独立；
- static 方法可以访问 static 字段、调用 static 方法；
- 实例方法可以通过 this 访问实例字段，也可以访问 static 成员。

题型包括概念判断、编译判断、输出预测、错误诊断和修改建议。禁止复用验证集中的 Session、Inventory、Window、Ticket、OrderService、Counter 等场景，也禁止复制验证题的问题、代码或参考答案。

训练时保持以下配置不变：

```text
epochs = 4
rank = 8
alpha = 16
learning rate = 1e-5
batch size = 1
context = 4096
```

新增数据后样本数与 steps 都会变化，必须一并记录，不能把变化简单归因于数据量。验收仍使用原来的独立 20 题，重点检查 static 的直接访问、显式对象引用、字段共享和方法调用是否真正改善。

当前技术状态也已确认：LoRA adapter 可以保存并严格重载；生成时基座与 adapter 的设备和 dtype 必须对齐，否则会出现 `mat1/mat2` 设备或 dtype 不一致错误。

## 十八、static-v2 实测：增训没有直接带来泛化

static-v2 使用 92 条原始训练样本和 30 条 static 补充样本，共 122 条。训练配置保持为 4 epochs、rank 8、alpha 16、learning rate 1e-5、batch size 1、context 4096。

真实训练记录：

```text
optimization steps：488
initial train loss：3.210011
initial validation loss：3.031298
final train loss：1.880346
final full validation loss：2.064561
best probe loss：2.181638（step 485）
trainable parameters：6,269,952
adapter reload：passed
```

best 与 final 都进行了独立 20 题评估。初版评估采用 legacy Prompt + BF16，结果不支持“增加 30 条 static 样本就能解决问题”：

- static 方法直接访问实例字段的错误仍然存在；
- 通过显式对象引用访问实例成员仍被误判；
- 模型能说出 static 字段“共享”，却仍然算错共享计数；
- final、整数除法、`== / equals` 等主题也存在回落或重复生成。

final 相比 best 只在少数题目上局部恢复，没有整体改善。值得注意的是，best step 为 485，总步数为 488，两者本来只差 3 个优化步骤，因此不能期待它们出现巨大差异。

当时的 best 实现只使用 `eval_iter=1`，即单个 validation batch 的 probe loss；final full validation loss 则使用全部 8 条 validation。两者的统计口径不同，不能直接比较数值，更不能把 best step 当成全体验证集上的最佳模型。

这轮实验后的决定是：暂停继续增加 static 数据和训练轮数，先检查评估契约、训练链路和任务设计。

## 十九、先修正评估契约：Prompt 与精度

### Prompt 不一致

回查脚本后发现，训练和生成评估的 Prompt 并不完全一致。

训练时的消息结构：

```text
system = 你是一名严谨的 Java 教师……
user   = 原始问题
```

旧评估则把教师要求和 `[问题]` 包装一起放进了 user：

```text
user = 教师要求 + [问题] + 原始问题
```

差异不仅是措辞，还包括 system / user 的角色分配。对于小模型、小训练集和 LoRA，这种分布差异可能影响生成，因此不能继续把它排除在实验变量之外。

随后给 `scripts/i6_java_concepts_generate.py` 增加了 `--sft-prompt`，同时保留 legacy 模式用于历史对照。Mac 上对全部 122 条训练样本进行了 token 前缀检查：

```text
syntax check: passed
training/eval prompt prefix: passed
samples: 122
```

这项检查直接比较 token ID，而不是只比较字符串，证明 SFT 评估 Prompt 与训练输入的前缀逐 token 一致。Prompt 对齐与 GPU 无关，但 WSL 上仍通过真实生成报告核验了 `prompt_mode`。

### 训练 FP32，旧生成却是 BF16

继续检查后又发现第二个不一致：

```text
训练：load_qwen3_dir 未传 dtype，使用 PyTorch 默认 FP32
旧生成：显式 dtype=torch.bfloat16
```

WSL 运行时核验结果：

```text
training path model dtype: torch.float32
saved adapter dtypes: ['torch.float32']
```

因此不需要为了统一精度重新训练。保留已有 adapter，给生成脚本增加 `--dtype bfloat16|float32`，即可使用 FP32 完成同精度对照；默认 BF16 则保留旧实验的可复现性。

FP32 确实改变了部分输出。例如 `STATIC-104` 的解释更完整，`STATIC-105` 的结论有所改善，`STATIC-113` 却出现了新的矛盾解释，其他多道题的核心答案几乎不变。

这说明模型对数值精度敏感，但不等于 BF16 是训练失败的主因。greedy decoding 也可能放大微小数值差异：当两个 token 的概率接近时，精度变化可能交换它们的顺序；一个 token 改变后，后续生成就会进入不同路径。

## 二十、训练原题回测：loss 下降不等于已经学会

为了区分“没见过所以不会”和“见过也没学会”，从实际训练文件中抽取 8 条 static 原题：

```text
L0-STATIC-101 / 102 / 104 / 105
L0-STATIC-109 / 113 / 114 / 127
```

同一个 static-v2 final adapter，分别使用 SFT Prompt 与 legacy Prompt 回测。两种 Prompt 会影响重复、措辞和局部完整性，但核心概念错误高度一致：

- `STATIC-102` 仍把合法的 `w.balance` 当成 static 方法不能访问的实例成员；
- `STATIC-105` 对实例方法与 static 字段混用仍然混乱；
- `STATIC-113` 能猜对 `2 2`，却给出“每个实例各加 1”的错误解释；
- `STATIC-114` 仍把共享计数算成 `1 1`；
- `STATIC-127` 的两种修复方案都不符合要求。

这说明 Prompt 不是主要矛盾，而且不能把所有失败都归因于独立题上的泛化不足——模型连训练原题都没有稳定掌握。

随后使用与训练一致的 FP32，对这 8 条样本进行 teacher-forced loss 对照。这里不自由生成，而是把标准答案交给模型，只计算 supervised assistant tokens 的交叉熵：

| 样本 | base loss | adapter loss | delta |
| --- | ---: | ---: | ---: |
| STATIC-101 | 3.258299 | 1.758984 | -1.499315 |
| STATIC-102 | 3.471673 | 2.063512 | -1.408161 |
| STATIC-104 | 3.200651 | 1.752747 | -1.447904 |
| STATIC-105 | 3.071568 | 1.551094 | -1.520474 |
| STATIC-109 | 2.291152 | 1.106854 | -1.184298 |
| STATIC-113 | 3.954923 | 2.247594 | -1.707328 |
| STATIC-114 | 2.664165 | 1.268620 | -1.395544 |
| STATIC-127 | 3.279952 | 2.089588 | -1.190365 |
| **平均** | **3.149048** | **1.729874** | **-1.419174** |

8 条样本的损失全部下降，平均相对下降约 45%。这证明 adapter 确实对训练答案产生了明显作用，不能说训练完全无效或 adapter 没有加载成功。

但自由生成仍然大量答错，因此也必须承认：**token 概率向参考答案靠近，不等于已经能够稳定执行对应规则。loss 是训练信号，不是概念正确率。**

## 二十一、数据审计与对齐后的独立 20 题

对实际进入训练的 122 条样本进行第一轮人工静态审查后，没有发现明确的 static 参考答案事实错误，但发现了数据与验收契约中的其他问题：

- `L0-DIV-003` 的参考答案是 4.0，scoring_points 却写成 2.0；
- `L0-DIV-010` 的 notes 残留了另一道题的 19 / 2 和 9.5；
- `L0-EQ-023` 的 scoring_points 要求 `@Override`，参考答案代码却没有写；
- 部分 equals 训练样本没有要求同步重写 hashCode，而独立验证题包含这一要求。

SFT 训练只把 question 和 reference_answer 放入 messages，scoring_points 与 notes 不参与 loss，所以前两类元数据错误不能解释 static 训练失败。equals / hashCode 则属于后续需要统一的课程与验收契约，不能与 static 结论混为一谈。

接着使用 static-v2 final adapter，以 **SFT Prompt + FP32** 重新生成完整独立 20 题：

```text
报告：data/reports/i6-l0-static-v2-final-sft-fp32
prompt_mode：sft
dtype：torch.float32
adapter：i6-l0-static-v2-lora.pth
```

对齐后出现了局部改善：

- `HOLDOUT-02` 从错误的“不能编译”变为正确的“能编译”，但构造器委托解释仍不够准确；
- `HOLDOUT-03` 从错误的 200 和重复乱码变为正确的输出 0，但整数除法解释仍错；
- `TRAIN-07` 的结果和修改方式基本正确；
- `TRAIN-04` 等题目则出现重复或回落，并非所有输出都因 FP32 而改善。

static 核心目标仍未实现：

- `TRAIN-03` 仍然一边声称 static 字段共享，一边输出 `0 0 0`；
- `VAL-01` 仍否定合法的 `s.region`；
- `HOLDOUT-01` 的共享计数和 static 方法编译判断仍错；
- `TRAIN-01` 没有区分合法的 `online = 0` 与非法的 `user = null`；
- `TRAIN-02` 仍未解释隐式 this、static 访问和能否编译。

因此，**static-v2 final 在对齐后的标准条件下仍未通过 L0 验收**。局部题目改善不能证明已经形成可迁移的 static 规则能力。若以后要精确排列 base、4 epochs、8 epochs 和 static-v2，应全部使用同一 Prompt 与精度重跑；当前不能把不同条件下的逐题排名当作严格结论。

## 二十二、8 样本故意过拟合：训练链路的环境验证

为了不再凭猜测讨论“模型不行”还是“训练不对”，增加了一个最小记忆实验：只取已经参与训练的 8 条 static 样本，故意加强优化，看模型到底能不能记住。

实验配置：

```text
训练样本：8 条 static 原题
epochs：64
optimization steps：512
learning rate：1e-4
rank / alpha：8 / 16
batch size：1
context：4096
训练精度：FP32
train / val：同一批 8 条，仅用于观察记忆，不表示泛化
不生成 best adapter，只检查 final
```

训练结果：

```text
initial train loss：3.149048
final train loss：0.000205
final val loss：0.000205
optimization steps：512
adapter reload：passed
adapter：data/model_pth/qwen3/i6-l0-static-overfit8-fp32-lora.pth
```

初始损失与此前 8 条样本的 base 均值完全一致，说明子集和计算口径吻合。随后使用新 adapter，以 SFT Prompt + FP32 回测相同 8 题，结果是：

```text
8 / 8 与 reference_answer 逐字一致
```

包括结论、解释、数字、代码和标点都能正确复述。这个结果只证明记忆，不证明泛化，因此没有必要拿这个故意过拟合的 adapter 去刷独立 20 题。

但它非常有价值，因为它验证了以下闭环：

```text
SFT 数据
→ LoRA 优化
→ adapter 保存
→ 严格加载
→ SFT Prompt
→ FP32 增量生成
→ 训练答案复述
```

之前那些“训练完全无效”“adapter 没有学上”“生成链路无法实现训练结果”“0.6B 完全学不会”的假设，都不能再用来解释当前现象。至少在这 8 条样本上，模型和工程链路具备明确的学习与复现能力。

**背下来在能力评估里不是成功，在链路验收里却是必要证据。**

## 二十三、像验证 Java 环境一样，先验证模型实验环境

这段排查让我联想到以前排查 Java 问题时的环境验证。

面对一个复杂故障，最容易做的是直接怀疑业务代码、框架原理或某种高深 bug。但更可靠的顺序往往是先确认基础环境：源码版本是否一致、依赖是否正确、配置是否生效、连的是不是同一个数据库、服务是否能够连通。环境没有验证清楚，上层的推理越复杂，越可能只是建立在错误前提上的解释。

模型训练也是同样的道理。看到答错就怀疑模型能力，看到 loss 下降就宣布能力提升，都跳过了中间大量本应验证的基础条件。

这次实验中的对应关系可以整理为：

| Java 问题排查 | 模型训练与评估 |
| --- | --- |
| 源码、依赖和配置版本是否一致 | 数据、tokenizer、基座、adapter 和评估任务是否一致 |
| 配置是否真正生效 | system / user 角色和 Prompt 是否真正按训练格式进入模型 |
| JVM、操作系统和运行参数是否明确 | FP32 / BF16、CPU / CUDA 和 decoding 参数是否明确 |
| 接口调用是否真的到达服务 | 训练输入的 token 前缀是否与评估输入逐 token 对齐 |
| 服务部署产物是否正确 | adapter 是否能保存并被 strict reload |
| 最小连通性或冒烟用例 | 8 条样本能否过拟合并在自由生成中复述 |
| 业务场景验收 | 冻结独立题上的泛化验收 |

由此形成了一条更可靠的排查顺序：

```text
1. 数据和参考答案是否可信，角色是否隔离
2. 训练与评估的输入契约是否一致
3. 训练、保存、加载和生成的设备与精度是否明确
4. 优化是否真的让目标 loss 下降
5. 训练产物是否能够恢复
6. 最小样本集能否被记住并通过自由生成复述
7. 最后才讨论泛化、课程设计和模型能力
```

低一层没有验证，就不急着在更高一层增加变量。Prompt 没有对齐时，不急着解释能力；精度没有核清时，不急着比较答案；训练原题都没有学会时，不急着讨论泛化；最小记忆闭环没有跑通时，也不急着设计更复杂的训练路线。

这并不意味着 LLM 不再是黑盒，而是说：**模型内部可以是黑盒，模型外部的数据、输入、数值、优化、产物和评估仍然可以逐层建立确定性。不能因为最里面有一层看不透，就把整个实验都当成玄学。**

这段经历真正珍贵的地方，不是已经得到了一个可用的 Java 模型——这个目标尚未完成——而是终于把“为什么又答错了”拆成了一条可以复核的证据链。以后无论成功还是失败，都能说清楚失败发生在哪一层，下一次应该改变哪个变量，而不是只能凭感觉再试一次。

### 三条进一步沉淀的认知

> **大模型是黑盒，但围绕它的工程管线必须是白盒。**

这里的“白盒”不是要求解释模型内部的每个参数，而是要求每次实验都能回答：用了哪份数据、哪套 Prompt、哪些 token、什么精度、什么优化器和学习率、哪个 adapter，以及最终由哪份报告支持结论。上述问题回答不清楚，实验结果就只能称为观察，还不能称为归因。

当模型表现不及预期时，不应该第一时间把所有问题都归咎于模型本身，而应先通过极端对照，检查数据、mask、loss、优化器、精度、adapter 保存加载和生成解码是否能够形成闭环。

> **8 条数据的强行过拟合，是排查整条训练链路是否失效的终极冒烟测试。**

这里的“终极”是工程比喻：用一个足够小、足够极端的任务，快速判断整条链路还有没有基本的学习能力。它的价值不是证明模型会泛化，而是让基础设施问题尽早暴露。

如果输入没有冲突、训练与生成契约已经对齐，并且已经给予充分优化，模型仍然无法显著拟合一小批样本，就应该优先检查训练管线和优化配置，而不是立刻归因于模型容量。反过来说，**过拟合失败不必然等价于代码 Bug，过拟合成功也不等于能力形成。**学习率、训练步数、优化器、正则化和冲突目标都可能影响拟合结果，loss 也不必精确等于 0；本次 final loss 为 0.000205，已经足以支持 8/8 逐字复述。

这次冒烟测试排除的是一批具体错误假设，而不是一个可以严谨量化的“99%”。它真正带来的收益，是让后续排查不再把大量时间浪费在已经验证过的方向上。

> **排查 AI 模型错误，和排查生产环境 JVM 崩溃一样，需要剥洋葱式的变量隔离。**

这次的实际路径，从怀疑数据污染，走到 Prompt 契约、dtype、训练原题回忆和优化强度。每一层都可能改变输出，但每一层也都有自己的验证方法。一次只切掉一个变量，看似更慢，实际上是在避免用新的混乱解释旧的混乱。

overfit8 同时改变了样本数、训练轮数和学习率，只能证明强优化条件下可以记住 8 条，不能证明全量数据只需要提高学习率。随后完成的 122 条单变量对照进一步表明：提高学习率虽然降低了 train / validation loss，却没有改善自由生成，反而造成明显退化。因此，“学习率过小”不能被写成当前问题的 Root Cause，“提高学习率就能学会 Java”也已经被真实结果否证。

真正的 Root Cause 必须能够被对照实验支持，而不能只是目前听起来最合理的解释。一次只切掉一个变量，看似更慢，实际上是在避免用新的混乱解释旧的混乱。

## 二十四、122 条、只提高学习率：loss 与行为分道扬镳

在 overfit8 验证训练与生成闭环后，回到 122 条数据进行全量对照。实验只改变学习率：

```text
数据：122 条，保持不变
epochs：4，保持不变
optimization steps：488，保持不变
learning rate：1e-5 → 1e-4
rank / alpha / batch size / context：保持不变
训练与生成：FP32
评估 Prompt：SFT
不生成 best adapter，只检查 final
```

初始 train / validation loss 与旧实验完全一致，说明数据与起点口径吻合。最终结果：

| 指标 | 旧 lr=1e-5 | 新 lr=1e-4 | 变化 |
| --- | ---: | ---: | ---: |
| final train loss | 1.880346 | 1.150991 | -0.729355 |
| final full validation loss | 2.064561 | 1.843811 | -0.220750 |
| optimization steps | 488 | 488 | 不变 |

如果只看 loss，很容易得出“提高学习率有效”的结论。但使用同一个新 adapter，以 SFT Prompt + FP32 回测训练原题和独立 20 题后，行为反而明显退化。

训练原题中的代表性回落：

- `STATIC-104` 把两个 static 方法的合法调用误判为实例方法调用；
- `STATIC-109` 从“不能编译”倒退为“能编译”；
- `STATIC-113` 从能猜对 `2 2` 倒退为 `1 1`；
- `STATIC-102、114、127` 的核心错误仍然存在。

独立题中的代表性回落：

- `HOLDOUT-02` 从“能编译”倒退为“不能编译”；
- `HOLDOUT-03` 从正确的输出 0 倒退为 80；
- `TRAIN-04` 从正确的 final 判断倒退为“能编译”；
- `TRAIN-10` 把本应为 true 的 equals 答成 false。

因此，`1e-4` adapter 不再作为候选，也不继续尝试 `1e-3` 或叠加更多 epochs。这轮实验最重要的收获不是找到了更好的参数，而是得到了一个真实反例：

> **train loss 和 validation loss 同时下降，训练原题回忆与独立题行为仍然可能一起变差。**

validation 的 8 条来自同一批生成数据，与独立 20 题并不等价。validation loss 可以描述优化过程，但不能代替目标行为验收。

```text
adapter：data/model_pth/qwen3/i6-l0-static-v2-lr1e4-fp32-lora.pth
训练报告：data/reports/i6-l0-static-v2-lr1e4-fp32-training.json
训练原题报告：data/reports/i6-l0-static-v2-lr1e4-train-recall-sft-fp32
独立题报告：data/reports/i6-l0-static-v2-lr1e4-eval-sft-fp32
```

## 二十五、逐样本 loss 与 KV cache：封闭最后的工程疑问

### 不是所有样本都被平均数掩盖

为了解释“loss 下降、行为变差”，先检查高学习率是否牺牲了这 8 条训练样本。使用与之前完全相同的 FP32 teacher-forced 计算，对比 base、旧 adapter 和新 adapter：

| 样本 | base | 旧 adapter | 新 adapter | new-old |
| --- | ---: | ---: | ---: | ---: |
| STATIC-101 | 3.258299 | 1.758984 | 0.970089 | -0.788895 |
| STATIC-102 | 3.471673 | 2.063512 | 1.020972 | -1.042540 |
| STATIC-104 | 3.200651 | 1.752747 | 0.947832 | -0.804915 |
| STATIC-105 | 3.071568 | 1.551094 | 0.567471 | -0.983623 |
| STATIC-109 | 2.291152 | 1.106854 | 0.472344 | -0.634510 |
| STATIC-113 | 3.954923 | 2.247594 | 1.147015 | -1.100579 |
| STATIC-114 | 2.664165 | 1.268620 | 0.695702 | -0.572918 |
| STATIC-127 | 3.279952 | 2.089588 | 0.993642 | -1.095945 |
| **平均** | **3.149048** | **1.729874** | **0.851884** | **-0.877991** |

8 条样本的 loss 全部进一步下降，没有一条例外。这排除了“全量平均 loss 下降，但这 8 条被单独牺牲”的解释。

真正需要面对的是：**参考答案在 teacher-forced 条件下更容易出现，不等于模型能够在自由生成时自主给出正确答案。**

计算 loss 时，每一步都会把正确前缀提供给模型。自由生成时，模型却必须消费自己刚生成的前缀。它一旦先把“不能”写成“能”，后续就可能沿着错误结论继续解释。长答案中的大量通用措辞还会摊薄“能/不能”、`1 1/2 2`、`true/false` 等关键结论 token 的影响。

### KV cache 对照

训练使用全序列前向，生成默认使用增量 KV cache。虽然 overfit8 已经证明整条链路可以复述训练答案，但接近零的 loss 可能掩盖细微差异，因此又增加了一个不训练的对照：

```text
同一个 lr=1e-4 adapter
同一个 SFT Prompt
同一个 FP32
同一个 greedy decoding
唯一变化：KV cache vs no-cache 全序列生成
```

结果为：**8 道题的回答全部逐字一致**。在当前配置下，KV cache 不是造成这次行为退化的原因，也不需要继续比较首个分叉 token。

```text
KV cache 报告：data/reports/i6-l0-static-v2-lr1e4-train-recall-sft-fp32
no-cache 报告：data/reports/i6-l0-static-v2-lr1e4-train-recall-sft-fp32-no-cache
```

至此，Prompt、精度、adapter 保存加载、最小记忆闭环、全序列与增量生成都已得到实际验证。继续把问题归咎于底层管线完全失效，已经不符合现有证据。

## 二十六、从长解释到成对规则：重新缩小问题

长解释实验之后，红队审查指出了两个会直接影响下一步判断的问题。

第一，短答案不能简单截取长答案首句。`L0-HOLDOUT-01` 的类包含非法的 `current()`，整个类无法编译，却又同时询问 main 输出；参考答案中的 `1 2 3` 需要先移除或修正非法方法才能实测。`L0-VAL-01` 的长答案以“不能这样理解”开头，但代码本身能够编译。如果短答案问代码行为，标签就必须由 javac 或实际运行决定，而不是从解释文字中猜测。

第二，原来的独立 20 题虽然全部标记为 `eval_holdout`，但已经反复用于结果分析、static 增训、Prompt 与精度调整以及新任务设计。题号里的 TRAIN / VAL 不代表训练泄漏，但这 20 题已经更适合作为 development regression，而不能再冒充从未参与设计决策的最终验收集。

因此，最后一轮不再追求“先学完整套 Java”，而把目标收缩为：

> **只验证一条 static 规则，并检查它能否迁移到未见判断和一个单行修复。**

这条规则是：static 方法不能直接访问实例字段，但可以通过显式对象引用访问。

## 二十七、成对规则决策实验：单题 50%，整对却是 0%

首先构造 4 对开发题。每对的类、方法签名和其他代码保持一致，只改变访问表达式，例如：

```java
return minutes;
```

与：

```java
return m.minutes;
```

这样隔离的正是“直接访问”与“通过显式对象引用访问”。所有标签由 javac 11.0.33.1 验证，非法版本必须编译失败，合法版本必须编译通过，结果为 8/8 通过。

随后让原始 0.6B 与旧 static-v2 `1e-5` adapter 同时进行两种评估：

- 自由生成短答案，只输出 `合法` 或 `非法`；
- 给同一 Prompt 分别接上两个候选答案，比较 `label + EOS` 的平均 logprob。

结果：

```text
base：8 个代码片段全部回答“合法”
旧 adapter：第一对的两个版本都回答“非法”，其余三对的两个版本都回答“合法”
base generation / score pair accuracy：0/4
旧 adapter generation / score pair accuracy：0/4
两个模型的 same_answer_pairs：均为 4/4
```

两个模型按单题计算都恰好是 4/8，看似有 50% 准确率；按整对计算却都是 0%。这证明成对验收的必要性：如果正反两个版本总是得到同一个答案，单题猜中不能算作掌握规则。

自由生成与候选评分结果一致，也说明问题不只是短答案输出协议，模型确实没有利用字段访问形式的变化来区分代码行为。

```text
开发数据：data/instruct/i6_static_access_dev_pairs_v1.json
javac 报告：data/reports/i6-static-access-dev-javac.json
决策报告：data/reports/i6-static-access-dev-decision.json
```

在训练之前，又冻结了 4 对全新最终题和一个 `Thermostat` 单行修复题。最终集只执行 javac 验签，不运行任何模型：

```text
4 对最终题：8/8 标签通过
修复 buggy 版本：按预期编译失败
修复 fixed 版本：编译通过
合计：10/10
model evaluation：not_run
```

## 二十八、短标签 SFT：最终成对题与微型修复均未通过

短标签训练只使用当前 4 对开发题，转换为 8 条样本，非法与合法各 4 条。训练与短答案评估的 token 前缀逐条对齐，最终 holdout 未参与训练或选模。

实际执行配置：

```text
起点：原始 Qwen3-0.6B，不叠加旧长答案 adapter
训练样本：8 条短标签
epochs：16
optimization steps：128
learning rate：1e-4
rank / alpha：8 / 16
batch size：1
训练与生成：FP32
不生成 best adapter
```

训练前曾讨论把学习率改为 `3e-5`，但实际命令仍执行为 `1e-4`，因此笔记和报告必须按真实运行值记录，不能写成 `3e-5`。

训练结果：

```text
initial train loss：0.933424
final train loss：0.989837
adapter reload：passed
```

最终平均 train loss 没有下降，而且日志中一部分样本接近 0，另一部分长期在 1.8 左右。train / val 使用同一批 8 条，只用于观察训练记忆，不代表泛化。

使用新 adapter 一次性评估冻结的 4 对最终题：

```text
8 个未见代码片段全部回答“合法”
generation_correct_pairs：0/4
score_correct_pairs：0/4
generation_same_answer_pairs：4/4
score_same_answer_pairs：4/4
```

短标签 SFT 没有让模型在未见代码上学会这条规则，候选评分同样没有区分能力。

最后进行 `Thermostat` 单行修复验收。模型需要输出一个 replace JSON，修复后还要通过 javac 和运行断言，确认 `Thermostat.read(t)` 返回传入对象的 `degrees`。

模型实际输出只有：

```text
int degrees;
```

因此：

```text
evaluation_status：invalid_edit
repair_passed：False
validation_error：Expecting value: line 1 column 1 (char 0)
compile_returncode：None
test_returncode：None
```

这里没有产出可应用的补丁，不能写成“补丁编译失败”，准确结论是：**模型没有生成符合契约、可供编译评估的修复。**

```text
短标签训练报告：data/reports/i6-static-access-short-sft-fp32-training.json
最终成对题报告：data/reports/i6-static-access-short-sft-final-decision.json
微型修复报告：data/reports/i6-static-access-short-sft-repair-final.json
```

至此，预先约定的停止条件已经满足：短标签训练既没有迁移到最终成对题，也没有完成同规则微型修复。不再继续增加 epochs、学习率、rank、数据量或新的 Java 主题。

## 二十九、0.6B 收官：停止路线，而不是宣布模型终审

当前可以下的结论是：

> **在当前数据规模、训练目标、LoRA 配置和实验预算内，我们没有教会 0.6B 形成可迁移的 Java 规则能力。继续沿现有路线加码，缺少证据支持。**

这不等于证明“0.6B 永远学不会 Java”，也不等于已经完成了 0.6B 基座能力的全面评估。我们真正探明的是：

- 它能够在强优化下记住 8 条长答案，并逐字复述；
- 它在当前长答案训练路线中没有形成稳定的自主概念判断；
- 它在新的 static 成对规则上，原始基座、旧 adapter 和本次短标签 adapter 都没有通过最终验收；
- 它本次没有产出符合契约的单行修复。

这些结果足以支持停止当前路线，但不足以把失败全部归因于模型容量。数据覆盖、课程设计、训练方法和其他优化策略仍然可能存在不同答案，只是继续探索它们已经不符合当前项目的收口目标。

升级到 4B 可以成为一个新的工程选择，但仍需使用相同成对题、Prompt、候选评分、javac 和微型修复做对照，不能预先把 0.6B 的失败解释为参数量不足。如果 4B 基座同样失败，模型大小就不是充分解释；如果 4B 能通过，则说明它在这组任务上的基座表现更强，但仍应与 0.6B 的训练结果分开记录。

这次收官的价值，不是得到了“0.6B 不行”这样一句宽泛结论，而是把停止决策建立在一条完整证据链上：**先验证管线，再验证记忆，再验证迁移，最后验证修复；哪一层没有通过，就停在哪一层，不用更多训练掩盖它。**

**先把工程管线变成白盒，再把训练目标变成可测量的行为。先确保基础是好的，再讨论上层；先让每一步都有证据，再让结论往前走。**
