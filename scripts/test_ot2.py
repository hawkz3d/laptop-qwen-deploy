# -*- coding: utf-8 -*-
"""测试 -ot 部分专家上 GPU：b8600 + -ot 后 N 层专家=CUDA0，测显存+速度"""
import sys, time, json, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

HOST = '<LAPTOP_IP>'
PORT = 8080
LAYERS = sys.argv[1] if len(sys.argv) > 1 else '89'  # 默认 blk.38-39
print(f'=== -ot blk.({LAYERS}) experts to CUDA0 ===')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username='<LAPTOP_USER>', password='<REDACTED>', timeout=15, look_for_keys=False, allow_agent=False)
try:
    ssh.exec_command('powershell -NoProfile -Command "Get-Process llama-server -ErrorAction SilentlyContinue | Stop-Process -Force"', timeout=20)[1].read()
    ssh.exec_command('cmd /c del D:\\llama_old\\server.log 2>nul', timeout=15)[1].read()
    ot = f'-ot "blk\\.({LAYERS})\\.ffn_(gate|up|down)_exps\\.weight=CUDA0"'
    bat = ('@echo off\r\ncd /d D:\\llama_old\\bin\r\n'
           f'llama-server.exe -m D:\\models\\ornith-1.0-35b-Q4_K_M.gguf -ngl 999 -cmoe --no-mmap '
           f'-c 131072 -kvo -ctk q8_0 -ctv q8_0 {ot} --jinja --host 0.0.0.0 --port 8080 > D:\\llama_old\\server.log 2>&1\r\n')
    sftp = ssh.open_sftp()
    with sftp.open('D:/llama_old/start_ot.bat', 'w') as f:
        f.write(bat)
    sftp.close()
    print('bat:', bat.splitlines()[2][:150])
    stdin, stdout, stderr = ssh.exec_command('wmic process call create "D:\\llama_old\\start_ot.bat"', timeout=30)
    print('WMIC:', stdout.read().decode('utf-8', errors='replace')[:120])

    def get_log():
        stdin, stdout, stderr = ssh.exec_command('cmd /c type D:\\llama_old\\server.log', timeout=20)
        return stdout.read().decode('utf-8', errors='replace')

    t0 = time.time(); log = ''
    while time.time() - t0 < 300:
        log = get_log()
        if 'model loaded' in log or 'CUDA error' in log or 'error:' in log:
            break
        time.sleep(8)
    print('--- loaded in', round(time.time()-t0), 's ---')
    for line in log.splitlines():
        if any(k in line.lower() for k in ['buffer size', 'cuda error', 'model loaded', 'listening', 'kv buffer', 'override']):
            print(line)
finally:
    ssh.close()

# 显存
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username='<LAPTOP_USER>', password='<REDACTED>', timeout=15, look_for_keys=False, allow_agent=False)
try:
    stdin, stdout, stderr = ssh.exec_command('cmd /c nvidia-smi --query-gpu=memory.used --format=csv', timeout=30)
    print('GPU:', stdout.read().decode('utf-8', errors='replace').strip())
finally:
    ssh.close()

# 测速
url = f'http://{HOST}:{PORT}/v1/chat/completions'
body = json.dumps({"model": "D:\\models\\ornith-1.0-35b-Q4_K_M.gguf",
                   "messages": [{"role": "user", "content": "Write a Python function is_prime(n). Code only."}],
                   "max_tokens": 250, "temperature": 0.6}).encode()
req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req, timeout=300) as resp:
        json.load(resp)
except Exception as e:
    print('REQ ERR:', repr(e)[:150])
time.sleep(2)
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username='<LAPTOP_USER>', password='<REDACTED>', timeout=15, look_for_keys=False, allow_agent=False)
try:
    stdin, stdout, stderr = ssh.exec_command(
        'cmd /c powershell -NoProfile -Command "Select-String -Path D:\\llama_old\\server.log -Pattern \'eval time\' | Select-Object -Last 2 | ForEach-Object {$_.Line}"',
        timeout=30)
    print('--- TIMING ---')
    print(stdout.read().decode('utf-8', errors='replace'))
finally:
    ssh.close()
