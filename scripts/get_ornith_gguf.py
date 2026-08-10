# -*- coding: utf-8 -*-
"""查询 Ornith-1.0-35B-GGUF 官方仓库量化文件列表（HF 直连失败则走 hf-mirror）"""
import sys, json, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)

for base in ('https://huggingface.co', 'https://hf-mirror.com'):
    url = f'{base}/api/models/deepreinforce-ai/Ornith-1.0-35B-GGUF/tree/main'
    try:
        data = fetch(url)
        print(f'== {base} OK ==')
        for f in data:
            size = f.get('size')
            gb = f'{size/1024/1024/1024:.2f} GB' if size else ''
            print(f"{f['path']}  {gb}")
        break
    except Exception as e:
        print(f'{base} ERR: {repr(e)[:200]}')
