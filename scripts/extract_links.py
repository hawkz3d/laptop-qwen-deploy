# -*- coding: utf-8 -*-
"""从 metaso 抓取的 releases 页面提取 ik_llama.cpp zip 下载链接"""
import json, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

path = r'<PROJECT_DIR>\<SESSION_ID>\tool-results\mcp-metaso-search-metaso_reader-1786194247346.txt'
with open(path, encoding='utf-8') as f:
    data = json.load(f)
text = data[0]['text']
print('len:', len(text))
# 找所有 release 下载链接
links = re.findall(r'https://github\.com/Thireus/ik_llama\.cpp/releases/download/[^\s"\'<>]+', text)
seen = set()
for l in links:
    if l not in seen:
        seen.add(l)
        print(l)
print('--- total unique:', len(seen))
