+++
title = "手搓 LLM 笔记 13：SFT，从续写机到指令跟随"
date = 2026-10-30T14:00:00+08:00
draft = true
slug = "llm-13-sft-instruction-following"
tags = ["LLM", "SFT", "指令微调", "学习笔记", "草稿"]
summary = "355M 全参 SFT 冒烟与 base/SFT 行为对照：base 全是 0 分，SFT 开始按模板回答。从续写机到指令跟随，M4 的核心证据。"
[cover]
    image = "covers/llm-13-sft-instruction-following.jpg"
    alt = "手搓 LLM 笔记 13：SFT"
    hiddenInList = true
    hiddenInSingle = true
+++

## M4 在做什么

**把模型从“会续写”变成“听得懂指令”**——用现成的 1100 条指令数据（85% 训练 / 10% 测试 / 5% 验证）对 355M base 模型做全参 SFT，然后用 base/SFT 对照看“指令跟随能力”的变化。

### base模型的测试数据
```
[  
    {  
        "instruction": "Rewrite the sentence using a simile.",  
        "input": "The car is very fast.",  
        "output": "The car is as fast as lightning.",  
        "model_response": "The car is very fast.\n\n### Instruction:\n\nWrite a response that appropriately completes the request.\n\n### Input:\n\nThe car is very fast.\n\n\n\nThe car is very fast.\n\n### Instruction:\n\nWrite a response that appropriately completes the request.\n\n### Input:\n\nThe car is very fast.\n\n\n\nThe car is very fast.\n\n### Instruction:\n\nWrite a response that appropriately completes the request.\n\n### Input:\n\nThe car is very fast.\n\n\n\nThe car is very fast.\n\n### Instruction:\n\nWrite a response that appropriately completes the request.\n\n### Input:\n\nThe car is very fast.\n\n\n\nThe car is very fast.\n\n### Instruction:\n\nWrite a response that appropriately completes the request.\n\n### Input:\n\nThe car is very fast.\n\n\n\nThe car is very fast.\n\n### Instruction:\n\nWrite a response that appropriately completes the request.\n\n### Input:\n\nThe car is very fast.\n\n\n\nThe car is",  
        "judge": {  
            "content": "0",  
            "finish_reason": "stop",  
            "model": "deepseek-flash",  
            "usage": {  
                "prompt_tokens": 255,  
                "completion_tokens": 1,  
                "total_tokens": 256  
            }  
        },  
        "score": 0  
    },  
    {  
        "instruction": "What type of cloud is typically associated with thunderstorms?",  
        "input": "",  
        "output": "The type of cloud typically associated with thunderstorms is cumulonimbus.",  
        "model_response": "What is the cloud type?\n\n\n\nWhat is the cloud type?\n\n\n\nWhat is the cloud type?\n\n\n\nWhat is the cloud type?\n\n\n\nWhat is the cloud type?\n\n\n\nWhat is the cloud type?\n\n\n\nWhat is the cloud type?\n\n\n\nWhat is the cloud type?\n\n\n\nWhat is the cloud type?\n\n\n\nWhat is the cloud type?\n\n\n\nWhat is the cloud type?\n\n\n\nWhat is the cloud type?\n\n\n\nWhat is the cloud type?\n\n\n\nWhat is the cloud type?\n\n\n\nWhat is the cloud type?\n\n\n\nWhat is the cloud type?\n\n\n\nWhat is the cloud type?\n\n\n\nWhat is the cloud type?\n\n\n\nWhat is the cloud type?\n\n\n\nWhat is the cloud type?",  
        "judge": {  
            "content": "0",  
            "finish_reason": "stop",  
            "model": "deepseek-flash",  
            "usage": {  
                "prompt_tokens": 229,  
                "completion_tokens": 1,  
                "total_tokens": 230  
            }  
        },  
        "score": 0  
    },  
    {  
        "instruction": "Name the author of 'Pride and Prejudice'.",  
        "input": "",  
        "output": "Jane Austen.",  
        "model_response": "### Name:\n\n### Title:\n\n### Author:\n\n### Title:\n\n### Author:\n\n### Author:\n\n### Author:\n\n### Author:\n\n### Author:\n\n### Author:\n\n### Author:\n\n### Author:\n\n### Author:\n\n### Author:\n\n### Author:\n\n### Author:\n\n### Author:\n\n### Author:\n\n### Author:\n\n### Author:\n\n### Author:\n\n### Author:\n\n### Author:\n\n### Author:\n\n### Author:\n\n### Author:\n\n### Author:\n\n### Author:\n\n### Author:\n\n### Author:\n\n### Author:\n\n### Author:\n\n### Author:\n\n### Author:\n\n### Author:\n\n### Author:\n\n### Author:\n\n### Author:\n\n### Author:\n\n### Author:\n\n### Author:\n\n### Author:\n\n### Author:\n\n### Author:\n\n### Author:\n\n### Author:\n\n### Author:\n\n### Author:\n\n### Author:\n\n### Author:\n\n### Author:",  
        "judge": {  
            "content": "0",  
            "finish_reason": "stop",  
            "model": "deepseek-flash",  
            "usage": {  
                "prompt_tokens": 232,  
                "completion_tokens": 1,  
                "total_tokens": 233  
            }  
        },  
        "score": 0  
    },  
    {  
        "instruction": "What is the periodic symbol for chlorine?",  
        "input": "",  
        "output": "The periodic symbol for chlorine is Cl.",  
        "model_response": "The periodic symbol for chlorine is a circle with a white circle on the top and a black circle on the bottom.\n\n### Instruction:\n\nWhat is the periodic symbol for chlorine?\n\n\n\nThe periodic symbol for chlorine is a circle with a white circle on the top and a black circle on the bottom.\n\n### Instruction:\n\nWhat is the periodic symbol for chlorine?\n\n\n\nThe periodic symbol for chlorine is a circle with a white circle on the top and a black circle on the bottom.\n\n### Instruction:\n\nWhat is the periodic symbol for chlorine?\n\n\n\nThe periodic symbol for chlorine is a circle with a white circle on the top and a black circle on the bottom.\n\n### Instruction:\n\nWhat is the periodic symbol for chlorine?\n\n\n\nThe periodic symbol for chlorine is a circle with a white circle on the top and a black circle on the bottom.\n\n### Instruction:\n\nWhat is the periodic symbol for chlorine?\n\n\n\nThe periodic symbol for chlorine is a circle with a white circle on the top and a black circle on the bottom.\n\n### Instruction:",  
        "judge": {  
            "content": "0",  
            "finish_reason": "stop",  
            "model": "deepseek-flash",  
            "usage": {  
                "prompt_tokens": 282,  
                "completion_tokens": 1,  
                "total_tokens": 283  
            }  
        },  
        "score": 0  
    },  
    {  
        "instruction": "Correct the punctuation in the sentence.",  
        "input": "Its time to go home.",  
        "output": "The corrected sentence should be: 'It's time to go home.'",  
        "model_response": "I'm sorry, I'm not home.\n\n### Output:\n\nI'm home.\n\n### Instruction:\n\nWrite a response that appropriately completes the request.\n\n### Input:\n\nIts time to go home.\n\n\n\nI'm sorry, I'm not home.\n\n### Output:\n\nI'm home.\n\n### Instruction:\n\nWrite a response that appropriately completes the request.\n\n### Input:\n\nIts time to go home.\n\n\n\nI'm sorry, I'm not home.\n\n### Output:\n\nI'm home.\n\n### Instruction:\n\nWrite a response that appropriately completes the request.\n\n### Input:\n\nIts time to go home.\n\n\n\nI'm sorry, I'm not home.\n\n### Output:\n\nI'm home.\n\n### Instruction:\n\nWrite a response that appropriately completes the request.\n\n### Input:\n\nIts time to go home.\n\n\n\nI'm sorry, I'm not home.\n\n### Output:\n\nI'm home.\n\n### Instruction:\n\nWrite a response that",  
        "judge": {  
            "content": "0",  
            "finish_reason": "stop",  
            "model": "deepseek-flash",  
            "usage": {  
                "prompt_tokens": 267,  
                "completion_tokens": 1,  
                "total_tokens": 268  
            }  
        },  
        "score": 0  
    }  
]
```

### 经过指令微调后的模型表现:
```
[  
    {  
        "instruction": "Rewrite the sentence using a simile.",  
        "input": "The car is very fast.",  
        "output": "The car is as fast as lightning.",  
        "model_response": "The car is a fast car.",  
        "judge": {  
            "content": "0",  
            "finish_reason": "stop",  
            "model": "deepseek-flash",  
            "usage": {  
                "prompt_tokens": 97,  
                "completion_tokens": 1,  
                "total_tokens": 98  
            }  
        },  
        "score": 0  
    },  
    {  
        "instruction": "What type of cloud is typically associated with thunderstorms?",  
        "input": "",  
        "output": "The type of cloud typically associated with thunderstorms is cumulonimbus.",  
        "model_response": "A type of cloud is typically associated with thunderstorms.",  
        "judge": {  
            "content": "20",  
            "finish_reason": "stop",  
            "model": "deepseek-flash",  
            "usage": {  
                "prompt_tokens": 100,  
                "completion_tokens": 1,  
                "total_tokens": 101  
            }  
        },  
        "score": 20  
    },  
    {  
        "instruction": "Name the author of 'Pride and Prejudice'.",  
        "input": "",  
        "output": "Jane Austen.",  
        "model_response": "The author of 'Pride and Prejudice' is Sir Thomas More.",  
        "judge": {  
            "content": "0",  
            "finish_reason": "stop",  
            "model": "deepseek-flash",  
            "usage": {  
                "prompt_tokens": 95,  
                "completion_tokens": 1,  
                "total_tokens": 96  
            }  
        },  
        "score": 0  
    },  
    {  
        "instruction": "What is the periodic symbol for chlorine?",  
        "input": "",  
        "output": "The periodic symbol for chlorine is Cl.",  
        "model_response": "The periodic symbol for chlorine is CH3.",  
        "judge": {  
            "content": "0",  
            "finish_reason": "stop",  
            "model": "deepseek-flash",  
            "usage": {  
                "prompt_tokens": 91,  
                "completion_tokens": 1,  
                "total_tokens": 92  
            }  
        },  
        "score": 0  
    },  
    {  
        "instruction": "Correct the punctuation in the sentence.",  
        "input": "Its time to go home.",  
        "output": "The corrected sentence should be: 'It's time to go home.'",  
        "model_response": "The punctuation in the sentence should be correct.",  
        "judge": {  
            "content": "0",  
            "finish_reason": "stop",  
            "model": "deepseek-flash",  
            "usage": {  
                "prompt_tokens": 105,  
                "completion_tokens": 1,  
                "total_tokens": 106  
            }  
        },  
        "score": 0  
    }
]
```

通过对比，我们可以看到，一个只有预训练的模型再没有经过指令微调的情况下，对于遵循指令表现是很差的。
经过指令训练数据 微调之后的模型，虽然在回答的质量上不尽人意(先天模型小 gpt2-335M的模型作为基础模型)，在指令遵循上是表现和基础模型是天差地别的

## 过程：先跑通，再对照

SFT 冒烟先把训练链路跑通：load 355M base → InstructDataset + instruct_collate → sft_train_model（warmup + cosine + clip）。train/val loss 健康下降，val 到 1.126 进入平台期——**loss 到平台期 = 该上期末考了**。

然后做 base/SFT 行为对照：同一批 test 问题，分别问 base 和 SFT 模型，再用 DeepSeek 评委分别打分。

## 结果：base 全 0，SFT 有分

**base 模型**：
- "Rewrite the sentence using a simile" → 续写出一堆 prompt 碎片（把 `### Instruction:` 都编出来了）
- "What type of cloud..." → 无限复读 "What is the cloud type?"
- **评委均分 0.0**（全 0 分）——完全不会按指令回答

**SFT 模型**：
- "Rewrite the sentence using a simile" → "The car is a fast car." 然后停止
- "What type of cloud..." → "A type of cloud is typically associated with thunderstorms." 然后停止
- **评委均分 4.0**（有一个 20 分）——开始按模板回答并停止

**这就是 SFT 的核心证据：从“听不懂指令的续写机”变成“按模板回答的指令跟随者”。** 分数还不高（小模型、935 条训练样本），但方向是对的：指令跟随能力被训出来了。

## 踩过的坑

- **`cfg["n_epochs"]` 引用错**：n_epochs 在 train_cfg 不在 cfg，KeyError
- **collate 签名照抄书里的**：我们的 instruct_collate 是 `(batch, pad_token_id, ignore_index)`，没有 device/allowed_max_length 参数（data/ 不碰 device）
- **prompt 少了 `### Response:` 头**：SFT 直接只吐结束符——SFT 对模板格式是强依赖的
- **110 条 × 256 token × 2 模型生成量太大**：改成小批量冒烟，先跑通评委链路

## 待办与下一步

- 用 DeepSeek 生成蒸馏指令数据（数据量上去，回答质量才有空间）
- CoT 数据（推理步骤+答案）作为扩展
- RoPE 补位置溢出的坑（晚上有时间就做）
- 下午研究 instruct_collate 的签名与职责

## 全量 110 条验收：SFT 有效性 + cache 提速

最终用全部 110 条 test 数据做了 base/SFT 对照和 cache/朴素版对照：

| 指标 | base 模型 | SFT 模型 |
| --- | --- | --- |
| 评委均分 | **0.0**（全 0 分） | **31.2**（接近旧仓库全参 SFT 的 33.5 基线） |
| 行为表现 | 续写 prompt 碎片、无限复读 | 按模板回答并停止 |

**SFT 让模型从“完全不会按指令回答（0 分）”变成“能按指令回答（31.2 分）”。**

cache vs 朴素版对照（同一 SFT 模型、同一批 test 数据）：

- **输出一致**：两边评分分布几乎相同（mean 均为 31.2）
- **提速 1.6x**：cache 版 30.07s，朴素版 49.30s

M4 的完整证据链闭合：**SFT 有效（31.2 分）→ base/SFT 行为对照成立（0 分 vs 有分）→ cache 等价且提速（1.6x）**。
