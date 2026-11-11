+++
title = "手搓 LLM 笔记 20：CUDA 对照"
date = 2026-11-11T10:57:55+08:00
draft = false
slug = "llm-20-i2-windows-cuda"
tags = ["LLM", "I2", "CUDA", "WSL2", "SSH", "torch.compile", "学习笔记"]
summary = "搭建 Windows + WSL2 + RTX 4070 Ti 环境，定位 torch.compile 的 typing 依赖根因，并在统一测量口径下完成 AMP、SDPA、compile、checkpointing 的 CUDA 三轮对照及 MPS 横向观察。"
[cover]
    image = "covers/llm-20-i2-windows-cuda.jpg"
    alt = "手搓 LLM 笔记 20：CUDA 对照"
    hiddenInList = true
    hiddenInSingle = true
+++

这次最直观的感受是：**RTX 4070 Ti + CUDA 确实猛**。一张 2023 年左右花六千多元买的 RTX 4070 Ti，和一台 2025 年年中花两万一千元买的 MacBook M4 Pro（48 GB），购买时间相隔约两三年，价格相差三倍多。我原本以为，更晚、更贵的设备至少不会在训练任务上吃亏；真正跑完对照才发现，在当前这套手搓模型的训练实验中，4070 Ti 的 FP32 吞吐已接近 Mac / MPS 的两倍，在 BF16、FP16 和 compile 等配置下甚至超过两倍。这个结果确实出乎我的意料。

当然，这不是一场严格的同台比价：显卡和 Mac 整机的定位不同，4070 Ti 的 12 GB 显存也会限制可训练的模型规模，MacBook 的 48 GB 统一内存则有另一方面的优势。真正让我有触动的，也不只是“N 卡更快”这个结论，而是我终于用同一套代码、同一份数据和自己跑出来的指标，把过去听别人说的“训练更适合 N 卡”，变成了亲手验证过的事实。

> 今天的主线原本只是“在 Windows 上复跑 I2 实验”。过程中不仅搭建了一套以后可以反复使用的 GPU 环境、完成了一次典型的依赖排障，也得到了六组 CUDA 正式结果和一份保留边界的 MPS / CUDA 对照。

## 一、为什么需要这套环境？

昨天的 I2 实验都在 Mac/MPS 上完成。它能验证模型逻辑和当前设备上的性能，但不能代表 CUDA、大显存和 NVIDIA 优化生态。

Windows 台式机里有一张 RTX 4070 Ti，显存约 12 GB。I2 番外要在同一套代码、同一份 token 数据、同一组训练配置下，复跑：

- FP32 / FP16 / BF16（AMP）；
- eager / SDPA；
- torch.compile；
- Activation Checkpointing。

目标不是推翻 Mac 结果，而是得到一组可以并列比较的 CUDA 对照。

## 二、从 Mac 远程操作 Windows

为了避免在 Mac 和 Windows 两套键盘、两个终端之间来回切换，这次使用 SSH。

Windows 上安装并启动 OpenSSH Server：

```powershell
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
Start-Service sshd
Set-Service -Name sshd -StartupType Automatic
```

安装过程中一度出现进度条不更新、`NotPresent` 和后台服务仍在运行的情况。检查后发现 BITS 处于停止状态，启动：

```powershell
Start-Service BITS
```

随后组件状态变为 `Installed`。

防火墙中已有 `OpenSSH-Server-In-TCP`，无需重复创建。规则状态为：

```text
Enabled = True
Direction = Inbound
Action = Allow
Profile = Private
```

然后使用 Windows 的以太网 IPv4 地址 `192.168.3.8`，从 Mac 登录：

```bash
ssh lv@192.168.3.8
```

登录成功后进入 Ubuntu：

```powershell
wsl -d Ubuntu-24.04
```

这样，后续命令就可以统一在 Mac 终端中执行，不再需要两套键盘和两套操作习惯。

这条链路是：

```text
Mac
→ SSH
→ Windows
→ WSL2 / Ubuntu 24.04
→ RTX 4070 Ti
```

不需要额外引入 KVM 或维护另一套独立虚拟机。

## 三、统一运行环境

进入 Ubuntu 后，确认：

```text
Git 2.43.0
Python 3.12.3（Ubuntu 系统初始版本）
```

随后安装 uv，并让项目使用与 Mac 一致的 Python 3.12.12：

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source "$HOME/.local/bin/env"

uv python install 3.12.12
uv sync --python 3.12.12
```

项目的 `requires-python = ">=3.12"` 只规定最低版本，并不会自动选择 Mac 的 3.12.12，因此这里显式指定版本。

代码克隆后锁定到与 Mac 相同的提交：

```bash
git switch --detach 5fcd3c2958e935dae805f051f8a628baa9e8ef59
```

`detached HEAD` 在这里是为了固定对照实验版本，不是要修改历史。

GPU 在 WSL 中已经可见：

```text
NVIDIA GeForce RTX 4070 Ti
显存：12282 MiB
CUDA UMD Version：13.3
```

PyTorch 检查结果：

```text
torch = 2.14.1+cu130
cuda_available = True
gpu = NVIDIA GeForce RTX 4070 Ti
torch_cuda = 13.0
```

## 四、同步同一份 token 数据

由于 `data/` 不进入 Git，Windows 需要单独获得 token store。

从 Mac 通过 SCP 复制到 Windows 用户目录，再进入 WSL 项目：

```bash
scp -r /Users/lv/lv_repo/squid-llms/data/token_store \
  lv@192.168.3.8:token_store
```

Ubuntu 中：

```bash
mkdir -p ~/lv_repo/squid-llms/data/token_store

cp -r /mnt/c/Users/lv/token_store/. \
  ~/lv_repo/squid-llms/data/token_store/
```

最终文件：

```text
train.uint32.bin    约 461 KiB
heldout.uint32.bin  约 22 KiB
metadata.json       约 17 KiB
```

文件大小也与 token 数一致：

```text
train：117890 × 4 = 471560 bytes
heldout：5485 × 4 = 21940 bytes
```

这样，Mac 与 Windows 使用的就是同一份代码、同一套 Python/依赖版本和同一份 token 数据。

## 五、第一次 compile 失败：缺少 C 编译器

环境探针中，FP16、BF16、autocast 和 SDPA 都通过，只有 `torch.compile` 报错：

```text
Failed to find C compiler
```

这说明 `torch.compile` 在当前 Linux 环境中需要调用系统编译器，而 Ubuntu 初始环境没有完整开发工具链。

安装：

```bash
sudo apt update
sudo apt install -y build-essential
```

安装后确认：

```text
gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
```

但再次运行时，错误变成了：

```text
SubprocPool unclean exit
Attempting to use a closed pool
```

这说明问题已经从“找不到编译器”变成了“编译 worker 进程池崩溃”。

## 六、先绕过，再抓真正的子进程错误

为了判断编译器和 CUDA 是否可用，先使用单线程编译：

```bash
TORCHINDUCTOR_COMPILE_THREADS=1 uv run python - <<'PY'
import torch


def function(x):
    return x * 2 + 1


compiled = torch.compile(function)
result = compiled(torch.tensor([1.0, 2.0], device="cuda"))
print(result)
PY
```

结果：

```text
tensor([3., 5.], device='cuda:0')
```

这证明：

- `torch.compile` 本身可用；
- GCC 可以参与编译；
- 生成的 kernel 能在 CUDA 上正确执行；
- 问题主要集中在并行编译 worker，而不是模型代码或基本 CUDA 计算。

但这只是 workaround，不是根因修复。

### 打开 worker 日志

随后不关闭并行编译，而是打开 worker 日志：

```bash
TORCHINDUCTOR_WORKER_SUPPRESS_LOGGING=0 \
TORCHINDUCTOR_WORKER_LOGPATH=/tmp/inductor-worker.log \
uv run python - <<'PY'
import torch


def function(x):
    return x * 2 + 1


compiled = torch.compile(function)
result = compiled(torch.tensor([1.0, 2.0], device="cuda"))
print(result)
PY
```

主进程仍然只显示 `closed pool`，但 worker 日志终于暴露了第一现场：

```text
File ".../.venv/lib/python3.12/site-packages/typing.py"
AttributeError: type object 'Callable' has no attribute '_abc_registry'
```

也就是说，编译 worker 不是死在了 CUDA 或模型计算上，而是**在启动后导入 `typing` 时就崩溃了**。

## 七、真正根因：旧 typing 包遮蔽了标准库

Python 3.12 自带标准库 `typing`，但虚拟环境中还存在：

```text
.venv/lib/python3.12/site-packages/typing.py
```

这是额外安装的旧版 `typing 3.10.0.0`，与当前 Python 标准库不兼容。

主进程里检查：

```bash
uv pip show typing
```

输出：

```text
Name: typing
Version: 3.10.0.0
Required-by: pyloco
```

继续沿 lockfile 追踪，得到完整依赖链：

```text
squid-llms
→ matplot
→ pyloco
→ typing 3.10.0.0
```

而项目中实际使用的是 `matplotlib`，没有代码直接 import `matplot`。

因此正确修复不是单独删掉 `typing`，而是：

```bash
uv add matplotlib
uv remove matplot
```

这样：

- 把真正使用的 `matplotlib` 提升为直接依赖；
- 移除不需要的 `matplot`；
- 同时移除 `pyloco` 和旧 `typing` 这条依赖链；
- `pyproject.toml` 与 `uv.lock` 同步更新，避免下次 `uv sync` 又装回来。

修复后：

```text
uv pip show typing
→ Package(s) not found for: typing
```

再次运行正常并行编译，不再设置 `TORCHINDUCTOR_COMPILE_THREADS=1`：

```text
tensor([3., 5.], device='cuda:0')
```

这次才真正解决了根因。

## 八、今天学到的不只是安装环境

这次排障有几个值得长期保留的经验：

### 1. 主进程错误不一定是真正根因

`closed pool` 只说明池关闭了，`SubprocPool unclean exit` 只说明子进程异常退出。真正原因需要打开 worker 日志。

### 2. 不要第一时间把问题归因于 CUDA 版本

单线程编译和 CUDA 执行已经成功，说明基本计算链路可用。继续沿子进程启动、导入和依赖路径排查，比盲目更换 CUDA 更有效。

### 3. 多余依赖也可能破坏运行时

这次不是缺依赖，而是**多了一个旧依赖**。它遮蔽了 Python 标准库，导致完全不相关的编译 worker 启动失败。

### 4. 修复要落到依赖清单

只在当前环境里卸载一个包还不够。需要更新 `pyproject.toml` 和 `uv.lock`，否则下一次同步环境时问题会重新出现。

### 5. 这套环境是后续主线的基础设施

它不仅服务今天的 I2 番外，也会服务：

- CUDA 下的 AMP / SDPA / compile / checkpointing 对照；
- I3 的推理、量化与 Serving；
- 第三阶段的 GPU、算子、分布式和 DeepInfer 学习。

## 九、统一 CUDA 的计时与显存口径

正式实验前，补齐了 CUDA 的同步计时和显存记录。GPU 操作是异步提交的，只记录 Python 调用的返回时间，可能并没有包含实际计算时间；因此正式测量前后需要同步设备，并在正式测量前重置峰值显存统计。

各训练脚本现在通过公共设备逻辑记录：

- `current_allocated`：当前仍由张量占用的显存；
- `peak_allocated`：测量期间张量实际分配显存的峰值；
- `current_reserved`：当前 PyTorch 缓存分配器向 CUDA 预留的显存；
- `peak_reserved`：测量期间缓存分配器预留显存的峰值。

`allocated` 更接近实际张量占用，`reserved` 还包含缓存分配器为复用而保留的空间。两者不能混为一谈。本次表格保留原始 bytes，同时用 `bytes ÷ 1,048,576` 换算为 MiB，便于阅读。

## 十、正式 CUDA 对照结果

### 测量条件

- 硬件：RTX 4070 Ti，约 12 GB 显存；
- 软件：Windows + WSL2 / Ubuntu 24.04，Python 3.12.12，PyTorch 2.14.1+cu130；
- 模型：2 层，`emb_dim=64`，`ffn_dim=256`，4 个 Q heads、2 个 KV heads，词表 151936；
- 数据与配置：与 Mac 使用同一份 token store，`batch_size=2`，`context_length=128`；
- 计时：2 步 warmup，随后 10 步正式测量，共处理 2560 个 token；
- 每个实验独立运行 3 次，吞吐取中位数；
- compile 的首次图捕获、代码生成和编译发生在 warmup 中，不计入下面的稳态吞吐。

| 实验 | 吞吐中位数（tokens/s） | 峰值分配 | 峰值预留 |
| --- | ---: | ---: | ---: |
| FP32 / eager | 21614.87 | 691.67 MiB | 854 MiB |
| BF16 / AMP | 22002.51 | 635.55 MiB | 876 MiB |
| FP16 / AMP | 20954.75 | 635.55 MiB | 876 MiB |
| SDPA + FP32 | 21588.02 | 690.81 MiB | 852 MiB |
| compile + FP32 | 25346.90 | 690.85 MiB | 首轮 778 MiB，后两轮 852 MiB |
| checkpointing + FP32 | 17140.50 | 687.53 MiB | 852 MiB |

这里的显存数字取三轮正式测量后报告中的峰值。compile 的峰值预留首轮为 `815792128 bytes`（778 MiB），后两轮为 `893386752 bytes`（852 MiB），因此保留波动，不选其中一个数字冒充固定结果。

### 1. BF16：小幅提速，但两种显存指标方向不同

相对 FP32 / eager：

- 吞吐中位数提高约 **1.79%**；
- 峰值分配减少 **56.12 MiB**，约 **8.11%**；
- 峰值预留却增加 **22 MiB**，约 **2.58%**。

所以准确结论是：当前配置下 BF16 有小幅吞吐收益，实际张量峰值分配有所下降，但缓存分配器的峰值预留没有同步下降。不能笼统写成“全面节省显存”。

FP16 的吞吐中位数比 FP32 低约 3.05%，比 BF16 低约 4.76%。这组结果只代表当前小模型、短序列和测量配置，不代表其他 GPU 或大模型上 FP16 一定慢于 BF16。

### 2. SDPA：本次基本持平

SDPA + FP32 相对 eager + FP32：

- 吞吐变化约 **-0.12%**，基本持平；
- 峰值分配减少约 **0.87 MiB**；
- 峰值预留减少 **2 MiB**。

这只能说明当前模型和上下文长度下，替换注意力实现没有带来明显差异。这里只验证了代码调用 SDPA，**没有确认实际落入 FlashAttention kernel**，也不能据此推断长序列下的收益。

### 3. compile：当前最明显的吞吐收益

compile + FP32 相对 eager + FP32：

- 三轮吞吐为 25369.12 / 25346.90 / 24348.93 tokens/s；
- 中位数提高约 **17.27%**；
- 峰值分配约 690.85 MiB，与 FP32 的 691.67 MiB 基本持平。

因此当前收益应写成**吞吐提升**，不能附带宣称 compile 节省了显存。预热后三轮的峰值预留存在 778 / 852 MiB 的波动，也提醒我们不能只看某一轮。

首轮出现的 `Not enough SMs to use max_autotune_gemm mode` 表示当前设备未启用相应的 GEMM 自动调优路径，不是编译失败；实际编译和后续 CUDA 执行均已成功。

### 4. checkpointing：降速明显，当前显存收益很小

checkpointing + FP32 相对 FP32 / eager：

- 三轮吞吐为 19454.24 / 17140.50 / 17051.76 tokens/s；
- 中位数从 21614.87 降至 17140.50，下降约 **20.70%**；
- 峰值分配从 691.67 MiB 降至 687.53 MiB，只减少 **4.14 MiB / 0.60%**；
- 峰值预留两边均为 852 MiB。

首轮吞吐较高，因此这里用三轮中位数而不是只取最好的一次。当前小模型上，额外重算带来了明显吞吐损失，却只换来很小的峰值分配下降。

这不否定 checkpointing 的价值。它本来就是用额外计算换取激活显存，只是当前小模型并没有显存瓶颈，交易不划算。是否值得开启，要在更大模型、更长上下文或接近 OOM 的配置下重新测量。

## 十一、Mac / MPS 与 Windows / CUDA 并列观察

下表只并列两边已有的三轮吞吐中位数，不把跨硬件差异归因于某一个单独优化：

| 实验 | Mac / MPS（tokens/s） | Windows / CUDA（tokens/s） |
| --- | ---: | ---: |
| FP32 / eager | 11001.65 | 21614.87 |
| BF16 / AMP | 9942.47 | 22002.51 |
| FP16 / AMP | 9892.09 | 20954.75 |
| SDPA + FP32 | 10613.57 | 21588.02 |
| compile + FP32 | 11801.10 | 25346.90 |
| checkpointing + FP32 | 10714.24 | 17140.50 |

两个值得带走的观察：

- compile 在 Mac / MPS 上相对 FP32 提高约 **7.27%**，在本次 CUDA 上提高约 **17.27%**。两种设备上都观察到了稳态吞吐收益，但幅度不同。
- checkpointing 在两种设备上的收益都不显著。Mac 当时使用同批次、带内存记录的 FP32 基线 11321.03 tokens/s 对照，不能把其他批次的 FP32 中位数混入计算；当时也没有与本次 CUDA 完全相同的峰值显存接口，因此不伪造跨设备的峰值显存对照。

这些数字不是硬件排行榜。两台机器的模型规模都很小，测量只有 10 个正式 step，编译成本也没有摊入稳态吞吐。它们回答的是“同一学习项目在当前两台设备上观察到了什么”，不是普遍性能定律。

## 十二、最终验收与边界

已经真实完成：

- Mac 通过 SSH 操作 Windows，Windows + WSL2 / Ubuntu 环境可用；
- RTX 4070 Ti 在 Ubuntu 和 PyTorch CUDA 中可见；
- 代码、Python 3.12.12、依赖与 token 数据已同步；
- `torch.compile` 从缺编译器到 worker 崩溃再到依赖根因修复；
- 修复后的环境探针通过，FP16 / BF16、autocast、SDPA 和 compile 均可用；
- 正常并行 compile 不再依赖单线程 workaround；
- FP32 / FP16 / BF16 / SDPA / compile / checkpointing 的 CUDA 三轮对照已完成；
- CUDA 同步计时和显存记录已补齐，Mac 上绘图验证正常。

尚未覆盖：

- 其他 GPU、更大模型、更长上下文或更大 batch；
- SDPA 实际选择的具体 attention backend；
- 把 compile 的首次编译成本摊入完整训练任务后的收益；
- MFU，以及 GPT-2 / model_v3 的额外吞吐对照；
- 接近显存上限时 checkpointing 能否避免 OOM。

所以这篇番外最终交付的是：**一套可复用的 Windows / CUDA 环境、一次有明确根因的依赖排障，以及一组保留测量边界的 MPS / CUDA 对照结果。**