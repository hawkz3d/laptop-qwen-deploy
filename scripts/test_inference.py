# -*- coding: utf-8 -*-
"""实测 Ornith 推理：代码生成 + token/s"""
import sys, time, json, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HOST = '<LAPTOP_IP>'
PORT = 8080
MODEL = 'D:\\models\\ornith-1.0-35b-Q4_K_M.gguf'

def chat(prompt, max_tokens=512, temp=0.6):
    url = f'http://{HOST}:{PORT}/v1/chat/completions'
    body = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temp,
    }).encode()
    req = urllib.request.Request(url, data=body,
                                 headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=300) as resp:
        data = json.load(resp)
    elapsed = time.time() - t0
    msg = data['choices'][0]['message']
    content = msg.get('content', '')
    reasoning = msg.get('reasoning_content', '')
    usage = data.get('usage', {})
    return content, reasoning, usage, elapsed

# 第一次请求（含预热）
print('=== TEST 1 (warmup): is_prime ===')
c, r, u, e = chat('Write a Python function is_prime(n) that returns True if n is prime. Keep it concise.')
ct = u.get('completion_tokens', 0)
print(f'elapsed={e:.1f}s completion_tokens={ct} speed={ct/e:.2f} tok/s')
if r:
    print('--- REASONING (truncated) ---')
    print(r[:600])
print('--- CONTENT ---')
print(c[:1200])

# 第二次请求（测速更准）
print()
print('=== TEST 2 (speed): quick sort ===')
c2, r2, u2, e2 = chat('Write a Python function quick_sort(arr). Return the sorted list. Be concise.')
ct2 = u2.get('completion_tokens', 0)
print(f'elapsed={e2:.1f}s completion_tokens={ct2} speed={ct2/e2:.2f} tok/s')
print('--- CONTENT ---')
print(c2[:1200])
