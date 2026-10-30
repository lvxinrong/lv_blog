+++
title = "lvchat 实现导图：开工顺序即依赖顺序"
slug = "lvchat-roadmap"
aliases = ["/nanochat/lvchat-roadmap/"]
date = 2026-10-19T19:10:00+08:00
lastmod = 2026-10-30T10:38:00+08:00
draft = false
tags = ["LLM", "nanochat", "lvchat", "diy-llm", "AI-Infra", "学习笔记"]
summary = "分两季推进：第一季从《从零构建大模型》手搓代码出发，按依赖顺序造出 lvchat v1 整车（已通关至 M3）；第二季结合原选修模块与 DataWhale diy-llm 教程，启动 AI-Infra 装备升级线，让模型完成现代工业级进化。"
[cover]
    image = "covers/lvchat-roadmap.jpg"
    alt = "lvchat 实现导图"
    hiddenInSingle = true
    hiddenInList = true
+++

{{< roadmap_progress
    season="SEASON 01 · 第一季（整车闭环线）"
    title="从零件到整车：自造 lvchat v1（nanochat-lite）"
    phase_state="active"
    repo="squid-llms"
    proposal_title="nanochat 立项书"
    proposal_url="/llm/nanochat-proposal/"
    theory_title="diy-llm 立项书"
    theory_url="/llm/diy-llm-proposal/"
    rules="基准原则::nanochat 当“标准答案”不当教材，从手搓代码长出整车 | 工程策略::M0 重写底座，M1 起同仓生长，不另起新工程 | 推进铁律::开工顺序即依赖顺序，先跑通 v1 全链路，进阶装备统一收归第二季"
    done="4"
    total="7"
    current="M3 · KV Cache 推理引擎"
    next="M4 · SFT 指令微调"
    steps="m0:M0:重写底座:done, m1:M1:手写 BPE:done, m2:M2:预训练:done, m3:M3:KV Cache:done, m4:M4:SFT 微调:next, m5:M5:评估框架:todo, m6:M6:对话界面:todo, m7:M7:彩蛋 midtrain:optional"
>}}

## 第一季施工流水线：跑通 `lvchat v1` 全链路（M0 → M7）

> 第一季只干一件事：**砍掉花哨选修，把从分词器到 Web 对话界面的整车链路亲手跑通。** 原先散落在各里程碑里的工业级选修项（RoPE、量化、投机解码、FlashAttention、CoT / DPO / GRPO 等）全部剥离，集中编入下方**第二季：AI-Infra 装备升级线**。

{{< milestone id="m0" code="M0" title="重写全书代码（底座重构）" status="done" date="2026-10-26" note1_title="笔记 08：重写 lvllm" note1_url="/llm/llm-08-rewrite-lvllm/" >}}
- **核心实现**：按工程结构重写《从零构建大模型》全书代码（`tokenizer` / `model` / `data` / `train` / `generate` / `eval` / `checkpoints` 七层解耦、单一 `config` 与 `device` 入口、checkpoint 三层标准化）
- **理论配套**：《从零构建大模型》第 1～7 章 + 附录 D/E 终极回炉
- **验收实绩**：13 个单元测试全绿；355M LoRA 回归评测 **23.6 vs 旧仓库 23.9**（分布一致），欠账注释清单归零
{{< /milestone >}}

{{< milestone id="m1" code="M1" title="自训 BPE Tokenizer" status="done" date="2026-10-27" note1_title="笔记 09：分词器全景" note1_url="/llm/llm-09-diy-llm-tokenizer/" note2_title="笔记 10：手写 BPE 与甜点区" note2_url="/llm/llm-10-handwritten-bpe/" >}}
- **核心实现**：纯 Python 手写 `count_pairs` / `merge` / `train_bpe` 训练与编解码，封装为 `MyBPETokenizer`，不调 `tiktoken`
- **理论配套**：[diy-llm 教程](https://datawhalechina.github.io/diy-llm/%E5%89%8D%E8%A8%80.html) 第 2 章（分词器）+ 作业 1
- **验收实绩**：编解码往返一字不差（无损）；完成压缩率曲线与微型模型固定 500 步 BPB 扫描，锁定博客语料合并甜点区在 **4000 merges（BPB 3.315）**
{{< /milestone >}}

{{< milestone id="m2" code="M2" title="预训练闭环（Pretrain）" status="done" date="2026-10-28" note1_title="笔记 11：资源核算与预训练" note1_url="/llm/llm-11-pytorch-resource-accounting/" >}}
- **核心实现**：token 流打包（`pack_tokens`）、流式 dataloader、梯度累积（小批立即 backward + 跨轮 `global_step`）、BPB 指标与带 `config` 的 checkpoint 存档
- **理论配套**：[diy-llm 教程](https://datawhalechina.github.io/diy-llm/%E5%89%8D%E8%A8%80.html) 第 3 章（PyTorch 与资源核算）+ 第 9 章（Scaling Laws 基础）+ 第 11 章（数据工程基础）
- **验收实绩**：完成容量与深度扫描，定位小语料甜点 **emb_dim=256、n_layers=2（BPB 3.10）**，复现 512 维过拟合拐点，模型成功咿呀学语
{{< /milestone >}}

{{< milestone id="m3" code="M3" title="推理引擎（KV Cache）" status="done" date="2026-10-29" note1_title="笔记 12：KV Cache 与第一次说人话" note1_url="/llm/llm-12-kv-cache/" >}}
- **核心实现**：给 `generate`、`GPTModel.forward`、`MHA.forward` 三层装上无状态 KV Cache 接力，处理增量步位置偏移 `arange(past_len, past_len + seq_len)` 与显式 `use_cache` 开关
- **理论配套**：[diy-llm 教程](https://datawhalechina.github.io/diy-llm/%E5%89%8D%E8%A8%80.html) 第 10 章（推理基础：KV Cache 机制）
- **验收实绩**：贪心采样下输出与朴素版**逐字一致**；512 tokens 生成从 **36.10s 降至 10.00s（实测提速 3.6x）**，第一次看到自己手搓的模型流畅说人话
{{< /milestone >}}

{{< milestone id="m4" code="M4" title="指令微调（SFT）" status="done" >}}
- **核心实现**：将第七章 SFT 数据与训练管道移植至自训底座，打开 completion-only 掩码（只对 response 答卷位置计分）
- **理论配套**：[diy-llm 教程](https://datawhalechina.github.io/diy-llm/%E5%89%8D%E8%A8%80.html) 第 13 章（后训练与 SFT 流程）
- **验收实绩**：套指令模板稳定作答；base 全 0 分 vs SFT 均分 31.2（110 条 test，接近旧仓库全参 33.5 基线）；cache 与朴素版输出一致，提速 1.6x
{{< /milestone >}}

{{< milestone id="m5" code="M5" title="评估框架（Eval & Judge）" status="todo" >}}
- **核心实现**：基模选择题评测 + DeepSeek LLM-as-judge 自动打分流水线（生成与打分分离、支持断点续跑）
- **理论配套**：[diy-llm 教程](https://datawhalechina.github.io/diy-llm/%E5%89%8D%E8%A8%80.html) 第 12 章（评估与基准）+ 作业 6
- **验收标准**：一键产出结构化 JSON 评估报告与分数分布统计
{{< /milestone >}}

{{< milestone id="m6" code="M6" title="对话界面（CLI + Web UI）" status="todo" >}}
- **核心实现**：命令行多轮对话 CLI + 轻量 Web 对话页，跑通从浏览器输入到自训模型生成的端到端闭环
- **理论配套**：推理服务最小封装与多轮上下文拼接
- **验收标准**：祁总打开浏览器能直接聊上（`lvchat v1` 正式整车交付）
{{< /milestone >}}

{{< milestone id="m7" code="M7" title="第一季彩蛋：个人语料中间训练（Midtrain）" status="optional" >}}
- **核心实现**：喂入个人年终总结 + 有道云笔记与博客全量语料做继续预训练（midtrain）
- **理论配套**：领域语料继续训练与风格注入思路
- **验收标准**：“吕炘嵘 GPT”第一次附体
{{< /milestone >}}

---

{{< roadmap_progress
    season="SEASON 02 · 第二季（AI-Infra 装备进化线）"
    title="从能跑到能打：结合 diy-llm 升级 lvchat v2"
    phase_state="planning"
    repo="squid-llms"
    theory_title="DataWhale diy-llm 教程"
    theory_url="https://datawhalechina.github.io/diy-llm/%E5%89%8D%E8%A8%80.html"
    rules="装备来源::剥离自第一季 M1～M7 的全部工业级选修项 + 第一季遗留欠账 | 理论蓝本::紧扣 DataWhale diy-llm（CS336 中文本土化 16 章 + 6 作业） | 进化目标::在 lvchat v1 整车底盘上逐件换装现代架构、算子加速、量化推理与强化对齐"
    done="0"
    total="6"
    next="待第一季 M6 整车交付并完成 nanochat 源码对照后开启"
    steps="i0:I0:现代架构:todo, i1:I1:数据与流式IO:todo, i2:I2:训练与算子加速:todo, i3:I3:量化与投机推理:todo, i4:I4:CoT与偏好对齐:todo, i5:I5:评委校准CI:todo, i6:I6:MoE与分布式:optional"
>}}

## 第二季施工流水线：AI-Infra 装备升级（I0 → I6）

> 第一季解决“**有没有一辆自己造的车**”，第二季解决“**怎么把 GPT-2 时代的老爷车改装成现代工业级大模型**”。每一站都直接改造 `squid-llms` 里的对应模块，用前后对照实验说话。

{{< milestone id="i0" code="I0" title="现代架构换装（RoPE + RMSNorm + SwiGLU + GQA）" status="todo" >}}
- **进化部位**：承接 M3 选修与“位置溢出”欠账，改造 `squid/model/`
- **装备升级**：
  1. 用 **RoPE（旋转位置编码）** 替代固定长度的 `pos_emb` 查表，彻底解决长文本位置越界，支持外推；
  2. 用 **RMSNorm** 替代 `LayerNorm`（省去均值中心化计算），FFN 换装 **SwiGLU** 门控线性单元；
  3. 多头注意力升级为 **GQA（分组查询注意力）**，成倍压缩推理期 KV Cache 显存占用。
- **diy-llm 结合**：[diy-llm](https://datawhalechina.github.io/diy-llm/%E5%89%8D%E8%A8%80.html) 第 4 章（现代 Transformer 架构演进）+ 作业 2
- **进化验收**：在同等参数预算与同一语料下，对比经典 GPT-2 结构与现代结构的训练吞吐、KV 显存占用与最终 BPB
{{< /milestone >}}

{{< milestone id="i1" code="I1" title="工业数据工程与流式 IO（Data Pipeline & Scaling）" status="todo" >}}
- **进化部位**：承接 M1 / M2 选修与复习线“流式 IO”欠账，改造 `squid/data/` 与 `squid/tokenizer/`
- **装备升级**：
  1. **语料工程管线**：网页/长文清洗、启发式质量过滤、MinHash 去重与多源语料配比；
  2. **内存映射流式加载（`np.memmap`）**：告别 `read_text()` 全量塞内存，支持 GB 级语料零拷贝随机切片；
  3. **分词器热路径提速**与 Chinchilla **Scaling Laws** 最优“参数量 vs Token 数”配比测算。
- **diy-llm 结合**：[diy-llm](https://datawhalechina.github.io/diy-llm/%E5%89%8D%E8%A8%80.html) 第 11 章（数据工程）+ 第 9 章（Scaling Laws）+ 作业 1 & 作业 5
- **进化验收**：内存占用与语料总体积脱钩（恒定低内存跑大语料），给出清洗前后同模型 BPB 对照
{{< /milestone >}}

{{< milestone id="i2" code="I2" title="训练加速与显存压榨（AMP + FlashAttention + Compile）" status="todo" >}}
- **进化部位**：承接 M2 / M3 选修，改造 `squid/train/` 与注意力算子
- **装备升级**：
  1. **BF16 自动混合精度（AMP）** 实战落地，对比 FP32 / FP16 / BF16 的动态范围、吞吐与显存账本；
  2. 接入 **FlashAttention** 与 `torch.compile` 算子融合，消除注意力 $O(T^2)$ 显存中间矩阵读写瓶颈；
  3. 激活重计算（Activation Checkpointing）用算力换显存，把单卡可训上下文窗口与 batch size 推到极限。
- **diy-llm 结合**：[diy-llm](https://datawhalechina.github.io/diy-llm/%E5%89%8D%E8%A8%80.html) 第 3 章（混合精度与算术强度）+ 第 6～7 章（GPU 架构与算子优化）+ 作业 3
- **进化验收**：产出单卡训练 MFU（算力利用率）、峰值显存与 tokens/sec 的前中后三档实测表
{{< /milestone >}}

{{< milestone id="i3" code="I3" title="高性能推理与服务引擎（量化 + 投机解码 + 流式 Serving）" status="todo" >}}
- **进化部位**：承接 M3 / M6 选修，改造 `squid/generate/` 与对话服务层
- **装备升级**：
  1. **滑动窗口 KV Cache** 与显存池预分配（消除动态 `torch.cat` 频繁内存拷贝）；
  2. **INT8 / INT4 权重量化推理**（W8A16 / W4A16），实测模型体积压缩比与困惑度损益；
  3. **投机解码（Speculative Decoding）**：用极小草稿模型（Draft Model）一次猜多个 token，主模型单次前向并行校验，打破自回归内存带宽墙；
  4. **SSE 流式输出**与多会话状态隔离管理。
- **diy-llm 结合**：[diy-llm](https://datawhalechina.github.io/diy-llm/%E5%89%8D%E8%A8%80.html) 第 10 章（推理加速：KV Cache 进阶、量化、投机解码）
- **进化验收**：在 M3 的 3.6x 提速基线上，测出量化与投机解码叠加后的首字延迟（TTFT）、解码吞吐（tokens/s）与显存降幅
{{< /milestone >}}

{{< milestone id="i4" code="I4" title="后训练深水区：CoT 思维链、DPO 与 GRPO 强化对齐" status="todo" >}}
- **进化部位**：承接 M4 选修，升级 `squid/data/instruct.py` 与 `squid/train/`
- **装备升级**：
  1. **指令数据工程 + 思维链（CoT）微调**：构造“推理步骤 `<think>` + 最终答案”格式数据，训练模型先推演再作答；
  2. **LoRA vs 全参微调**在现代底座上的系统对标；
  3. **偏好对齐与强化学习**：手写 **DPO（直接偏好优化）** 损失函数，并探索 **RLVR / GRPO**（群组相对策略优化）在数学/代码可验证任务上的最小闭环。
- **diy-llm 结合**：[diy-llm](https://datawhalechina.github.io/diy-llm/%E5%89%8D%E8%A8%80.html) 第 13 章（Pre-training / SFT / DPO 全流程）+ 第 14 章（GRPO / RLVR 强化学习）
- **进化验收**：同底座下 SFT vs CoT-SFT vs DPO 的评委胜率（Win Rate）与推理题准确率对比
{{< /milestone >}}

{{< milestone id="i5" code="I5" title="评估校准与回归基准自动化（Judge Calibration）" status="todo" >}}
- **进化部位**：承接 M5 选修，升级 `squid/eval/`
- **装备升级**：
  1. **LLM-as-Judge 偏见校准**：双向交换位置消除先后偏见（Position Bias）、控制长度偏见（Length Bias）；
  2. **多评委交叉一致性检验**：计算人工评分与 AI 评委的相关系数，建立每次架构/数据改动后的自动化回归门禁。
- **diy-llm 结合**：[diy-llm](https://datawhalechina.github.io/diy-llm/%E5%89%8D%E8%A8%80.html) 第 12 章（评估与基准）+ 作业 6
- **进化验收**：每次装备升级（I0～I4）均可一键跑出带置信区间与胜率矩阵的对比报告
{{< /milestone >}}

{{< milestone id="i6" code="I6" title="第二季彩蛋：MoE 稀疏专家与分布式并行沙盘" status="optional" >}}
- **进化部位**：捡回第一季“明确砍掉”的高阶竞技装备
- **装备升级**：
  1. 把稠密 FFN 改造为迷你 **MoE（Mixture of Experts）** 层：实现 Top-K 门控路由与负载均衡辅助损失（Load Balancing Loss）；
  2. 走通数据并行（DDP）与分片优化器状态（ZeRO / FSDP 核心思想）的最小复现。
- **diy-llm 结合**：[diy-llm](https://datawhalechina.github.io/diy-llm/%E5%89%8D%E8%A8%80.html) 第 5 章（MoE 混合专家模型）+ 第 8 章（分布式训练）+ 作业 4
- **进化验收**：在总参数量放大但单 token 激活参数不变的前提下，验证 MoE 模型的收敛曲线与路由均衡度
{{< /milestone >}}

---

## 日常节奏：复习线与输出线

- **默写与回炉（2026-10-29 增补）**：`GPTModel` 每两周在 A4 纸脱稿默写一次（首次记录见[《手搓 LLM 番外：A4 纸默写 GPTModel》](/llm/llm-extra-handwrite-gptmodel/)），`MHA` / `FFN` / `LayerNorm` 单独补漏；两周后对照进步。
- **nanochat 源码对照时机**：**第一季 M6 对话界面收官后、第二季 I0 启动前**，把 Karpathy 的 `nanochat` 源码从头到尾当“标准答案”通读对照一遍——这时手里已经有自己的 `lvchat v1` 完整实现，正好带着问题去查他怎么处理现代架构与工程细节，无缝导入第二季。
- **博客与掘金专栏输出**：每个里程碑（M0～M7、I0～I6）产出一篇实录笔记；实验数据（容量扫描、BPB 曲线、KV Cache 3.6x 提速、后续 RoPE / 量化 / 投机解码对照）直接整理成可复现报告。
