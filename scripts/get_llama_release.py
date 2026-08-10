# -*- coding: utf-8 -*-
"""查询 llama.cpp 最新 release 及 Windows CUDA 12.4 x64 资产下载链接"""
import json, urllib.request

url = 'https://api.github.com/repos/ggml-org/llama.cpp/releases/latest'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.load(r)
    print('TAG:', data.get('tag_name'))
    print('NAME:', data.get('name'))
    print('PUBLISHED:', data.get('published_at'))
    for a in data.get('assets', []):
        n = a['name']
        if 'win-cuda-12.4-x64' in n or 'win-cuda-13' in n:
            print('ASSET:', n, '|', a['browser_download_url'], '|', round(a['size']/1024/1024, 1), 'MB')
except Exception as e:
    print('ERR:', repr(e))
