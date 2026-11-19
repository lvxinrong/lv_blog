+++
title = "Qwen 源码图谱"
description = "Qwen 家族按模块源码阅读地图；当前规划中，尚未开始逐模块阅读"
columnKind = "column"
+++

**当前状态：规划中阅读地图。** 尚未开始逐模块源码阅读，尚未形成 Qwen 完整架构结论；不宣称已下载、已读或已实现 Qwen 全部模型。

## 系列定位

- 以已有学习锚点为起点，按模块读懂 Qwen 的现代架构、权重映射与模板演进。
- 不以覆盖 Qwen 全部型号为目标。
- 不预设所有训练、推理和部署源码都已公开。

## 公共阅读骨架

按实际源码情况选择以下模块，不要求全读：

- config、Tokenizer、Chat Template；
- Embedding 与位置编码；
- Attention、QKV、Head、KV Cache；
- Norm 与残差结构；
- Dense FFN 或 MoE；
- 顶层 forward 与权重加载；
- Generation、Decode 与 Cache 状态；
- 量化、稀疏、压缩、MTP 等特有机制；
- 推理部署与 Kernel 接口。

## 证据要求

每篇正式专题未来至少保留：

- 官方模型卡、官方仓库与固定 tag / commit；
- config 字段 → 源码类 / 初始化参数 → 权重 key 的对应关系；
- forward 和 cache decode 的关键张量流；
- 已确认事实、结构推断、官方明确设计意图和待核实项的区分；
- 条件允许时，一个最小实现、最小探针或受控官方对照。

不用“官方 config 写了”直接推出训练资源、质量或性能结论。

## 阅读提示（方向，非已核实结论）

- 现有学习锚点为 Qwen2.5-0.5B / Instruct 与 Qwen3-0.6B Dense（见手搓 LLM 主线 I0 与 I3 番外）。
- 后续可从 config、weight map、forward、QK RMSNorm、GQA、RoPE、thinking 与模板演进开始。
- 不预设 Qwen 全系列结构相同，也不预设尚未核实的未来型号信息。

## 当前状态

- 当前为规划中阅读地图；
- 尚未开始逐模块源码阅读；
- 尚未形成该家族的完整架构结论；
- 不宣称已下载、已读或已实现该家族全部模型。