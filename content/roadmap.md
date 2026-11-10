+++
title = "lvchat 实现导图：开工顺序即依赖顺序"
slug = "roadmap"
aliases = ["/llm/lvchat-roadmap/", "/nanochat/lvchat-roadmap/"]
date = 2026-10-19T19:10:00+08:00
lastmod = 2026-11-10T13:05:02+08:00
draft = false
series = "llm"
hiddenInRss = true
ShowBreadCrumbs = false
ShowPostNavLinks = false
tags = ["LLM", "nanochat", "lvchat", "diy-llm", "AI-Infra", "学习笔记"]
summary = "按能力层级划分为六个阶段：第一阶段（从零手搓 LLM，M0～M6）已 7/7 完整交付；第二阶段（当前阶段，进度 2/6）已完成 I0 现代架构与 Qwen2.5 承接、I1 工业数据工程与流式 IO，下一站 I2；第三阶段（工业级训练、推理与分布式系统，S0～S6）已建立完整规划蓝图；第四至第六阶段保留演进方向与依赖。"
[cover]
    image = "covers/lvchat-roadmap.jpg"
    alt = "lvchat 实现导图"
    hiddenInSingle = true
    hiddenInList = true
+++

{{< roadmap_overview
    north_star="目标：用纯 PyTorch 交付一个可对话的 355M 模型，并打通从数据到 WebUI 的全链路。"
    phases="phase-01::STAGE 01 · 第一阶段::从零手搓 LLM::done::2026.10.13 → 2026.11.04 (M0～M6 已完成) | phase-02::STAGE 02 · 第二阶段::现代架构与模型承接::active::2026.11.04 启动 · 进度 2/6 (I0、I1 已完成，下一站 I2) | phase-03::STAGE 03 · 第三阶段::工业级训练、推理与分布式系统::planning::规划中 · S0～S6 蓝图与 DeepInfer 对照 | phase-04::STAGE 04 · 第四阶段::后训练与领域能力形成::planning::规划中 · 对齐/诊断/M7 个人语料 | phase-05::STAGE 05 · 第五阶段::Skill 工程与工具生态::planning::远期 · 扫描/排查/MCP/开源规范 | phase-06::STAGE 06 · 第六阶段::Agent 与多模型协作::planning::远期 · 多角色分工与编排闭环"
>}}

{{< roadmap_progress
    id="phase-01"
    season="STAGE 01 · 第一阶段（已完成）"
    title="从零手搓 LLM：自造 lvchat v1（M0 ～ M6）"
    phase_state="done"
    start_date="2026年10月13日"
    end_date="2026年11月04日"
    duration="历时 23 天"
    repo="squid-llms"
    proposal_title="nanochat 立项书"
    proposal_url="/llm/nanochat-proposal/"
    rules="核心交付::完成从 tokenizer、模型、预训练、KV cache、SFT、评估到 CLI/Web UI 的完整工程闭环 | 工程策略::M0 重写底座，M1 起同仓生长，不另起新工程 | 推进铁律::nanochat 当“标准答案”不当教材，开工顺序即依赖顺序"
    done="7"
    total="7"
    current="M6 · 对话界面"
    delivered="第一季核心链路已交付"
    next="第二阶段 I1 · 工业数据工程与流式 IO（I0 已于 2026-11-06 完成）"
    steps="m0:M0:重写底座:done, m1:M1:手写 BPE:done, m2:M2:预训练闭环:done, m3:M3:KV Cache:done, m4:M4:SFT 微调:done, m5:M5:评估框架:done, m6:M6:对话界面:done"
>}}

{{< phase_drawer summary="已归档 · 点击展开第一阶段 M0 ～ M6 全部 7 张验收卡片与实录笔记（点击上方 M0～M6 节点可直接跳转）" >}}

{{< milestone id="m0" code="M0" title="重写底座" status="done" date="2026-10-26" note1_title="笔记 08：重写 lvllm" note1_url="/llm/llm-08-rewrite-lvllm/" >}}
- **核心实现**：按工程结构重写《从零构建大模型》全书代码（`tokenizer` / `model` / `data` / `train` / `generate` / `eval` / `checkpoints` 七层解耦、单一 `config` 与 `device` 入口、checkpoint 三层标准化）
- **验收实绩**：13 个单元测试全绿；355M LoRA 回归评测 **23.6 vs 旧仓库 23.9**（分布一致），欠账注释清单归零
{{< /milestone >}}

{{< milestone id="m1" code="M1" title="手写 BPE" status="done" date="2026-10-27" note1_title="笔记 09：分词器全景" note1_url="/llm/llm-09-diy-llm-tokenizer/" note2_title="笔记 10：手写 BPE 与甜点区" note2_url="/llm/llm-10-handwritten-bpe/" >}}
- **核心实现**：纯 Python 手写 `count_pairs` / `merge` / `train_bpe` 训练与编解码，封装为 `MyBPETokenizer`，不调 `tiktoken`
- **验收实绩**：编解码往返一字不差（无损）；完成压缩率曲线与微型模型固定 500 步 BPB 扫描，锁定博客语料合并甜点区在 **4000 merges（BPB 3.315）**
{{< /milestone >}}

{{< milestone id="m2" code="M2" title="预训练闭环" status="done" date="2026-10-28" note1_title="笔记 11：资源核算与预训练" note1_url="/llm/llm-11-pytorch-resource-accounting/" >}}
- **核心实现**：token 流打包（`pack_tokens`）、流式 dataloader、梯度累积（小批立即 backward + 跨轮 `global_step`）、BPB 指标与带 `config` 的 checkpoint 存档
- **验收实绩**：完成容量与深度扫描，定位小语料甜点 **emb_dim=256、n_layers=2（BPB 3.10）**，复现 512 维过拟合拐点，模型成功咿呀学语
{{< /milestone >}}

{{< milestone id="m3" code="M3" title="KV Cache" status="done" date="2026-10-29" note1_title="笔记 12：KV Cache 与第一次说人话" note1_url="/llm/llm-12-kv-cache/" >}}
- **核心实现**：给 `generate`、`GPTModel.forward`、`MHA.forward` 三层装上无状态 KV Cache 接力，处理增量步位置偏移 `arange(past_len, past_len + seq_len)` 与显式 `use_cache` 开关
- **验收实绩**：贪心采样下输出与朴素版**逐字一致**；512 tokens 生成从 **36.10s 降至 10.00s（实测提速 3.6x）**，第一次看到自己手搓的模型流畅说人话
{{< /milestone >}}

{{< milestone id="m4" code="M4" title="SFT 微调" status="done" date="2026-10-30" note1_title="笔记 13：SFT，从续写机到指令跟随" note1_url="/llm/llm-13-sft-instruction-following/" >}}
- **核心实现**：将第七章 SFT 数据与训练管道移植至自训底座，打开 completion-only 掩码（只对 response 答卷位置计分）
- **验收实绩**：套指令模板稳定作答；base 全 0 分 vs SFT 均分 31.2（110 条 test，接近旧仓库全参 33.5 基线）；cache 与朴素版输出一致，提速 1.6x
{{< /milestone >}}

{{< milestone id="m5" code="M5" title="评估框架" status="done" date="2026-11-04" note1_title="笔记 14：M5，让评估能够中断后继续" note1_url="/llm/llm-14-eval-resume/" >}}
- **核心实现**：选择题评测（字母 logits、完整答案条件似然与选项打乱对照）+ DeepSeek LLM-as-judge 自由生成自动打分与双端断点续跑流水线
- **验收实绩**：
  - 完成选择题字母 logits、完整答案条件似然和选项打乱对照；
  - 完成 DeepSeek 自由生成评分；
  - 生成与评分分离，双方均支持断点续跑；
  - 110 条 held-out test 全部完成，`valid_scores=110/110`；
  - 生成结构化 JSON 报告，包含均分、中位数、分布和逐题明细；
  - 相关回归 `17 passed`。
{{< /milestone >}}

{{< milestone id="m6" code="M6" title="对话界面" status="done" date="2026-11-04" note1_title="笔记 16：给 355M 模型装上对话界面" note1_url="/llm/llm-16-chat-web-ui/" >}}
- **核心实现**：命令行多轮对话 CLI + Python 标准库 HTTP 推理服务 + 纯 HTML/CSS/JavaScript Web 对话页，打通从浏览器输入到本地自训 355M 模型回答的完整应用链路
- **验收实绩**：
  - 完成 `ChatSession`、原始问答 history 和最近 5 轮滑动窗口；
  - 完成 CLI 多轮输入、`/clear` 和 `/exit`；
  - 使用 Python 标准库完成 HTTP 推理服务；
  - 完成纯 HTML/CSS/JavaScript Web UI；
  - 真实浏览器中输入问题并收到本地 355M 模型回答；
  - CLI、HTTP 服务与 Web UI 工程链路均已跑通。
- **能力边界**：当前 355M SFT 模型没有经过可靠的多轮对话训练，连续对话会复制旧回答，因此可靠多轮语义能力未通过。工程验收完成不等于模型多轮能力合格。
{{< /milestone >}}

{{< /phase_drawer >}}

---

{{< roadmap_progress
    id="phase-02"
    season="STAGE 02 · 第二阶段（当前阶段）"
    title="现代架构与模型承接（全量展开 I0 ～ I6）"
    phase_state="active"
    start_date="2026年11月04日"
    end_date="进行中"
    repo="squid-llms"
    proposal_title="diy-llm 立项书"
    proposal_url="/llm/diy-llm-proposal/"
    theory_title="DataWhale diy-llm 教程"
    theory_url="https://datawhalechina.github.io/diy-llm/%E5%89%8D%E8%A8%80.html"
    rules="装备来源::剥离自第一阶段的全部工业级选修项 + 第一阶段实测暴露的工程与模型边界 | 理论蓝本::以 DataWhale diy-llm（CS336 中文本土化 16 章 + 6 作业）为系统理论蓝本，按需调用 | 进化目标::新建独立 model_v3 承接现代架构与 Qwen 权重，并按 I0～I6 逐件升级数据、训练、推理与后训练"
    done="2"
    total="6"
    current="I1 · 工业数据工程与流式 IO（2026-11-10 已完成）"
    delivered="I0 模型承接与 I1 数据管线已交付；I1 完成 38+2 文档隔离、uint32 token store、memmap、训练冒烟与 BPB / Scaling 基线"
    next="第二阶段 I2 · 训练加速与显存压榨（AMP / FlashAttention / Compile）"
    steps="i0:I0:现代架构:done, i1:I1:数据与流式IO:done, i2:I2:训练与算子加速:next, i3:I3:量化与投机推理:todo, i4:I4:CoT与偏好对齐:todo, i5:I5:评委校准CI:todo, i6:I6:MoE与分布式:optional"
>}}

## 第二阶段施工流水线：现代架构承接与 AI-Infra 全量里程碑（I0 → I6）

> 第一阶段解决“**有没有一辆自己造的车**”，第二阶段以 [DataWhale `diy-llm`](https://datawhalechina.github.io/diy-llm/%E5%89%8D%E8%A8%80.html) 为系统理论蓝本，解决“**怎么把 GPT-2 时代的老爷车改装成现代工业级大模型**”。每一站都直接改造 `squid-llms` 里的对应模块，用前后对照实验说话。

{{< milestone id="i0" code="I0" title="现代架构与模型承接（model_v3：RoPE + RMSNorm + SwiGLU + GQA + Qwen 权重加载）" status="done" date="2026-11-06" note1_title="笔记 14：RoPE 先行闭环" note1_url="/llm/llm-14-eval-resume/" note2_title="笔记 17：model_v3 承接 Qwen" note2_url="/llm/llm-17-model-v3-qwen/" >}}
- **版本演进策略**：
  - 新建独立的 `model_v3`（`v3_modern`）模型版本，不持续修改旧模型；
  - 旧版本保持独立，体现学习演进和版本差异：
    - `v1_gpt`：GPT-2 绝对位置 + KV cache；
    - `v2_rope`：独立 RoPE 模型；
    - `v3_modern`：现代架构（RMSNorm + SwiGLU + GQA + RoPE + Weight Tying）与 Qwen2.5 权重承接；
  - 能复用的底层组件直接复用，不能复用的组件在新版本中重写；每个版本独立测试、独立验收。
- **已完成成果（2026-11-06，详见[笔记 14](/llm/llm-14-eval-resume/) 与[笔记 17](/llm/llm-17-model-v3-qwen/)）**：
  1. **架构组件与 Qwen2.5 Base / Instruct 权重承接**：完成 `RoPE`（先行闭环见[笔记 14](/llm/llm-14-eval-resume/)）、`RMSNorm`、`SwiGLU`、`GQA`（14 Q 头 / 2 KV 头）与输入输出权重绑定，严格承接 `Qwen2.5-0.5B` 与 `Qwen2.5-0.5B-Instruct` 官方 `.safetensors` 权重；
  2. **分词、模板与本地实验台**：完成 `QwenTokenizerAdapter`、`chat template` 多轮消息组装、`Chat Server` 与单 Session 本地实验台 Web UI；
  3. **参考实现对照、固定行为回归与测试评估方法**：建立与 Hugging Face 官方参考实现的同输入对照、固定行为回归与测试评估方法；**Qwen 专项 `7 passed`**，**当前测试套件全量 `46 passed`**（包含本地训练、旧模型评估和 DeepSeek 外部评估）。
- **结论限定与能力边界**：
  - **数值对齐限定条件**：中文、英文和代码输入通过 CPU `float32` 的 logits 容差对照；`124-token` 多轮 prompt 在官方 `eager` 路径下全量 logits 零误差；`prefill` 与连续三次单 token cache decode 在官方 `eager` 路径下零误差。**仅限上述受控条件，不代表任意输入、任意设备、`SDPA` 或任意生成过程都逐 token 完全一致**；
  - **多轮对话边界**：仅证明固定代表性用例通过，**不代表 `0.5B Instruct` 在任意自然提问下都稳定**；
  - **GQA 存储边界**：KV Cache 降至 `1/7` 目前是理论存储关系（2 KV 头 vs 14 Q 头），**实际字节数与设备占用尚未测量**；
  - **性能对照拆分（未在 I0 完成）**：`BPB` 对照归入 `I1`，`训练吞吐`对照归入 `I2`，`KV 实际占用`测量归入 `I3`。
- **diy-llm 结合**：[diy-llm](https://datawhalechina.github.io/diy-llm/%E5%89%8D%E8%A8%80.html) 第 4 章（现代 Transformer 架构演进）+ 作业 2
{{< /milestone >}}

{{< milestone id="i1" code="I1" title="工业数据工程与流式 IO（Data Pipeline & Scaling）" status="done" date="2026-11-10" note1_title="笔记 18：I1，让语料从文本流向可训练数据" note1_url="/llm/llm-18-i1-data-pipeline/" >}}
- **进化部位**：改造 `squid/data/` 与 `squid/tokenizer/`
- **已完成成果**：
  1. **可追溯语料管线**：建立 42 条源文档清单与类型区分，保留 39 篇 article + 1 篇 profile 为 40 个候选，固定 38 条训练候选与 2 篇 held-out；最小 Markdown 清洗通过 `5 passed`；
  2. **JSONL 与 uint32 token store**：一行一篇文档，标题 + 正文进入编码，逐篇追加 EOS，记录正文与实际编码文本 hash、offset 和 length；生成 train `117,890` tokens、held-out `5,485` tokens；
  3. **memmap 按需读取**：token 二进制与旧 `pack_tokens()` 逐元素一致，新旧 Dataset 在 stride 64/128 下样本一致；同输入 117,890 tokens、921 窗口时，Python 当前分配由旧版 `2,004,496` bytes 降为 memmap `1,766` bytes；
  4. **训练与指标基线**：完成 5 步小模型训练、checkpoint 保存重载与前向一致性；算出 held-out 冒烟 `BPB=4.9495`，完成参数量、token 量与 Chinchilla 参考基线测算。
- **diy-llm 结合**：[diy-llm](https://datawhalechina.github.io/diy-llm/%E5%89%8D%E8%A8%80.html) 第 2 章（分词器进阶）+ 第 11 章（数据工程）+ 第 9 章（Scaling Laws）+ 作业 1 & 作业 5
- **边界与后续扩展**：本次为自有博客的小语料最小闭环；GB 级实测、多源语料配比、MinHash 近似去重、清洗前后及 GPT-2 / model_v3 的完整 BPB 对照留待真实数据需求与后续实验，不作为当前阻塞项。
{{< /milestone >}}

{{< milestone id="i2" code="I2" title="训练加速与显存压榨（AMP + FlashAttention + Compile）" status="todo" >}}
- **进化部位**：改造 `squid/train/` 与注意力算子
- **装备升级**：
  1. **BF16 自动混合精度（AMP）** 实战落地，对比 FP32 / FP16 / BF16 的动态范围、吞吐与显存账本；
  2. 接入 **FlashAttention** 与 `torch.compile` 算子融合，消除注意力 $O(T^2)$ 显存中间矩阵读写瓶颈；
  3. 激活重计算（Activation Checkpointing）用算力换显存，把单卡可训上下文窗口与 batch size 推到极限。
- **diy-llm 结合**：[diy-llm](https://datawhalechina.github.io/diy-llm/%E5%89%8D%E8%A8%80.html) 第 3 章（混合精度与算术强度）+ 第 6～7 章（GPU 架构与算子优化）+ 作业 3
- **待完成验收（含 I0 拆出的训练吞吐对照）**：产出单卡训练 MFU（算力利用率）、峰值显存与 tokens/sec 的前中后三档实测表，并完成经典 GPT-2 与 `model_v3` 在同数据、同训练配置下的**训练吞吐对照**
{{< /milestone >}}

{{< milestone id="i3" code="I3" title="高性能推理与服务引擎（量化 + 投机解码 + 流式 Serving）" status="todo" >}}
- **进化部位**：承接 M3 / M6 遗留的服务层进阶项，改造 `squid/generate/` 与对话服务层
- **装备升级**：
  1. **滑动窗口 / 会话级 KV Cache** 与按 token 预算的 history 截断管理（消除动态 `torch.cat` 拷贝与粗粒度轮数截断）；
  2. **INT8 / INT4 权重量化推理**（W8A16 / W4A16），实测模型体积压缩比与困惑度损益；
  3. **投机解码（Speculative Decoding）**：用极小草稿模型（Draft Model）一次猜多个 token，主模型单次前向并行校验，打破自回归内存带宽墙；
  4. **SSE 流式输出**与多用户/多会话状态隔离管理。
- **diy-llm 结合**：[diy-llm](https://datawhalechina.github.io/diy-llm/%E5%89%8D%E8%A8%80.html) 第 10 章（推理加速：KV Cache 进阶、量化、投机解码）
- **待完成验收（含 I0 拆出的 KV 实际占用测量）**：在 M3 的 3.6x 提速基线上，测出量化与投机解码叠加后的首字延迟（TTFT）、解码吞吐（tokens/s）与显存降幅，并实测 MHA / GQA 的 **KV Cache 实际字节数与设备占用对照**
{{< /milestone >}}

{{< milestone id="i4" code="I4" title="后训练深水区：多轮对话 SFT、CoT 思维链与 DPO / GRPO 对齐" status="todo" >}}
- **进化部位**：承接 M4 与 M6 暴露的“多轮旧答案复制”边界，升级 `squid/data/instruct.py` 与 `squid/train/`
- **装备升级**：
  1. **真正的多轮对话 SFT + 思维链（CoT）微调**：引入多轮对话指令数据与按轮掩码（解决 M6 暴露的多轮历史复制问题），并构造“推理步骤 `<think>` + 最终答案”数据；
  2. **LoRA vs 全参微调**在现代底座上的系统对标；
  3. **偏好对齐与强化学习**：手写 **DPO（直接偏好优化）** 损失函数，并探索 **RLVR / GRPO**（群组相对策略优化）在数学/代码可验证任务上的最小闭环。
- **diy-llm 结合**：[diy-llm](https://datawhalechina.github.io/diy-llm/%E5%89%8D%E8%A8%80.html) 第 13 章（Pre-training / SFT / DPO 全流程）+ 第 14 章（GRPO / RLVR 强化学习）
- **待完成验收**：解决 Web UI 多轮对话复制旧答案问题，并给出 SFT vs CoT-SFT vs DPO 的评委胜率（Win Rate）对比
{{< /milestone >}}

{{< milestone id="i5" code="I5" title="评估校准与回归基准自动化（Judge Calibration）" status="todo" >}}
- **进化部位**：承接 M5 评估流水线，升级 `squid/eval/`
- **装备升级**：
  1. **LLM-as-Judge 偏见校准**：双向交换位置消除先后偏见（Position Bias）、控制长度偏见（Length Bias）；
  2. **多评委交叉一致性检验**：计算人工评分与 AI 评委的相关系数，建立每次架构/数据改动后的自动化回归门禁。
- **diy-llm 结合**：[diy-llm](https://datawhalechina.github.io/diy-llm/%E5%89%8D%E8%A8%80.html) 第 12 章（评估与基准）+ 作业 6
- **待完成验收**：每次装备升级（I0～I4）均可一键跑出带置信区间与胜率矩阵的对比报告
{{< /milestone >}}

{{< milestone id="i6" code="I6" title="第二阶段独立彩蛋：MoE 稀疏专家与分布式并行沙盘" status="optional" >}}
- **定位说明**：独立高阶架构彩蛋，不计入主线进度；与 GPU 和分布式一起学——先在小模型上实现 Top-K 路由和负载均衡，再理解 Expert Parallelism 与通信开销
- **装备升级**：
  1. 把稠密 FFN 改造为迷你 **MoE（Mixture of Experts）** 层：实现 Top-K 门控路由与负载均衡辅助损失（Load Balancing Loss）；
  2. 走通数据并行（DDP）与分片优化器状态（ZeRO / FSDP 核心思想）的最小复现。
- **diy-llm 结合**：[diy-llm](https://datawhalechina.github.io/diy-llm/%E5%89%8D%E8%A8%80.html) 第 5 章（MoE 混合专家模型）+ 第 8 章（分布式训练）+ 作业 4
- **待完成验收**：在总参数量放大但单 token 激活参数不变的前提下，验证 MoE 模型的收敛曲线与路由均衡度
{{< /milestone >}}

---

## 第三阶段规划蓝图：工业级训练、推理与分布式系统（S0 → S6 · 规划中）

> **阶段定位**：从会写模型，进阶到理解工业级训练与推理系统；在自己的工程中完成最小机制实现，再对照 [DeepSeek `DeepInfer`](https://github.com/deepseek-ai/DeepInfer) 理解生产级系统设计。**本阶段当前处于“规划中”（尚未开始，不设固定排期，也不承诺学习周期；DeepInfer 尚未在本机部署或跑通）。**

{{< roadmap_progress
    id="phase-03"
    season="STAGE 03 · 第三阶段（规划中）"
    title="工业级训练、推理与分布式系统（S0 ～ S6）"
    phase_state="planning"
    repo="squid-llms"
    theory_title="DeepSeek DeepInfer"
    theory_url="https://github.com/deepseek-ai/DeepInfer"
    rules="阶段定位::从会写模型，进阶到理解工业级训练与推理系统；在自己的工程中完成最小机制实现，再对照 DeepInfer 理解生产级系统设计 | 前置依赖::先完成第二阶段 I0～I3 相关基础，具备 Python / PyTorch / Transformer 与训练推理链路知识，准备 Linux GPU 实验环境 | 硬件与验收边界::Mac + MPS 不作为 DeepInfer 部署验收环境；DeepInfer 要求 NVIDIA SM100 或 Ascend 950，源码研读不依赖本机部署，官方部署验证仅作匹配硬件后的选修"
    done="0"
    total="7"
    unit="规划里程碑（尚未启动）"
    planning_note="规划中 · 待第二阶段 I0～I3 与 Linux GPU 实验环境就绪后按 S0 → S6 依赖顺序启动"
    steps="s0:S0:性能基线:todo, s1:S1:源码地图:todo, s2:S2:算子优化:todo, s3:S3:分布式训练:todo, s4:S4:MoE并行:todo, s5:S5:推理调度:todo, s6:S6:稳定性验收:todo"
>}}

{{< phase_drawer open="true" variant="planning" summary="规划蓝图（尚未启动） · 点击收起/展开第三阶段前置依赖、S0 ～ S6 全部 7 张里程碑卡片与总交付目标（点击上方 S0～S6 节点可直接跳转）" >}}

{{< milestone id="s-pre" code="前置条件" title="第三阶段前置依赖与硬件环境边界" status="planning" question="进入工业级训练、推理与分布式系统之前，必须先满足哪些基础与硬件边界？" note1_title="DeepInfer 仓库" note1_url="https://github.com/deepseek-ai/DeepInfer" >}}
1. **先完成第二阶段 `I0～I3` 的相关基础**：
   - 现代模型结构与 Qwen 权重承接（`I0` 已完成）；
   - 数据与流式 IO（`I1` 待完成）；
   - 训练加速与资源核算（`I2` 待完成）；
   - KV Cache、量化、投机解码和基础推理指标（`I3` 待完成）。
2. **知识储备**：具备 Python、PyTorch、Transformer 和基础训练/推理链路知识。
3. **实验环境**：准备 Linux GPU 实验环境后再开展真实多卡与底层算子实验。
4. **本地环境边界**：当前 Mac + MPS 环境不作为 [DeepInfer](https://github.com/deepseek-ai/DeepInfer) 部署验收环境。
5. **DeepInfer 硬件边界说明**：[DeepInfer](https://github.com/deepseek-ai/DeepInfer) 官方目前要求特定的 NVIDIA SM100 或 Ascend 950 环境，因此：
   - **源码研读不依赖本机部署**；
   - **官方部署验证只作为具备匹配硬件后的选修**；
   - **不把普通 GPU 上无法运行 DeepInfer 写成学习失败**。
{{< /milestone >}}

{{< milestone id="s0" code="S0" title="GPU 系统基础与性能基线" status="planning" question="优化之前，能不能先建立一张可信的性能与资源账本？" >}}
- **学习内容**：
  - CPU / GPU、Host / Device、SM、Warp、HBM 与内存带宽；
  - 算术强度、Roofline、计算瓶颈与带宽瓶颈；
  - FP32 / FP16 / BF16 的精度与资源差异；
  - `torch.profiler`，按需了解 Nsight 等工具；
  - warmup、重复测量、均值、P50/P95、方差与可复现 benchmark；
  - TTFT、TPOT、tokens/s、峰值显存、MFU 等指标。
- **规划交付物**：
  - 一套统一的训练与推理 benchmark 入口；
  - 经典 GPT-2 与 `model_v3` 的固定输入性能基线；
  - 每次实验记录设备、dtype、batch、上下文长度、warmup 和重复次数。
- **规划验收标准**：
  - 同一场景可重复测量；
  - 结果包含资源与正确性数据，不只报告“变快了”；
  - 性能测试与数值正确性测试分开，不用速度掩盖错误。
{{< /milestone >}}

{{< milestone id="s1" code="S1" title="DeepInfer 请求链路与源码地图" status="planning" question="一条请求从输入到输出，究竟穿过了哪些工业级推理组件？" note1_title="DeepInfer 源码仓库" note1_url="https://github.com/deepseek-ai/DeepInfer" >}}
- **阅读顺序**：
  1. `examples/offline_inference.py`
  2. `engine/llm_engine.py`
  3. `worker`
  4. `model_executor`
  5. `models / layers / sampler`
  6. `distributed`
  7. `tests`
- **重点理解**：
  - entrypoint、engine、worker、model executor 的职责；
  - prefill 与 decode 的调用关系；
  - DP / CP / EP 参数出现在哪里；
  - scheduler、模型执行和采样如何衔接；
  - 日志、指标、断言与测试如何进入主链路；
  - [DeepInfer](https://github.com/deepseek-ai/DeepInfer) 与 vLLM、SGLang、TensorRT-LLM 的继承与借鉴关系。
- **规划交付物**：
  - 一张 DeepInfer 请求链路图；
  - 一张源码目录与职责地图；
  - 一条 prefill/decode 调用链；
  - 一份“它已经解决什么、开源版没有包含什么”的边界说明。
- **规划验收标准**：
  - 能从一次 `llm.generate()` 讲到模型执行与输出；
  - 不把底层算子、推理框架和完整生产集群混为一谈；
  - 不虚构未实际阅读过的源码细节。
{{< /milestone >}}

{{< milestone id="s2" code="S2" title="自定义算子与 Kernel 优化" status="planning" question="同一个数学公式，为什么不同计算路径会有不同的性能与浮点结果？" >}}
- **学习内容**：
  - eager、SDPA、FlashAttention 与融合算子的关系；
  - Triton 入门，按需了解 CUDA / TileLang；
  - 中间张量生成、显存读写、算子融合与分块计算；
  - 从 RMSNorm、RoPE 或简单 FFN 算子开始，再进入 attention；
  - DeepGEMM、FlashMLA、TileKernels 等组件在系统中的位置。
- **规划交付物**：
  - 一个小型自定义算子或融合算子；
  - eager / SDPA / 自定义实现的对照实验；
  - 正确性、吞吐和显存报告。
- **规划验收标准**：
  - 使用固定输入与明确容差验证正确性；
  - 报告性能提升时同时报告测试条件；
  - 不把“数学公式相同”写成“所有后端逐 bit 相同”；
  - 不在没有测量的情况下声称优化有效。
{{< /milestone >}}

{{< milestone id="s3" code="S3" title="分布式训练与参数分片" status="planning" question="模型和数据变大以后，计算、梯度、参数与 checkpoint 怎样分布到多个设备？" >}}
- **学习顺序**：
  1. 数据并行与 DDP；
  2. Gradient All-Reduce 与通信开销；
  3. FSDP / ZeRO 参数、梯度、优化器状态分片；
  4. Tensor Parallelism；
  5. Pipeline Parallelism；
  6. Context Parallelism；
  7. 分布式 checkpoint、保存、恢复与故障处理。
- **规划交付物**：
  - 一个最小分布式训练沙盘；
  - 单进程与多进程的训练对照；
  - 参数/梯度分片与通信示意；
  - 可恢复的分布式 checkpoint 实验。
- **规划验收标准**：
  - 在相同数据与初始状态下，分布式结果与单进程保持合理一致；
  - 能解释通信量、显存和吞吐的变化；
  - checkpoint 能保存并恢复训练现场；
  - 不以“启动了多个进程”冒充分布式训练已经掌握。
{{< /milestone >}}

{{< milestone id="s4" code="S4" title="MoE 与专家并行" status="planning" question="怎样增加模型容量，同时避免每个 token 都执行全部专家？" >}}
- **学习内容**：
  - Dense FFN → Sparse MoE；
  - Router、Top-K、capacity factor；
  - load balancing auxiliary loss；
  - expert collapse 与路由稳定性；
  - Expert Parallelism；
  - DeepEP、EPLB 与专家负载均衡；
  - MoE 的训练稳定性、通信成本与评估方法。
- **规划交付物**：
  - 一个小模型 Top-K MoE 层；
  - 路由与负载均衡指标；
  - Dense FFN 与 MoE 的同规模对照；
  - 单机模拟与分布式专家并行示意。
- **规划验收标准**：
  - 能证明 token 被路由到正确专家；
  - 能观察专家负载是否失衡；
  - 同时报告模型质量、训练稳定性、通信与资源成本；
  - 不把“参数量变大”直接写成“能力必然提升”。
{{< /milestone >}}

{{< milestone id="s5" code="S5" title="生产推理调度与服务化" status="planning" question="当一个请求变成成千上万个请求，推理系统怎样保持吞吐、延迟与隔离？" >}}
- **学习内容**：
  - continuous batching；
  - 异步调度与 CPU/device 工作重叠；
  - paged/bounded KV Cache 与内存管理；
  - prefill/decode 分离；
  - 多副本负载均衡；
  - 流式输出、多 Session 隔离、背压与超时；
  - DSpark、推测解码与置信度调度验证；
  - SWA bounded replay 的适用边界。
- **规划交付物**：
  - 一个最小推理调度器或服务沙盘；
  - 多请求并发与 Session 隔离实验；
  - KV Cache 上限、背压和超时处理；
  - 吞吐、TTFT、TPOT、P95 延迟与资源占用报告。
- **规划验收标准**：
  - 并发请求不会串 Session；
  - 长请求不会无限制耗尽资源；
  - 服务异常时有明确错误与恢复行为；
  - 性能结论必须来自实测，不照抄官方数字。
{{< /milestone >}}

{{< milestone id="s6" code="S6" title="稳定性、确定性与综合验收" status="planning" question="系统不只要能跑，还要能证明它稳定、可复现、可诊断、可恢复。" >}}
- **学习内容**：
  - batch-invariant inference；
  - deterministic sampling；
  - structured outputs；
  - 数值、行为、性能与分布式回归；
  - 日志、指标、trace 与故障定位；
  - 压测、故障注入、超时、重试与恢复；
  - 官方参考实现对照与结论边界。
- **规划交付物**：
  - 第三阶段完整测试与评估报告；
  - 一张训练/推理系统全景图；
  - 一份 [DeepInfer](https://github.com/deepseek-ai/DeepInfer) 对照学习总结；
  - 一篇完整的第三阶段收官笔记。
- **规划验收标准**：
  - 固定条件下结果可复现；
  - 不同 batch 组合与采样场景的差异有明确测试；
  - 失败时能通过日志、指标和最小复现定位；
  - 报告明确区分已实现、已测量、未覆盖和受硬件限制的部分；
  - 不以“参考了 DeepInfer”冒充“已经达到 DeepInfer 的生产能力”。
{{< /milestone >}}

{{< milestone id="s-goal" code="总目标" title="第三阶段总交付目标与“六不追求”边界" status="planning" question="第三阶段收官时应当能够回答什么问题？明确不追求哪些事情？" >}}
- **阶段结束时应当能够回答的 6 个核心问题**：
  1. 一个模型的训练和推理性能瓶颈如何测量？
  2. 一个请求如何穿过推理引擎？
  3. 一个算子为什么可能同时改变性能与浮点误差？
  4. 多设备如何分担数据、参数、梯度和专家？
  5. 多请求如何调度、隔离并控制 KV Cache？
  6. 系统如何通过测试、指标和故障恢复证明自身可靠？
- **第三阶段明确不追求的 6 件事**：
  - 不追求从头训练一个超大模型；
  - 不追求在当前 Mac 上强行部署 [DeepInfer](https://github.com/deepseek-ai/DeepInfer)；
  - 不追求照搬全部生产功能；
  - 不追求只读源码不做最小实现；
  - 不追求只报告速度，不验证正确性；
  - 不追求为了 roadmap 好看而提前填写成果。
{{< /milestone >}}

{{< /phase_drawer >}}

---

## 后续演进阶段（第四至第六阶段 · 方向与依赖）

> 第四至第六阶段只保留演进方向与前置依赖，不提前拆细任务清单，也不承诺时间；**[DataWhale `diy-llm`](https://datawhalechina.github.io/diy-llm/%E5%89%8D%E8%A8%80.html)** 作为第二至第四阶段的系统理论蓝本，按实际项目需要随时调用，无需无差别重读所有章节。

{{< roadmap_progress
    id="phase-04"
    season="STAGE 04 · 第四阶段（规划中）"
    title="后训练与领域能力形成"
    phase_state="planning"
    hide_bar="true"
    repo="squid-llms"
    rules="前置依赖::现代架构底座已就绪，待训练/推理与后训练基础设施完成后展开 | 探索衔接::承载推理强化、模型诊断、扩层后训练（后续选修），以及下方尚未开始训练的 M7 个人中文语料 Midtrain"
>}}

- **推理强化与对齐**：CoT、DPO、GRPO、RLVR；
- **数据与评测工程**：指令数据工程与评委校准；
- **领域模型与权重诊断**：领域模型训练与评估、模型诊断和权重空间编程（探索记录见[《手搓 LLM 笔记 15：让 AI 直接修改模型权重，能学会四则运算吗？》](/llm/llm-15-weight-space-arithmetic/)）；
- **模型增长与扩层后训练（后续选修）**：研究 Block Expansion / Depth Up-Scaling（Net2Net、LLaMA Pro、SOLAR），在原有 Transformer Block 之后、`final_norm` 之前插入少量新层，重点理解恒等初始化、冻结与逐步解冻，并与 LoRA、全参数训练做同数据对照；不阻塞当前主线或 `M7`；
- **个人中文语料 midtrain（尚未开始训练）**：承载下方 `M7` 独立彩蛋。

{{< milestone id="m7" code="M7" title="第四阶段独立彩蛋：个人中文语料中间训练（Midtrain）" status="optional" >}}
- **定位与当前状态**：属于第四阶段独立彩蛋（不计入第一或第二阶段主线完成度），**目前尚未开始训练**（仅完成个人语料盘点，尚未产生 midtrain loss 或新 checkpoint）。
- **底座边界说明**：第一阶段 GPT-2 355M 底座偏英文，不适合直接承接全中文个人语料；现 `I0` 现代架构改造与 Qwen 权重加载已就绪，后续将在 Qwen 底座上启动。
- **前置依赖**：
  1. 已就绪：完成现代架构改造（`I0`）并能正确加载运行 Qwen 权重；
  2. 待执行：使用个人中文语料（个人年终总结、有道云笔记与博客全量中文语料）进行 midtrain 与评估对照。
- **待完成验收**：“吕炘嵘 GPT”第一次附体
{{< /milestone >}}

{{< roadmap_progress
    id="phase-05"
    season="STAGE 05 · 第五阶段（远期）"
    title="Skill 工程与工具生态"
    phase_state="planning"
    hide_bar="true"
    rules="阶段定位::在扎实的模型与后训练认知之上，沉淀面向真实工程现场的 Skill 工具链与标准规范"
>}}

- **核心方向**：系统扫描、生产排查、学习辅助、MCP / CLI、权限、评估、开源文档（前期实践见[《生产排查 Skill 深解》](/incident-skill/introduction/)与[《系统扫描 Skill 深解》](/scan-skill/introduction/)）。

{{< roadmap_progress
    id="phase-06"
    season="STAGE 06 · 第六阶段（远期）"
    title="Agent 与多模型协作"
    phase_state="planning"
    hide_bar="true"
    rules="阶段定位::将专用模型能力与 Skill 工具生态合流，构建可审计的多角色协作系统（多模态暂不作为主阶段，只保留未来选修）"
>}}

- **核心方向**：规划、执行、测试、运维分工（思路见[《企业级 AI 编程的终极形态：当模型开始分工》](/ai/enterprise-ai-model-division/)），以及记忆、上下文、权限、反馈闭环和多模型编排。

---

## 支线探索与日常节奏

- **权重空间编程（不阻塞主线）**：三轮 Weight-Space Programming 实验已独立整理为[《手搓 LLM 笔记 15：让 AI 直接修改模型权重，能学会四则运算吗？》](/llm/llm-15-weight-space-arithmetic/)，不放入主线依赖，不阻塞 M5、M6 或后续阶段。
- **默写与回炉（2026-10-29 增补）**：`GPTModel` 每两周在 A4 纸脱稿默写一次（首次记录见[《手搓 LLM 番外：A4 纸默写 GPTModel》](/llm/llm-extra-handwrite-gptmodel/)），`MHA` / `FFN` / `LayerNorm` 单独补漏；两周后对照进步。
- **nanochat 与官方参考实现对照**：第一阶段 `M0～M6` 与第二阶段 `I0`（`model_v3` 承接 Qwen2.5）已交付，后续推进 `I1～I5` 时继续以 `nanochat` 与 Hugging Face 官方参考实现作为对照基线，按实际依赖验证数据管线、训练吞吐与推理服务。
- **博客与掘金专栏输出**：每个里程碑（M0～M6、I0～I6、M7）产出一篇实录笔记；实验数据直接整理成可复现报告。
