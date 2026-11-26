+++
title = "手搓 LLM 笔记 30：I6-3 先验证模型会不会 Java"
date = 2026-11-26
draft = true
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

**I6 仍未完成，但这一次先验证最基础的能力假设。**
