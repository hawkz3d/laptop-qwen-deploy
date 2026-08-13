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
五个关键命令行参数优化流程
1. 基础方案与核心矛盾
首次尝试： 将模型按层数对半切分（前20层放GPU，其余放CPU），速度仅约 3 Token/s。瓶颈在于PCIe总线传输（每秒仅能处理3个Token），且每个Token触发CPU上整层（含专家块）计算，延迟极高。
2. 专家卸载参数： --no-moe-offload
原理： MoE模型中大部分权重位于专家模块，每个Token仅唤醒少数专家。将专家模块从GPU分离并固定在CPU上，仅将非专家部分（小且响应快）留在GPU。GPU首先处理非专家部分，再查询所需专家ID，最后在CPU上完成专家计算。
操作： 在llama.cpp中使用 --no-moe-offload 标志，将每层的专家取出并钉在CPU内存中。
效果： 相同硬件下速度从 3 Token/s 提升至 10 Token/s （提升约230%）。
3. 禁用内存映射： --no-mmap
问题： 默认启用内存映射（mmap）时，操作系统假装模型文件完整存在于内存，实际仅在需要时从磁盘加载页面块。推理时遇到未加载的专家会触发磁盘缺页中断，导致Token生成延迟。
操作： 添加 --no-mmap 标志，将模型（约20GB）一次性预加载至内存中。加载完成后所有专家就绪，推理时无磁盘交互。
效果： 速度从 10 Token/s 提升至 13.5 Token/s （提升约35%）。
4. 调整GPU负载：增加 --gpu-layers 参数值
剩余显存利用： 调整后GPU占用约4GB，尚有2GB显存空闲。将参数 --gpu-layers 从41减少至35（实际为调整CPU上专家层数，原文意为将更多层放回GPU），将6层专家从CPU拉回GPU。
权衡： GPU显存占用增加至5.5GB，上下文窗口从100K压缩至约64K Token。
效果： 速度从 13.5 Token/s 提升至 17 Token/s。该速度为朗读速度水平，达到实用门槛。
5. KV缓存量化：TurboQuant技术
目标： 恢复因GPU显存占用增加而缩减的上下文窗口（从64K恢复到256K）。
原理： 上下文窗口消耗显存（KV缓存），线性增长。默认使用Q8量化缓存（近无损）。Google DeepMind推出的 TurboQuant 技术允许将键（Key）量化至4位、值（Value）量化至3位，保持几乎无损的质量（论文显示Q3-Q4范围内无法与Q8区分）。
不对称量化： 模型采用分组查询注意力（8:1），因此键可以承受更重压缩。
操作： 添加参数 --turbo-keys 4 和 --turbo-values 4 （实际根据模型调整为不同比特位，测试中再次调整专家层数：将CPU上的专家从35层增至36层以释放显存）。
最终配置： GPU显存占用5.9GB，上下文窗口成功扩展至 256K Token，速度仍保持 17 Token/s。显存占用未增加的原因是KV缓存经过量化后体积缩小，补偿了GPU层数增加带来的额外消耗。
6. 内存锁定： --mlock 与 Docker 权限
问题： 放置于CPU内存中的专家模块可能被操作系统换出至磁盘（页面交换），导致推理中出现随机卡顿（慢Token）。
操作： 需在三个层面设置：
Docker容器获得 --cap-add=IPC_LOCK 权限。
llama.cpp启用 --mlock 标志。
检查确认 mlock 生效（显示 Memory Locked: 16GB）。
效果： 专家模块被锁定在内存中，不被换页或移动。长时间运行（数天）性能不降级，速度稳定在 17 Token/s。
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
| 杀掉多余进程 | 速度不变（不是进程竞争） |
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
硬件不再成为瓶颈的核心洞察
默认设置（如分层对半切、启用mmap、不量化缓存）严重低估了旧硬件的潜力。通过5个命令行参数和一条Docker命令，即可将性能从3 Token/s提升至17 Token/s。
该配置基于性能底线（GTX 1060），任何更新的硬件（如RTX系列、更快内存、PCIe Gen4）将获得更高速度。
限制模型可用性的已不再是硬件，而是对命令行参数的正确调配。
后续值得探索的方向：在相同GTX 1060上测试D-Flash草稿器配合270亿密集版模型，尝试突破25 Token/s

