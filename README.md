# Ornith-1.0-35B 本地部署：GTX1060 实战

在 **Dell G3579（i7-8750H 6C12T + GTX1060 Max-Q 6GB + 32GB DDR4-2666）** 上本地运行
**Ornith-1.0-35B（qwen35moe 架构，MoE 35B 总参 / 3B 激活）Q4_K_M 量化**，
达到 **192K 上下文 + 18 t/s** 的完整部署记录与调试脚本。

> 仓库内的 IP / 账户 / 本地路径均为占位符（`<LAPTOP_IP>`、`<LAPTOP_USER>`、`<REDACTED>` 等），
> 使用前需替换为实际值。

---

## 硬件与模型

| 项 | 值 |
|----|----|
| CPU | i7-8750H（6C12T，Turbo Boost 被 BIOS 锁定在 2.2GHz） |
| GPU | GTX 1060 Max-Q 6GB（cc 6.1，CUDA 12.4） |
| 内存 | 32GB DDR4-2666 双通道 |
| 模型 | `ornith-1.0-35b-Q4_K_M.gguf`，19.71GB，Q4_K 量化（file_type 15） |
| 架构 | qwen35moe：40 层 hybrid sliding + full attention，256 routed + 1 shared expert，8 active |
| 上下文 | 262K（模型上限） |

**为什么是这个模型**：MoE 35B 总参 / 3B 激活，GTX1060 + 32GB 下能完整放下并跑出实用速度；
Q4_K_M 是速度与质量的平衡点。Q3 量化更小的 13GB IQ3_XXS 能更快，但质量略降，未采用。

---

## 最终最优配置

```
llama-server -m ornith-1.0-35b-Q4_K_M.gguf \
  -ngl 999 -cmoe --no-mmap \
  -c 196608 -kvo -ctk q8_0 -ctv q8_0 \
  -fit off --jinja --host 0.0.0.0 --port 8080
```

| 指标 | 值 |
|------|-----|
| 生成速度 | **18 t/s**（Q4 在此内存上的物理极限） |
| 上下文 | 192K（KV q8_0 量化，2.04GB 在 GPU） |
| 显存占用 | 4.9GB / 6GB |
| 系统内存余量 | ~7GB |
| 接口 | OpenAI 兼容 `http://<LAPTOP_IP>:8080/v1` |

**进程优先级 High（+9%）**：启动后把 `llama-server` 进程优先级设为 High。
**High Performance 电源计划**：prefill 从 9.67 → 28.33 t/s。

---

## 一键启动

`scripts/start_ornith.py` — SSH 连到目标机 → 杀旧进程 → 写入并拉起 `start_ornith.bat`
（固化上述 192K 配置）→ 设 High 优先级 → 轮询 `server.log` 等待 `model loaded` → 健康检查 `/health`。

---

## 部署前提：为什么必须用老版 llama.cpp b8600

**主线 b10301（2026-03 起加入 fused metadata 要求，PR #19139）对缺少 fused metadata 的
qwen35moe GGUF 强制全部 40 层跑 CPU**，GPU 完全闲置（`-lv 6` 日志铁证 `assigned to device CPU`）。

**老版 b8600（2026-02，fused 要求引入之前）能正常 offload qwen35moe**。
部署到 `D:\llama_old\bin`（从新版目录复制 cudart/cublas DLL 后 CUDA 正常识别 GTX1060）。
**纯 CPU 10 t/s → GPU offload 17.8 t/s**。

### 环境布置（一次性）

1. 下载 llama.cpp b8600 CUDA 版 + **cudart 包**（CUDA 主包不含 cuBLAS/cudart DLL，
   缺它 `--list-devices` 显示 `(none)`、后端只加载 CPU）
2. 验证：`llama-server --list-devices` 应显示 `CUDA0: GTX 1060 Max-Q (6143 MiB, cc 6.1)`
3. 下载模型：`hf-mirror.com/deepreinforce-ai/Ornith-1.0-35B-GGUF/resolve/main/ornith-1.0-35b-Q4_K_M.gguf`（19.71GB）
4. 驱动 566.36 / CUDA 12.7，兼容 cu12.4 build

---

## 关键参数解读

| 参数 | 作用 |
|------|------|
| `-ngl 999` | 尽可能把所有层 offload 到 GPU |
| `-cmoe` | **MoE 专家层固定 CPU**。6GB 显存放不下 15GB 专家（硬上限），只把 non-expert / SSM 层放 GPU |
| `--no-mmap` | 模型一次性预载内存，推理时不触发磁盘缺页中断 |
| `-c 196608` | 192K 上下文 |
| `-kvo` + `-ctk q8_0 -ctv q8_0` | KV cache 量化后放 GPU，192K KV 仅 2.04GB，不占 CPU 内存带宽 |
| `-fit off` | **必须**。否则 fit 逻辑会静默把 `-c 196608` 压回 131072 |
| `--jinja` | 启用 chat template |

---

## 速度优化历程

**阶段一（主线 b10301，早期路径）** —— 3 → 17 t/s：

| 步骤 | 变更 | 效果 |
|------|------|------|
| 基线 | 分层对半切（前 20 层 GPU） | 3 t/s（PCIe 传输瓶颈） |
| `--no-moe-offload` | 专家钉 CPU，只留 non-expert 在 GPU | 10 t/s（+230%） |
| `--no-mmap` | 模型预载内存 | 13.5 t/s（+35%） |
| 调整 `-ngl` | 更多层拉回 GPU | 17 t/s |
| TurboQuant KV | Key 4bit / Value 3bit 量化 | 17 t/s @ 256K |
| `--mlock` | 锁定内存防换页（需容器 IPC_LOCK） | 长跑不掉速 |

> 此阶段为 b10301 + TurboQuant 路线的探索结论。qwen35moe 最终走 b8600 + `-cmoe` 定稿
> （KV 用 `-ctk/-ctv q8_0`，未用 TurboQuant，也未开 `--mlock`——32GB 下不必要）。

**阶段二（b8600，最终定稿）**：

| 阶段 | 速度 |
|------|------|
| 纯 CPU（主线 b10301） | 10.3 t/s |
| b8600 GPU offload | 17.76 t/s |
| + KV q8_0 / 128K | 16.14 t/s |
| + `-fit off` / 192K | 18.03 t/s |
| + 进程优先级 High | 18.0 t/s（+9%） |
| + High Performance 电源 | prefill 9.67 → 28.33 t/s |

**18 t/s = Q4 在 DDR4-2666 双通道的物理极限**：
每 token 从内存读 ~1.69GB（3B 激活 × 0.563B），18 t/s = 30.4 GB/s，吃到带宽 90%+。
**128K 与 192K 速度完全相同**（KV 在 GPU，不占 CPU 带宽瓶颈），故定稿 192K。

---

## 验证过的死路（避免重复踩坑）

| 尝试 | 结果 |
|------|------|
| 杀掉多余进程 | 速度不变（不是进程竞争） |
| `--no-kv-offload`（KV 放 CPU） | 11.25 t/s，大降 |
| `-ncmoe` / `-ot` 部分专家 GPU | 15GB pinned 卡死 / override 无效 |
| ngram 投机解码 | GDN 架构不支持 partial sequence removal |
| 主线 b10301 | 无法 offload qwen35moe |
| Turbo Boost 软件开启 | BIOS 锁定，MaxClockSpeed 2208，需进 BIOS（预期 <1 t/s，带宽已饱和） |

---

## 目录结构

- `scripts/` — 全部调试脚本（SSH 连接、下载、部署、测速、诊断、一键启动）
- `scripts/start_ornith.py` — 一键启动（推荐入口）
- `docs/调试记录.md` — 完整部署决策与结论归档

---

## 进阶方向

- **换更小量化提速**（唯一路径，用户决策停在 Q4 18 t/s 未采用）：
  - Q3_K_M（~16.5GB）→ 预期 ~20-21 t/s
  - IQ3_XXS（13GB）→ 预期 ~24-25 t/s，还省 6-7GB 内存给 KV
- 更强硬件（RTX 系列 / DDR5 / PCIe Gen4）直接线性获益，该配置思路不变
- 在相同 GTX1060 上测试 D-Flash 草稿器配合 27B dense 模型，探索突破 25 t/s
