"""Claude CLI Web Chat v2 — NAS 值守式 Web 前端

v2 改动:
- 动态解析 Claude CLI 路径 (PATH / npx glob / 常见位置), 免疫 Claude 升级后 npx 缓存路径变化
- SSE 流式输出: thinking / text 实时推送, 告别阻塞等待
- 每会话串行锁: 多个会话并行, 不再全局排队
- 模型选择: /api/models + chat 请求带 model
- 会话删除: DELETE /api/sessions/<sid>
"""
from flask import Flask, request, jsonify, make_response, Response
import subprocess, uuid, os, json, threading, glob, time, select

app = Flask(__name__)

HOME = os.environ.get("HOME", "/home/<USER>")
PORT = int(os.environ.get("PORT", "9025"))
TIMEOUT = int(os.environ.get("CLAUDE_TIMEOUT", "600"))
CLAUDE_BIN = os.environ.get("CLAUDE_BIN", "")   # 可选: 显式指定则优先, 否则动态解析
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "")  # 全局默认模型
MODELS = [m.strip() for m in os.environ.get(
    "CLAUDE_MODELS",
    "claude-opus-4-7,claude-sonnet-4-6,claude-haiku-4-5-20251001"
).split(",") if m.strip()]

PROJ_DIRS = [
    f"{HOME}/.claude/projects/-vol1-1000",
    f"{HOME}/.claude/projects/-home-<USER>",
    f"{HOME}/.claude/projects/-tmp",
    "/vol2/1000/claude-sync/projects/-",
]
HTML_FILE = "/vol1/1000/bots/claude_web/index.html"
PROVIDERS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "providers.json")

SYSTEM_PROMPT = os.environ.get(
    "CLAUDE_SYSTEM_PROMPT",
    "使用中文进行所有内部推理和思考。所有 thinking 过程必须用中文。"
)

_session_locks = {}
_locks_lock = threading.Lock()


def get_lock(sid):
    with _locks_lock:
        if sid not in _session_locks:
            _session_locks[sid] = threading.Lock()
        return _session_locks[sid]


def find_claude_bin():
    """解析 Claude CLI 路径, 免疫 npx 升级导致的路径变化。"""
    if CLAUDE_BIN and os.path.isfile(CLAUDE_BIN):
        return CLAUDE_BIN
    for d in os.environ.get("PATH", "").split(":"):
        p = os.path.join(d, "claude")
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    cands = glob.glob(os.path.join(
        HOME, ".npm/_npx/*/node_modules/@anthropic-ai/claude-code-linux-x64/claude"))
    if cands:
        return max(cands, key=os.path.getmtime)
    for p in (os.path.join(HOME, ".local/bin/claude"), "/usr/local/bin/claude"):
        if os.path.isfile(p):
            return p
    return None


def session_exists(sid):
    for d in PROJ_DIRS:
        if os.path.isfile(os.path.join(d, sid + ".jsonl")):
            return True
    return False


def sse(event, payload):
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


def load_providers():
    """读取 providers.json 的配置表（每次读取, 编辑热生效）"""
    try:
        with open(PROVIDERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f).get('providers', {})
    except Exception:
        return {}


def provider_env(config_key):
    """指定 provider 的环境覆盖（base_url/token/Claude 模型角色映射），无则空"""
    if not config_key:
        return {}
    p = load_providers().get(config_key)
    if not p:
        return {}
    default = p.get('default_model', '')
    mapping = p.get('mapping', {})
    env = {
        "ANTHROPIC_BASE_URL": p.get('base_url', ''),
        "ANTHROPIC_AUTH_TOKEN": p.get('auth_token', ''),
        "ANTHROPIC_MODEL": default,
        "ANTHROPIC_DEFAULT_OPUS_MODEL": mapping.get('opus', default),
        "ANTHROPIC_DEFAULT_SONNET_MODEL": mapping.get('sonnet', default),
        "ANTHROPIC_DEFAULT_HAIKU_MODEL": mapping.get('haiku', default),
    }
    return {k: v for k, v in env.items() if v}


def generate(message, session_id, config_key):
    claude_bin = find_claude_bin()
    if not claude_bin:
        yield sse("error", {"message": "找不到 Claude CLI, 请检查安装"})
        return
    provider = load_providers().get(config_key) if config_key else None
    model = provider.get('default_model', '') if provider else CLAUDE_MODEL
    effort = provider.get('effort', '') if provider else ''
    env_override = provider_env(config_key)
    if provider:
        # toolsearch: MCP Tool Search（第三方代理易 400, 默认关）
        if 'toolsearch' in provider:
            env_override["ENABLE_TOOL_SEARCH"] = "true" if provider.get('toolsearch') else "false"
        # teammate: Agent Teams 实验特性
        if provider.get('teammate'):
            env_override["CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS"] = "1"
    with get_lock(session_id):
        args = [claude_bin]
        if session_exists(session_id):
            args += ["--resume", session_id]
        else:
            args += ["--session-id", session_id]
        args += ["--print", "--verbose", "--output-format", "stream-json",
                 "--permission-mode", "bypassPermissions",
                 "--append-system-prompt", SYSTEM_PROMPT, "-p", message]
        if model:
            args += ["--model", model]
        if effort:
            args += ["--effort", effort]
        if provider and 'teammate' in provider and not provider.get('teammate'):
            args += ["--disallowedTools", "Agent"]
        try:
            proc = subprocess.Popen(
                args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, bufsize=1,
                env={**os.environ, **env_override, "HOME": HOME}, cwd=HOME)
        except Exception as e:
            yield sse("error", {"message": f"启动 Claude CLI 失败: {e}"})
            return

        thinking = reply = model_used = ""
        duration_ms = 0
        deadline = time.time() + TIMEOUT
        while True:
            if time.time() > deadline:
                proc.kill()
                yield sse("error", {"message": f"请求超时 ({TIMEOUT}s)"})
                return
            r, _, _ = select.select([proc.stdout], [], [], 1.0)
            if not r:
                if proc.poll() is not None:
                    break
                continue
            line = proc.stdout.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            t = obj.get("type", "")
            if t == "assistant":
                msg = obj.get("message", {})
                if msg.get("model"):
                    model_used = msg["model"]
                for c in msg.get("content", []):
                    ct = c.get("type", "")
                    if ct == "thinking":
                        thinking += c.get("thinking", "")
                        yield sse("thinking", {"delta": c.get("thinking", "")})
                    elif ct == "text":
                        reply += c.get("text", "")
                        yield sse("text", {"delta": c.get("text", "")})
                    elif ct == "tool_use":
                        yield sse("tool", {"name": c.get("name", ""), "input": c.get("input", {})})
            elif t == "result":
                duration_ms = obj.get("duration_ms", 0)

        proc.wait()
        if proc.returncode != 0:
            err = proc.stderr.read()
            yield sse("error", {"message": (err or f"Claude CLI 退出码 {proc.returncode}")[-500:]})
            return
        yield sse("done", {"session_id": session_id, "duration_ms": duration_ms, "model": model_used})


@app.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    data = request.get_json(force=True, silent=True) or {}
    message = (data.get('message') or '').strip()
    session_id = data.get('session_id') or str(uuid.uuid4())
    config_key = data.get('config') or ''
    if not message:
        return jsonify({"error": "消息不能为空"}), 400
    return Response(
        generate(message, session_id, config_key),
        mimetype='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


@app.route('/api/configs')
def list_configs():
    providers = load_providers()
    return jsonify([{'key': k, 'label': p.get('label', k), 'models': p.get('models', [])}
                    for k, p in providers.items()])


@app.route('/api/config')
def get_config():
    try:
        with open(PROVIDERS_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        return jsonify({"ok": True, "content": content})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/api/config', methods=['POST'])
def save_config():
    data = request.get_json(force=True, silent=True) or {}
    content = data.get('content', '')
    if not content:
        return jsonify({"ok": False, "error": "内容为空"}), 400
    try:
        obj = json.loads(content)
    except Exception as e:
        return jsonify({"ok": False, "error": f"JSON 格式错误: {e}"}), 400
    if 'providers' not in obj or not isinstance(obj.get('providers'), dict):
        return jsonify({"ok": False, "error": "缺少 providers 字段"}), 400
    for key, p in obj['providers'].items():
        if not isinstance(p, dict):
            return jsonify({"ok": False, "error": f"provider [{key}] 不是对象"}), 400
    try:
        if os.path.exists(PROVIDERS_FILE):
            with open(PROVIDERS_FILE, 'r', encoding='utf-8') as f:
                old = f.read()
            with open(PROVIDERS_FILE + '.bak', 'w', encoding='utf-8') as f:
                f.write(old)
        with open(PROVIDERS_FILE, 'w', encoding='utf-8') as f:
            f.write(json.dumps(obj, ensure_ascii=False, indent=2))
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/')
def index():
    resp = make_response(open(HTML_FILE, 'r', encoding='utf-8').read())
    resp.headers['Content-Type'] = 'text/html; charset=utf-8'
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp


def _text_of(content):
    """提取消息中的纯文字, 忽略 tool_use / tool_result 等工具消息"""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return ' '.join(c.get('text', '') for c in content if c.get('type') == 'text')
    return ''


def parse_jsonl_sessions():
    sessions = {}
    files = []
    for d in PROJ_DIRS:
        if os.path.isdir(d):
            files.extend(glob.glob(f"{d}/*.jsonl"))
    for fpath in sorted(files, key=os.path.getmtime, reverse=True):
        sid = os.path.basename(fpath).replace('.jsonl', '')
        msgs = []
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except Exception:
                        continue
                    t = obj.get('type', '')
                    msg = obj.get('message', {})
                    if t == 'user':
                        text = _text_of(msg.get('content', '')).strip()
                        if not text:
                            continue  # 过滤 tool_result 等无文字消息
                        msgs.append({'role': 'user', 'content': text, 'time': ''})
                    elif t == 'assistant':
                        content = msg.get('content', [])
                        thinking_text = ''
                        text = ''
                        tools = []
                        for c in content if isinstance(content, list) else []:
                            ct = c.get('type', '')
                            if ct == 'thinking':
                                thinking_text += c.get('thinking', '')
                            elif ct == 'text':
                                text += c.get('text', '')
                            elif ct == 'tool_use':
                                tools.append({'name': c.get('name', ''), 'input': c.get('input', {})})
                        if not text.strip() and not thinking_text.strip() and not tools:
                            continue  # 完全空的消息
                        if msgs and msgs[-1]['role'] == 'assistant':
                            msgs[-1]['thinking'] += thinking_text
                            msgs[-1]['content'] += text
                            msgs[-1]['tools'] += tools
                        else:
                            msgs.append({'role': 'assistant', 'thinking': thinking_text, 'content': text, 'tools': tools, 'time': ''})
        except Exception:
            continue
        if msgs:
            first = next((m['content'] for m in msgs if m['role'] == 'user'), '')
            sessions[sid] = {
                'id': sid, 'first_msg': first[:80], 'msg_count': len(msgs),
                'updated': os.path.getmtime(fpath), 'msgs': msgs
            }
    return sessions


@app.route('/api/sessions')
def list_sessions():
    sessions = parse_jsonl_sessions()
    result = [{'id': s['id'], 'first_msg': s['first_msg'], 'msg_count': s['msg_count'],
               'updated': s['updated']} for s in
              sorted(sessions.values(), key=lambda x: x.get('updated', 0), reverse=True)]
    return jsonify(result)


@app.route('/api/sessions/<sid>')
def get_session(sid):
    sessions = parse_jsonl_sessions()
    if sid not in sessions:
        return jsonify({"error": "会话不存在"}), 404
    return jsonify(sessions[sid])


@app.route('/api/sessions/<sid>', methods=['DELETE'])
def delete_session(sid):
    for d in PROJ_DIRS:
        p = os.path.join(d, sid + ".jsonl")
        if os.path.isfile(p):
            try:
                os.remove(p)
                return jsonify({"ok": True})
            except Exception as e:
                return jsonify({"error": str(e)}), 500
    return jsonify({"error": "会话不存在"}), 404


if __name__ == '__main__':
    print(f"Claude Web Chat v2: http://0.0.0.0:{PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False, threaded=True)
