# -*- coding: utf-8 -*-
"""解析 DC 输出 JSON 文件，提取 llama-server 加载日志中的 offload/device 关键行"""
import json, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

path = r'<PROJECT_DIR>\<SESSION_ID>\tool-results\mcp-desktop-commander-start_process-1786193536738.txt'
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)
text = data[0]['text']
lines = text.splitlines()
print('total lines:', len(lines))
print('=== KEY LINES ===')
for line in lines:
    low = line.lower()
    if any(k in low for k in ['offload', 'cuda0', 'cuda1', 'buffer', 'device', 'llm_load_tensors', 'ssm', 'fused', 'kv cache', 'alloc', 'error', 'unknown', 'not supported']):
        print(line)
