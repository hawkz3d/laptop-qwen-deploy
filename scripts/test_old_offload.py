# -*- coding: utf-8 -*-
"""用 b8600 加载 Ornith，测试 GPU offload：显存/日志/速度"""
import sys, time, json, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

HOST = '<LAPTOP_IP>'
PORT = 8080

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username='<LAPTOP_USER>', password='<REDACTED>',
            timeout=15, look_for_keys=False, allow_agent=False)
try:
    # 杀旧服务
    ssh.exec_command(
        'powershell -NoProfile -Command "Get-Process llama-server -ErrorAction SilentlyContinue | Stop-Process -Force"', timeout=20)[1].read()
    print('[cleaned old server]')
    # 启动 b8600 服务（后台 bat 方式）
    bat = ('@echo off\r\ncd /d D:\\llama_old\\bin\r\n'
           'llama-server.exe -m D:\\models\\ornith-1.0-35b-Q4_K_M.gguf -ngl 999 -cmoe --no-mmap '
           '-c 32768 --jinja --host 0.0.0.0 --port 8080 > D:\\llama_old\\server.log 2>&1\r\n')
    sftp = ssh.open_sftp()
    with sftp.open('D:/llama_old/start.bat', 'w') as f:
        f.write(bat)
    sftp.close()
    stdin, stdout, stderr = ssh.exec_command(
        'wmic process call create "D:\\llama_old\\start.bat"', timeout=30)
    print('WMIC:', stdout.read().decode('utf-8', errors='replace')[:200])

    def get_log():
        stdin, stdout, stderr = ssh.exec_command('cmd /c type D:\\llama_old\\server.log', timeout=20)
        return stdout.read().decode('utf-8', errors='replace')

    # 等 model loaded
    t0 = time.time()
    log = ''
    while time.time() - t0 < 300:
        log = get_log()
        if 'model loaded' in log or 'error' in log.lower():
            break
        time.sleep(5)
    print('--- LOG (offload lines) ---')
    for line in log.splitlines():
        if any(k in line.lower() for k in ['offload', 'cuda', 'gpu', 'layer', 'error', 'model loaded', 'listening', 'buffer', 'kv']):
            print(line)
finally:
    ssh.close()

# 显存 + 速度
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username='<LAPTOP_USER>', password='<REDACTED>', timeout=15, look_for_keys=False, allow_agent=False)
try:
    stdin, stdout, stderr = ssh.exec_command('cmd /c nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv', timeout=30)
    print('GPU:', stdout.read().decode('utf-8', errors='replace').strip())
finally:
    ssh.close()

print('=== SPEED TEST ===')
url = f'http://{HOST}:{PORT}/v1/chat/completions'
body = json.dumps({"model": "D:\\models\\ornith-1.0-35b-Q4_K_M.gguf",
                   "messages": [{"role": "user", "content": "Write a Python function is_prime(n). Code only."}],
                   "max_tokens": 200, "temperature": 0.6}).encode()
req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
try:
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.load(resp)
    elapsed = time.time() - t0
    ct = data.get('usage', {}).get('completion_tokens', 0)
    content = data['choices'][0]['message'].get('content', '')
    print(f'elapsed={elapsed:.1f}s completion_tokens={ct} speed={ct/elapsed:.2f} tok/s')
    print('--- ANSWER ---')
    print(content[:400] if content else '(empty)')
except Exception as e:
    print('SPEED ERR:', repr(e)[:200])
