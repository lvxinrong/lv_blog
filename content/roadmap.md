+++
title = "lvchat 实现导图：开工顺序即依赖顺序"
slug = "roadmap"
aliases = ["/llm/lvchat-roadmap/", "/nanochat/lvchat-roadmap/"]
date = 2026-10-19T19:10:00+08:00
lastmod = 2026-11-14T20:46:53+08:00
draft = false
series = "llm"
hiddenInRss = true
ShowBreadCrumbs = false
ShowPostNavLinks = false
tags = ["LLM", "nanochat", "lvchat", "diy-llm", "AI-Infra", "学习笔记"]
summary = "按能力层级划分为六个阶段：第一阶段（从零手搓 LLM，M0～M6）已 7/7 完整交付；第二阶段（当前阶段，进度 4/6，证明结构写对了）已完成 I0～I3 主线与 CUDA、ModelV4 / Qwen3 两个番外，主线下一站 I4，I6 架构进阶番外（Mini MoE / MLA / MTP）为选修；第三阶段（证明系统真的有效，S0～S6 + S2.5 长上下文选修）覆盖性能基线、源码地图、算子优化、分布式训练与稳定性、专家并行、生产 Serving 与综合验收；第四阶段（证明模型能力真的变强了）聚焦 Agentic 后训练与能力形成；第五、第六阶段保留演进方向与依赖。"
[cover]
    image = "covers/lvchat-roadmap.jpg"
    alt = "lvchat 实现导图"
    hiddenInSingle = true
    hiddenInList = true
+++

{{< roadmap_overview
    north_star="目标：用纯 PyTorch 交付一个可对话的 355M 模型，并打通从数据到 WebUI 的全链路。"
    phases="phase-01::STAGE 01 · 第一阶段::从零手搓 LLM::done::2026.10.13 → 2026.11.04 (M0～M6 已完成) | phase-02::STAGE 02 · 第二阶段::现代架构与模型承接::active::2026.11.04 启动 · 进度 4/6 (I0～I3 及番外已完成，主线下一站 I4；结构最小验证) | phase-03::STAGE 03 · 第三阶段::工业级训练、推理与分布式系统::planning::规划中 · S0～S6 + S2.5 长上下文 · 性能/分布式/Serving | phase-04::STAGE 04 · 第四阶段::后训练与领域能力形成::planning::规划中 · Agentic 后训练/能力形成/M7 个人语料 | phase-05::STAGE 05 · 第五阶段::Skill 工程与工具生态::planning::远期 · 扫描/排查/MCP/开源规范 | phase-06::STAGE 06 · 第六阶段::Agent 与多模型协作::planning::远期 · 多角色分工与编排闭环"
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
    next="第二阶段 I4 · 后训练深水区（I0～I3 及番外已完成）"
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
    rules="阶段定位::证明结构写对了——I0～I3 主线与 I6 架构进阶番外做最小结构验证，系统级性能、分布式与 Serving 留待第三阶段 | 装备来源::剥离自第一阶段的全部工业级选修项 + 第一阶段实测暴露的工程与模型边界 | 理论蓝本::以 DataWhale diy-llm（CS336 中文本土化 16 章 + 6 作业）为系统理论蓝本，按需调用 | 进化目标::新建独立 model_v3 / v4 承接现代架构与 Qwen 权重，并按 I0～I6 逐件升级数据、训练、推理与后训练"
    done="4"
    total="6"
    current="I3 · 高性能推理与服务引擎（2026-11-13 收官）"
    delivered="I0～I3 主线及 CUDA、ModelV4 / Qwen3 两个番外已交付；完成推理基线、会话级 KV Cache、INT8 / INT4 量化、贪心投机解码、SSE 流式与多会话隔离，Mac / CUDA 双环境对照"
    next="I4 · 后训练深水区（主线下一站；I3 番外 ModelV4 / Qwen3 已验收，Qwen 谱系表选修仍规划中）"
    steps="i0:I0:现代架构:done, i1:I1:数据与流式IO:done, i2:I2:训练与算子加速:done, i3:I3:量化与投机推理:done, i4:I4:CoT与偏好对齐:todo, i5:I5:评委校准CI:todo, i6:I6:架构进阶番外:optional"
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
- **定位说明**：面向模型承接能力的选修番外，已验收；不计入第二阶段 `I0～I6` 主线完成度（主线仍 `4/6`），主线下一站仍为 `I4`。`V3` 继续作为 Qwen2.5-0.5B / 0.5B-Instruct 的稳定对照，`V4` 独立承接 Qwen3-0.6B。
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

{{< milestone id="i4" code="I4" title="后训练深水区：多轮对话 SFT、CoT 思维链与 DPO / GRPO 对齐" status="todo" summary="解决 M6 多轮历史复制问题：引入多轮对话 SFT 与按轮掩码、CoT 思维链微调、LoRA/全参对标，以及 DPO / GRPO 最小对齐闭环。" >}}
- **进化部位**：承接 M4 与 M6 暴露的“多轮旧答案复制”边界，升级 `squid/data/instruct.py` 与 `squid/train/`
- **装备升级**：
  1. **真正的多轮对话 SFT + 思维链（CoT）微调**：引入多轮对话指令数据与按轮掩码（解决 M6 暴露的多轮历史复制问题），并构造“推理步骤 `<think>` + 最终答案”数据；
  2. **LoRA vs 全参微调**在现代底座上的系统对标；
  3. **偏好对齐与强化学习**：手写 **DPO（直接偏好优化）** 损失函数，并探索 **RLVR / GRPO**（群组相对策略优化）在数学/代码可验证任务上的最小闭环。
- **diy-llm 结合**：[diy-llm](https://datawhalechina.github.io/diy-llm/%E5%89%8D%E8%A8%80.html) 第 13 章（Pre-training / SFT / DPO 全流程）+ 第 14 章（GRPO / RLVR 强化学习）
- **待完成验收**：解决 Web UI 多轮对话复制旧答案问题，并给出 SFT vs CoT-SFT vs DPO 的评委胜率（Win Rate）对比
{{< /milestone >}}

{{< milestone id="i5" code="I5" title="评估校准与回归基准自动化（Judge Calibration）" status="todo" summary="承接 M5 评估流水线：校准 LLM-as-Judge 位置与长度偏见、检验多评委一致性，并建立一键对比门禁报告。" >}}
- **进化部位**：承接 M5 评估流水线，升级 `squid/eval/`
- **装备升级**：
  1. **LLM-as-Judge 偏见校准**：双向交换位置消除先后偏见（Position Bias）、控制长度偏见（Length Bias）；
  2. **多评委交叉一致性检验**：计算人工评分与 AI 评委的相关系数，建立每次架构/数据改动后的自动化回归门禁。
- **diy-llm 结合**：[diy-llm](https://datawhalechina.github.io/diy-llm/%E5%89%8D%E8%A8%80.html) 第 12 章（评估与基准）+ 作业 6
- **待完成验收**：每次装备升级（I0～I4）均可一键跑出带置信区间与胜率矩阵的对比报告
{{< /milestone >}}

{{< milestone id="i6" code="I6" title="I6 架构进阶番外：Mini MoE + MLA + MTP" status="optional" summary="可选架构进阶番外（不计入主线）：按 I6-A Mini MoE → I6-B MLA → I6-C MTP 顺序，在小模型上逐一验证现代结构写对了；分布式与专家并行留待第三阶段 S3 / S4，生产部署留待 S5。" >}}
- **定位说明**：独立架构进阶番外，不计入第二阶段 `I0～I6` 主线完成度，不阻塞主线 `I4 → I5`；第二阶段只证明结构写对了，系统级性能、分布式与 Serving 留待第三阶段。
- **三个子任务（依次推进）**：
  1. **I6-A Mini MoE**：Top-K 路由、Shared Expert 与负载均衡，验证路由正确、负载可观察；
  2. **I6-B MLA**：KV 低秩压缩进 Cache、上投影与 RoPE 兼容，对照 MHA / GQA；
  3. **I6-C MTP**：多 token 预测辅助头与训练损失，推理与目标模型贪心路径一致。
- **diy-llm 结合**：[diy-llm](https://datawhalechina.github.io/diy-llm/%E5%89%8D%E8%A8%80.html) 第 5 章（MoE 混合专家模型）；MLA / MTP 结合官方论文与源码按需调用。
- **边界**：本番外只做结构最小验证，不要求小模型提速，不在此引入分布式；DDP / ZeRO / FSDP 与 Expert Parallel 的详细内容见第三阶段 `S3` / `S4`。
{{< /milestone >}}

{{< milestone id="i6-moe" code="↳ I6-A" title="Mini MoE：从稠密 FFN 到稀疏专家" status="planning" status_label="规划中 · 选修（不计入主线）" sub="true" question="怎样在总参数量放大的同时，让单 token 只激活部分专家？" summary="I6 架构进阶番外第一步：在小模型上实现 Top-K 路由、Shared Expert 与负载均衡辅助损失的迷你 MoE 层，验证结构正确性；不引入分布式，不要求提速。" >}}
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

{{< milestone id="i6-mla" code="↳ I6-B" title="MLA：KV 低秩压缩与缓存" status="planning" status_label="规划中 · 选修（不计入主线）" sub="true" question="KV 低秩压缩如何进入 KV Cache，又怎样与 RoPE 兼容？" summary="I6 架构进阶番外第二步：实现 mini MLA 的低秩 KV 压缩、上投影与 RoPE 兼容，对照 MHA / GQA 的缓存与计算差异；理论缓存与实测占用分开，不要求加载 DeepSeek-V3。" >}}
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

{{< milestone id="i6-mtp" code="↳ I6-C" title="MTP：多 token 预测辅助头" status="planning" status_label="规划中 · 选修（不计入主线）" sub="true" question="多 token 预测辅助头怎样训练，又怎样与 I3 的 Draft / Target 投机解码区分？" summary="I6 架构进阶番外第三步：实现至少一个 MTP 辅助头并让训练损失正确进入总 loss，推理接受 / 修正 / Cache 回滚与目标模型贪心路径一致；最后再测吞吐，不预设提速。" >}}
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

---

## 第三阶段规划蓝图：工业级训练、推理与分布式系统（S0 → S6 · 规划中）

> **阶段定位**：从会写模型，进阶到理解工业级训练与推理系统；在自己的工程中完成最小机制实现，再对照 [DeepSeek `DeepInfer`](https://github.com/deepseek-ai/DeepInfer) 理解生产级系统设计。**本阶段当前处于“规划中”（尚未开始，不设固定排期，也不承诺学习周期；DeepInfer 尚未在本机部署或跑通）。**
>
> **推进顺序**：`I4 → I5 → I6-A Mini MoE → I6-B MLA → I6-C MTP → S0 → S1 → S2 → S2.5 长上下文（选修）→ S3 分布式训练与稳定性 → S4 专家并行 → S5 生产 Serving → S6 综合验收 → 第四阶段 Agentic 后训练与能力形成`。I6 与 S2.5 均为选修，不计入主线完成度，也不阻塞主线推进。

{{< roadmap_progress
    id="phase-03"
    season="STAGE 03 · 第三阶段（规划中）"
    title="工业级训练、推理与分布式系统（S0 ～ S6）"
    phase_state="planning"
    repo="squid-llms"
    theory_title="DeepSeek DeepInfer"
    theory_url="https://github.com/deepseek-ai/DeepInfer"
    rules="阶段定位::证明系统真的有效——性能基线、分布式训练与稳定性、专家并行与生产 Serving；在自己的工程中完成最小机制实现，再对照 DeepInfer 理解生产级系统设计 | 前置依赖::第二阶段 I0～I3 相关基础已完成，具备 Python / PyTorch / Transformer 与训练推理链路知识，Linux GPU 实验环境按阶段需要继续扩展；S4 专家并行以 I6-A Mini MoE 为前置 | 硬件与验收边界::Mac + MPS 不作为 DeepInfer 部署验收环境；DeepInfer 要求 NVIDIA SM100 或 Ascend 950，源码研读不依赖本机部署，官方部署验证仅作匹配硬件后的选修"
    done="0"
    total="7"
    unit="规划里程碑（尚未启动）"
    planning_note="规划中 · I0～I3 已完成，待其余前置条件就绪后按 S0 → S1 → S2 → S2.5 选修 → S3 → S4 → S5 → S6 启动"
    steps="s0:S0:性能基线:todo, s1:S1:源码地图:todo, s2:S2:算子优化:todo, s3:S3:分布式训练:todo, s4:S4:MoE并行:todo, s5:S5:推理调度:todo, s6:S6:稳定性验收:todo"
>}}

{{< phase_drawer open="true" variant="planning" summary="规划蓝图（尚未启动） · 点击收起/展开第三阶段前置依赖、S0 ～ S6 共 7 个主里程碑、S2.5 长上下文选修与总交付目标（点击上方 S0～S6 节点可直接跳转）" >}}

{{< milestone id="s-pre" code="前置条件" title="第三阶段前置依赖与硬件环境边界" status="planning" question="进入工业级训练、推理与分布式系统之前，必须先满足哪些基础与硬件边界？" note1_title="DeepInfer 仓库" note1_url="https://github.com/deepseek-ai/DeepInfer" summary="明确 `I0～I3` 前置基础、Linux GPU 实验环境、Mac/MPS 非部署环境边界，以及 DeepInfer 对 SM100 / Ascend 950 的硬件约束。" >}}
1. **第二阶段 `I0～I3` 的相关基础（均已完成）**：
   - 现代模型结构与 Qwen 权重承接（`I0` 已完成）；
   - 数据与流式 IO（`I1` 已完成，见[笔记 18](/llm/llm-18-i1-data-pipeline/)）；
   - 训练加速与资源核算（`I2` 及 RTX 4070 Ti CUDA 番外已完成，见[笔记 19](/llm/llm-19-i2-environment-probe/) 与[笔记 20](/llm/llm-20-i2-windows-cuda/)）；
   - KV Cache、量化、投机解码和基础推理指标（`I3` 已完成，见[笔记 21](/llm/llm-21-i3-inference-baseline/)）。
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

{{< milestone id="s1" code="S1" title="DeepInfer 请求链路与源码地图" status="planning" question="一条请求从输入到输出，究竟穿过了哪些工业级推理组件？" note1_title="DeepInfer 源码仓库" note1_url="https://github.com/deepseek-ai/DeepInfer" summary="按 `offline_inference.py` → `llm_engine.py` → `worker` → `model_executor` → `tests` 顺序研读 DeepInfer 源码，并对照 vLLM / SGLang 观察 MoE / MLA / MTP 如何接入推理引擎，理清 Scheduler、KV Cache 与 Kernel 的职责。" >}}
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
- **规划交付物**：
  - 一张 DeepInfer 请求链路图；
  - 一张源码目录与职责地图；
  - 一条 prefill/decode 调用链；
  - 一份 MoE / MLA / MTP 接入方式的对照说明；
  - 一份“它已经解决什么、开源版没有包含什么”的边界说明。
- **规划验收标准**：
  - 能从一次 `llm.generate()` 讲到模型执行与输出；
  - 不把底层算子、推理框架和完整生产集群混为一谈；
  - 不虚构未实际阅读过的源码细节。
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
  4. 不要求一开始就实现 Gated DeltaNet Kernel（长上下文架构见 `S2.5`）。
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

{{< milestone id="s4" code="S4" title="MoE 与专家并行" status="planning" question="会写 MoE 层之后，怎样把专家分布到多个设备并控制通信与负载？" summary="以 I6-A Mini MoE 为前置，先会写 MoE 层再学习其分布式系统：保留 Expert Parallel、All-to-All、Capacity 与负载均衡，加入 DeepEP / EPLB，理解专家并行的通信成本与稳定性。" >}}
- **前置依赖**：`I6-A Mini MoE`（先在小模型上写对 MoE 层，再进入分布式专家并行）。
- **学习内容**：
  - Expert Parallelism 与 All-to-All 通信；
  - Capacity Factor、Token Dropping 与负载均衡；
  - expert collapse 与路由稳定性；
  - DeepEP、EPLB 与专家负载均衡；
  - MoE 的训练稳定性、通信成本与评估方法。
- **规划交付物**：
  - 基于 I6-A MoE 层的分布式专家并行沙盘；
  - 路由与负载均衡指标；
  - All-to-All 通信量与单机模拟对照；
  - 单机模拟与分布式专家并行示意。
- **规划验收标准**：
  - 能证明 token 被路由到正确专家；
  - 能观察专家负载是否失衡；
  - 同时报告模型质量、训练稳定性、通信与资源成本；
  - 不把“参数量变大”直接写成“能力必然提升”。
{{< /milestone >}}

{{< milestone id="s5" code="S5" title="生产推理与 Serving" status="planning" question="当一个请求变成成千上万个请求，推理系统怎样保持吞吐、延迟与隔离？" summary="搭建最小生产 Serving 沙盘：保留 Paged KV Cache、Continuous Batching 与 TP / EP，加入 MTP 生产部署、量化 Kernel、背压 / 超时 / 多会话隔离，实测 TTFT / TPOT / 吞吐 / P95；区分 I6-C 的结构正确与本阶段的部署有效。" >}}
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
  - 区分 I6-C 的“结构正确”和本阶段的“部署有效”，不把结构跑通当成生产可用；
  - 性能结论必须来自实测（TTFT / TPOT / 吞吐 / P95），不照抄官方数字。
{{< /milestone >}}

{{< milestone id="s6" code="S6" title="稳定性、确定性与综合验收" status="planning" question="系统不只要能跑，还要能证明它稳定、可复现、可诊断、可恢复。" summary="补齐 batch-invariant inference、确定性采样、日志 trace 与故障注入压测，加入长上下文质量与性能、Dense V4 与各新架构的同口径对照，产出全景图、DeepInfer 总结与第三阶段收官笔记。" >}}
- **学习内容**：
  - batch-invariant inference；
  - deterministic sampling；
  - structured outputs；
  - 数值、行为、性能与分布式回归；
  - 长上下文质量与性能验收；
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
    rules="阶段定位::证明模型能力真的变强了——以 Agentic 后训练与能力形成为核心，多模态保持选修 | 前置依赖::现代架构底座已就绪，待 I4 / I5 后训练基础与第三阶段系统能力完成后展开 | 探索衔接::承载推理强化、模型诊断、扩层后训练（后续选修），以及下方尚未开始训练的 M7 个人中文语料 Midtrain"
>}}

- **Agentic 后训练与能力形成**：大规模 Agentic 数据合成、RLVR、自我评价奖励、工具调用与环境交互，以及更进一步的推理强化；
- **推理强化与对齐**：CoT、DPO、GRPO、RLVR（承接 I4 后训练基础）；
- **数据与评测工程**：指令数据工程与评委校准；
- **领域模型与权重诊断**：领域模型训练与评估、模型诊断和权重空间编程（探索记录见[《手搓 LLM 笔记 15：让 AI 直接修改模型权重，能学会四则运算吗？》](/llm/llm-15-weight-space-arithmetic/)）；
- **模型增长与扩层后训练（后续选修）**：研究 Block Expansion / Depth Up-Scaling（Net2Net、LLaMA Pro、SOLAR），在原有 Transformer Block 之后、`final_norm` 之前插入少量新层，重点理解恒等初始化、冻结与逐步解冻，并与 LoRA、全参数训练做同数据对照；不阻塞当前主线或 `M7`；
- **多模态（保持选修）**：不作为主阶段，只保留未来选修，不为补清单改变当前主线；
- **个人中文语料 midtrain（尚未开始训练）**：承载下方 `M7` 独立彩蛋。

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
    rules="阶段定位::将专用模型能力与 Skill 工具生态合流，构建可审计的多角色协作系统（多模态暂不作为主阶段，只保留未来选修）"
>}}

- **核心方向**：规划、执行、测试、运维分工（思路见[《企业级 AI 编程的终极形态：当模型开始分工》](/ai/enterprise-ai-model-division/)），以及记忆、上下文、权限、反馈闭环和多模型编排。

---

## 支线探索与日常节奏

- **权重空间编程（不阻塞主线）**：三轮 Weight-Space Programming 实验已独立整理为[《手搓 LLM 笔记 15：让 AI 直接修改模型权重，能学会四则运算吗？》](/llm/llm-15-weight-space-arithmetic/)，不放入主线依赖，不阻塞 M5、M6 或后续阶段。
- **默写与回炉（2026-10-29 增补）**：`GPTModel` 每两周在 A4 纸脱稿默写一次（首次记录见[《手搓 LLM 番外：A4 纸默写 GPTModel》](/llm/llm-extra-handwrite-gptmodel/)），`MHA` / `FFN` / `LayerNorm` 单独补漏；两周后对照进步。
- **nanochat 与官方参考实现对照**：第一阶段 `M0～M6` 与第二阶段 `I0`（`model_v3` 承接 Qwen2.5）、`I1`（工业数据工程与流式 IO）、`I2`（训练加速与显存压榨，含 RTX 4070 Ti CUDA 对照番外）、`I3`（高性能推理与服务引擎）已交付，后续推进 `I4～I5` 时继续以 `nanochat` 与 Hugging Face 官方参考实现作为对照基线，按实际依赖验证后训练与评估校准。
- **博客与掘金专栏输出**：每个里程碑（M0～M6、I0～I6、M7）产出一篇实录笔记；实验数据直接整理成可复现报告。
