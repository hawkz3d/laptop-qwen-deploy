# -*- coding: utf-8 -*-
"""查社区 Ornith GGUF 仓库文件列表（找带 fused metadata 的 re-quant 版）"""
import json, urllib.request, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.load(r)

repos = [
    'SC117/Ornith-1.0-35B-MTP-APEX-GGUF',
    'mudler/Ornith-1.0-35B-APEX-GGUF',
    'FreedomAISVR/Ornith-1.0-35B-MXFP4-MOE-GGUF',
]
for repo in repos:
    try:
        data = fetch(f'https://huggingface.co/api/models/{repo}/tree/main')
        print(f'===== {repo} =====')
        for f in data:
            if f.get('type') == 'file':
                size = f.get('size')
                gb = f'{size/1024**3:.2f} GB' if size else ''
                print(f"  {f['path']}  {gb}")
    except Exception as e:
        print(f'{repo} ERR: {repr(e)[:200]}')
