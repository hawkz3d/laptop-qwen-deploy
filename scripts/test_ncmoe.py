# -*- coding: utf-8 -*-
"""b8600 + -ncmoe N 测试：部分专家上 GPU，查显存 + 稳态速度"""
import sys, time, json, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

HOST = '<LAPTOP_IP>'
PORT = 8080
NCMOE = sys.argv[1] if len(sys.argv) > 1 else '33'
print(f'=== TEST -ncmoe {NCMOE} ===')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username='<LAPTOP_USER>', password='<REDACTED>', timeout=15, look_for_keys=False, allow_agent=False)
try:
    ssh.exec_command('powershell -NoProfile -Command "Get-Process llama-server -ErrorAction SilentlyContinue | Stop-Process -Force"', timeout=20)[1].read()
    bat = (f'@echo off\r\ncd /d D:\\llama_old\\bin\r\n'
           f'llama-server.exe -m D:\\models\\ornith-1.0-35b-Q4_K_M.gguf -ngl 999 -ncmoe {NCMOE} --no-mmap '
           f'-c 32768 --jinja --host 0.0.0.0 --port 8080 > D:\\llama_old\\server.log 2>&1\r\n')
    sftp = ssh.open_sftp()
    with sftp.open('D:/llama_old/start.bat', 'w') as f:
        f.write(bat)
    sftp.close()
    stdin, stdout, stderr = ssh.exec_command('wmic process call create "D:\\llama_old\\start.bat"', timeout=30)
    print('WMIC:', stdout.read().decode('utf-8', errors='replace')[:150])

    def get_log():
        stdin, stdout, stderr = ssh.exec_command('cmd /c type D:\\llama_old\\server.log', timeout=20)
        return stdout.read().decode('utf-8', errors='replace')

    t0 = time.time(); log = ''
    while time.time() - t0 < 300:
        log = get_log()
        if 'model loaded' in log or 'error' in log.lower() or 'CUDA error' in log:
            break
        time.sleep(5)
    # 打印关键行
    for line in log.splitlines():
        if any(k in line.lower() for k in ['buffer size', 'offloaded', 'kv buffer', 'recurrent', 'cuda error', 'model loaded', 'listening', 'compute buffer']):
            print(line)
finally:
    ssh.close()

# 显存
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username='<LAPTOP_USER>', password='<REDACTED>', timeout=15, look_for_keys=False, allow_agent=False)
try:
    stdin, stdout, stderr = ssh.exec_command('cmd /c nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv', timeout=30)
    print('GPU:', stdout.read().decode('utf-8', errors='replace').strip())
finally:
    ssh.close()

# 发请求后读 timing
url = f'http://{HOST}:{PORT}/v1/chat/completions'
body = json.dumps({"model": "D:\\models\\ornith-1.0-35b-Q4_K_M.gguf",
                   "messages": [{"role": "user", "content": "Write a Python function is_prime(n). Code only."}],
                   "max_tokens": 150, "temperature": 0.6}).encode()
req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req, timeout=180) as resp:
        json.load(resp)
except Exception as e:
    print('REQ ERR:', repr(e)[:150])

time.sleep(2)
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username='<LAPTOP_USER>', password='<REDACTED>', timeout=15, look_for_keys=False, allow_agent=False)
try:
    stdin, stdout, stderr = ssh.exec_command(
        'cmd /c powershell -NoProfile -Command "Select-String -Path D:\\llama_old\\server.log -Pattern \'print_timing|eval time\' | Select-Object -Last 4 | ForEach-Object {$_.Line}"',
        timeout=30)
    print('--- TIMING ---')
    print(stdout.read().decode('utf-8', errors='replace'))
finally:
    ssh.close()
