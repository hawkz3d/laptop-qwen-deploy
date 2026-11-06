# 模型服务接入：流式 Web 客户端与协议适配

本模块是[AI 基础设施实践项目](../README.md)的应用接入层。通过 Flask Web 服务调用 Claude CLI，将本地推理端点接入浏览器，展示从模型服务到用户交互的调用链路。

本地 llama.cpp 提供 OpenAI 兼容接口，Claude CLI 使用 Anthropic Messages 协议；本项目的接入示例通过 LiteLLM 完成协议转换。

## 已实现能力

| 能力 | 实现 |
| --- | --- |
| 流式响应 | 将 CLI 的流式事件转发为 SSE，展示思考、正文和工具事件 |
| 后端配置切换 | 按 Provider 配置设置 CLI 子进程环境，配置文件修改后在后续读取时生效 |
| 会话管理 | 列出、加载和删除会话，读取 CLI 保存的 JSONL 记录 |
| 生成控制 | 跟踪运行中的 CLI 子进程，提供停止生成接口和请求超时处理 |
| 浏览器交互 | 单页客户端，支持移动端布局、思考与工具事件展示 |

后端切换通过配置选择实现。本模块使用现有 CLI 和模型服务，工程工作集中在子进程管理、协议接入和流式交互。

## 调用链路

```mermaid
flowchart LR
    Browser[浏览器] -->|SSE| Web[Flask Web 服务]
    Web --> CLI[Claude CLI]
    CLI -->|Anthropic Messages| Proxy[LiteLLM]
    Proxy -->|OpenAI Chat Completions| Model[llama.cpp 本地模型服务]
```

## 代码入口

| 文件 | 用途 |
| --- | --- |
| [claude_web_server.py](claude_web_server.py) | Flask 路由、CLI 子进程启动与终止、SSE 转发、配置与会话接口 |
| [index.template.html](index.template.html) | Web 客户端模板 |
| [build.py](build.py) | 历史前端构建脚本，内联静态资源；运行前需补齐脚本引用的外部图标来源 |
| [index.html](index.html) | 构建后的单页客户端 |
| [configs/litellm.service](configs/litellm.service) | 协议转换服务的 systemd 配置示例 |

## 配置与部署说明

安装并验证 Claude CLI、Python Web 依赖与模型推理服务后，按自己的环境配置 Provider。仓库中的连接信息为示例占位符，不包含可直接使用的私人运行配置。

Provider 配置描述后端地址、认证信息及模型映射；Web 后端将所选配置注入 CLI 子进程环境。配置接口为 `GET/POST /api/config`，后端列表通过 `/api/configs` 获取。

常用环境配置包括 `PORT`、`CLAUDE_TIMEOUT`、`CLAUDE_MODELS` 和 `CLAUDE_SYSTEM_PROMPT`。会话记录读取自 CLI 的项目目录。

本地模型的 LiteLLM 接入参数示例：

```bash
litellm --model openai/ornith-1.0-35b-Q4_K_M.gguf \
  --api_base http://<INFERENCE_HOST>:8080/v1 \
  --port 4025 --host 0.0.0.0
```

运行时与依赖版本应结合实际环境验证。推理模型可能先消耗输出预算进行思考，检查接入是否成功时，应同时确认正文输出与流式事件转换，避免仅凭 HTTP 成功判定完整可用。

该 Web 服务会启动具备工具执行权限的 CLI 子进程，配置接口也可修改后端信息，部署时应限制访问范围并按使用场景配置权限。

## 验证要点

- 先单独验证推理端点，再验证 LiteLLM 转换链路，最后测试 Web 流式响应。
- 分别验证会话加载、配置切换、停止生成与超时行为。
- `/health` 就绪检查属于推理节点验证，不能替代整条调用链的功能验证。

模型配置与历史性能结果见[部署与性能实验说明](../docs/deployment.md)。
