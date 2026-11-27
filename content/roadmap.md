+++
title = "lvchat 实现导图：主干先行，局部进化，持续验收"
slug = "roadmap"
aliases = ["/llm/lvchat-roadmap/", "/nanochat/lvchat-roadmap/"]
date = 2026-10-19T19:10:00+08:00
lastmod = 2026-11-27T11:49:36+08:00
draft = false
series = "llm"
hiddenInRss = true
ShowBreadCrumbs = false
ShowPostNavLinks = false
tags = ["LLM", "nanochat", "lvchat", "diy-llm", "AI-Infra", "学习笔记"]
summary = "按能力层级划分为六个阶段：第一阶段（从零手搓 LLM，M0～M6）已 7/7 完整交付；第二阶段（已收官，进度 7/7）完成 I0～I6 主线与 CUDA、ModelV4 / Qwen3 两个番外，I6 领域后训练收官但真实 Defects4J 未见缺陷稳定最小修复目标尚未完成、暂缓待复入（后续带着新机制与明确假设在云端或其他合适算力重新打开 4B 微调）；第三阶段（当前阶段，证明系统真的有效，S0～S6 + I7 架构进阶（Mini MoE / MLA / MTP 主线必修）+ V5/V6 版本主线 + Mini-Serving 手搓推理引擎主干实践 + S2.5 长上下文选修，共 10 个里程碑，里程碑尚未启动）覆盖性能基线、架构进阶（MoE / MLA / MTP）、源码地图、手搓推理引擎、算子优化、稀疏架构与低秩表示、分布式训练与稳定性、专家并行、生产 Serving、长上下文记忆与推理协同与综合验收；第四阶段（证明模型能力真的变强了）聚焦 Agentic 后训练与能力形成，并含 V4 Pro vs Flash 架构选型研究；第五阶段沉淀 Skill 工程与工具生态；第六阶段构建多角色协作与 Agent Team 软件交付沙盘。"
[cover]
    image = "covers/lvchat-roadmap.jpg"
    alt = "lvchat 实现导图"
    hiddenInSingle = true
    hiddenInList = true
+++

{{< roadmap_overview
    north_star="构建并持续演进可对话的小模型及其工程系统，贯通数据、训练、后训练、推理、评估与服务；用可复现、可对照、可解释的证据说明每一代版本的能力、成本与边界。"
    north_star_archived="用纯 PyTorch 交付一个可对话的 355M 模型，并打通从数据到 WebUI 的全链路。"
    phases="phase-01::STAGE 01 · 第一阶段::从零手搓 LLM::done::2026.10.13 → 2026.11.04 (M0～M6 已完成) | phase-02::STAGE 02 · 第二阶段::现代架构与模型承接::done::2026.11.04 → 2026.11.27 · I0～I6 收官 (I6 真实修复暂缓待复入) | phase-03::STAGE 03 · 第三阶段::工业级训练、推理与分布式系统::active::当前阶段 · S0～S6 + I7 架构进阶 + V5/V6 版本主线 + Mini-Serving + S2.5 · 10 个主里程碑尚未启动 | phase-04::STAGE 04 · 第四阶段::后训练与领域能力形成::planning::规划中 · Agentic 后训练/能力形成/V4 Pro–Flash 选型/M7 个人语料 | phase-05::STAGE 05 · 第五阶段::Skill 工程与工具生态::planning::远期 · 扫描/排查/MCP/开源规范 | phase-06::STAGE 06 · 第六阶段::Agent 与多模型协作::planning::远期 · 多角色分工与编排闭环 · Agent Team 交付沙盘"
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
    next="第二阶段 I0～I6 已收官（I6 真实修复目标暂缓待复入），当前阶段第三阶段"
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
    season="STAGE 02 · 第二阶段（已收官）"
    title="现代架构与模型承接（全量展开 I0 ～ I6）"
    phase_state="done"
    start_date="2026年11月04日"
    end_date="2026年11月27日"
    repo="squid-llms"
    proposal_title="diy-llm 立项书"
    proposal_url="/llm/diy-llm-proposal/"
    theory_title="DataWhale diy-llm 教程"
    theory_url="https://datawhalechina.github.io/diy-llm/%E5%89%8D%E8%A8%80.html"
    rules="阶段定位::证明结构写对了——I0～I3 最小结构验证、I4 后训练与 I5 评估校准里程碑收官，I6 领域后训练收官（真实 Defects4J 修复目标暂缓待复入）；系统级性能、分布式与 Serving 留待第三阶段 | 装备来源::剥离自第一阶段的全部工业级选修项 + 第一阶段实测暴露的工程与模型边界 | 理论蓝本::以 DataWhale diy-llm（CS336 中文本土化 16 章 + 6 作业）为系统理论蓝本，按需调用 | 进化目标::新建独立 model_v3 / v4 承接现代架构与 Qwen 权重，并按 I0～I6 主线逐件升级数据、训练、推理与后训练"
    done="7"
    total="7"
    current="I6 · 领域后训练与可复现打榜（2026-11-27 收官，真实修复目标暂缓待复入）"
    delivered="I0～I5 主线及 CUDA、ModelV4 / Qwen3 番外已交付；完成多轮 SFT、CoT-SFT、DPO、LoRA / 全参对照、RLVR / GRPO 最小更新，以及人工盲评、位置校准、多评委对照、paired bootstrap 与 I0～I4 注册范围一键回归报告。I6 建立 Defects4J 全链路并完成方法 / 样本量 / 轮数 / rank 对照、0.6B 收官、原始 4B 基座复测与 120 题同题基线；真实 Defects4J 稳定最小修复目标未完成，暂缓待复入。"
    next="第三阶段 S0 · GPU 系统基础与性能基线（I6 真实修复目标暂缓待复入，见 I6 卡片）"
    steps="i0:I0:现代架构:done, i1:I1:数据与流式IO:done, i2:I2:训练与算子加速:done, i3:I3:量化与投机推理:done, i4:I4:CoT与偏好对齐:done, i5:I5:评委校准CI:done, i6:I6:领域后训练打榜:done"
>}}

## 第二阶段施工流水线：现代架构承接与 AI-Infra 全量里程碑（I0 → I6）

> 第一阶段解决“**有没有一辆自己造的车**”，第二阶段以 [DataWhale `diy-llm`](https://datawhalechina.github.io/diy-llm/%E5%89%8D%E8%A8%80.html) 为系统理论蓝本，解决“**怎么把 GPT-2 时代的老爷车改装成现代工业级大模型**”。每一站都直接改造 `squid-llms` 里的对应模块，用前后对照实验说话。

{{< milestone id="i0" code="I0" title="现代架构与模型承接（model_v3：RoPE + RMSNorm + SwiGLU + GQA + Qwen 权重加载）" status="done" date="2026-11-06" note1_title="笔记 14：RoPE 先行闭环" note1_url="/llm/llm-14-eval-resume/" note2_title="笔记 17：model_v3 承接 Qwen" note2_url="/llm/llm-17-model-v3-qwen/" summary="新建独立 `model_v3` 并完成 `Qwen2.5-0.5B` Base/Instruct 权重承接、chat template、Chat Server 与本地实验台；Qwen 专项 `7 passed`、全量 `46 passed`（已严格限定受控对齐与 GQA 理论存储边界）。" >}}
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

{{< milestone id="i1" code="I1" title="工业数据工程与流式 IO（Data Pipeline & Scaling）" status="done" date="2026-11-10" note1_title="笔记 18：I1，让语料从文本流向可训练数据" note1_url="/llm/llm-18-i1-data-pipeline/" summary="完成 38+2 文档隔离、JSONL + `uint32` token store、`np.memmap` 按需切片（Python 分配降至 `1,766` bytes）、5 步训练冒烟及 held-out `BPB=4.9495` 与 Chinchilla 基线测算。" >}}
- **进化部位**：改造 `squid/data/` 与 `squid/tokenizer/`
- **已完成成果**：
  1. **可追溯语料管线**：建立 42 条源文档清单与类型区分，保留 39 篇 article + 1 篇 profile 为 40 个候选，固定 38 条训练候选与 2 篇 held-out；最小 Markdown 清洗通过 `5 passed`；
  2. **JSONL 与 uint32 token store**：一行一篇文档，标题 + 正文进入编码，逐篇追加 EOS，记录正文与实际编码文本 hash、offset 和 length；生成 train `117,890` tokens、held-out `5,485` tokens；
  3. **memmap 按需读取**：token 二进制与旧 `pack_tokens()` 逐元素一致，新旧 Dataset 在 stride 64/128 下样本一致；同输入 117,890 tokens、921 窗口时，Python 当前分配由旧版 `2,004,496` bytes 降为 memmap `1,766` bytes；
  4. **训练与指标基线**：完成 5 步小模型训练、checkpoint 保存重载与前向一致性；算出 held-out 冒烟 `BPB=4.9495`，完成参数量、token 量与 Chinchilla 参考基线测算。
- **diy-llm 结合**：[diy-llm](https://datawhalechina.github.io/diy-llm/%E5%89%8D%E8%A8%80.html) 第 2 章（分词器进阶）+ 第 11 章（数据工程）+ 第 9 章（Scaling Laws）+ 作业 1 & 作业 5
- **边界与后续扩展**：本次为自有博客的小语料最小闭环；GB 级实测、多源语料配比、MinHash 近似去重、清洗前后及 GPT-2 / model_v3 的完整 BPB 对照留待真实数据需求与后续实验，不作为当前阻塞项。
{{< /milestone >}}

{{< milestone id="i2" code="I2" title="训练加速与显存压榨（AMP + SDPA + Compile + Checkpointing）" status="done" date="2026-11-10" note1_title="笔记 19：I2，训练加速与显存压榨" note1_url="/llm/llm-19-i2-environment-probe/" summary="在 Mac/MPS 完成 FP32/FP16/BF16、SDPA、`torch.compile`（`+7.27%`）与 Activation Checkpointing（驱动分配降 `8 MiB`）三轮对照；收官回归 `16 passed`。" >}}
- **进化部位**：改造 `squid/train/` 与注意力算子
- **已完成成果**：
  1. **混合精度（AMP）**：完成 FP32 / FP16 / BF16 探针与三轮训练对照；中位数分别为 `11001.65 / 9892.09 / 9942.47` tokens/s，当前 Mac/MPS 小模型未体现混合精度吞吐收益，loss 无 NaN/Inf；
  2. **SDPA**：增加可切换的 eager/SDPA 路径并保留 causal mask 语义；小模型 CPU prefill/decode 对照通过，MPS 训练吞吐中位数 `10613.57` tokens/s，未体现收益；FlashAttention 不预设已使用；
  3. **torch.compile**：稳态训练吞吐中位数 `11801.10` tokens/s，相对 eager FP32 基线约提升 `7.27%`；首次编译成本不计入稳态测量；
  4. **Activation Checkpointing**：logits、loss 与反向梯度对照通过；吞吐中位数下降约 `5.36%`，驱动分配内存减少 `8 MiB`，当前分配内存不变，体现用计算换显存的代价与收益。
- **收官回归**：相关测试 `16 passed in 33.02s`，覆盖 Qwen 专项、SDPA、checkpointing、Markdown、token store 与 memmap Dataset，不调用外部评估 API。
- **diy-llm 结合**：[diy-llm](https://datawhalechina.github.io/diy-llm/%E5%89%8D%E8%A8%80.html) 第 3 章（混合精度与算术强度）+ 第 6～7 章（GPU 架构与算子优化）+ 作业 3
- **边界与后续对照**：当前结果仅适用于 Mac/MPS、小模型和已记录的测量配置；Windows + RTX 4070 Ti 的 CUDA 硬件对照与峰值显存统计已于下方 `I2 番外` 完成，MFU 与经典 GPT-2 / `model_v3` 的额外吞吐对照留待第三阶段 `S0` 深入。
{{< /milestone >}}

{{< milestone id="i2-windows" code="↳ I2 番外" title="I2 番外：Windows + RTX 4070 Ti CUDA 对照复测" status="done" status_label="✓ 已验收（番外）" sub="true" date="2026-11-11" note1_title="笔记 20：CUDA 对照" note1_url="/llm/llm-20-i2-windows-cuda/" question="在 Windows 台式机的 RTX 4070 Ti 上复跑同一批 I2 训练实验，作为 Mac/MPS 之外的 CUDA 硬件对照（比较不同硬件与计算后端下的性能、显存与正确性表现，非推翻 Mac 结果）。" summary="打通 SSH + WSL2 + RTX 4070 Ti 远程链路并根除 `typing` 遮蔽编译崩溃；完成 6 组 CUDA 三轮对照（`compile` 稳态 `+17.27%`）及 `allocated/reserved` 峰值显存与 MPS 横向观察。" >}}
- **环境与排障闭环**：打通 `Mac → SSH → Windows → WSL2 (Ubuntu 24.04) → RTX 4070 Ti (12 GB, PyTorch 2.14.1+cu130)` 远程实验链路，锁定同一代码提交、Python `3.12.12` 与同一份 token store（train `117,890` / held-out `5,485` tokens）；通过 Inductor worker 日志定位并根除 `matplot → pyloco → typing 3.10.0.0` 遮蔽标准库导致的并行 `torch.compile` 崩溃，补齐 CUDA 同步计时与 `allocated / reserved`（`current / peak`）显存口径。
- **CUDA 三轮正式对照**（同 2 层小模型、`batch=2`、`context=128`、2 步 warmup + 10 步测量，取三轮中位数）：
  1. `FP32 / eager`：吞吐中位数 `21614.87` tokens/s，峰值分配 `691.67 MiB`，峰值预留 `854 MiB`；
  2. `BF16 / AMP` vs `FP16 / AMP`：BF16 吞吐 `22002.51` tokens/s（`+1.79%`），峰值分配降至 `635.55 MiB`（`-56.12 MiB / -8.11%`），但缓存分配器峰值预留升至 `876 MiB`（`+22 MiB`）；FP16 吞吐 `20954.75` tokens/s（`-3.05%`）；
  3. `SDPA + FP32`：吞吐 `21588.02` tokens/s（`-0.12%`，基本持平），峰值分配 `690.81 MiB`、峰值预留 `852 MiB`（仅验证调用 SDPA，未确认实际落入 FlashAttention kernel）；
  4. `compile + FP32`：稳态吞吐中位数 `25346.90` tokens/s（相对 FP32 基线提升约 **`17.27%`**），峰值分配 `690.85 MiB` 基本持平，峰值预留首轮 `778 MiB`、后两轮 `852 MiB`；
  5. `checkpointing + FP32`：吞吐中位数 `17140.50` tokens/s（下降约 `20.70%`），峰值分配 `687.53 MiB`（仅减少 `4.14 MiB / 0.60%`），当前小模型无显存瓶颈，重算代价大于显存收益。
- **MPS / CUDA 横向观察与边界**：同一配置下 RTX 4070 Ti 吞吐约为 Mac/MPS 的 `1.6x ～ 2.2x`，`compile` 在两边均体现稳态收益（MPS `+7.27%` vs CUDA `+17.27%`）；结果仅代表当前两台设备的小模型短步测量（首次编译成本未摊入稳态吞吐，不伪造跨设备峰值显存对照），更大模型/长上下文、SDPA 具体后端确认、MFU 及 GPT-2 / `model_v3` 额外吞吐对照尚未覆盖。
{{< /milestone >}}

{{< milestone id="i3" code="I3" title="高性能推理与服务引擎（量化 + 投机解码 + 流式 Serving）" status="done" date="2026-11-13" note1_title="笔记 21：I3 推理与服务" note1_url="/llm/llm-21-i3-inference-baseline/" summary="完成推理基线、增量 prefill 掩码修复、会话级 KV Cache 与滑动裁剪、INT8 / INT4 权重量化、贪心投机解码、SSE 流式输出与多会话隔离，并实测 MHA / GQA KV 占用与 CUDA 同口径复测；量化与投机当前均未提速，保留教学路径边界。" >}}
- **进化部位**：承接 M3 / M6 遗留的服务层进阶项，改造 `squid/generate/` 与对话服务层
- **已完成成果（2026-11-11 → 2026-11-13，详见[笔记 21](/llm/llm-21-i3-inference-baseline/)）**：
  1. **推理基线**：拆分 Prefill / Decode，实测 TTFT、decode tokens/s、KV Cache 实际字节数与设备内存；
  2. **增量 prefill 修复**：修复 v1 / v2 多 token 增量 prefill 的掩码偏移；
  3. **会话级 KV Cache**：token 预算管理、v3 滑动裁剪与位置进度；
  4. **INT8 / INT4 权重量化**：packing / unpacking，W8A32 / W4A32 与 W8A16 / W4A16 对照；
  5. **贪心投机解码**：Draft / Target 接受、修正、bonus 与双方 cache 回滚同步；
  6. **SSE 流式输出**：连接中断状态失效与浏览器流式渲染；
  7. **多会话管理**：状态隔离与有界 LRU，新建会话、切换会话与历史恢复入口；
  8. **MHA / GQA 实测**：实际 KV 占用、量化叠加投机与 TTFT、CUDA 同口径复测。
- **真实结果与结论**：
  - KV Cache decode 提速 Mac 基线约 `1.73x`，CUDA 当前短 prompt 约 `1.06x`，收益依设备而变；
  - GQA 实际 KV Cache 为 MHA 的 `1/7`（减少 `85.71%`），张量字节数与设备增量一致；
  - INT8 持久张量减少 `54.26%`，当前 heldout PPL 损失较小；INT4 减少 `63.31%`，但当前逐行实现质量损失显著；
  - 当前量化路径在 Mac / CUDA 上均未提速，CUDA 的相对反量化开销通常更小；
  - 贪心投机在 FP32 下保持 Target 逐 token 一致，但 k=2 / 4 / 8 均为负收益，接受率依次为 `48.48% / 33.93% / 20.41%`；
  - BF16 在 Mac k=2 与 CUDA k=4 上出现输出不一致，严格数值等价性尚不稳定，相关性能结果不作为正确性验收通过；
  - FP16 PPL 异常定位为 RMSNorm 的 FP16 平方溢出，改为 FP32 累积后 PPL 与生成恢复正常；
  - SSE、多轮对话、多会话新建 / 切换与历史恢复已由用户真实验收。
- **收官回归**：当前学习范围相关回归由用户实际运行达到 `44 passed`；不同阶段的测试数字不累加为一次全量回归。
- **diy-llm 结合**：[diy-llm](https://datawhalechina.github.io/diy-llm/%E5%89%8D%E8%A8%80.html) 第 10 章（推理加速：KV Cache 进阶、量化、投机解码）
- **边界与后续**：
  - 当前量化与投机实现均为教学路径，不代表生产 kernel 或生产 Serving；
  - 预分配 KV Cache 后移，动态 `torch.cat` 尚未消除；
  - 严格采样投机、自适应 lookahead、融合量化 kernel 尚未实现；
  - 多会话请求当前串行，不是并发模型推理；
  - 实际量化文件大小、多任务质量评测尚未覆盖；
  - 滑动窗口细节与 INT4 pack / unpack 仍需独立复盘；
  - 功能跑通不等于所有内容已经吃透。
{{< /milestone >}}

{{< milestone id="i3-model-v4" code="↳ I3 番外" title="I3 番外：模型兼容性审计与 ModelV4（面向 Qwen3）" status="done" status_label="✓ 已验收（番外）" sub="true" date="2026-11-13" note1_title="笔记 22：Qwen3 兼容性" note1_url="/llm/llm-22-qwen3-compatibility/" question="面对一个陌生模型时，如何系统判断当前代码能否加载、还缺哪些结构与工程能力，并以 Qwen3-0.6B Dense 为最小案例在隔离的 V4 中实现 ModelV4？" summary="选修番外（已验收，不计入主线）：完成 config / safetensors / 官方 forward 兼容性审计，从零实现完全隔离的 V4（显式 head_dim=128、QK RMSNorm、Qwen3 配置 / 权重映射）；Qwen3-0.6B Dense 在 CPU / FP32 / eager 下通过官方 logits、连续 cache decode 与固定生成对照，并接通本地 thinking 对话与流式修复。结论限定单模型与受控环境，不代表 Qwen3 全系列。" >}}
- **定位说明**：面向模型承接能力的选修番外，已验收；不计入第二阶段 `I0～I6` 主线完成度（主线 `7/7` 收官，I6 真实修复目标暂缓待复入）。`V3` 继续作为 Qwen2.5-0.5B / 0.5B-Instruct 的稳定对照，`V4` 独立承接 Qwen3-0.6B。
- **已完成成果（详见[笔记 22](/llm/llm-22-qwen3-compatibility/)）**：
  1. **V4 独立实现**：新建 `src/squid/model/v4_qwen3/`、独立加载器 `src/squid/checkpoints/qwen3.py`、独立测试 `tests/test_qwen3/`；RMSNorm、SwiGLU、RoPE、Attention、TransformerBlock、GPTModelV4 全部重新实现，没有复制或 import V3 的模型实现；RMSNorm 带入 FP32 累积修复，避免重新引入 FP16 平方溢出。
  2. **Qwen3-0.6B 兼容性审计**：完成 config、safetensors 权重键、形状与官方 forward 语义审计，新增可复用检查能力 `src/squid/checkpoints/inspect.py`（只读元数据，最小回归 `1 passed`）；支持显式 `head_dim=128`、16 Q heads、8 KV heads、QK RMSNorm；checkpoint 中 embedding 与 lm_head 虽重复保存，实测逐元素完全一致（`torch.equal=True`），加载后共享一份参数。
  3. **官方数值与生成验收**：条件为 Qwen3-0.6B、CPU、FP32、eager、固定英文 prompt；最大 logit 差异 `4.1008e-05`、平均 `4.3524e-06`，`allclose(1e-4)=true`、top-1 一致；连续 3 次 cache decode 与官方 token 一致；固定 8-token 贪心生成的 token IDs 与文本完全一致。
  4. **本地对话与流式修复**：`chat_server` 与 Web UI 切换到 V4 / Qwen3-0.6B（后训练对话模型，非 Base）；支持 thinking 开关、思考区折叠与正式回答分离；修复流式中思考区跑到正文下方（明确 DOM 顺序）与临时 `U+FFFD` 被提前推送导致的中文乱码（不稳定前缀暂缓推送）；默认 `context_size=8192`、`max_new_tokens=1024`，保留 `LVCHAT_CONTEXT_SIZE` / `LVCHAT_MAX_NEW_TOKENS` 覆盖；SSE done 事件新增 `finish_reason` / `generated_tokens` / `max_new_tokens`，`finish_reason=length` 时页面明确提示回答可能不完整；1024 下同一注意力机制问题完整生成到总结，清理后历史回答重新编码为 `585` tokens；临时 16-token 实验已真实验证截断提示。
- **本轮回归与边界**：本轮对话修复相关指定回归 `10 passed`，JavaScript `node --check` 通过；这只是本轮指定回归集合，不是全量测试，不与早期 `13 passed` 或 I3 主线收官 `44 passed` 相加，也不覆盖 I3 主线原有记录。
- **能力边界**：
  - 当前只验收 `Qwen3-0.6B Dense`，不代表 Qwen3 全系列；不包含 MoE、GGUF、NVFP4 或 27B；
  - 数值对齐结论限定于当前输入及 CPU / FP32 / eager，不扩大为所有设备、dtype 或任意生成过程；
  - 本地对话功能通过不等于模型回答质量稳定（小模型仍有算错、重复耗尽预算等情况），不用工程测试替模型能力背书；
  - 当前服务仍不是生产级并发推理系统；上下文与生成预算是本地实验配置，因果掩码平方级开销与 KV Cache 增长尚未做长上下文性能优化。
{{< /milestone >}}

{{< milestone id="i3-qwen-lineage" code="↳ 番外子任务" title="Qwen 谱系表：建立自己的技术脉络坐标系" status="planning" status_label="规划中 · 选修子任务（不阻塞主线）" sub="true" question="看到某个 Qwen 模型的 config、权重键和 tokenizer 时，能否判断它位于哪一代、继承了什么、新增或删除了什么，以及这些变化服务于什么目标？" summary="I3 番外下的规划中选修子任务：建立 Qwen 技术演进的个人坐标系（非对外展示或营销）。以 Qwen2.5-0.5B（V3 已验证）与 Qwen3-0.6B Dense（V4 已验收）为锚点，逐代扩充覆盖结构、规范化、位置编码、模板与 thinking 的谱系表并保留官方来源；当前只建立谱系与学习计划，不宣称已下载、已加载或已实测所有模型。" >}}
- **定位说明**：`i3-model-v4` 下的规划中选修子任务，目的是建立个人技术坐标系而非对外展示或营销——看到某个模型的 config、权重键和 tokenizer 时，能知道它位于哪一代、继承了什么、新增或删除了什么，以及这些变化服务于什么目标；不计入第二阶段 `I0～I6` 主线完成度，不阻塞主线推进。
- **表格字段（每代 / 每个代表模型至少覆盖）**：
  - 世代 / 代表模型与参数规模；
  - 层数；
  - Q heads、KV heads、head_dim；
  - Dense / MoE（若为 MoE，补充 experts 与激活专家数）；
  - 最大上下文（单位明确为 tokens，不是字符）；
  - 规范化方式：RMSNorm、Pre-Norm、是否存在 QK RMSNorm；
  - 位置编码：RoPE、rope_theta、rope scaling / 其他变体；
  - chat template、特殊 token、是否支持 thinking 及其开关；
  - 相对上一代新增 / 删除了什么；
  - 为什么这样变化。
- **内容组织要求**：
  1. 不只按“代”给一行就掩盖同代不同尺寸的差异；层数、head 配置与上下文可能随具体型号变化，应注明代表模型或给出明确范围；
  2. 优先使用 Qwen 官方模型卡、官方 `config.json`、官方源码与发布说明，并保留来源链接；
  3. 当前已知学习锚点：`Qwen2.5-0.5B / 0.5B-Instruct`（V3 已验证）、`Qwen3-0.6B Dense`（V4 已验收）；视频中的“Qwen3.8 27B”属于社区 / 定制模型内容，不能未经官方证据写成 Qwen 官方新世代；
  4. 某代若同时包含 Dense 与 MoE，应分开标注，不把 MoE 当成整代所有模型的统一结构；
  5. “新增 / 删除 / 为什么”必须区分三类证据：官方明确说明的设计动机、从 config / 源码可确认的结构事实、尚无官方解释的推测；没有证据的“为什么”写“官方未说明”，不编造设计意图；
  6. 上下文长度、模板与 thinking 要区分：模型结构支持的上下文、当前本地实验使用的上下文、官方生成配置或 chat template 默认行为；
  7. 当前只建立谱系与学习计划，不虚构已下载、已加载或已实测所有模型。
- **希望形成的学习产出**：
  - 一张可逐代扩充的 Qwen 谱系表；
  - 每个代表模型的官方来源；
  - 一段“从 Qwen 到 Qwen3 的演进主线”；
  - 一组与 ModelV4 兼容性审计直接相关的观察点：head_dim、QK RMSNorm、GQA / MoE、RoPE、权重绑定、chat template / thinking。
- **官方来源入口（建表时逐一核对并扩充）**：
  - [Qwen Hugging Face 组织](https://huggingface.co/Qwen)；
  - [Qwen2.5-0.5B 模型卡](https://huggingface.co/Qwen/Qwen2.5-0.5B)（V3 锚点）；
  - [Qwen3-0.6B 模型卡](https://huggingface.co/Qwen/Qwen3-0.6B)（V4 锚点）；
  - [QwenLM Qwen3 仓库](https://github.com/QwenLM/Qwen3)。
{{< /milestone >}}

{{< milestone id="i4" code="I4" title="后训练深水区：多轮对话 SFT、CoT 思维链与 DPO / GRPO 对齐" status="done" date="2026-11-17" note1_title="笔记 26：I4 后训练收官" note1_url="/llm/llm-26-i4-post-training-recap/" summary="完成多轮 Assistant-only mask、SFT 与训练干预、CoT-SFT、DPO 批量训练、LoRA / 全参对照、RLVR / GRPO 单组更新、同题规则胜率与真实 Web UI 回归。I4 作为学习里程碑收官，但没有证明任何方法全面优于原始模型。" >}}
- **进化部位**：承接 M4 与 M6 暴露的“多轮旧答案复制”边界，升级 `squid/data/instruct.py` 与 `squid/train/`
- **已完成成果（详见[笔记 23](/llm/llm-23-i4-multiturn-sft/)、[笔记 24](/llm/llm-24-i4-cot-sft/)、[笔记 25](/llm/llm-25-i4-dpo-preference/) 与[笔记 26](/llm/llm-26-i4-post-training-recap/)）**：
  1. **多轮非 CoT SFT**：完成多轮 Assistant-only loss mask、Qwen 模板编码、Dataset 与 Batch padding；128 train / 32 val 合成数据；v2 冻结行为基线 `6/6`、独立验证 `30/32`；v1 出现名字与偏好能力回退，已完成同题对照与训练量干预。
  2. **CoT-SFT**：完成 CoT 数据协议与 Qwen 历史 CoT 可见性修复；160 条 CoT 数据、272 条显式算式审计；原始模型最终答案 `30/32`、完整 CoT `32/32`；`peak_lr=1e-6` 的 v2 为 `29/32` 正确、`32/32` 完整 CoT，数值更新 `16/16`、输出缩短但整体正确率未超原始模型；高学习率版本出现 CoT 丢失或结构性退化。
  3. **DPO**：完成 chosen / rejected、序列 logprob、score、loss、beta 与梯度更新；32 train / 8 val 合成偏好对、四类 rejected 均衡；16 个 Batch、`beta=0.1`、`LR=1e-7`、grad clip 1.0；val loss `0.628564 → 0.155683`、val score `1.3776 → 22.8115`；行为 `29/32` 正确、`32/32` 完整 CoT，输出缩短、推理算式错误减少但整体正确率未超原始模型。
  4. **LoRA / 全参数**：`rank=8`、`alpha=16`；可训练参数 `6,269,952`（约 1.05%）；adapter 约 25.2 MB、全参数 checkpoint 约 2.38 GB；LoRA 独立行为验证 `29/32`、全参数 v2 `30/32`；LoRA 体现明显参数效率与不同的能力保持取舍，不宣称 LoRA 全面更好或 rank=8 为最佳配置。
  5. **RLVR / GRPO**：完成可验证分层奖励、组内均值 / 标准差、相对优势、概率比裁剪与一次参数更新；使用 shaped reward v2；仅一组、一次序列级 GRPO 更新，未加入参考模型 KL；更新后最终答案 `30/32`、完整 CoT `32/32`、自然结束 `32/32`；不宣称 GRPO 已稳定提升能力。
  6. **总对照与回归**：同一 32 条 CoT 样本上原始模型 `30/32`、CoT-SFT v2 `29/32`、DPO v1 `29/32`、GRPO 单组更新 `30/32`；完成同题规则 win / tie / loss 及 `win_rate_all` / `decisive_win_rate`；相关回归实际运行 `30 passed`；这些不是 I5 校准后的 LLM 评委胜率。
  7. **真实 Web UI**：`chat_server` 支持 `LVCHAT_CHECKPOINT` 加载训练后模型；非 CoT SFT v2 两轮 Assistant 完全同文，非同文复制验收未通过；GRPO checkpoint 第二轮含正确历史名字且未复制第一轮，但存在“我叫小吕”的说话视角混淆；当前验收仅针对 V4 / Qwen3 Web UI，M6 旧 355M 模型未重新回归。
- **收官回归**：相关测试实际运行 `30 passed`；不与其它阶段测试数字累加为一次全量回归。
- **diy-llm 结合**：[diy-llm](https://datawhalechina.github.io/diy-llm/%E5%89%8D%E8%A8%80.html) 第 13 章（Pre-training / SFT / DPO 全流程）+ 第 14 章（GRPO / RLVR 强化学习）
- **能力边界（里程碑完成 ≠ 能力全面达成）**：
  - 这是学习里程碑完成，不是所有能力目标全面达成；实验主要基于 Qwen3-0.6B 与受控合成数据；
  - 没有证明 SFT、DPO 或 GRPO 全面提升通用能力；loss / score 改善不等于行为改善；
  - GRPO 只有一组、一次更新，未加入参考 KL；DPO 偏好数据不是人工标注；
  - 规则胜率不是校准后的 LLM 评委胜率（`I5` 已完成位置校准与多评委对照，见笔记 27，仍非普遍评委排名）；
  - Web UI 多轮表达仍有视角混淆；M6 旧 355M 模型未重新回归，不写成旧模型已彻底修复。
{{< /milestone >}}

{{< milestone id="i5" code="I5" title="评估校准与回归基准自动化（Judge Calibration）" status="done" date="2026-11-18" note1_title="笔记 27：I5 评估校准与回归基准" note1_url="/llm/llm-27-i5-judge-calibration-regression/" summary="完成人工盲评与三层评价协议、AB/BA 位置交换校准、无效填充与有效信息的长度控制、DeepSeek / Qwen4 Max 双评委对照、10 对独立 held-out、paired bootstrap 置信区间、I4 回归门禁，以及 I0～I4 当前注册范围的一键总报告；全量回归 173 passed。工程里程碑完成，但小样本与 inconclusive 边界保留。" >}}
- **进化部位**：承接 M5 评估流水线，升级 `squid/eval/`
- **已完成成果（详见[笔记 27](/llm/llm-27-i5-judge-calibration-regression/)）**：
  1. **人工评价与盲评协议**：建立 correctness / instruction / reasoning / clarity 四类原因编码；人工评价整理为任务结果 → 推理质量 → 信息密度三层递进；首批 8 对开发盲评保留匿名公开文件、私密 key、源哈希与标签写保护；新增 10 对独立 held-out 覆盖正确性、有效验算、无效填充、实质等价与指令遵循。
  2. **成对评委与位置校准**：完成 AB/BA 双顺序调用、结果坐标还原、严格解析、逐次落盘与断点续跑；区分 consistent / position_sensitive / decisive_flip / unresolved；接入 DeepSeek 与 Qwen4 Max 并保存原始结果与配置；双顺序稳定不等于与人工一致，未决样本不自动算平局或从总体描述中隐藏。
  3. **长度控制**：完成完全重复、无效填充变长、有效验算变长、错误且冗长四类控制条件；当前实验中没有双顺序共识选择更长回答；有效验算变长与无效填充变长分别解释，不把信息增量误判为长度偏见。
  4. **独立 held-out 与多评委**：DeepSeek 4 对人工一致 / 2 对稳定分歧 / 4 对未决；Qwen4 Max 6 对一致 / 4 对分歧 / 0 对未决；双方都有共识的 6 对结论全部相同；这些是少量合成样本的原始计数，不是普遍评委准确率或模型排名。
  5. **paired bootstrap 与 I4 门禁**：按 case 配对重采样 2000 次，生成 95% 区间与 6 组胜率矩阵；original / CoT-SFT v2 / DPO v1 / GRPO 单组更新共用同一 32 题；六组 net_win_rate 对照全部 inconclusive；I4 门禁 artifact_status=pass、regression_detected=False、evidence_status=inconclusive；不把「未检测到回退」写成「已经证明无回退」或「模型等效」。
  6. **I0～I4 注册范围一键报告**：为 I0 新增受控数值对齐 JSON（4/4 完整 logits、首末层 KV、3/3 cache decode 通过，固定 CPU / FP32 / eager 下受控张量最大差异为 0）；建立 8 组注册产物覆盖清单与统一总报告；缓存版与 --refresh-controlled 版均实际运行；受控刷新只重跑 I0/I4，I1～I3 始终读取历史测量；full_live_refresh=False；总状态 artifacts_valid_capability_inconclusive。
  7. **全量回归**：学习项目实际运行 `uv run pytest -q`，结果 `173 passed in 594.64s`；`git diff --check` 通过；笔记 27 的内容检查、Hugo 构建与封面生成均已通过。
- **diy-llm 结合**：[diy-llm](https://datawhalechina.github.io/diy-llm/%E5%89%8D%E8%A8%80.html) 第 12 章（评估与基准）+ 作业 6
- **能力边界**：
  - 主要是小模型、算术与多轮数值更新的受控合成样本；8 对开发样本与 10 对 held-out 都较小，不支持普遍评委排名或统计显著结论；
  - 人工标签来自单一标注者，代表当前个人评价口径；尚未进行有统计意义的人机相关系数分析，不为满足原规划硬算相关指标；
  - Qwen 与 DeepSeek 的推理方式及输出预算不同，行为差异不能全部归因于模型本身；没有同批 v1 / v2 对照，不宣称 v2 prompt 的因果提升；
  - 一键报告只覆盖当前注册范围（registered_scope_only），不等于 I0～I4 所有历史实验已完整接入；I1～I3 在总报告中仍是历史缓存，不是完整 live 回归；
  - I5 工程里程碑完成不代表已经独立掌握评估工程；后续独立复现、现成框架对照和更多任务评估属于回顾任务，不新增里程碑、不阻塞 I6。
- **与 I6 衔接**：I6 已按该边界定义 Java 缺陷定位与最小修复的评估协议（数据隔离、定位正确、编译成功、测试通过、基线与通用能力保持）并收官；loss 下降没有替代可验证的行为提升，真实 Defects4J 修复目标暂缓待复入（见 I6 卡片）。
{{< /milestone >}}

{{< milestone id="i6" code="I6" title="领域后训练与可复现打榜：Java 缺陷定位与修复" status="done" status_label="✓ 收官 · 真实修复暂缓待复入" date="2026-11-27" note1_title="笔记 31：I6-4 4B 基座对照" note1_url="/llm/llm-31-i6-4b-capability-boundary/" note2_title="0.6B Java 修复三天复盘" note2_url="/llm/llm-06b-java-three-day-repair-retro/" summary="第二阶段主线 capstone 收官（2026-11-27）：建立 Defects4J 数据、训练、结构化局部编辑、补丁应用、javac、触发测试与回归评估全链路，完成方法 / 样本量 / 轮数 / rank 对照与 0.6B / 4B 同题基线。收官不等于完成——真实 Defects4J 未见缺陷的稳定最小修复尚未达成；暂停本地高成本加码，目标暂缓待复入：第三阶段学习形成可证伪假设后，在云端或其他合适算力上重新评估 4B 微调。" >}}
- **收官范围**：建立 Defects4J 数据、训练、结构化局部编辑、补丁应用、javac、触发测试与回归评估链路；完成完整方法、结构化局部编辑、样本量（8/16/32）、训练轮数与 LoRA rank 对照；把输出契约、原文引用、补丁可应用、编译、行为通过和未见样本迁移分层区分，用真实行为而不是 loss 判断能力（见[笔记 28](/llm/llm-28-i6-java-defect-repair/)、[笔记 29](/llm/llm-29-i6-capability-layers-loss-boundary/)、[笔记 30](/llm/llm-30-i6-3-java-basics/)）。
- **0.6B 收官**：0.6B 当前路线收官，后续主要用于低成本管线 CI 与基础设施探针；不再为修复通过率在本地继续加 epochs 或样本成本。
- **4B 基座复测（不加载微调）**：J0 Java 基础生成从 0.6B 的 2/6 提升到 4B 的 5/6；static 开发集与最终集成对规则均为 4/4；Thermostat 微型修复通过合法 JSON、唯一替换、javac 编译与运行断言。0.6B / 4B 的 120 题同题基线（相同 Prompt、BF16、贪心解码、128 token 预算）人工能力矩阵：0.6B 核心正确 24 / 部分正确 34 / 关键错误 62，4B 核心正确 71 / 部分正确 24 / 关键错误 25；该结果只用于开发能力画像，不包装成通用 Java benchmark 排名，且 4B 是显著净收益、不是逐题严格更优。
- **资源分工**：0.6B 做管线 CI、4B 做能力假设验证、真实 Defects4J 做最终行为验收。
- **能力边界（收官 ≠ 完成）**：真实 Defects4J 未见缺陷的稳定最小修复目标尚未完成；微调路线证明的是契约学习与局部行为证据，不是修复泛化，也不是“微调路线全部失败”；公开排行榜提交仍只作可选后续，不以公开名次代替本地可复现验收。
- **暂缓待复入（长期目标保留）**：暂停当前本地高成本加码。复入顺序：第三阶段学习 → 积累新的机制、工具与实验方法 → 形成可证伪的 I6 训练假设 → 在明确预算下评估云端 4B 微调 → 用真实 Defects4J 做行为验收 → 将成功或失败证据带回学习与下一轮实验。云端 4B 微调尚未执行、也未验证有效，不预设分数或结论。
{{< /milestone >}}

---

## 第三阶段施工流水线：工业级训练、推理与分布式系统（S0 → S6 + I7 · 10 个主里程碑）

> **阶段定位**：从会写模型，进阶到理解工业级训练与推理系统；在自己的工程中完成最小机制实现，再对照 [DeepSeek `DeepInfer`](https://github.com/deepseek-ai/DeepInfer) 理解生产级系统设计。**本阶段为当前阶段（2026-11-27 I6 收官后切入；S0～S6、I7 与 V5/V6 里程碑仍规划中、尚未启动，不设固定排期，也不承诺学习周期；DeepInfer 尚未在本机部署或跑通）。**
>
> **推进顺序**：`I4 → I5 → I6 领域后训练与可复现打榜（已收官，真实修复暂缓待复入）→ S0 GPU 系统基础与性能基线 → I7 架构进阶（Mini MoE → MLA → MTP，主线必修）→ S1 → Mini-Serving 主干实践 → S2 → S2.5 长上下文（选修）→ V5 稀疏架构与低秩表示 → S3 分布式训练与稳定性 → S4 专家并行 → S5 生产 Serving → V6 长上下文记忆与推理协同 → S6 综合验收 → 第四阶段 Agentic 后训练与能力形成`。先建立可信的显存、吞吐与性能测量口径（S0），再验证 MoE / MLA / MTP（I7），避免把结构正确、缓存收益和实际性能混为一谈；Mini-Serving 主干实践与 S2.5 均为选修或实践子项目，不计入主线完成度；I7 计一个主里程碑，V5 / V6 为第三阶段正式版本里程碑，均计入该阶段里程碑总数（共 10 个）。I6 暂缓目标的复入回路：第三阶段学习 → 积累新的机制、工具与实验方法 → 形成可证伪的 I6 训练假设 → 在明确预算下评估云端 4B 微调 → 用真实 Defects4J 做行为验收 → 将证据带回学习与下一轮实验（见 I6 卡片）。

{{< roadmap_progress
    id="phase-03"
    season="STAGE 03 · 第三阶段（当前阶段）"
    title="工业级训练、推理与分布式系统（S0 ～ S6 + I7 + V5/V6）"
    phase_state="active"
    repo="squid-llms"
    theory_title="DeepSeek DeepInfer"
    theory_url="https://github.com/deepseek-ai/DeepInfer"
    rules="阶段定位::证明系统真的有效——性能基线、I7 架构进阶（Mini MoE / MLA / MTP 主线必修，计一个主里程碑，置于 S0 之后）、手搓推理引擎主干实践（Mini-Serving）、分布式训练与稳定性、专家并行与生产 Serving，并以 V5 稀疏架构与低秩表示、V6 长上下文记忆与推理协同完成正式版本演进；在自己的工程中完成最小机制实现，再对照 DeepInfer / vLLM / SGLang 理解生产级系统设计 | 前置依赖::第二阶段 I0～I5 相关基础已完成，具备 Python / PyTorch / Transformer 与训练推理链路知识，Linux GPU 实验环境按阶段需要继续扩展；I7-A Mini MoE 为 V5 与 S4 专家并行的必要前置；V5 承接 I7 与 S0～S2，V6 承接 S5 / Mini-Serving / I3 | 硬件与验收边界::Mac + MPS 不作为 DeepInfer 部署验收环境；DeepInfer 要求 NVIDIA SM100 或 Ascend 950，源码研读不依赖本机部署，官方部署验证仅作匹配硬件后的选修"
    done="0"
    total="10"
    unit="规划里程碑（尚未启动）"
    delivered="尚未交付；S0～S6、I7 与 V5 / V6 均为规划里程碑"
    next="S0 · GPU 系统基础与性能基线（规划起点）"
    planning_note="当前阶段 · I6 收官后切入；S0～S6、I7 与 V5/V6 仍规划中、尚未启动，按 S0 → I7 架构进阶 → S1 → Mini-Serving → S2 → S2.5 选修 → V5 → S3 → S4 → S5 → V6 → S6 推进；I6 真实修复目标待本阶段形成可证伪假设后在云端 4B 复入（见 I6 卡片）"
    steps="s0:S0:性能基线:planning, i7:I7:架构进阶:planning, s1:S1:源码地图:planning, s2:S2:算子优化:planning, v5:V5:稀疏架构与低秩表示:planning, s3:S3:分布式训练:planning, s4:S4:MoE并行:planning, s5:S5:推理调度:planning, v6:V6:记忆与推理协同:planning, s6:S6:稳定性验收:planning"
>}}

{{< phase_drawer open="true" variant="planning" summary="规划蓝图（当前阶段 · 里程碑尚未启动） · 点击收起/展开第三阶段前置依赖、S0～S6、I7 与 V5/V6 共 10 个主里程碑、Mini-Serving 主干实践、S2.5 长上下文选修与总交付目标（点击上方节点可直接跳转）" >}}

{{< milestone id="s-pre" code="前置条件" title="第三阶段前置依赖与硬件环境边界" status="planning" question="进入工业级训练、推理与分布式系统之前，必须先满足哪些基础与硬件边界？" note1_title="DeepInfer 仓库" note1_url="https://github.com/deepseek-ai/DeepInfer" summary="明确 `I0～I5` 前置基础、Linux GPU 实验环境、Mac/MPS 非部署环境边界，以及 DeepInfer 对 SM100 / Ascend 950 的硬件约束。" >}}
1. **第二阶段 `I0～I5` 的相关基础（均已完成）**：
   - 现代模型结构与 Qwen 权重承接（`I0` 已完成）；
   - 数据与流式 IO（`I1` 已完成，见[笔记 18](/llm/llm-18-i1-data-pipeline/)）；
   - 训练加速与资源核算（`I2` 及 RTX 4070 Ti CUDA 番外已完成，见[笔记 19](/llm/llm-19-i2-environment-probe/) 与[笔记 20](/llm/llm-20-i2-windows-cuda/)）；
   - KV Cache、量化、投机解码和基础推理指标（`I3` 已完成，见[笔记 21](/llm/llm-21-i3-inference-baseline/)）；
   - 多轮 SFT、CoT-SFT、DPO、LoRA / 全参对照与 RLVR / GRPO 最小更新（`I4` 已完成，见[笔记 26](/llm/llm-26-i4-post-training-recap/)）；
   - 人工盲评、位置校准、多评委对照、paired bootstrap 与注册范围一键回归报告（`I5` 已完成，见[笔记 27](/llm/llm-27-i5-judge-calibration-regression/)）。
2. **知识储备**：具备 Python、PyTorch、Transformer 和基础训练/推理链路知识。
3. **实验环境**：已打通 Windows + WSL2（Ubuntu 24.04）+ RTX 4070 Ti 单卡 CUDA 实验环境（见[笔记 20](/llm/llm-20-i2-windows-cuda/)），真实多卡与底层算子实验按后续阶段需要继续扩展。
4. **本地环境边界**：当前 Mac + MPS 环境不作为 [DeepInfer](https://github.com/deepseek-ai/DeepInfer) 部署验收环境。
5. **DeepInfer 硬件边界说明**：[DeepInfer](https://github.com/deepseek-ai/DeepInfer) 官方目前要求特定的 NVIDIA SM100 或 Ascend 950 环境，因此：
   - **源码研读不依赖本机部署**；
   - **官方部署验证只作为具备匹配硬件后的选修**；
   - **不把普通 GPU 上无法运行 DeepInfer 写成学习失败**。
{{< /milestone >}}

{{< milestone id="s0" code="S0" title="GPU 系统基础与性能基线" status="planning" question="优化之前，能不能先建立一张可信的性能与资源账本？" summary="建立 GPU 硬件、Roofline 瓶颈与 `torch.profiler` 基础认知，交付统一 benchmark 入口；把 GPT-2、`model_v3`、V4 与 Mini MoE / MLA / MTP 纳入同口径基线，区分 FLOPs 与实际耗时、理论 KV 与设备占用、总参 / 激活参数与显存。" >}}
- **学习内容**：
  - CPU / GPU、Host / Device、SM、Warp、HBM 与内存带宽；
  - 算术强度、Roofline、计算瓶颈与带宽瓶颈；
  - FP32 / FP16 / BF16 的精度与资源差异；
  - `torch.profiler`，按需了解 Nsight 等工具；
  - warmup、重复测量、均值、P50/P95、方差与可复现 benchmark；
  - TTFT、TPOT、tokens/s、峰值显存、MFU 等指标。
- **规划交付物**：
  - 一套统一的训练与推理 benchmark 入口；
  - 经典 GPT-2、`model_v3`、V4 与 Mini MoE / MLA / MTP 的固定输入性能基线；
  - 每次实验记录设备、dtype、batch、上下文长度、warmup 和重复次数。
- **规划验收标准**：
  - 同一场景可重复测量；
  - 区分 FLOPs 与实际耗时，不把理论计算量当成实测速度；
  - 区分理论 KV 大小与设备实际占用，区分总参数、激活参数与显存占用；
  - 结果包含资源与正确性数据，不只报告“变快了”；
  - 性能测试与数值正确性测试分开，不用速度掩盖错误，也不把结构上的效率直接写成实测提速。
{{< /milestone >}}

{{< milestone id="i7" code="I7" title="I7 架构进阶：Mini MoE + MLA + MTP" status="planning" status_label="规划中 · 第三阶段主线必修" summary="第三阶段主线必修节点（计一个主里程碑，内部 I7-A/B/C 三个子任务均必修、不分别计数）：在 S0 建立可信测量口径后，按 I7-A Mini MoE → I7-B MLA → I7-C MTP 顺序逐一验证现代结构写对了；I7-A 为 V5 与 S4 的必要前置；不预设小模型提速，不在 I7 内提前引入分布式或生产 Serving。" >}}
- **定位说明**：第三阶段主线必修（不再作为第二阶段遗留选修）：计一个主里程碑，置于 S0 之后、S1 / V5 之前；先建立可信的显存、吞吐与性能测量口径，再验证 MoE / MLA / MTP，避免把结构正确、缓存收益和实际性能混为一谈。
- **三个子任务（依次推进，均必修）**：
  1. **I7-A Mini MoE**：Top-K 路由、Shared Expert 与负载均衡，验证路由正确、负载可观察；
  2. **I7-B MLA**：KV 低秩压缩进 Cache、上投影与 RoPE 兼容，对照 MHA / GQA；
  3. **I7-C MTP**：多 token 预测辅助头与训练损失，推理与目标模型贪心路径一致。
- **前置关系**：I7-A Mini MoE 是 V5 稀疏架构与 S4 专家并行的必要前置；I7-B / I7-C 同样不得默认为可跳过。必修化不意味着先做分布式、生产部署或性能优化。
- **diy-llm 结合**：[diy-llm](https://datawhalechina.github.io/diy-llm/%E5%89%8D%E8%A8%80.html) 第 5 章（MoE 混合专家模型）；MLA / MTP 结合官方论文与源码按需调用。
- **边界**：本节点只做结构最小验证，不要求小模型提速，不在此引入分布式；DDP / ZeRO / FSDP 与 Expert Parallel 的详细内容见 `S3` / `S4`，生产部署见 `S5`。
{{< /milestone >}}

{{< milestone id="i7-moe" code="↳ I7-A" title="Mini MoE：从稠密 FFN 到稀疏专家" status="planning" status_label="规划中 · 主线必修子任务" sub="true" question="怎样在总参数量放大的同时，让单 token 只激活部分专家？" summary="I7 架构进阶第一步（主线必修）：在小模型上实现 Top-K 路由、Shared Expert 与负载均衡辅助损失的迷你 MoE 层，验证结构正确性；不引入分布式，不要求提速。" >}}
- **学习内容**：
  - Router、Top-K 门控路由；
  - Shared Expert（共享专家）；
  - 负载均衡辅助损失（Load Balancing Loss）；
  - Capacity Factor 与 Token Dropping；
  - 总参数量与激活参数量的区别。
- **最小验收**：
  - 路由结果正确（token 被路由到正确专家）；
  - 专家负载可观察（能看出是否失衡）；
  - 与 Dense FFN 做同数据收敛对照；
  - 不要求小模型提速；
  - 不在此阶段引入分布式（Expert Parallel 留待 `S4`）。
- **diy-llm 结合**：[diy-llm](https://datawhalechina.github.io/diy-llm/%E5%89%8D%E8%A8%80.html) 第 5 章（MoE 混合专家模型）
{{< /milestone >}}

{{< milestone id="i7-mla" code="↳ I7-B" title="MLA：KV 低秩压缩与缓存" status="planning" status_label="规划中 · 主线必修子任务" sub="true" question="KV 低秩压缩如何进入 KV Cache，又怎样与 RoPE 兼容？" summary="I7 架构进阶第二步（主线必修）：实现 mini MLA 的低秩 KV 压缩、上投影与 RoPE 兼容，对照 MHA / GQA 的缓存与计算差异；理论缓存与实测占用分开，不要求加载 DeepSeek-V3。" >}}
- **学习内容**：
  - KV 低秩压缩（low-rank KV compression）；
  - 压缩表示如何进入 KV Cache；
  - 上投影与 RoPE 的兼容；
  - MLA 与 MHA、GQA 的缓存和计算差异。
- **最小验收**：
  - mini MLA 前向、Cache 与生成对照；
  - 理论缓存大小与设备实测占用分开报告；
  - 不要求下载或加载 DeepSeek-V3。
{{< /milestone >}}

{{< milestone id="i7-mtp" code="↳ I7-C" title="MTP：多 token 预测辅助头" status="planning" status_label="规划中 · 主线必修子任务" sub="true" question="多 token 预测辅助头怎样训练，又怎样与 I3 的 Draft / Target 投机解码区分？" summary="I7 架构进阶第三步（主线必修）：实现至少一个 MTP 辅助头并让训练损失正确进入总 loss，推理接受 / 修正 / Cache 回滚与目标模型贪心路径一致；最后再测吞吐，不预设提速。" >}}
- **学习内容**：
  - 多 token 预测辅助头（Multi-Token Prediction）；
  - MTP 训练损失；
  - 推理接受、修正与 Cache 回滚；
  - MTP 与 I3 Draft / Target 投机解码的区别。
- **最小验收**：
  - 至少一个 MTP 辅助头；
  - 训练损失正确进入总 loss；
  - 输出与目标模型贪心路径一致；
  - 最后再测吞吐，不预设一定提速。
{{< /milestone >}}

{{< milestone id="s1" code="S1" title="DeepInfer 请求链路与源码地图" status="planning" question="一条请求从输入到输出，究竟穿过了哪些工业级推理组件？" note1_title="DeepInfer 源码仓库" note1_url="https://github.com/deepseek-ai/DeepInfer" summary="按 `offline_inference.py` → `llm_engine.py` → `worker` → `model_executor` → `tests` 顺序研读 DeepInfer 源码，对照 vLLM / SGLang 观察 MoE / MLA / MTP 如何接入推理引擎，理清 Scheduler、KV Cache 与 Kernel 的职责；补充 vLLM V1 主读链路与 SGLang Radix 前缀复用对照，固定研读 tag / commit，供 Mini-Serving 主干实践验证理解。" >}}
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
  - Scheduler、KV Cache 与 Kernel 各自的职责与衔接；
  - 对照 vLLM / SGLang，观察 MoE、MLA、MTP 如何接入推理引擎；
  - 日志、指标、断言与测试如何进入主链路；
  - [DeepInfer](https://github.com/deepseek-ai/DeepInfer) 与 vLLM、SGLang、TensorRT-LLM 的继承与借鉴关系。
- **vLLM V1 / SGLang 对照研读**：
  - vLLM V1 主读链路：请求入口 → Scheduler → KV Cache Manager → Model Executor → Sampler / 输出；
  - SGLang 对照路径：Radix Cache 前缀复用及其与调度的衔接；
  - 为 vLLM V1 与 SGLang 分别记录实际研读的 tag / commit，源码路径以固定版本为准；
  - 用 `Mini-Serving` 主干实践验证理解，而不是抄完整源码。
- **规划交付物**：
  - 一张 DeepInfer 请求链路图；
  - 一份 vLLM V1 / SGLang 主读链路与固定版本对照记录；
  - 一张源码目录与职责地图；
  - 一条 prefill/decode 调用链；
  - 一份 MoE / MLA / MTP 接入方式的对照说明；
  - 一份“它已经解决什么、开源版没有包含什么”的边界说明。
- **规划验收标准**：
  - 能从一次 `llm.generate()` 讲到模型执行与输出；
  - 不把底层算子、推理框架和完整生产集群混为一谈；
  - 不虚构未实际阅读过的源码细节。
{{< /milestone >}}

{{< milestone id="mini-vllm" code="↳ 第三阶段主干实践" title="Mini-Serving：手搓 vLLM / SGLang 主干推理引擎" status="planning" status_label="规划中 · 教学版推理引擎" sub="true" question="怎样像手搓 Transformer 那样，先搭稳定主干、再逐局部替换，亲手写懂推理引擎的调度、KV 管理与输出？" summary="S0～S6 之外的教学版推理引擎主干实践（不计入主里程碑，尚未开始）：同一个引擎先完成请求调度、模型执行、KV 管理与流式输出，再逐步替换 Scheduler、KV Store、Attention Backend 与 Output Processor；用 vLLM 对照调度与分页、SGLang 对照 Radix 前缀复用，不分别重写两套框架。第一版只支持单个 V4 / Qwen3 模型、单进程单设备固定 dtype、贪心与最小流式。" >}}
- **定位与类比**：手搓 Transformer 先完成稳定主干，再替换 Attention / Norm / FFN；手搓推理引擎同理，先完成请求调度、模型执行、KV 管理与输出，再逐局部替换 Scheduler、KV Store、Attention Backend、Output Processor。vLLM 与 SGLang 都具备调度、分页 KV 与前缀复用；本项目用 vLLM 对照调度与分页管理、用 SGLang 对照 Radix 前缀复用，这只是学习侧重点，不是两者的独占功能划分。所有机制都在同一个引擎上逐步加入，不分别重写一套 vLLM 和一套 SGLang。
- **前置依赖**：`S0` 性能基线与 `S1` 源码地图（含 vLLM V1 / SGLang 对照研读），以及已验收的 V4 / Qwen3-0.6B 串行贪心基线；位于 `S1` 之后、`S2` 之前，是 `S0～S6` 之外的实践子项目，不计入主里程碑数量，不改变任何阶段完成度。
- **第一版范围**：一个现有 V4 / Qwen3 模型；单进程、单设备、固定 dtype；贪心生成；最小流式输出。Session 多轮历史不是第一版前置，先验收独立请求，之后再适配现有 ChatSession。
- **明确不做**：TP / PP / EP；CUDA / Triton 自定义 Kernel；MoE / MLA / MTP；量化与投机解码；全模型家族兼容；完整 vLLM / SGLang API 或 SGLang DSL；生产级高可用、鉴权与权限系统；Mamba / SSM 状态管理（属后续模型架构专题，若支持须另行抽象 SequenceStateStore，不在本项目提前改造主干）。
- **引擎骨架**：Request / Sequence 状态 → Scheduler → Model Executor → Sampler / Logits Processor → Streaming Output → 资源释放与指标记录。两条 KV 交互并行存在：Scheduler ↔ KV Store（容量检查、准入、分配与释放）与 Model Executor ↔ KV Store（读历史 KV、写回新 KV），KV Store 不是前向完成后才访问的串行步骤。Streaming Output 独立处理 token 增量解码、增量事件、finish_reason、取消与异常结束。需明确请求生命周期、Prefill / Decode 边界、token 与位置进度、KV Cache 所有权、输出与停止条件，以及完成 / 取消 / 异常后的清理。
- **内部迭代（非博客主阶段）**：
  1. **M0 单请求基线**：搭好引擎骨架，在固定设备 / dtype / Attention Backend / 输入 / 参考权重下与 V4 串行贪心基线对照，后续机制必须保留此基线回归。
  2. **M1 变长 Batch + Continuous Batching**：在独立 Model Executor / 模型适配路径处理逐请求 position IDs、有效 KV 长度、padding、causal mask 与动态加入退出（V4 统一 past_len 不能直接承接混合历史长度，原 V4 单请求实现保留作参照）；调度步决定 Prefill / Decode / 等待 / 结束释放与资源不足暂停，状态覆盖 waiting / running / finished / cancelled / failed；同一步 Prefill 与 Decode 可分别 forward，不要求单次混合两类 token，设每步 token 预算与最大活跃请求数，chunked prefill 可留后续；最终证明两个不同历史长度请求在同一次 forward 正确执行并支持动态加入退出。逐请求循环 forward 只是调度原型，不能据此宣称动态组批完成；中间迭代允许 Continuous Batching + 连续 KV。
  3. **M2 真实 Paged KV + 容量前进保证**：有限容量物理 KV Block Pool、逻辑 Token Block、Block Table、分配 / 读取 / 增量写回 / 引用 / 释放与碎片统计；允许临时 gather 为连续 KV，但 Block Table 必须真实参与读写与释放、有效新 KV 写回物理块、不长期另存每请求完整连续副本、padding 不得写成有效历史。定义上下文上限 / max_new_tokens / 准入与等待原因，空池容纳不下的请求明确拒绝，可按 prompt + max_new_tokens 预留逻辑额度、物理块按需分配，优先淘汰无活跃引用缓存以保证已准入请求继续生成，不允许永久互等；第一版不强制运行中抢占，未实现不得写成已支持。清理必须幂等（完成 / 取消 / 重复取消 / 异常 / 部分分配失败均正确，不双重释放、不负引用、不把旧结果交给新请求，failed 与 finish_reason 明确）。完成 M2 才能宣称 Continuous Batching + 真实 Paged KV 已验收，连续 KV 只是中间迭代而非最终交付。
  4. **M3 SGLang 局部扩展——Radix 前缀 KV 复用**：只实现 Prefix Cache / RadixAttention 核心思想，不复制完整 SGLang；用 Radix Tree 或等价结构按完全一致的 token ID 前缀复用 KV，接入已有 Block Table 与 Scheduler，管理引用计数 / 淘汰 / 取消 / 异常释放与共享前缀后的新分支。安全范围：只复用从位置 0 起、具完整因果历史的精确前缀，不复用滑动裁剪后的会话后缀；缓存命名空间含权重版本 / tokenizer 词表语义 / dtype / RoPE 位置语义 / 执行配置（后续 adapter 须加入身份或整体失效）；块身份含此前完整前缀，只共享已填满且不可变的块，未满尾块请求私有，分支分配私有块（不要求 CoW）；Radix 索引可在 token 层匹配但复用长度先向下对齐完整块，若只做整块哈希索引须注明与 Radix Tree 最长前缀匹配 / 节点分裂的差异。全部 Prompt 命中时保守保留至少一个 token 重算（reuse_len 向下对齐完整块），分别记录命中长度 / 真实跳过计算 / 重算 token，不虚报节省。请求释放与缓存淘汰区分：ref_cnt 只表活跃引用，零引用前缀块可按策略保留再淘汰，被引用块不可回收，warm cache 请求结束不要求内存归零；清空索引并结束全部请求后物理块回到可分配，预分配池本身可继续占用设备内存。
- **局部替换关系**：KV Store 按 Contiguous → Paged → Prefix-Sharing Paged 推进；Scheduler 按 Serial → Continuous Batching → Prefix-Aware（按需）；Attention Backend 按 Eager + 临时拼接 KV → Paged Attention（留到 `S2` 或后续）；Sampler 按 Greedy → 后续可选受约束解码；Streaming Output 独立处理解码 / 增量事件 / 结束原因 / 取消，不与采样或语法约束混为一模块。每次只推进一个机制，接口可做必要小幅协调修改但必须重跑对应基线，不为维持抽象拒绝必要修改，也不为新概念重写整个引擎。
- **验收摘要**：
  - 数值正确性：固定设备 / dtype / 后端 / 输入 / 参考权重，固定样例逐 token 回归，记录 logits 容差与首个输出分歧；Prefix Cache 命中 / 未命中路径同后端同配置受控回归；不预设任意 Batch / 设备 / 后端天然逐 token 一致，分歧必须调查，不一律归咎浮点误差或用速度 / 宽松阈值掩盖 KV / mask 错误；严格 batch invariance 留到 `S6`。
  - 状态与资源：混合长度不串历史 / 不串 KV，随机到达 / 动态加入退出 / 取消 / 异常状态正确，活跃引用最终归零，保留缓存有界可淘汰，容量耗尽仍能前进，旧结果不交付新请求。
  - 对照负载与指标：固定随机种子或可重放到达轨迹，区分只验证状态机的虚拟执行器与真实 V4 执行，区分 cold / warm cache 与零共享 / 共享前缀负载；TTFT 从请求到达算到首 token 对外产出（含排队），TPOT 明确统计范围（少于两个输出 token 记不适用），记录总吞吐 / 逐请求等待 / 延迟分布 / KV 与临时内存，Prefix Cache 记录命中率 / 实际节省 Prefill tokens / 共享私有块与引用计数，调度 / 分配 / 共享 / 释放 / 淘汰可追踪。
  - 对照组：当前串行服务、Continuous Batching + Paged KV、加入 Prefix Cache 的同一实现，同模型 / 同输入 / 同解码参数 / 同测量口径；不预设提速，允许得出当前规模下调度开销大于收益的结论；保留无饥饿或有界等待测试条件，第一版若不做强公平保证须明确边界。
- **版本与阶段衔接**：为 vLLM V1 与 SGLang 分别记录实际研读的 tag / commit，源码路径以固定版本为准。`S2` 的真正 Paged Attention 与融合 Kernel 属后续优化，不阻塞前面的 Block Manager 与调度验收；`S5` 与生产级 vLLM / SGLang 对照，分析 Continuous Batching / Paged KV / Prefix Cache / 背压与生产实现的差距，不用教学实现冒充生产能力；`S6` 将随机到达 / 混合长度 / 取消 / 异常 / Cache 耗尽 / 共享前缀 / 恢复纳入综合验收。
- **结构化生成**：后续可选：受约束解码专项（不纳入当前主干验收，不展开 JSON Schema / Regex / 语法编译器 / SGLang DSL；未来单独立项再定义每请求语法状态、token 到字符 / 字节约束、EOS 终态与失败语义）。
{{< /milestone >}}

{{< milestone id="s2" code="S2" title="自定义算子与 Kernel 优化" status="planning" question="同一个数学公式，为什么不同计算路径会有不同的性能与浮点结果？" summary="理解 eager / SDPA / FlashAttention / 融合算子与 Triton，按 RMSNorm / RoPE / SwiGLU → Attention → MoE / 稀疏 Kernel 的顺序实现小型自定义算子并完成容差与吞吐显存对照。" >}}
- **学习内容**：
  - eager、SDPA、FlashAttention 与融合算子的关系；
  - Triton 入门，按需了解 CUDA / TileLang；
  - 中间张量生成、显存读写、算子融合与分块计算；
  - DeepGEMM、FlashMLA、TileKernels 等组件在系统中的位置。
- **实现顺序**：
  1. RMSNorm / RoPE / SwiGLU 等基础算子；
  2. Attention（含 SDPA / FlashAttention 对照）；
  3. MoE / 稀疏 Kernel；
  4. 不要求一开始就实现 Gated DeltaNet Kernel（长上下文架构见 `S2.5`）；
  5. 真正的 Paged Attention 与融合 Kernel 属后续优化，不阻塞 `Mini-Serving` 的 Block Manager 与调度验收。
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

{{< milestone id="s2-long-context" code="↳ S2.5 选修" title="长上下文架构：YaRN + DSA + Hybrid Attention" status="planning" status_label="规划中 · 选修（不计入 S0～S6 主里程碑）" sub="true" question="怎样把上下文真正做长，而不只是把 context_size 配置调大？" summary="S2 之后、S3 之前的选修专题：按 YaRN / RoPE Scaling → DSA → Gated DeltaNet / 线性注意力 → Hybrid Attention → RULER 评测的顺序做最小混合架构实验；速度、显存与质量分别验收，不复刻完整 Qwen3-Next。" >}}
- **定位说明**：第三阶段选修专题，不计入 `S0～S6` 的 7 个主里程碑数量，不阻塞 `S3`；只做最小混合架构实验，不直接复刻完整 Qwen3-Next。
- **学习顺序**：
  1. YaRN / RoPE Scaling；
  2. DSA：Lightning Indexer、Top-K token 选择、稀疏核心注意力；
  3. Gated DeltaNet / 线性注意力；
  4. Hybrid Attention：为什么仍保留部分全注意力层；
  5. RULER 等长上下文质量评测。
- **边界**：
  - 只做最小混合架构实验，不直接复刻完整 Qwen3-Next；
  - `context_size` 配置增大不等于长上下文能力；
  - 长上下文速度、显存和质量必须分别验收。
- **官方参考入口**：
  - [Qwen3-Next-80B-A3B-Instruct](https://huggingface.co/Qwen/Qwen3-Next-80B-A3B-Instruct)；
  - [DeepSeek-V3.2-Exp](https://github.com/deepseek-ai/DeepSeek-V3.2-Exp)。
{{< /milestone >}}

{{< milestone id="s-v5" code="V5" title="V5：稀疏架构与低秩表示" status="planning" question="怎样在不复刻 DeepSeek 的前提下，亲手实现一个小型、可验证的稀疏架构与原生低秩表示主干？" summary="第三阶段正式版本里程碑（规划中）：承接 I7 的 MoE / MLA 与 S0～S2 的测量 / 源码 / Kernel 基础，实现 Top-K Router + Shared Expert、原生低秩 Q / O 投影、部分 RoPE 与 KV Cache 位置进度的小型稀疏主干；与 V4 Dense 基线同口径对照，不预设提速或优于 V4。" >}}
- **定位说明**：正式版本演进（非番外），计入第三阶段里程碑；承接 `I7` 的 MoE / MLA 基础（其中 `I7-A Mini MoE` 为必要前置）与 `S0～S2` 的测量、源码与 Kernel 基础。不是复刻 DeepSeek，而是先实现一个小型、可验证的稀疏架构主干。
- **第一版范围**：
  - Top-K Router + Shared Expert；
  - 原生低秩 Q / O 投影；
  - 部分 RoPE；
  - KV Cache 与逐 token 位置进度。
- **重点学习**：
  - 原生低秩结构与后训练 LoRA adapter 的区别（前者预训练即存在，后者是已有权重的低秩补丁）；
  - Top-K 路由、负载均衡与共享专家；
  - 部分通道 RoPE 与全通道 RoPE 的差异；
  - 总参数、激活参数、KV Cache 与实际生成行为的关系。
- **规划验收标准**：
  - 路由、共享专家、投影形状与位置进度正确；
  - 前向、cache decode 与固定生成测试通过；
  - 与 V4 Dense 基线比较参数量、激活参数、KV Cache、生成行为与资源成本；
  - 不预设一定提速或一定优于 V4；
  - 不直接加载或复刻 DeepSeek 大模型权重。
{{< /milestone >}}

{{< milestone id="s3" code="S3" title="分布式训练与训练稳定性" status="planning" question="模型和数据变大以后，计算、梯度、参数与 checkpoint 怎样分布到多个设备，训练又怎样保持稳定？" summary="沿 DDP → All-Reduce → FSDP/ZeRO → TP/PP/CP → 分布式 checkpoint 构建最小沙盘，并纳入 FP8 / Activation Storage、Muon / MuonClip、Attention Logit 稳定性与通信 / 重算 / Activation Offload；硬件不支持的内容只做源码或最小实验。" >}}
- **学习顺序**：
  1. 数据并行与 DDP；
  2. Gradient All-Reduce 与通信开销；
  3. FSDP / ZeRO 参数、梯度、优化器状态分片；
  4. Tensor Parallelism；
  5. Pipeline Parallelism；
  6. Context Parallelism；
  7. 分布式 checkpoint、保存、恢复与故障处理。
- **训练稳定性专题**：
  - FP8 训练或 Activation Storage；
  - Muon / MuonClip 优化器；
  - Attention Logit 稳定性；
  - 通信、重算与 Activation Offload 的取舍。
- **规划交付物**：
  - 一个最小分布式训练沙盘；
  - 单进程与多进程的训练对照；
  - 参数/梯度分片与通信示意；
  - 可恢复的分布式 checkpoint 实验；
  - 一份训练稳定性（FP8 / Muon / Attention Logit）最小实验或源码研读记录。
- **规划验收标准**：
  - 在相同数据与初始状态下，分布式结果与单进程保持合理一致；
  - 能解释通信量、显存和吞吐的变化；
  - checkpoint 能保存并恢复训练现场；
  - 硬件不支持的内容只做源码或最小实验，不伪造大规模训练结果；
  - 不以“启动了多个进程”冒充分布式训练已经掌握。
- **diy-llm 结合**：[diy-llm](https://datawhalechina.github.io/diy-llm/%E5%89%8D%E8%A8%80.html) 第 8 章（分布式训练）+ 作业 4
- **参考入口**：[训练稳定性参考论文](https://arxiv.org/html/2507.20534v1)。
{{< /milestone >}}

{{< milestone id="s4" code="S4" title="MoE 与专家并行" status="planning" question="会写 MoE 层之后，怎样把专家分布到多个设备并控制通信与负载？" summary="以 I7-A Mini MoE 为前置，先会写 MoE 层再学习其分布式系统：保留 Expert Parallel、All-to-All、Capacity 与负载均衡，加入 DeepEP / EPLB，理解专家并行的通信成本与稳定性。" >}}
- **前置依赖**：`I7-A Mini MoE`（先在小模型上写对 MoE 层，再进入分布式专家并行）。
- **学习内容**：
  - Expert Parallelism 与 All-to-All 通信；
  - Capacity Factor、Token Dropping 与负载均衡；
  - expert collapse 与路由稳定性；
  - DeepEP、EPLB 与专家负载均衡；
  - MoE 的训练稳定性、通信成本与评估方法。
- **规划交付物**：
  - 基于 I7-A MoE 层的分布式专家并行沙盘；
  - 路由与负载均衡指标；
  - All-to-All 通信量与单机模拟对照；
  - 单机模拟与分布式专家并行示意。
- **规划验收标准**：
  - 能证明 token 被路由到正确专家；
  - 能观察专家负载是否失衡；
  - 同时报告模型质量、训练稳定性、通信与资源成本；
  - 不把“参数量变大”直接写成“能力必然提升”。
{{< /milestone >}}

{{< milestone id="s5" code="S5" title="生产推理与 Serving" status="planning" question="当一个请求变成成千上万个请求，推理系统怎样保持吞吐、延迟与隔离？" summary="搭建最小生产 Serving 沙盘：保留 Paged KV Cache、Continuous Batching 与 TP / EP，加入 MTP 生产部署、量化 Kernel、背压 / 超时 / 多会话隔离，实测 TTFT / TPOT / 吞吐 / P95；区分 I7-C 的结构正确与本阶段的部署有效。" >}}
- **学习内容**：
  - continuous batching；
  - 异步调度与 CPU/device 工作重叠；
  - paged/bounded KV Cache 与内存管理；
  - prefill/decode 分离；
  - Tensor / Expert Parallel 推理；
  - 多副本负载均衡；
  - MTP 的生产部署；
  - 量化 Kernel、流式输出、多 Session 隔离、背压与超时；
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
  - 区分 I7-C 的“结构正确”和本阶段的“部署有效”，不把结构跑通当成生产可用；
  - 与生产级 vLLM / SGLang 对照，分析 Continuous Batching / Paged KV / Prefix Cache / 背压与生产实现的差距，不用 `Mini-Serving` 教学实现冒充生产能力；
  - 性能结论必须来自实测（TTFT / TPOT / 吞吐 / P95），不照抄官方数字。
{{< /milestone >}}

{{< milestone id="s-v6" code="V6" title="V6：长上下文、记忆与推理协同" status="planning" question="怎样把长上下文、记忆与推理调度协同起来，并让草稿—验证链路可验证、可对照？" summary="第三阶段正式版本里程碑（规划中）：同时依赖模型结构、KV 管理、缓存复用、推理调度与验证机制；首选 DSpark 方向（衔接 I3 Draft / Target、Mini-Serving、GRPO 与缓存验证链路），第一版做草稿—目标验证、Markov 顺序依赖、置信度调度与接受率 / 错误处理对照；Engram / 压缩 / 索引留作后续可选扩展。" >}}
- **定位说明**：正式版本演进（非番外），计入第三阶段里程碑；同时依赖模型结构、KV 管理、缓存复用、推理调度与验证机制。首选方向为 DSpark，因为它与 `I3` 的 Draft / Target 投机解码、`Mini-Serving`、GRPO、缓存和验证链路衔接最自然。
- **第一版范围**：
  - 草稿结构与目标模型验证；
  - Markov 顺序依赖与块内一致性；
  - 置信度调度；
  - 接受率与错误处理；
  - 输出一致性、速度、内存与行为质量对照。
- **规划验收标准**：
  - 草稿与目标模型的 token 一致性可验证；
  - 接受率、置信度调度与失败路径有记录；
  - 能解释与普通 Draft / Target 投机解码的差异；
  - 同 prompt、同解码参数、同任务集下比较吞吐、内存与输出质量；
  - 不把草稿直接当成目标输出，不预设一定提速。
- **范围边界**：Engram、压缩与索引作为 V6 后续可选扩展，不要求第一版同时完成，避免把版本范围无限扩大。
{{< /milestone >}}

{{< milestone id="s6" code="S6" title="稳定性、确定性与综合验收" status="planning" question="系统不只要能跑，还要能证明它稳定、可复现、可诊断、可恢复。" summary="补齐 batch-invariant inference、确定性采样、日志 trace 与故障注入压测，加入长上下文质量与性能、Dense V4 与各新架构的同口径对照，产出全景图、DeepInfer 总结与第三阶段收官笔记。" >}}
- **学习内容**：
  - batch-invariant inference；
  - deterministic sampling；
  - structured outputs；
  - 数值、行为、性能与分布式回归；
  - 长上下文质量与性能验收；
  - Mini-Serving 综合验收：随机到达、混合长度、取消、异常、Cache 耗尽、共享前缀与恢复；
  - Dense V4 与 Mini MoE / MLA / MTP / 混合注意力的同口径对照；
  - 日志、指标、trace 与故障定位；
  - 压测、故障注入、超时、重试与恢复；
  - 官方参考实现对照与结论边界。
- **规划交付物**：
  - 第三阶段完整测试与评估报告；
  - 一张训练/推理系统全景图；
  - 一份 Dense V4 与各新架构的同口径对照报告；
  - 一份 [DeepInfer](https://github.com/deepseek-ai/DeepInfer) 对照学习总结；
  - 一篇完整的第三阶段收官笔记。
- **规划验收标准**：
  - 固定条件下结果可复现（可复现 benchmark）；
  - 数值正确性、并发隔离与故障恢复均有明确测试；
  - 不同 batch 组合与采样场景的差异有明确测试；
  - 失败时能通过日志、指标和最小复现定位；
  - 报告明确区分已实现、已测量、未覆盖和受硬件限制的部分；
  - 不以“参考了 DeepInfer”冒充“已经达到 DeepInfer 的生产能力”。
{{< /milestone >}}

{{< milestone id="s-goal" code="总目标" title="第三阶段总交付目标与“六不追求”边界" status="planning" question="第三阶段收官时应当能够回答什么问题？明确不追求哪些事情？" summary="收官需能回答测量、引擎链路、算子误差、多设备分担、并发隔离与可靠性 6 个核心问题，并守住“六不追求”边界。" >}}
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
    rules="阶段定位::证明模型能力真的变强了——以 Agentic 后训练与能力形成为核心，多模态保持选修 | 前置依赖::现代架构底座已就绪，待 I4 / I5 后训练基础与第三阶段系统能力完成后展开 | 架构选型::V4 Pro vs Flash 不同资源约束下的架构取舍（模型谱系、架构选型与场景适配），逐项机制回答节省什么 / 放松条件 / 买到什么 / 是否能力形成，具备部署条件再做同口径对照 | 探索衔接::承载推理强化、模型诊断、扩层后训练（后续选修），以及下方尚未开始训练的 M7 个人中文语料 Midtrain"
>}}

- **Agentic 后训练与能力形成**：大规模 Agentic 数据合成、RLVR、自我评价奖励、工具调用与环境交互，以及更进一步的推理强化；
- **推理强化与对齐**：CoT、DPO、GRPO、RLVR（承接 I4 后训练基础）；
- **数据与评测工程**：指令数据工程与评委校准；
- **领域模型与权重诊断**：领域模型训练与评估、模型诊断和权重空间编程（探索记录见[《手搓 LLM 笔记 15：让 AI 直接修改模型权重，能学会四则运算吗？》](/llm/llm-15-weight-space-arithmetic/)）；
- **模型谱系与架构选型**：V4 Pro vs Flash 不同资源约束下的架构取舍（见下方研究节点）；Flash 侧以 `text_config` 解读为依据、Pro 侧待官方来源核对，不提前断言谁更强更快；
- **模型增长与扩层后训练（后续选修）**：研究 Block Expansion / Depth Up-Scaling（Net2Net、LLaMA Pro、SOLAR），在原有 Transformer Block 之后、`final_norm` 之前插入少量新层，重点理解恒等初始化、冻结与逐步解冻，并与 LoRA、全参数训练做同数据对照；不阻塞当前主线或 `M7`；
- **多模态（保持选修）**：不作为主阶段，只保留未来选修，不为补清单改变当前主线；
- **个人中文语料 midtrain（尚未开始训练）**：承载下方 `M7` 独立彩蛋。

{{< milestone id="v4-pro-flash-comparison" code="V4 Pro / Flash" title="V4 Pro vs Flash：不同资源约束下的架构取舍" status="planning" question="当资源不再那么紧张时，哪些压缩可以放松、哪些稀疏机制即使面对更高成本仍然值得保留，为什么？" summary="第四阶段正式架构选型研究（规划中，非番外 / 追新）：主线是不同资源约束下的架构取舍——逐项机制回答它节省什么资源、放松需要什么条件、增加资源买到什么、是硬件适配还是能力形成的一部分；对照覆盖参数 / 激活、Attention / KV / RoPE、长上下文、稀疏机制、量化、部署成本与任务适配，不只比参数规模。Flash 侧已有 text_config 解读，Pro 侧待官方核对；具备部署条件后再做同口径对照，不提前断言谁更强更快。" >}}
- **定位说明**：正式研究方向（非番外、非临时追新），研究同一模型家族中 Pro 与 Flash 在不同资源约束下的架构取舍及其各自适合的任务与部署环境；服务于模型谱系、架构选型与场景适配。
- **逐项机制四问**（对照每项机制时回答）：
  1. 它节省的是什么资源：显存、访存带宽、计算量，还是通信与调度成本？
  2. 放松它需要什么条件：只调整部署参数，还是涉及架构和训练适配？
  3. 增加资源后买到了什么：更高质量、更长上下文、更低延迟，还是更高并发？
  4. 它只是为了适配硬件，还是已经成为模型能力形成的一部分？
- **配置对照维度**（不只比较参数规模）：
  - 参数规模与激活参数；
  - 专家数、路由方式与激活比例；
  - Attention / KV / RoPE；
  - 长上下文长度与扩展方式；
  - 稀疏机制（MoE 激活、Attention / KV 稀疏与压缩等）；
  - Engram 与 DSpark 配置；
  - 量化格式、权重存储与部署成本；
  - 本地可运行性、云端资源、推理成本与任务适配。
- **研究边界**：
  - 量化压缩不等于稀疏机制；
  - 资源更充足不等于应该全面取消稀疏、改成稠密计算；
  - MoE 激活专家数、Attention / KV 的稀疏与压缩等设计可能与训练过程耦合，不能预设为推理时可随意调整的开关；
  - Engram、DSpark 等机制在配置与实现核实前，不提前归类为单纯的资源压缩手段；
  - DeepSeek V4.1 中尚未由官方 modeling 源码确认的字段继续保持待核实，不补充未经确认的实现解释。
- **证据边界**：Flash 侧已有 `text_config` 逐字段解读番外可作依据；Pro 侧配置尚未核对官方来源，不虚构 Pro 数值或 Pro / Flash 实测差异。
- **部署对照（具备条件后）**：同 prompt、同解码参数、同任务集、同硬件、同测量口径下的质量、速度与成本对照。
- **暂无部署条件时**：只写配置与架构差异，不提前声称 Pro 一定更强或 Flash 一定更快；没有同口径实验不写性能 / 质量 / 成本结论。
{{< /milestone >}}

{{< milestone id="m7" code="M7" title="第四阶段独立彩蛋：个人中文语料中间训练（Midtrain）" status="optional" summary="第四阶段独立彩蛋（尚未开始训练，仅完成语料盘点）：基于已就绪的 Qwen 底座与个人中文语料开展 midtrain 与评估对照。" >}}
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
    rules="阶段定位::将专用模型能力与 Skill 工具生态合流，构建可审计的多角色协作系统（多模态暂不作为主阶段，只保留未来选修） | 交付闭环::以 Agent Team 沙盘打通需求—数据—后端—前端—测试—运维上线的完整软件交付链路，自动上线仅限隔离环境，生产部署与资金操作保留人工批准"
>}}

- **核心方向**：规划、执行、测试、运维分工（思路见[《企业级 AI 编程的终极形态：当模型开始分工》](/ai/enterprise-ai-model-division/)），以及记忆、上下文、权限、反馈闭环和多模型编排。
- **独立支线**：下方 `Agent Team 软件交付沙盘` 以已有炒股系统为业务载体，演练多角色协作与可审计交付，不阻塞其他阶段。

{{< milestone id="agent-team-stock-delivery" code="↳ 第六阶段支线" title="Agent Team：从需求到上线的炒股系统交付沙盘" status="planning" status_label="规划中 · 多角色软件交付沙盘" sub="true" question="怎样让多角色 Agent Team 在真实工程约束下，完成从需求到运维上线的可审计软件交付？" summary="第六阶段独立规划支线（不阻塞其他阶段）：以已有炒股系统为业务载体，组建产品 / 数据 / 后端 / 前端 / 测试 / SRE 多角色 Agent Team，打通需求—数据—后端—前端—测试—运维上线的完整交付闭环；重点是多角色协作、工具权限、工程质量与可审计交付，不是学习炒股策略，也不让 Agent 自动进行真实资金交易。" >}}
- **任务定位**：以已有炒股系统的真实前端、后端与数据复杂度为业务载体，组建多角色 Agent Team，打通从需求产生到运维上线的完整软件交付链路；重点是多角色协作、工具权限、工程质量和可审计交付，不是学习炒股策略，也不是让 Agent 自动进行真实资金交易。
- **角色与交付物**：
  1. **产品 / 需求 Agent**：需求说明、用户故事、验收条件、范围边界；
  2. **数据 Agent**：数据字典、数据质量检查、血缘、异常与缺失处理报告；
  3. **后端 Agent**：API 契约、领域逻辑、数据库变更、单元与集成测试；
  4. **前端 Agent**：页面、交互、状态管理、前端测试与可访问性检查；
  5. **测试 / Review Agent**：测试计划、E2E、回归、代码审查与安全检查；不能由实现者单独宣布自己验收通过；
  6. **SRE / Release Agent**：CI 构建、隔离预览环境、部署清单、监控、日志、告警与回滚方案。
- **完整链路**：需求产生 → 需求规格与验收条件 → 数据检查 → API / 后端 → 前端 → 测试与审查 → CI 构建 → 隔离环境部署 → 监控与反馈 → 必要时回滚。
- **工程约束**：
  - 每个角色必须交付可检查的文件、报告、测试或运行结果，不能只输出聊天文字；
  - 明确任务分工、代码修改范围和冲突处理；
  - 保存任务状态、工具调用、测试结果和发布轨迹；
  - 密钥、数据库迁移、外部服务与部署权限必须分级；
  - 自动上线仅面向隔离的开发 / 预览环境；
  - 真实生产部署、高风险数据库变更和任何真实资金交易必须保留人工批准；
  - 支持失败后的停止、恢复与回滚，不允许 Agent 为通过检查而绕过测试。
- **支线验收指标**：
  - 需求到预览环境的端到端完成率；
  - 测试通过率与返工次数；
  - 人工干预次数及介入位置；
  - 发布与回滚是否可复现；
  - Token、耗时与实际成本；
  - 是否发生越权、跨任务污染或不可追踪修改；
  - 是否留下完整、可审计的需求—代码—测试—发布证据链。
- **可视化边界**：可展示角色时间线、任务依赖、工件流转、质量门禁与发布状态，但可视化不能代替真实工程验收。
{{< /milestone >}}

---

## 支线探索与日常节奏

- **权重空间编程（不阻塞主线）**：三轮 Weight-Space Programming 实验已独立整理为[《手搓 LLM 笔记 15：让 AI 直接修改模型权重，能学会四则运算吗？》](/llm/llm-15-weight-space-arithmetic/)，不放入主线依赖，不阻塞 M5、M6 或后续阶段。
- **默写与回炉（2026-10-29 增补）**：`GPTModel` 每两周在 A4 纸脱稿默写一次（首次记录见[《手搓 LLM 番外：A4 纸默写 GPTModel》](/llm/llm-extra-handwrite-gptmodel/)），`MHA` / `FFN` / `LayerNorm` 单独补漏；两周后对照进步。
- **nanochat 与官方参考实现对照**：第一阶段 `M0～M6` 与第二阶段 `I0`（`model_v3` 承接 Qwen2.5）、`I1`（工业数据工程与流式 IO）、`I2`（训练加速与显存压榨，含 RTX 4070 Ti CUDA 对照番外）、`I3`（高性能推理与服务引擎）、`I4`（后训练深水区）、`I5`（评估校准与回归基准自动化）已交付，`I6` 已收官（真实修复暂缓待复入）；第三阶段推进继续以 `nanochat` 与 Hugging Face 官方参考实现作为对照基线，按实际依赖验证工业级训练、推理与分布式理解。
- **博客与掘金专栏输出**：每个里程碑（M0～M6、I0～I7、M7）产出一篇实录笔记；实验数据直接整理成可复现报告。
