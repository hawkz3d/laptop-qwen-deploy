# -*- coding: utf-8 -*-
"""验证 -ot 效果：显存 + server.log 加载信息 + 推理速度"""
import sys, time, json, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

HOST = '<LAPTOP_IP>'
PORT = 8080

# 1) 显存 + 进程
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username='<LAPTOP_USER>', password='<REDACTED>', timeout=15, look_for_keys=False, allow_agent=False)
try:
    stdin, stdout, stderr = ssh.exec_command('cmd /c nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv', timeout=30)
    print('GPU:', stdout.read().decode('utf-8', errors='replace').strip())
    stdin, stdout, stderr = ssh.exec_command('cmd /c powershell -NoProfile -Command "Get-Content D:\\llama\\server.log -TotalCount 25"', timeout=30)
    print('--- LOG HEAD ---')
    print(stdout.read().decode('utf-8', errors='replace'))
finally:
    ssh.close()

# 2) 推理测速
print()
print('=== SPEED TEST (-ot) ===')
url = f'http://{HOST}:{PORT}/v1/chat/completions'
body = json.dumps({"model": "D:\\models\\ornith-1.0-35b-Q4_K_M.gguf",
                   "messages": [{"role": "user", "content": "Write a Python function fibonacci(n). Code only."}],
                   "max_tokens": 300, "temperature": 0.6}).encode()
req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
t0 = time.time()
with urllib.request.urlopen(req, timeout=180) as resp:
    data = json.load(resp)
elapsed = time.time() - t0
ct = data.get('usage', {}).get('completion_tokens', 0)
content = data['choices'][0]['message'].get('content', '')
print(f'elapsed={elapsed:.1f}s completion_tokens={ct} speed={ct/elapsed:.2f} tok/s')
print('--- ANSWER ---')
print(content[:500] if content else '(empty)')
