+++
title = "lvchat 实现导图：开工顺序即依赖顺序"
slug = "lvchat-roadmap"
aliases = ["/nanochat/lvchat-roadmap/"]
date = 2026-10-19T19:10:00+08:00
lastmod = 2026-10-30T09:56:00+08:00
draft = false
tags = ["LLM", "nanochat", "lvchat", "学习笔记"]
summary = "不照抄 nanochat，以它为标准答案，从书里的手搓代码出发，自己长一个 nanochat-lite。八个里程碑按依赖排序，目前已通关至 M3（KV Cache 推理引擎）。"
[cover]
    image = "covers/lvchat-roadmap.jpg"
    alt = "lvchat 实现导图"
    hiddenInSingle = true
    hiddenInList = true
+++

> 本图是 [nanochat 立项书](/llm/nanochat-proposal/) 的施工图。工程落地在 `squid-llms` 仓库：M0 重写底座，M1 起所有里程碑都在同一仓库内生长，不另起新工程（2026-10-26 定）。原则：nanochat 仓库当“标准答案”，不当教材；从《从零构建大模型》的手搓代码出发，自己长一个 `nanochat-lite`（暂名 `lvchat`）。里程碑按依赖排序——开工顺序就是下面这条流水线的顺序。

{{< roadmap_progress done="4" total="7" current="M3 · KV Cache 推理引擎" next="M4 · SFT 指令微调" >}}

## 统一施工流水线（M0 → M7）

{{< milestone id="m0" code="M0" title="重写全书代码（底座重构）" status="done" date="2026-10-26" note1_title="笔记 08：重写 lvllm" note1_url="/llm/llm-08-rewrite-lvllm/" >}}
- **实现**：按工程结构重写全书代码（七层解耦、单一 `config` / `device` 入口、checkpoint 三层标准化）
- **配套与选修**：全书第一至七章 + 附录 D/E 终极回炉
- **验收实绩**：13 个单元测试全绿；355M LoRA 回归评测 **23.6 vs 旧仓库 23.9**（分布一致），欠账注释清单归零
{{< /milestone >}}

{{< milestone id="m1" code="M1" title="自训 BPE Tokenizer" status="done" date="2026-10-27" note1_title="笔记 09：分词器全景" note1_url="/llm/llm-09-diy-llm-tokenizer/" note2_title="笔记 10：手写 BPE 与甜点区" note2_url="/llm/llm-10-handwritten-bpe/" >}}
- **实现**：纯 Python 手写 `count_pairs` / `merge` / `train_bpe` 训练与编解码，封装为 `MyBPETokenizer`，不调 `tiktoken`
- **配套**：diy-llm 第 2 章（分词器）+ 作业 1
- **选修**：压缩率曲线（`bytes/token`）与微型模型固定 500 步 BPB 联合扫描
- **验收实绩**：编解码往返一字不差（无损）；测出博客语料合并甜点区在 **4000 merges（BPB 3.315）**
{{< /milestone >}}

{{< milestone id="m2" code="M2" title="预训练闭环（Pretrain）" status="done" date="2026-10-28" note1_title="笔记 11：资源核算与预训练" note1_url="/llm/llm-11-pytorch-resource-accounting/" >}}
- **实现**：token 流打包（`pack_tokens`）、流式 dataloader、梯度累积（小批立即 backward + 跨轮 `global_step`）、BPB 指标与带 `config` 的 checkpoint 存档
- **配套**：diy-llm 第 3 章（资源核算）+ 第 11 章（数据工程）+ 第 9 章（Scaling Laws）
- **选修**：混合精度（BF16 vs FP16）、算术强度（Memory-bound vs Compute-bound）、`emb_dim` 与 `n_layers` 容量扫描
- **验收实绩**：定位小语料容量甜点 **emb_dim=256、n_layers=2（BPB 3.10）**，复现 512 维过拟合拐点，模型成功咿呀学语
{{< /milestone >}}

{{< milestone id="m3" code="M3" title="推理引擎（KV Cache）" status="done" date="2026-10-29" note1_title="笔记 12：KV Cache 与第一次说人话" note1_url="/llm/llm-12-kv-cache/" >}}
- **实现**：给 `generate`、`GPTModel.forward`、`MHA.forward` 三层装上无状态 KV Cache 接力，处理增量步位置偏移 `arange(past_len, past_len + seq_len)` 与显式 `use_cache` 开关
- **配套**：diy-llm 第 10 章 推理（KV Cache、投机解码、量化）
- **选修**：**RoPE**（替代 `pos_emb`，解决位置溢出）、量化（INT8/INT4）、投机解码、FlashAttention
- **验收实绩**：贪心采样下输出与朴素版**逐字一致**；512 tokens 生成从 **36.10s 降至 10.00s（实测提速 3.6x）**，第一次看到自己手搓的模型流畅说人话
{{< /milestone >}}

{{< milestone id="m4" code="M4" title="指令微调（SFT）" status="next" >}}
- **实现**：第七章管道移植至自训底座，打开 completion-only 掩码（只对答卷计分）
- **配套**：diy-llm 第 13 章（Pre-training / SFT / DPO 全流程）
- **选修**：指令数据工程、completion-only 掩码、LoRA 与全参对比、**思维链（CoT）数据**（推理步骤+答案）、RLVR / GRPO（后置了解）
- **验收标准**：套指令模板稳定作答 + 评估集分数对比
{{< /milestone >}}

{{< milestone id="m5" code="M5" title="评估框架（Eval & Judge）" status="todo" >}}
- **实现**：基模选择题评测 + DeepSeek LLM-as-judge 自动打分流水线
- **配套**：diy-llm 第 12 章（评估与基准）+ 作业 6
- **选修**：评委一致性校准、断点续跑、分位与直方图报告自动化
- **验收标准**：一键产出结构化 JSON 评估报告
{{< /milestone >}}

{{< milestone id="m6" code="M6" title="对话界面（CLI + Web UI）" status="todo" >}}
- **实现**：命令行多轮对话 CLI + 轻量 Web 对话页
- **配套**：推理服务封装与多轮上下文拼接
- **选修**：Token 流式输出（SSE）、serving 基础、对话状态与历史截断管理
- **验收标准**：祁总打开浏览器能直接聊上
{{< /milestone >}}

{{< milestone id="m7" code="M7" title="彩蛋：领域中间训练（Midtrain）" status="optional" >}}
- **实现**：喂入个人年终总结 + 有道云笔记与博客语料做继续训练
- **配套**：midtrain 领域注入思路
- **选修**：领域语料清洗、配比与防遗忘回放
- **验收标准**：“吕炘嵘 GPT”第一次附体
{{< /milestone >}}

---

## 明确砍掉与风险复盘

- **明确砍掉**：分布式训练（单卡够用）、Muon 优化器（先 AdamW）、FP8、排行榜刷榜调优。竞技装备不是学习装备。
- **主风险复盘（M2 已跨过）**：原定全图最贵也最陌生的风险点在 M2（数据打包与预训练稳定性）。通过先跑极小配置闭环、再做 `emb_dim` 与 `n_layers` 扫描，已经顺利把甜点区（256 维 2 层，BPB 3.10）和梯度累积的坑全部趟平。

## 并列理论线：diy-llm（2026-10-24 增补）

[diy-llm](https://github.com/datawhalechina/diy-llm)（DataWhale 出品，斯坦福 CS336 中文本土化课程，16 章 + 6 作业）与 nanochat 并列：作品线负责“做得出”，理论线负责“懂得深”。立项书见 [diy-llm 立项书](/llm/diy-llm-proposal/)。用法：每个里程碑先读对应章节再动手，交付后可选做对应作业当加试题，不另开顺序通读的新主线。

| 里程碑 | 状态 | diy-llm 配套章节 |
| --- | --- | --- |
| M1 自训 BPE Tokenizer | ✓ 已完成 | 第 2 章 分词器 + 作业 1 |
| M2 预训练闭环 | ✓ 已完成 | 第 3 章（梯度累积/资源核算）+ 第 11 章（数据工程）+ 第 9 章（Scaling Laws） |
| M3 KV Cache 推理引擎 | ✓ 已完成 | 第 10 章 推理（KV Cache、投机解码、量化） |
| **M4 SFT 指令微调** | **◎ 下一站** | 第 13 章（Pre-training / SFT / DPO 全流程） |
| M5 评估框架 | 待开工 | 第 12 章 评估与基准 + 作业 6 |
| 架构升级（GPT-2 → 现代） | 选修穿插 | 第 4 章 RoPE / RMSNorm / SwiGLU |

“明确砍掉”部分的捡回路径也留好了：MoE（第 5 章）、GPU / 分布式（第 6～8 章）、GRPO / RLVR（第 14 章）、多模态（第 15 章）——以后想扩装备时有教材，不急着现在看。

## 复习线与 AI Infra 选修区（M3 后穿插）

### 复习线（2026-10-29 增补）

- **默写**：`GPTModel` 每两周默一次（A4 纸，首次默写见[《手搓 LLM 番外：A4 纸默写 GPTModel》](/llm/llm-extra-handwrite-gptmodel/)），`MHA` / `FFN` / `LayerNorm` 单独补漏；两周后对照进步
- **复盘**：每个里程碑结束后写笔记 + 小复盘
- **欠账清单**：位置溢出（滑动窗口 / RoPE）、流式 IO、分布式训练，标好捡回时机

### AI Infra 选修区

KV Cache 只是开胃菜，AI Infra 的硬通货按需插入 M4～M6 之间：

- **RoPE**：替代 `pos_emb`，解决 M3 留下的 `context_length` 位置溢出欠账（现代架构的位置编码）
- **量化**：INT8 / INT4 推理降本
- **投机解码**：小模型带大模型提速
- **FlashAttention**：注意力显存与性能优化

原则：不影响主线，哪个里程碑用到就先读哪块，不顺序全学。

## 输出线与 nanochat 源码对照

- **博客**：每个里程碑一篇笔记（M0～M3 已产出笔记 08～12）
- **掘金专栏**：每周 1～2 篇，把实验写成可复现报告（容量扫描、BPB 曲线、KV Cache 3.6x 提速对照）
- **nanochat 源码阅读（后置）**：nanochat 源码不当教材，**M6 对话界面完成后**再拿它当标准答案对照——那时手里已经有了自己的完整实现，它是参考书不是天花板。
