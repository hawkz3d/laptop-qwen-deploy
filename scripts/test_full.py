# -*- coding: utf-8 -*-
"""读 server.log offload 详情 + 大 max_tokens 测试完整输出"""
import sys, time, json, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

HOST = '<LAPTOP_IP>'
PORT = 8080
MODEL = 'D:\\models\\ornith-1.0-35b-Q4_K_M.gguf'

# 1) 读 server.log 里 offload/gpu/kv 相关
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username='<LAPTOP_USER>', password='<REDACTED>', timeout=15, look_for_keys=False, allow_agent=False)
try:
    stdin, stdout, stderr = ssh.exec_command(
        'cmd /c powershell -NoProfile -Command "Select-String -Path D:\\llama\\server.log -Pattern \'offload|CUDA0|CPU buffer|KV|buffer size|mem needed|load_tensors|compute buffer|layers\' | Select-Object -First 40 | ForEach-Object {$_.Line}"',
        timeout=30)
    print('=== SERVER LOG (offload/kv lines) ===')
    print(stdout.read().decode('utf-8', errors='replace'))
finally:
    ssh.close()

# 2) 大 max_tokens 测试
def chat(prompt, max_tokens=2048, temp=0.6):
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

print()
print('=== FULL TEST: is_prime (max_tokens=2048) ===')
c, r, u, e = chat('Write a Python function is_prime(n). Keep it concise, return the code only.')
ct = u.get('completion_tokens', 0)
print(f'elapsed={e:.1f}s completion_tokens={ct} speed={ct/e:.2f} tok/s')
print('--- FINAL ANSWER ---')
print(c[:2000] if c else '(empty)')
