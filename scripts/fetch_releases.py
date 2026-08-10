# -*- coding: utf-8 -*-
"""抓 Thireus/ik_llama.cpp releases 网页，提取最新 Windows CUDA zip 链接"""
import urllib.request, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

url = 'https://github.com/Thireus/ik_llama.cpp/releases'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        html = r.read().decode('utf-8', errors='replace')
    print('html len:', len(html))
    links = re.findall(r'/Thireus/ik_llama\.cpp/releases/download/[^\s"\'<>]+', html)
    seen = set()
    cuda_links = []
    for l in links:
        full = 'https://github.com' + l
        if full not in seen:
            seen.add(full)
            if 'cuda' in l.lower() or 'win' in l.lower():
                cuda_links.append(full)
    print('--- ANY WIN LINKS ---')
    win_links = [l for l in seen if 'win' in l.lower()]
    for l in win_links[:30]:
        print(l)
    print('--- total win:', len(win_links))
    print('--- ALL TAGS ---')
    tags = set(re.findall(r'/releases/download/([^/]+)/', html))
    for t in sorted(tags):
        print('  tag:', t)
except Exception as e:
    print('ERR:', repr(e)[:300])
