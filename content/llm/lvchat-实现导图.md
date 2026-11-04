+++
title = "lvchat 实现导图：开工顺序即依赖顺序"
slug = "lvchat-roadmap"
aliases = ["/nanochat/lvchat-roadmap/"]
date = 2026-10-19T19:10:00+08:00
lastmod = 2026-11-04T16:55:00+08:00
draft = false
tags = ["LLM", "nanochat", "lvchat", "diy-llm", "AI-Infra", "学习笔记"]
summary = "按能力层级划分为六个阶段：第一阶段（从零手搓 LLM，M0～M6）已 7/7 完整交付；当前处于第二阶段（现代架构与模型承接，聚焦 I0 model_v3 演进与 Qwen 权重承接）；第三至第六阶段保留方向与依赖。"
[cover]
    image = "covers/lvchat-roadmap.jpg"
    alt = "lvchat 实现导图"
    hiddenInSingle = true
    hiddenInList = true
+++

{{< roadmap_overview
    north_star="目标：用纯 PyTorch 交付一个可对话的 355M 模型，并打通从数据到 WebUI 的全链路。"
    phases="phase-01::第一阶段::从零手搓 LLM::done::2026.10.13 → 2026.11.04 (M0～M6 已完成) | phase-02::第二阶段::现代架构与模型承接::active::当前阶段 · 聚焦 I0 (RoPE 已先行落地) | phase-03::第三阶段::训练、推理基础设施与 MoE::planning::规划中 · 算子/量化/分布式/MoE | phase-04::第四阶段::后训练与领域能力形成::planning::规划中 · 对齐/诊断/M7 个人语料 | phase-05::第五阶段::Skill 工程与工具生态::planning::远期 · 扫描/排查/MCP/开源规范 | phase-06::第六阶段::Agent 与多模型协作::planning::远期 · 多角色分工与编排闭环"
>}}

> **路线组织原则**：阶段数量由能力层级决定；**LLM 是长期主线**，横跨第一至第四阶段，之后再自然延伸至 Skill 工程与多模型 Agent 协作（多模态暂不作为主阶段，仅保留为未来选修）。目前只为**第一阶段**与**第二阶段**编写详细里程碑，第三至第六阶段仅保留演进方向与依赖关系，不拆细任务、不承诺时间。

---

{{< roadmap_progress
    id="phase-01"
    season="第一阶段 · 已完成"
    title="从零手搓 LLM（M0 ～ M6）"
    phase_state="done"
    start_date="2026年10月13日"
    end_date="2026年11月04日"
    duration="历时 23 天"
    repo="squid-llms"
    proposal_title="nanochat 立项书"
    proposal_url="/llm/nanochat-proposal/"
    rules="核心交付::完成从 tokenizer、模型、预训练、KV cache、SFT、评估到 CLI/Web UI 的完整工程闭环 | 工程策略::M0 重写底座，M1 起在 squid-llms 同仓生长，不另起新工程 | 推进铁律::nanochat 当“标准答案”不当教材，开工顺序即依赖顺序"
    done="7"
    total="7"
    current="M6 · 对话界面"
    delivered="第一季核心链路已交付"
    next="第二阶段 I0 · 现代架构"
    steps="m0:M0:重写底座:done, m1:M1:手写 BPE:done, m2:M2:预训练闭环:done, m3:M3:KV Cache:done, m4:M4:SFT 微调:done, m5:M5:评估框架:done, m6:M6:对话界面:done"
>}}

{{< phase_drawer open="true" summary="第一阶段里程碑明细（M0 ～ M6 全部已验收 · 点击可收起或展开）" >}}

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
- **核心实现**：选择题评测（字母 logits、完整答案条件似然和选项打乱对照）+ DeepSeek 自由生成评分与双端断点续跑流水线
- **验收实绩**：
  - 完成选择题字母 logits、完整答案条件似然和选项打乱对照；
  - 完成 DeepSeek 自由生成评分；
  - 生成与评分分离，双方均支持断点续跑；
  - 110 条 held-out test 全部完成，`valid_scores=110/110`；
  - 生成结构化 JSON 报告，包含均分、中位数、分布和逐题明细；
  - 相关回归 `17 passed`。
{{< /milestone >}}

{{< milestone id="m6" code="M6" title="对话界面" status="done" date="2026-11-04" note1_title="笔记 16：给 355M 模型装上对话界面" note1_url="/llm/llm-16-chat-web-ui/" >}}
- **核心实现**：命令行多轮对话 CLI + Python 标准库 HTTP 推理服务 + 纯 HTML/CSS/JavaScript Web UI，打通从浏览器输入到本地 355M 模型回答的完整工程闭环
- **验收实绩**：
  - 完成 `ChatSession`、原始问答 history 和最近 5 轮滑动窗口；
  - 完成 CLI 多轮输入、`/clear` 和 `/exit`；
  - 使用 Python 标准库完成 HTTP 推理服务；
  - 完成纯 HTML/CSS/JavaScript Web UI；
  - 真实浏览器中输入问题并收到本地 355M 模型回答；
  - CLI、HTTP 服务与 Web UI 工程链路均已跑通。
- **能力边界**：当前 355M SFT 模型没有经过可靠的多轮对话训练，连续对话会复制旧回答。工程链路完成，不代表可靠多轮语义能力已经合格。
{{< /milestone >}}

{{< /phase_drawer >}}

---

{{< roadmap_progress
    id="phase-02"
    season="第二阶段 · 当前阶段"
    title="现代架构与模型承接（聚焦 I0）"
    phase_state="active"
    repo="squid-llms"
    proposal_title="diy-llm 立项书"
    proposal_url="/llm/diy-llm-proposal/"
    theory_title="DataWhale diy-llm 教程"
    theory_url="https://datawhalechina.github.io/diy-llm/%E5%89%8D%E8%A8%80.html"
    rules="核心聚焦::只聚焦 I0 现代架构与开源权重承接，训练加速、分布式与后训练移交后续阶段 | 版本隔离策略::新建独立 model_v3，保持 v1_gpt、v2_rope、v3_modern 三代并存、独立测试与验收 | 理论蓝本::以 DataWhale diy-llm 为第二至第四阶段系统理论蓝本，按实际项目需要调用"
    done="1"
    total="5"
    unit="I0 架构子项已完成"
    current="RoPE 已完成（提前落地）"
    next="第二阶段 I0 · 现代架构（RMSNorm / SwiGLU / GQA / Qwen 权重承接）"
    steps="i0:RoPE:已完成(提前落地):done, i0:RMSNorm:待开工:next, i0:SwiGLU:待开工:todo, i0:GQA:待开工:todo, i0:Qwen承接:待开工:todo"
>}}

{{< milestone id="i0" code="I0" title="现代架构与模型承接（model_v3）" status="next" note1_title="RoPE 先行记录：笔记 14" note1_url="/llm/llm-14-eval-resume/" >}}
- **工程演进与版本策略**：
  - 新建独立的 `model_v3` 模型版本，不持续修改旧模型；
  - 旧版本保持独立，清晰体现学习演进与版本差异：
    - `v1_gpt`：GPT-2 绝对位置编码 + KV cache；
    - `v2_rope`：独立 RoPE 模型；
    - `v3_modern`：现代架构与 Qwen 权重承接；
  - 能复用的底层组件直接复用，不能复用的组件在新版本中重写；每个版本独立测试、独立验收。
- **I0 子项当前状态（仅 RoPE 部分完成，整体未完结）**：
  1. **RoPE 已完成（提前落地）**：已完成独立模型、数学性质测试、非零 `past_len` 下 cache 对齐、以及小模型训练冒烟与 checkpoint 验收（详见[《手搓 LLM 笔记 14：M5，让评估能够中断后继续》](/llm/llm-14-eval-resume/)）；
  2. **RMSNorm**：待开工；
  3. **SwiGLU**：待开工；
  4. **GQA（分组查询注意力）**：待开工；
  5. **Qwen 权重加载与评估**：待开工——需要同时处理 tokenizer、权重命名、模型配置和 checkpoint 路由，不是只改一个模型类。
{{< /milestone >}}

---

## 后续演进阶段（第三至第六阶段 · 只列方向与依赖）

> 第三至第六阶段只保留演进方向与前置依赖，不提前拆细任务清单，也不承诺时间；**[DataWhale `diy-llm`](https://datawhalechina.github.io/diy-llm/%E5%89%8D%E8%A8%80.html)** 作为第二至第四阶段的系统理论蓝本，按实际项目需要随时调用，无需无差别重读所有章节。

{{< roadmap_progress
    id="phase-03"
    season="第三阶段 · 规划中"
    title="训练、推理基础设施与 MoE"
    phase_state="planning"
    hide_bar="true"
    repo="squid-llms"
    rules="前置依赖::第二阶段 I0 现代架构（model_v3）与 Qwen 权重承接验收完成后启动 | MoE 学习策略::与 GPU 和分布式一起学——先在小模型上实现 Top-K 路由和负载均衡，再理解 Expert Parallelism 与通信开销"
>}}

- **训练与算子优化**：GPU 硬件原理、混合精度（BF16 / FP16）、FlashAttention、CUDA / Triton 等训练与算子优化；
- **推理与服务基础设施**：量化（INT8 / INT4）、投机解码（Speculative Decoding）、流式推理和高性能服务；
- **分布式与资源核算**：分布式训练、ZeRO / FSDP、资源核算；
- **MoE 混合专家模型**：先在小模型上实现 Top-K 路由和负载均衡，再结合 GPU 与分布式理解 Expert Parallelism 与通信开销。

{{< roadmap_progress
    id="phase-04"
    season="第四阶段 · 规划中"
    title="后训练与领域能力形成"
    phase_state="planning"
    hide_bar="true"
    repo="squid-llms"
    rules="前置依赖::现代架构底座与训练/推理基础设施就绪后展开 | 探索衔接::含模型诊断与权重空间编程（笔记 15），以及 M7 个人中文语料 Midtrain 独立彩蛋"
>}}

- **推理强化与偏好对齐**：CoT（思维链）、DPO、GRPO、RLVR；
- **数据与评测工程**：指令数据工程与评委校准；
- **领域化与模型诊断**：领域模型训练与评估、模型诊断和权重空间编程（前期探索见[《手搓 LLM 笔记 15：让 AI 直接修改模型权重，能学会四则运算吗？》](/llm/llm-15-weight-space-arithmetic/)）；
- **个人中文语料 midtrain**：承载下方 `M7` 独立彩蛋。

{{< milestone id="m7" code="M7" title="第四阶段独立彩蛋：个人中文语料中间训练（Midtrain）" status="optional" >}}
- **定位说明**：从第一阶段移入第四阶段，作为独立彩蛋，不计入第一阶段完成度。
- **底座边界说明**：当前 GPT-2 355M 底座偏英文，不适合直接承接全中文个人语料，因此不再把 `M7` 放在第一阶段硬做。
- **前置依赖**：先完成第二阶段 `I0` 现代架构改造并能正确加载 Qwen，再使用个人中文语料（年终总结、有道云笔记与博客全量中文语料）进行 midtrain。
{{< /milestone >}}

{{< roadmap_progress
    id="phase-05"
    season="第五阶段 · 远期"
    title="Skill 工程与工具生态"
    phase_state="planning"
    hide_bar="true"
    rules="阶段定位::在扎实的模型与后训练认知之上，沉淀面向真实工程现场的 Skill 工具链与标准规范"
>}}

- **核心方向**：系统扫描、生产排查、学习辅助、MCP / CLI 工具封装、权限边界控制、Skill 评估体系与开源文档建设（前期实践见[《生产排查 Skill 深解》](/incident-skill/introduction/)与[《系统扫描 Skill 深解》](/scan-skill/introduction/)）。

{{< roadmap_progress
    id="phase-06"
    season="第六阶段 · 远期"
    title="Agent 与多模型协作"
    phase_state="planning"
    hide_bar="true"
    rules="阶段定位::将专用模型能力与 Skill 工具生态合流，构建可审计的多角色协作系统"
>}}

- **核心方向**：规划、执行、测试、运维角色分工（思路雏形见[《企业级 AI 编程的终极形态：当模型开始分工》](/ai/enterprise-ai-model-division/)），以及记忆管理、上下文路由、权限门禁、反馈闭环和多模型编排（多模态暂保留为未来选修方向）。

---

## 支线探索与日常节奏

- **权重空间编程（不阻塞主线）**：三轮 Weight-Space Programming 实验已独立整理为[《手搓 LLM 笔记 15：让 AI 直接修改模型权重，能学会四则运算吗？》](/llm/llm-15-weight-space-arithmetic/)，不放入主线依赖，不阻塞 M5、M6 或后续阶段。
- **默写与回炉**：`GPTModel` 每两周在 A4 纸脱稿默写一次（首次记录见[《手搓 LLM 番外：A4 纸默写 GPTModel》](/llm/llm-extra-handwrite-gptmodel/)），`MHA` / `FFN` / `LayerNorm` 单独补漏；两周后对照进步。
- **nanochat 源码对照**：第一阶段 `M0～M6` 已完整交付，配合第二阶段 `I0` 现代架构改造对照 Karpathy 的 `nanochat` 源码。
