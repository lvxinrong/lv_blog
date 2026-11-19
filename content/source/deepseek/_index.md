+++
title = "DeepSeek 源码图谱"
description = "DeepSeek 家族按模块源码阅读地图；当前规划中，尚未开始逐模块阅读"
columnKind = "column"
aliases = ["/llm/source/deepseek/"]
+++

**当前状态：规划中阅读地图。** 尚未开始逐模块源码阅读，尚未形成 DeepSeek 完整架构结论；不宣称已下载、已读或已实现 DeepSeek 全部模型。

## 系列定位

- 以已有的 DeepSeek V4.1 Flash text_config 初步解读为起点，把架构拆成可独立验证的机制专题。
- 不以覆盖 DeepSeek 全部型号为目标。
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

- 已有 DeepSeek V4.1 Flash 的 text_config 初步解读（见手搓 LLM 番外）。
- 后续可拆成 MoE、低秩投影、部分 RoPE、KV 压缩与跨层来源、Indexer、Engram、DSpark、量化等独立专题。
- 未经官方 modeling 源码确认的字段继续保留待核实，不提前编造实现语义。

## 当前状态

- 当前为规划中阅读地图；
- 尚未开始逐模块源码阅读；
- 尚未形成该家族的完整架构结论；
- 不宣称已下载、已读或已实现该家族全部模型。