# -*- coding: utf-8 -*-
"""GitHub API 翻页查 llama.cpp releases，找 2026-02/03（qwen35moe 支持但 fused 前）"""
import urllib.request, json, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

for page in range(1, 12):
    url = f'https://api.github.com/repos/ggml-org/llama.cpp/releases?per_page=100&page={page}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.load(r)
    except Exception as e:
        print('page', page, 'ERR', repr(e)[:150])
        break
    if not data:
        print('empty at page', page)
        break
    dates = [rel.get('published_at', '') for rel in data]
    print(f'page {page}: {len(data)} releases, range {min(dates)[:10]} .. {max(dates)[:10]}')
    for rel in data:
        pub = rel.get('published_at', '')
        if '2026-02-01' <= pub[:10] <= '2026-03-20':
            print('  TARGET:', rel.get('tag_name'), pub[:10])
    if any(d < '2026-02-01' for d in dates):
        break
