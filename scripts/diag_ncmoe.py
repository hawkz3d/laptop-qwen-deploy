# -*- coding: utf-8 -*-
"""前台跑 b8600 -ncmoe，抓取报错（参数错误/OOM）"""
import sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

NCMOE = sys.argv[1] if len(sys.argv) > 1 else '33'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('<LAPTOP_IP>', username='<LAPTOP_USER>', password='<REDACTED>',
            timeout=15, look_for_keys=False, allow_agent=False)
try:
    ssh.exec_command('powershell -NoProfile -Command "Get-Process llama-server -ErrorAction SilentlyContinue | Stop-Process -Force"', timeout=20)[1].read()
    print('[cleaned]')
    cmd = (f'D:\\llama_old\\bin\\llama-server.exe -m D:\\models\\ornith-1.0-35b-Q4_K_M.gguf '
           f'-ngl 999 -ncmoe {NCMOE} --no-mmap -c 512 --jinja --port 8080 2>&1')
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=90)
    buf = b''
    t0 = time.time()
    while time.time() - t0 < 85:
        if stdout.channel.recv_ready():
            buf += stdout.channel.recv(65536)
        else:
            time.sleep(0.2)
        if b'model loaded' in buf or b'error' in buf.lower() or b'CUDA error' in buf:
            time.sleep(2)
            while stdout.channel.recv_ready():
                buf += stdout.channel.recv(65536)
            break
    text = buf.decode('utf-8', errors='replace')
    print(f'--- {len(buf)} bytes ---')
    for line in text.splitlines():
        if any(k in line.lower() for k in ['error', 'cuda', 'buffer', 'offload', 'ncpu', 'n_cpu', 'oom', 'failed', 'unknown']):
            print(line)
    ssh.exec_command('powershell -NoProfile -Command "Get-Process llama-server -ErrorAction SilentlyContinue | Stop-Process -Force"', timeout=20)[1].read()
finally:
    ssh.close()
