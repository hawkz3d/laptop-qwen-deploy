# -*- coding: utf-8 -*-
"""抓 llama.cpp releases 找 2026-02/03 老版本 build 号 + Windows CUDA 下载链接"""
import urllib.request, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

url = 'https://github.com/ggml-org/llama.cpp/releases'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=30) as r:
    html = r.read().decode('utf-8', errors='replace')
print('html len:', len(html))

# release tags + 日期
tags = re.findall(r'/ggml-org/llama\.cpp/releases/tag/([^"<]+)', html)
print('--- tags (recent) ---')
for t in tags[:30]:
    print('  ', t)

# 找日期（tag 附近）
# GitHub 页面有 datetime 属性
dates = re.findall(r'datetime="([^"]+)"', html)
print('--- dates ---')
for d in dates[:30]:
    print('  ', d)
