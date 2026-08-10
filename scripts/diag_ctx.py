# -*- coding: utf-8 -*-
"""前台跑 b8600 -c 131072，抓崩溃原因"""
import sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('<LAPTOP_IP>', username='<LAPTOP_USER>', password='<REDACTED>',
            timeout=15, look_for_keys=False, allow_agent=False)
try:
    ssh.exec_command('powershell -NoProfile -Command "Get-Process llama-server -ErrorAction SilentlyContinue | Stop-Process -Force"', timeout=20)[1].read()
    print('[cleaned]')
    cmd = ('D:\\llama_old\\bin\\llama-server.exe -m D:\\models\\ornith-1.0-35b-Q4_K_M.gguf '
           '-ngl 999 -cmoe --no-mmap -c 131072 --jinja --port 8080 2>&1')
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=110)
    buf = b''
    t0 = time.time()
    while time.time() - t0 < 105:
        if stdout.channel.recv_ready():
            buf += stdout.channel.recv(65536)
        else:
            time.sleep(0.2)
        if b'model loaded' in buf or b'error' in buf.lower() or b'CUDA error' in buf or b'abort' in buf.lower():
            time.sleep(2)
            while stdout.channel.recv_ready():
                buf += stdout.channel.recv(65536)
            break
    text = buf.decode('utf-8', errors='replace')
    print(f'--- {len(buf)} bytes ---')
    for line in text.splitlines():
        if any(k in line.lower() for k in ['error', 'cuda', 'buffer', 'kv', 'context', 'slot', 'abort', 'oom', 'failed', 'memory', 'ctx']):
            print(line)
    ssh.exec_command('powershell -NoProfile -Command "Get-Process llama-server -ErrorAction SilentlyContinue | Stop-Process -Force"', timeout=20)[1].read()
finally:
    ssh.close()
