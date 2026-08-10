# -*- coding: utf-8 -*-
"""查 ik_llama.cpp releases：找 Windows CUDA 构建"""
import json, urllib.request, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.load(r)

for repo in ['Thireus/ik_llama.cpp', 'ikawrakow/ik_llama.cpp']:
    try:
        data = fetch(f'https://api.github.com/repos/{repo}/releases?per_page=6')
        print(f'===== {repo} =====')
        for rel in data:
            print('TAG:', rel.get('tag_name'), '|', rel.get('published_at'))
            print('  body:', (rel.get('body') or '')[:200].replace('\n', ' '))
            for a in rel.get('assets', []):
                print('  ASSET:', a['name'])
                print('    ', a['browser_download_url'])
    except Exception as e:
        print(f'{repo} ERR: {repr(e)[:200]}')
