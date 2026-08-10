# -*- coding: utf-8 -*-
"""前台启动 llama-server（-ngl 999 -cmoe），抓取启动日志尾部看 offload/报错，超时后杀进程"""
import sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('<LAPTOP_IP>', username='<LAPTOP_USER>', password='<REDACTED>',
            timeout=15, look_for_keys=False, allow_agent=False)
try:
    cmd = ('D:\\llama\\llama-server.exe -m D:\\models\\ornith-1.0-35b-Q4_K_M.gguf '
           '-ngl 999 -cmoe --no-mmap --no-kv-offload -ctk q8_0 -ctv q8_0 '
           '-c 32768 --jinja --host 0.0.0.0 --port 8080 2>&1')
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=80)
    buf = b''
    deadline = time.time() + 75
    while time.time() < deadline:
        if stdout.channel.recv_ready():
            buf += stdout.channel.recv(65536)
        else:
            time.sleep(0.2)
        if b'model loaded' in buf or b'listening' in buf or b'error' in buf.lower() or b'CUDA' in buf and b'error' in buf.lower():
            # 给一点缓冲
            time.sleep(2)
            while stdout.channel.recv_ready():
                buf += stdout.channel.recv(65536)
            break
    text = buf.decode('utf-8', errors='replace')
    # 打印关键行
    for line in text.splitlines():
        if any(k in line.lower() for k in ['offload', 'cuda', 'gpu', 'buffer', 'mem', 'error', 'layer', 'kv', 'model', 'listen', 'slot', 'load']):
            print(line)
    print('--- total bytes:', len(buf))
    # 杀进程
    stdin2, stdout2, stderr2 = ssh.exec_command(
        'powershell -NoProfile -Command "Get-Process llama-server -ErrorAction SilentlyContinue | Stop-Process -Force"', timeout=20)
    stdout2.read()
finally:
    ssh.close()
