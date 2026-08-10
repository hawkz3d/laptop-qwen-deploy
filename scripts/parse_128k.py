# -*- coding: utf-8 -*-
"""从会话转录里提取 128K / 131072 相关的速度测试记录"""
import sys, json, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PATH = r'<PROJECT_DIR>\<SESSION_ID>.jsonl'

hits = []
with open(PATH, 'r', encoding='utf-8', errors='replace') as f:
    for i, line in enumerate(f, 1):
        if '131072' not in line and '128K' not in line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        # 提取消息文本
        msg = obj.get('message', {})
        text = ''
        c = msg.get('content')
        if isinstance(c, str):
            text = c
        elif isinstance(c, list):
            for part in c:
                if isinstance(part, dict):
                    t = part.get('text', '')
                    if t:
                        text += t + '\n'
        if not text:
            continue
        role = msg.get('role', '?')
        # 只要包含速度关键词的行
        speed_lines = []
        for ln in text.splitlines():
            if re.search(r'131072|128K|eval time|tokens per second|t/s', ln):
                speed_lines.append(ln)
        if speed_lines:
            hits.append((i, role, speed_lines))

print(f'total matching messages: {len(hits)}')
for i, role, lines in hits:
    print(f'\n===== line {i} [{role}] =====')
    for ln in lines[:30]:
        print(' ', ln[:300])
