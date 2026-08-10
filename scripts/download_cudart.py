# -*- coding: utf-8 -*-
"""本机流式下载 llama.cpp cudart 包（CUDA 运行时 DLL，373MB）"""
import urllib.request, sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

url = 'https://github.com/ggml-org/llama.cpp/releases/download/b10301/cudart-llama-bin-win-cuda-12.4-x64.zip'
dest = r'<TEMP_DIR>\cudart-llama-bin-win-cuda-12.4-x64.zip'
os.makedirs(os.path.dirname(dest), exist_ok=True)

req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=60) as r, open(dest, 'wb') as f:
    total = int(r.headers.get('Content-Length', 0))
    done = 0
    while True:
        chunk = r.read(1 << 20)
        if not chunk:
            break
        f.write(chunk)
        done += len(chunk)
        pct = done / total * 100 if total else 0
        print(f'\r{done/1024/1024:.1f}/{total/1024/1024:.1f} MB ({pct:.0f}%)', end='', flush=True)
print()
print('DONE:', dest, round(os.path.getsize(dest)/1024/1024, 1), 'MB')
