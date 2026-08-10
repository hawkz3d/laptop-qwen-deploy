# -*- coding: utf-8 -*-
"""翻页抓 llama.cpp releases，找 2026-02/03 的 build 号（qwen35moe 支持但 fused 要求前）"""
import urllib.request, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

for page in range(1, 15):
    url = f'https://github.com/ggml-org/llama.cpp/releases?page={page}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            html = r.read().decode('utf-8', errors='replace')
    except Exception as e:
        print('page', page, 'ERR', repr(e)[:100])
        continue
    items = re.findall(r'/ggml-org/llama\.cpp/releases/tag/(b\d+)', html)
    dates = re.findall(r'datetime="(2026-[0-9]{2}-[0-9]{2})', html)
    print(f'page {page}: tags={items[:10]} dates={sorted(set(dates))[:6]}')
    if any(d <= '2026-03-20' for d in dates):
        break
