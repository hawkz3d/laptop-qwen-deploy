# claude-web

NAS 值守式 Claude CLI Web 聊天前端（9025 端口）。通过 Claude CLI 连接多个 LLM 后端，
实现浏览器里的流式对话。

## 功能

- Claude CLI 流式 SSE 聊天（thinking / text / 工具气泡实时推送）
- Provider 配置系统：多后端切换，`providers.json` 编辑热生效
- 会话管理（列表 / 加载 / 删除）、模型与配置下拉、配置 JSON 编辑器
- 移动端适配（抽屉侧边栏、安全区适配）

## 结构

- `claude_web_server.py` — Flask 后端（SSE 流、provider env 注入、会话存储）
- `index.html` — 单页前端
- `providers.json` — Provider 配置表
- `configs/litellm.service` — 本地模型接入用的 litellm 代理 unit

## 部署

- 目录：`/vol1/1000/bots/claude_web/`
- systemd：`claude-web.service`（`PORT=9025`、`CLAUDE_TIMEOUT=600`）
- 关键 env：`CLAUDE_MODELS`、`CLAUDE_SYSTEM_PROMPT`（可覆盖中文 thinking 提示）

## Provider 配置

`providers.json` 定义后端，前端下拉切换；后端把 `base_url/auth_token/模型角色映射`
以进程 env 注入 Claude CLI（覆盖 `~/.claude/settings.json`）。

| key | 说明 | base_url |
|-----|------|----------|
| deepseek | 云端 DeepSeek（Anthropic 兼容端点） | https://api.deepseek.com/anthropic |
| ornith | laptop 本地 Ornith-1.0-35B（经 litellm 代理） | http://127.0.0.1:4025 |

### 本地 Ornith 接入（litellm 协议转换）

laptop 的 llama.cpp（b8600）只提供 OpenAI 兼容端点（`/v1/chat/completions`），
而 Claude CLI 走 Anthropic 格式（`/v1/messages`），故在 NAS 上用 litellm 做转换：

```
litellm --model openai/ornith-1.0-35b-Q4_K_M.gguf \
  --api_base http://<LAPTOP_IP>:8080/v1 --port 4025 --host 0.0.0.0
```

systemd 托管：`configs/litellm.service`。

调用链：

```
前端(9025) → Claude CLI --model openai/ornith-1.0-35b-Q4_K_M.gguf
           → litellm(:4025 /v1/messages)
           → laptop Ornith(:8080 /v1/chat/completions)
```

注意：Ornith 是推理模型，回复前会输出长思考（`reasoning_content`），
`max_tokens` 需足够大才有正文；litellm 会把思考转成 Anthropic thinking 块透传。

## 维护

- `providers.json` 编辑热生效（`GET/POST /api/config`）
- 会话 JSONL 存于 `~/.claude/projects/`
- Claude CLI 路径动态解析（PATH / npx glob），免疫升级后路径变化
