# -*- coding: utf-8 -*-
"""发请求期间采样 GPU 显存，验证 5GB 是推理峰值（非 OOM）"""
import sys, time, json, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

HOST = '<LAPTOP_IP>'
PORT = 8080

# 启动 GPU 采样（后台，1s 间隔）
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username='<LAPTOP_USER>', password='<REDACTED>', timeout=15, look_for_keys=False, allow_agent=False)
try:
    ssh.exec_command(
        'powershell -NoProfile -Command "Start-Process nvidia-smi -ArgumentList \'--query-gpu=memory.used,utilization.gpu --format=csv -lms 500\' -RedirectStandardOutput C:\\gpu_mon.txt -WindowStyle Hidden"',
        timeout=20)[1].read()
    time.sleep(2)
finally:
    ssh.close()

# 发请求（生成 ~300 token）
print('sending request...')
url = f'http://{HOST}:{PORT}/v1/chat/completions'
body = json.dumps({"model": "D:\\models\\ornith-1.0-35b-Q4_K_M.gguf",
                   "messages": [{"role": "user", "content": "Write a Python function to parse JSON and extract keys. Provide detailed code."}],
                   "max_tokens": 300, "temperature": 0.6}).encode()
req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req, timeout=300) as resp:
        data = json.load(resp)
    ct = data.get('usage', {}).get('completion_tokens', 0)
    print(f'completion_tokens={ct}')
except Exception as e:
    print('REQ ERR:', repr(e)[:150])

# 停采样，读结果
time.sleep(2)
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username='<LAPTOP_USER>', password='<REDACTED>', timeout=15, look_for_keys=False, allow_agent=False)
try:
    ssh.exec_command('powershell -NoProfile -Command "Get-Process nvidia-smi -ErrorAction SilentlyContinue | Stop-Process -Force"', timeout=20)[1].read()
    time.sleep(1)
    stdin, stdout, stderr = ssh.exec_command('cmd /c type C:\\gpu_mon.txt', timeout=20)
    lines = stdout.read().decode('utf-8', errors='replace').splitlines()
    # 解析峰值
    vals = []
    for l in lines[1:]:
        parts = l.replace(',', ' ').split()
        if parts:
            try:
                vals.append((int(parts[0]), int(parts[1]) if len(parts) > 1 else 0))
            except Exception:
                pass
    if vals:
        peak_mem = max(v[0] for v in vals)
        peak_util = max(v[1] for v in vals)
        print(f'samples={len(vals)} peak_mem={peak_mem}MiB peak_util={peak_util}%')
        print('idle_mem=', vals[0][0] if vals else '?', 'MiB')
    else:
        print('no valid samples')
    print('--- tail ---')
    for l in lines[-5:]:
        print(l)
finally:
    ssh.close()
