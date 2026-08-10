# -*- coding: utf-8 -*-
"""HEAD 检查估算的 llama.cpp 老版本 Windows CUDA build 是否存在"""
import urllib.request, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

for tag in ['b8700', 'b8800', 'b8600', 'b8500', 'b8900', 'b8400']:
    url = f'https://github.com/ggml-org/llama.cpp/releases/download/{tag}/llama-{tag}-bin-win-cuda-12.4-x64.zip'
    req = urllib.request.Request(url, method='HEAD', headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            cl = r.headers.get('content-length')
            print(f'{tag}: {r.status} size={int(cl)/1024/1024:.1f}MB' if cl else f'{tag}: {r.status}')
    except Exception as e:
        print(f'{tag}: {repr(e)[:100]}')
