+++
title = "lvchat 实现导图：开工顺序即依赖顺序"
slug = "lvchat-roadmap"
aliases = ["/nanochat/lvchat-roadmap/"]
date = 2026-10-19T19:10:00+08:00
lastmod = 2026-11-04T17:27:00+08:00
draft = false
tags = ["LLM", "nanochat", "lvchat", "diy-llm", "AI-Infra", "学习笔记"]
summary = "多阶段推进：第一阶段（2026.10.13—2026.11.04）已完成 M0～M6 整车核心链路交付（7/7）；当前处于第二阶段，全量展开 I0～I6 + M7（现代架构 model_v3 与 Qwen 权重承接、AI-Infra 装备升级及个人中文语料 Midtrain），并预留后续 Skill 与 Agent 演进阶段。"
[cover]
    image = "covers/lvchat-roadmap.jpg"
    alt = "lvchat 实现导图"
    hiddenInSingle = true
    hiddenInList = true
+++

{{< roadmap_overview
    north_star="目标：用纯 PyTorch 交付一个可对话的 355M 模型，并打通从数据到 WebUI 的全链路。"
    phases="phase-01::STAGE 01 · 第一阶段::从零手搓 LLM (M0～M6)::done::2026.10.13 → 2026.11.04 (7/7 已交付) | phase-02::STAGE 02 · 第二阶段::现代架构与 AI-Infra 装备进化 (I0～I6+M7)::active::2026.11.04 启动 · 当前主战场 | phase-03::STAGE 03 · 第三阶段::Skill 工程与工具生态::planning::远期规划 · 扫描/排查/MCP/开源规范 | phase-04::STAGE 04 · 第四阶段::Agent 与多模型协作::planning::远期规划 · 多角色分工与编排闭环"
>}}

{{< roadmap_progress
    id="phase-01"
    season="STAGE 01 · 第一阶段（已完成）"
    title="从零件到整车：自造 lvchat v1（M0 ～ M6）"
    phase_state="done"
    start_date="2026年10月13日"
    end_date="2026年11月04日"
    duration="历时 23 天"
    repo="squid-llms"
    proposal_title="nanochat 立项书"
    proposal_url="/llm/nanochat-proposal/"
    rules="基准原则::nanochat 当“标准答案”不当教材，从手搓代码长出整车 | 工程策略::M0 重写底座，M1 起同仓生长，不另起新工程 | 推进铁律::开工顺序即依赖顺序，M0～M6 核心链路已完整交付"
    done="7"
    total="7"
    current="M6 · 对话界面"
    delivered="第一季核心链路已交付"
    next="第二阶段 I0 · 现代架构"
    steps="m0:M0:重写底座:done, m1:M1:手写 BPE:done, m2:M2:预训练闭环:done, m3:M3:KV Cache:done, m4:M4:SFT 微调:done, m5:M5:评估框架:done, m6:M6:对话界面:done"
>}}

{{< phase_drawer summary="已归档 · 点击展开第一阶段 M0 ～ M6 全部 7 张验收卡片与实录笔记（点击上方 M0～M6 节点可直接跳转）" >}}

{{< milestone id="m0" code="M0" title="重写全书代码（底座重构）" status="done" date="2026-10-26" note1_title="笔记 08：重写 lvllm" note1_url="/llm/llm-08-rewrite-lvllm/" >}}
- **核心实现**：按工程结构重写《从零构建大模型》全书代码（`tokenizer` / `model` / `data` / `train` / `generate` / `eval` / `checkpoints` 七层解耦、单一 `config` 与 `device` 入口、checkpoint 三层标准化）
- **验收实绩**：13 个单元测试全绿；355M LoRA 回归评测 **23.6 vs 旧仓库 23.9**（分布一致），欠账注释清单归零
{{< /milestone >}}

{{< milestone id="m1" code="M1" title="自训 BPE Tokenizer" status="done" date="2026-10-27" note1_title="笔记 09：分词器全景" note1_url="/llm/llm-09-diy-llm-tokenizer/" note2_title="笔记 10：手写 BPE 与甜点区" note2_url="/llm/llm-10-handwritten-bpe/" >}}
- **核心实现**：纯 Python 手写 `count_pairs` / `merge` / `train_bpe` 训练与编解码，封装为 `MyBPETokenizer`，不调 `tiktoken`
- **验收实绩**：编解码往返一字不差（无损）；完成压缩率曲线与微型模型固定 500 步 BPB 扫描，锁定博客语料合并甜点区在 **4000 merges（BPB 3.315）**
{{< /milestone >}}

{{< milestone id="m2" code="M2" title="预训练闭环（Pretrain）" status="done" date="2026-10-28" note1_title="笔记 11：资源核算与预训练" note1_url="/llm/llm-11-pytorch-resource-accounting/" >}}
- **核心实现**：token 流打包（`pack_tokens`）、流式 dataloader、梯度累积（小批立即 backward + 跨轮 `global_step`）、BPB 指标与带 `config` 的 checkpoint 存档
- **验收实绩**：完成容量与深度扫描，定位小语料甜点 **emb_dim=256、n_layers=2（BPB 3.10）**，复现 512 维过拟合拐点，模型成功咿呀学语
{{< /milestone >}}

{{< milestone id="m3" code="M3" title="推理引擎（KV Cache）" status="done" date="2026-10-29" note1_title="笔记 12：KV Cache 与第一次说人话" note1_url="/llm/llm-12-kv-cache/" >}}
- **核心实现**：给 `generate`、`GPTModel.forward`、`MHA.forward` 三层装上无状态 KV Cache 接力，处理增量步位置偏移 `arange(past_len, past_len + seq_len)` 与显式 `use_cache` 开关
- **验收实绩**：贪心采样下输出与朴素版**逐字一致**；512 tokens 生成从 **36.10s 降至 10.00s（实测提速 3.6x）**，第一次看到自己手搓的模型流畅说人话
{{< /milestone >}}

{{< milestone id="m4" code="M4" title="指令微调（SFT）" status="done" date="2026-10-30" note1_title="笔记 13：SFT，从续写机到指令跟随" note1_url="/llm/llm-13-sft-instruction-following/" >}}
- **核心实现**：将第七章 SFT 数据与训练管道移植至自训底座，打开 completion-only 掩码（只对 response 答卷位置计分）
- **验收实绩**：套指令模板稳定作答；base 全 0 分 vs SFT 均分 31.2（110 条 test，接近旧仓库全参 33.5 基线）；cache 与朴素版输出一致，提速 1.6x
{{< /milestone >}}

{{< milestone id="m5" code="M5" title="评估框架（Eval & Judge）" status="done" date="2026-11-04" note1_title="笔记 14：M5，让评估能够中断后继续" note1_url="/llm/llm-14-eval-resume/" >}}
- **核心实现**：选择题评测（字母 logits、完整答案条件似然与选项打乱对照）+ DeepSeek LLM-as-judge 自由生成自动打分与双端断点续跑流水线
- **验收实绩**：
  - 完成选择题字母 logits、完整答案条件似然和选项打乱对照；
  - 完成 DeepSeek 自由生成评分；
  - 生成与评分分离，双方均支持断点续跑；
  - 110 条 held-out test 全部完成，`valid_scores=110/110`；
  - 生成结构化 JSON 报告，包含均分、中位数、分布和逐题明细；
  - 相关回归 `17 passed`。
{{< /milestone >}}

{{< milestone id="m6" code="M6" title="对话界面（CLI + Web UI）" status="done" date="2026-11-04" note1_title="笔记 16：给 355M 模型装上对话界面" note1_url="/llm/llm-16-chat-web-ui/" >}}
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
    season="STAGE 02 · 第二阶段（正在进行）"
    title="从能跑到能打：现代架构承接与 AI-Infra 装备升级（I0 ～ I6 + M7）"
    phase_state="active"
    start_date="2026年11月04日"
    end_date="进行中"
    repo="squid-llms"
    proposal_title="diy-llm 立项书"
    proposal_url="/llm/diy-llm-proposal/"
    theory_title="DataWhale diy-llm 教程"
    theory_url="https://datawhalechina.github.io/diy-llm/%E5%89%8D%E8%A8%80.html"
    rules="装备来源::剥离自第一季的全部工业级选修项 + 第一季实测暴露的工程与模型边界 | 理论蓝本::第二阶段统一以 DataWhale diy-llm（CS336 中文本土化 16 章 + 6 作业）为系统学习蓝本 | 进化目标::在 lvchat v1 整车底盘上按 I0～I6 项目驱动逐件换装现代架构、算子加速、量化推理与强化对齐"
    done="0"
    total="6"
    current="I0 子项 RoPE 已提前落地"
    next="I0 · 现代架构与模型承接（model_v3 / RMSNorm / SwiGLU / GQA / Qwen 权重加载）"
    steps="i0:I0:现代架构:next, i1:I1:数据与流式IO:todo, i2:I2:训练与算子加速:todo, i3:I3:量化与投机推理:todo, i4:I4:CoT与偏好对齐:todo, i5:I5:评委校准CI:todo, i6:I6:MoE与分布式:optional, m7:M7:中文语料Midtrain:optional"
>}}

## 第二阶段施工流水线：现代架构承接与 AI-Infra 装备全量蓝图（I0 → I6 + M7）

> 第一季解决“**有没有一辆自己造的车**”，第二季以 [DataWhale `diy-llm`](https://datawhalechina.github.io/diy-llm/%E5%89%8D%E8%A8%80.html) 为系统理论蓝本，解决“**怎么把 GPT-2 时代的老爷车改装成现代工业级大模型**”。每一站都直接改造 `squid-llms` 里的对应模块，用前后对照实验说话。

{{< milestone id="i0" code="I0" title="现代架构与模型承接（model_v3：RoPE + RMSNorm + SwiGLU + GQA + Qwen 权重加载）" status="next" note1_title="RoPE 先行记录：笔记 14" note1_url="/llm/llm-14-eval-resume/" >}}
- **版本演进策略**：
  - 新建独立的 `model_v3` 模型版本，不持续修改旧模型；
  - 旧版本保持独立，体现学习演进和版本差异：
    - `v1_gpt`：GPT-2 绝对位置 + KV cache；
    - `v2_rope`：独立 RoPE 模型；
    - `v3_modern`：现代架构与 Qwen 权重承接；
  - 能复用的底层组件直接复用，不能复用的组件在新版本中重写；每个版本独立测试、独立验收。
- **I0 子项状态（仅 RoPE 部分完成，整体待收官）**：
  1. **RoPE 已完成（提前落地）**：已完成独立模型、数学性质测试、非零 `past_len` 下 cache 对齐、小模型训练冒烟与 checkpoint 验收（详见[笔记 14](/llm/llm-14-eval-resume/)）；
  2. **RMSNorm**：待开工（替代 `LayerNorm`，省去均值中心化计算）；
  3. **SwiGLU**：待开工（FFN 换装门控线性单元）；
  4. **GQA（分组查询注意力）**：待开工（成倍压缩推理期 KV Cache 显存占用）；
  5. **Qwen 权重加载与评估**：待开工——需要同时处理 tokenizer、权重命名、模型配置和 checkpoint 路由，不是只改一个模型类。
- **diy-llm 结合**：[diy-llm](https://datawhalechina.github.io/diy-llm/%E5%89%8D%E8%A8%80.html) 第 4 章（现代 Transformer 架构演进）+ 作业 2
- **进化验收**：完成 `model_v3`（RMSNorm / SwiGLU / GQA）拼装并正确加载与评估 Qwen 权重，对比经典 GPT-2 结构与现代结构的训练吞吐、KV 显存占用与最终 BPB
{{< /milestone >}}

{{< milestone id="i1" code="I1" title="工业数据工程与流式 IO（Data Pipeline & Scaling）" status="todo" >}}
- **进化部位**：改造 `squid/data/` 与 `squid/tokenizer/`
- **装备升级**：
  1. **语料工程管线**：网页/长文清洗、启发式质量过滤、MinHash 去重与多源语料配比；
  2. **内存映射流式加载（`np.memmap`）**：告别 `read_text()` 全量塞内存，支持 GB 级语料零拷贝随机切片；
  3. **分词器热路径提速**与 Chinchilla **Scaling Laws** 最优“参数量 vs Token 数”配比测算。
- **diy-llm 结合**：[diy-llm](https://datawhalechina.github.io/diy-llm/%E5%89%8D%E8%A8%80.html) 第 2 章（分词器进阶）+ 第 11 章（数据工程）+ 第 9 章（Scaling Laws）+ 作业 1 & 作业 5
- **进化验收**：内存占用与语料总体积脱钩（恒定低内存跑大语料），给出清洗前后同模型 BPB 对照
{{< /milestone >}}

{{< milestone id="i2" code="I2" title="训练加速与显存压榨（AMP + FlashAttention + Compile）" status="todo" >}}
- **进化部位**：改造 `squid/train/` 与注意力算子
- **装备升级**：
  1. **BF16 自动混合精度（AMP）** 实战落地，对比 FP32 / FP16 / BF16 的动态范围、吞吐与显存账本；
  2. 接入 **FlashAttention** 与 `torch.compile` 算子融合，消除注意力 $O(T^2)$ 显存中间矩阵读写瓶颈；
  3. 激活重计算（Activation Checkpointing）用算力换显存，把单卡可训上下文窗口与 batch size 推到极限。
- **diy-llm 结合**：[diy-llm](https://datawhalechina.github.io/diy-llm/%E5%89%8D%E8%A8%80.html) 第 3 章（混合精度与算术强度）+ 第 6～7 章（GPU 架构与算子优化）+ 作业 3
- **进化验收**：产出单卡训练 MFU（算力利用率）、峰值显存与 tokens/sec 的前中后三档实测表
{{< /milestone >}}

{{< milestone id="i3" code="I3" title="高性能推理与服务引擎（量化 + 投机解码 + 流式 Serving）" status="todo" >}}
- **进化部位**：承接 M3 / M6 遗留的服务层进阶项，改造 `squid/generate/` 与对话服务层
- **装备升级**：
  1. **滑动窗口 / 会话级 KV Cache** 与按 token 预算的 history 截断管理（消除动态 `torch.cat` 拷贝与粗粒度轮数截断）；
  2. **INT8 / INT4 权重量化推理**（W8A16 / W4A16），实测模型体积压缩比与困惑度损益；
  3. **投机解码（Speculative Decoding）**：用极小草稿模型（Draft Model）一次猜多个 token，主模型单次前向并行校验，打破自回归内存带宽墙；
  4. **SSE 流式输出**与多用户/多会话状态隔离管理。
- **diy-llm 结合**：[diy-llm](https://datawhalechina.github.io/diy-llm/%E5%89%8D%E8%A8%80.html) 第 10 章（推理加速：KV Cache 进阶、量化、投机解码）
- **进化验收**：在 M3 的 3.6x 提速基线上，测出量化与投机解码叠加后的首字延迟（TTFT）、解码吞吐（tokens/s）与显存降幅
{{< /milestone >}}

{{< milestone id="i4" code="I4" title="后训练深水区：多轮对话 SFT、CoT 思维链与 DPO / GRPO 对齐" status="todo" >}}
- **进化部位**：承接 M4 与 M6 暴露的“多轮旧答案复制”边界，升级 `squid/data/instruct.py` 与 `squid/train/`
- **装备升级**：
  1. **真正的多轮对话 SFT + 思维链（CoT）微调**：引入多轮对话指令数据与按轮掩码（解决 M6 暴露的多轮历史复制问题），并构造“推理步骤 `<think>` + 最终答案”数据；
  2. **LoRA vs 全参微调**在现代底座上的系统对标；
  3. **偏好对齐与强化学习**：手写 **DPO（直接偏好优化）** 损失函数，并探索 **RLVR / GRPO**（群组相对策略优化）在数学/代码可验证任务上的最小闭环。
- **diy-llm 结合**：[diy-llm](https://datawhalechina.github.io/diy-llm/%E5%89%8D%E8%A8%80.html) 第 13 章（Pre-training / SFT / DPO 全流程）+ 第 14 章（GRPO / RLVR 强化学习）
- **进化验收**：解决 Web UI 多轮对话复制旧答案问题，并给出 SFT vs CoT-SFT vs DPO 的评委胜率（Win Rate）对比
{{< /milestone >}}

{{< milestone id="i5" code="I5" title="评估校准与回归基准自动化（Judge Calibration）" status="todo" >}}
- **进化部位**：承接 M5 评估流水线，升级 `squid/eval/`
- **装备升级**：
  1. **LLM-as-Judge 偏见校准**：双向交换位置消除先后偏见（Position Bias）、控制长度偏见（Length Bias）；
  2. **多评委交叉一致性检验**：计算人工评分与 AI 评委的相关系数，建立每次架构/数据改动后的自动化回归门禁。
- **diy-llm 结合**：[diy-llm](https://datawhalechina.github.io/diy-llm/%E5%89%8D%E8%A8%80.html) 第 12 章（评估与基准）+ 作业 6
- **进化验收**：每次装备升级（I0～I4）均可一键跑出带置信区间与胜率矩阵的对比报告
{{< /milestone >}}

{{< milestone id="i6" code="I6" title="第二季独立彩蛋 A：MoE 稀疏专家与分布式并行沙盘" status="optional" >}}
- **定位说明**：独立高阶架构彩蛋，不计入主线进度；与 GPU 和分布式一起学——先在小模型上实现 Top-K 路由和负载均衡，再理解 Expert Parallelism 与通信开销
- **装备升级**：
  1. 把稠密 FFN 改造为迷你 **MoE（Mixture of Experts）** 层：实现 Top-K 门控路由与负载均衡辅助损失（Load Balancing Loss）；
  2. 走通数据并行（DDP）与分片优化器状态（ZeRO / FSDP 核心思想）的最小复现。
- **diy-llm 结合**：[diy-llm](https://datawhalechina.github.io/diy-llm/%E5%89%8D%E8%A8%80.html) 第 5 章（MoE 混合专家模型）+ 第 8 章（分布式训练）+ 作业 4
- **进化验收**：在总参数量放大但单 token 激活参数不变的前提下，验证 MoE 模型的收敛曲线与路由均衡度
{{< /milestone >}}

{{< milestone id="m7" code="M7" title="第二季独立彩蛋 B：个人中文语料中间训练（Midtrain）" status="optional" >}}
- **新定位**：个人中文语料中间训练（Midtrain）——喂入个人年终总结、有道云笔记与博客全量中文语料做继续训练与个人风格注入（与 `I6` 彩蛋分开，不计入第一季或第二季主线进度）
- **底座边界说明**：当前第一季 GPT-2 355M 底座偏英文，不适合直接承接全中文个人语料；`M7` 等到现代架构和 Qwen 权重加载能力完成后再启动
- **前置依赖条件**：
  1. 先完成 `I0` 现代架构改造；
  2. 能正确加载并运行 Qwen 权重；
  3. 再使用个人中文语料进行 midtrain。
- **验收标准**：“吕炘嵘 GPT”第一次附体
{{< /milestone >}}

---

## 远期阶段规划池（第三至第四阶段 · 只列方向与依赖）

> 后续阶段在手搓 LLM 与 AI-Infra 满配之后承接，只保留方向与前置依赖，不提前拆细任务清单，也不承诺时间。

{{< roadmap_progress
    id="phase-03"
    season="STAGE 03 · 第三阶段（远期规划）"
    title="Skill 工程与工具生态"
    phase_state="planning"
    hide_bar="true"
    rules="阶段定位::在扎实的模型、架构与后训练认知之上，沉淀面向真实工程现场的 Skill 工具链与标准规范 | 核心方向::系统扫描、生产排查、学习辅助、MCP / CLI 工具封装、权限边界控制、评估体系与开源文档（前期实践见《生产排查 Skill 深解》与《系统扫描 Skill 深解》）"
>}}

{{< roadmap_progress
    id="phase-04"
    season="STAGE 04 · 第四阶段（远期规划）"
    title="Agent 与多模型协作"
    phase_state="planning"
    hide_bar="true"
    rules="阶段定位::将专用模型能力与 Skill 工具生态合流，构建可审计的多角色协作系统（多模态暂保留为未来选修） | 核心方向::规划、执行、测试、运维角色分工（思路见《企业级 AI 编程的终极形态：当模型开始分工》），以及记忆、上下文、权限、反馈闭环和多模型编排"
>}}

---

## 支线探索与日常节奏

- **独立支线探索（不阻塞主线）**：三轮 Weight-Space Programming（权重空间编程）实验已独立整理为[《手搓 LLM 笔记 15：让 AI 直接修改模型权重，能学会四则运算吗？》](/llm/llm-15-weight-space-arithmetic/)，不作为 M5、M6 或后续阶段主线阻塞条件。
- **默写与回炉（2026-10-29 增补）**：`GPTModel` 每两周在 A4 纸脱稿默写一次（首次记录见[《手搓 LLM 番外：A4 纸默写 GPTModel》](/llm/llm-extra-handwrite-gptmodel/)），`MHA` / `FFN` / `LayerNorm` 单独补漏；两周后对照进步。
- **nanochat 源码对照时机**：**第一季 M0～M6 整车核心链路已交付**，接下来把 Karpathy 的 `nanochat` 源码从头到尾当“标准答案”通读对照一遍——手里已经有了自己的 `lvchat v1` 完整实现，正好带着问题去查他怎么处理现代架构与多轮对话细节，无缝推进第二季 I0。
- **博客与掘金专栏输出**：每个里程碑（M0～M6、I0～I6、M7）产出一篇实录笔记；实验数据直接整理成可复现报告。
