# Ornith-1.0-35B 本地部署：GTX1060 实战

在 **Dell G3579（i7-8750H 6C12T + GTX1060 Max-Q 6GB + 32GB DDR4-2666）** 上本地运行
**Ornith-1.0-35B（qwen35moe 架构，MoE 35B 总参 / 3B 激活）Q4_K_M 量化**，
达到 **192K 上下文 + 18 t/s** 的完整调试记录与脚本。

> 环境相关的 IP / 账户 / 本地路径在仓库中为占位符（`<LAPTOP_IP>`、`<SCRIPT_DIR>`、`<REDACTED>` 等），
> 直接使用前需替换为实际值。

---

## 最终最优配置

```
llama-server -m ornith-1.0-35b-Q4_K_M.gguf \
  -ngl 999 -cmoe --no-mmap \
  -c 196608 -kvo -ctk q8_0 -ctv q8_0 \
  -fit off --jinja --host 0.0.0.0 --port 8080
+ 进程优先级 High（脚本固化）
+ High Performance 电源计划
```

| 指标 | 值 |
|------|-----|
| 生成速度 | **18 t/s**（Q4 在此内存上的物理极限） |
| 上下文 | 192K（KV q8_0 量化，2.04GB 在 GPU） |
| 显存占用 | 4.9GB / 6GB |
| 系统内存余量 | ~7GB |
| 接口 | OpenAI 兼容 `http://<LAPTOP_IP>:8080/v1` |

一键启动：`start_ornith.py`（自动写 bat → 拉起服务 → 设 High 优先级 → 健康检查）。

---

## 关键技术突破

1. **老版 llama.cpp b8600 才能 offload qwen35moe**
   主线 b10301（2026-03 起加入 fused metadata 要求，PR #19139）对缺少 fused metadata 的
   qwen35moe GGUF 强制全部 40 层跑 CPU。降级到 b8600（2026-02，fused 要求之前）后
   GPU 正常接管 non-expert / SSM 层。**纯 CPU 10 t/s → GPU offload 17.8 t/s**。

2. **`-fit off` 解锁 192K 且提速**
   b8600 的 fit 逻辑会静默把 `-c 196608` 压回 131072。禁用 fit 后 192K 才真正生效，
   速度反而从 16 → 18 t/s（compute buffer 配置变化）。

3. **KV q8_0 量化 + `-kvo` 放 GPU**
   192K KV 只要 2.04GB，不占 CPU 内存带宽。这是 128K/192K 都维持 18 t/s 的原因。

---

## 速度优化历程

| 阶段 | 速度 |
|------|------|
| 纯 CPU（主线 b10301） | 10.3 t/s |
| b8600 GPU offload | 17.76 t/s |
| + KV q8_0 / 128K | 16.14 t/s |
| + `-fit off` / 192K | 18.03 t/s |
| + 进程优先级 High | 18.0 t/s（+9%） |
| + High Performance 电源 | prefill 9.67 → 28.33 t/s |

**18 t/s = Q4 在 DDR4-2666 双通道的物理极限**：
每 token 读 ~1.69GB（3B 激活 × 0.563B），18 t/s = 30.4 GB/s，吃到带宽 90%+。

---

## 验证过的死路（避免重复踩坑）

| 尝试 | 结果 |
|------|------|
| 杀 MAA / MuMu 进程 | 速度不变（不是进程竞争） |
| 128K + `-fit off` | 18.0 t/s，与 192K 相同（上下文不拖速） |
| `--no-kv-offload`（KV 在 CPU） | 11.25 t/s，大降 |
| `-ncmoe` / `-ot` 部分专家 GPU | 15GB pinned 卡死 / override 无效 |
| ngram 投机解码 | GDN 架构不支持 partial sequence removal |
| 主线 b10301 | 无法 offload qwen35moe |
| Turbo Boost 软件开启 | BIOS 锁定，MaxClockSpeed 2208，需进 BIOS |

---

## 目录结构

- `scripts/` — 全部调试脚本（SSH 连接、启动、测速、诊断、下载、部署）
- `docs/调试记录.md` — 完整部署决策与结论归档
- `start_ornith.py` — 一键启动（推荐入口）

## 进阶方向

想冲 **21+ t/s**：换 `Q3_K_M`（~20-21 t/s）或 `IQ3_XXS` 13GB（~24-25 t/s，还省 6-7GB 内存给 KV）。
Q4 已到这台机器带宽物理极限。
