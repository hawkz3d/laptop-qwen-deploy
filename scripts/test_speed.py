# -*- coding: utf-8 -*-
"""验证 -ngl 999 -cmoe：显存占用 + 推理速度 + 输出质量"""
import sys, time, json, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

HOST = '<LAPTOP_IP>'
PORT = 8080
MODEL = 'D:\\models\\ornith-1.0-35b-Q4_K_M.gguf'

# 1) 显存
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username='<LAPTOP_USER>', password='<REDACTED>', timeout=15, look_for_keys=False, allow_agent=False)
try:
    stdin, stdout, stderr = ssh.exec_command('cmd /c nvidia-smi --query-gpu=memory.used,memory.total --format=csv', timeout=30)
    print('GPU MEM:', stdout.read().decode('utf-8', errors='replace').strip())
finally:
    ssh.close()

def chat(prompt, max_tokens=1024, temp=0.6):
    url = f'http://{HOST}:{PORT}/v1/chat/completions'
    body = json.dumps({"model": MODEL,
                       "messages": [{"role": "user", "content": prompt}],
                       "max_tokens": max_tokens, "temperature": temp}).encode()
    req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=600) as resp:
        data = json.load(resp)
    elapsed = time.time() - t0
    msg = data['choices'][0]['message']
    return msg.get('content', ''), msg.get('reasoning_content', ''), data.get('usage', {}), elapsed

# 2) 第一次（预热）
print('=== TEST 1 (warmup) ===')
c, r, u, e = chat('Write a Python function is_prime(n). Return the code only, be concise.', max_tokens=1024)
ct = u.get('completion_tokens', 0)
print(f'elapsed={e:.1f}s completion_tokens={ct} speed={ct/e:.2f} tok/s')
print('--- ANSWER ---')
print(c[:800] if c else '(empty!)')

# 3) 第二次（测速）
print('=== TEST 2 (speed) ===')
c2, r2, u2, e2 = chat('Write Python function quick_sort(arr). Code only.', max_tokens=1024)
ct2 = u2.get('completion_tokens', 0)
print(f'elapsed={e2:.1f}s completion_tokens={ct2} speed={ct2/e2:.2f} tok/s')
print('--- ANSWER ---')
print(c2[:800] if c2 else '(empty!)')
