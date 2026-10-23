+++
title = "手搓 LLM 笔记 08：重写 lvllm，按工程结构再串一遍"
date = 2026-10-20T12:00:00+08:00
draft = false
slug = "llm-08-rewrite-lvllm"
tags = ["LLM", "工程化", "重写", "学习笔记"]
summary = "终极回炉：不按章节收拢，按工程结构重写全书代码——分层、单一配置、单一 device 入口、checkpoint 标准化。重写完成时发布。"
[cover]
    image = "covers/llm-08-rewrite-lvllm.jpg"
    alt = "手搓 LLM 笔记 08：重写 lvllm"
    hiddenInList = true
    hiddenInSingle = true
+++

> 预告：本篇目前只有计划，重写 lvllm 完成后正式撰写正文。施工图见 [lvchat 实现导图](/nanochat/lvchat-roadmap/) 的 M0。

## 计划

- 分层：tokenizer / model / data / train / generate / eval / checkpoints
- 单一配置入口（config）、单一 device 入口（get_device）、checkpoint 标准化（权重 + config + val_loss）
- 军规：能不翻书就不翻，翻一次记一笔欠账注释，写完清单归零
- 验收：分类、指令微调、生成三个回归测试与旧仓库结果一致

## 素材积累（M0 进行中）

**Day 1（10-20）**：
- MHA 重写：骨架对、细节丢四个（多头拆解、√d_k、logits/权重命名、out_proj）；抓到两个致命 bug（`foward` 拼写、mask 切片错写成 `[:T, T:]`，正确是 `[:T, :T]`）
- 「张量的第一维永远是 batch」幻觉拔除——generate 的一维切法 bug 全源于此
- LayerNorm vs BatchNorm：「BatchNorm 统计别人，LayerNorm 只管自己」
- pre-norm 的「干净通道」：残差主干恒等直通，warmup 与 pre-norm 是同一问题的两代武器
- checkpoints 三层设计：gpt2.py（进口）/ store.py（自用）/ lora.py（附加）；键名映射吸收旧格式
- LoRA merge 验收的双重计数坑：merge 是搬家不是复制
- 竖切终点：355M 权重加载，squid 第一次开口

**Day 2（10-23）**：
- data 层按任务分不按格式分：pretrain（定长滑窗，dataset 内偏移）/ classify（collate 补 batch 内最长）/ instruct（掩码五连）
- collate 职责钉死：「定长的活 dataset 干，变长的活 collate 干，pad 永远在偏移前面」
- instruct collate 五步手术：追加 EOS → pad → +1 错位 → prompt 位 -100 → 除第一个 EOS 外全 -100
- 掩码两笔账：pad 掩码是卫生（必做），prompt 掩码是战术（看目标）；「prompt 是考场，response 是答卷，遮盖是不计分不是拆考场」
- pad_id 不许写死 50256：词表知识只从 tokenizer.eos_id 一个口进（GPT-2 ≠ Qwen，07-2 的前科）
- list 思维切 tensor 三坑：tensor 没有 .index、切片是视图要 clone、标量广播代替 list 赋值
- cross_entropy 契约 (N,C)+(N,)：N=预测点数。pretrain 要 flatten（N=B×T），classify 取 last-token 天然对齐（N=B）——同名不同身，各放各家
- 函数自足原则：no_grad 内收进 calc_loss_loader，不依赖调用方记得规矩（Java 直觉的胜利）；但训练用 loss 函数绝不能包 no_grad
- 训练层分工：common 提供能力，循环决定节奏；prepare（模型手术）归调用前，循环闭着眼跑
- lr_at_step 抽纯函数的意义 = 可测性：给出过 bug 的 warmup 公式配三锚点断言当验尸官
- named_modules 遍历、named_children 手术：替换要拿爹的句柄；named_modules 会 yield 自身，递归即套娃（RecursionError 实锤）
- LoRA：α/r 缩放 forward 与 merge 必须同尺；merged_weight 生命周期 = 训练并联省显存 → 部署 merge 省计算；存档两路线（adapter 小而专用 / merged 大而通用）
- sanity check：初始 loss ≈ ln(vocab_size)，一眼辨训练真假
- stride 语义钉死：窗口滑动的步长，不是窗口大小；stride=max_length/2 → 50% 重叠抗上下文割裂
- Kimi 翻车帧：出考题忘了等长样本没有 pad 路径；「我的时间来自对话时间戳，不是真的钟」
