# -*- coding: utf-8 -*-
"""决定性测试：-ngl 1 -lv 6 启动，抓加载日志看是否有 offload 层数信息"""
import sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('<LAPTOP_IP>', username='<LAPTOP_USER>', password='<REDACTED>',
            timeout=15, look_for_keys=False, allow_agent=False)
try:
    # 杀现有服务
    ssh.exec_command(
        'powershell -NoProfile -Command "Get-Process llama-server -ErrorAction SilentlyContinue | Stop-Process -Force"', timeout=20)[1].read()
    print('[cleaned]')

    cmd = ('D:\\llama\\llama-server.exe -m D:\\models\\ornith-1.0-35b-Q4_K_M.gguf '
           '-ngl 1 -lv 6 --no-mmap --no-kv-offload -ctk q8_0 -ctv q8_0 '
           '-c 512 --jinja --host 0.0.0.0 --port 8080 2>&1')
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=100)
    buf = b''
    t0 = time.time()
    while time.time() - t0 < 95:
        if stdout.channel.recv_ready():
            buf += stdout.channel.recv(65536)
        else:
            time.sleep(0.2)
        if b'listening' in buf or b'error' in buf.lower():
            time.sleep(2)
            while stdout.channel.recv_ready():
                buf += stdout.channel.recv(65536)
            break
    text = buf.decode('utf-8', errors='replace')
    print(f'--- {len(buf)} bytes ---')
    # 打印所有含 offload/gpu/cuda/tensor/layer 的行
    for line in text.splitlines():
        low = line.lower()
        if any(k in low for k in ['offload', 'cuda', 'gpu', 'tensor', 'layer', 'buffer', 'device', 'ngl', 'ssm', 'fused', 'kv']):
            print(line)
    # 杀
    ssh.exec_command(
        'powershell -NoProfile -Command "Get-Process llama-server -ErrorAction SilentlyContinue | Stop-Process -Force"', timeout=20)[1].read()
finally:
    ssh.close()
