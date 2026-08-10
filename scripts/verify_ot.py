# -*- coding: utf-8 -*-
"""等待 -ot 配置模型加载完成，验证显存/offload/速度/质量"""
import sys, time, json, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

HOST = '<LAPTOP_IP>'
PORT = 8080
MODEL = 'D:\\models\\ornith-1.0-35b-Q4_K_M.gguf'

def get_log():
    stdin, stdout, stderr = ssh.exec_command('cmd /c type D:\\llama\\server.log', timeout=20)
    return stdout.read().decode('utf-8', errors='replace')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username='<LAPTOP_USER>', password='<REDACTED>', timeout=15, look_for_keys=False, allow_agent=False)

# 1) 等模型加载完成
print('Waiting model loaded...')
t0 = time.time()
while time.time() - t0 < 300:
    log = get_log()
    if 'model loaded' in log:
        print('MODEL LOADED after', round(time.time()-t0, 1), 's')
        break
    time.sleep(5)
else:
    print('TIMEOUT waiting model loaded')
    print('--- LOG TAIL ---')
    print(log[-2000:])

# 2) 显存
stdin, stdout, stderr = ssh.exec_command('cmd /c nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv', timeout=30)
print('GPU:', stdout.read().decode('utf-8', errors='replace').strip())

# 3) server.log 前 45 行（找 offload 信息）
stdin, stdout, stderr = ssh.exec_command('cmd /c powershell -NoProfile -Command "Get-Content D:\\llama\\server.log -TotalCount 45"', timeout=30)
print('--- LOG HEAD ---')
print(stdout.read().decode('utf-8', errors='replace'))

# 4) 测速
print('=== SPEED TEST ===')
url = f'http://{HOST}:{PORT}/v1/chat/completions'
body = json.dumps({"model": MODEL,
                   "messages": [{"role": "user", "content": "Write a Python function is_prime(n). Code only."}],
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
ssh.close()
