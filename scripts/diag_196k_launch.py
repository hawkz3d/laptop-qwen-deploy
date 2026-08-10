# -*- coding: utf-8 -*-
"""前台启动 196608 抓真实报错：杀干净 -> 等句柄释放 -> 前台跑 llama-server -> 读输出"""
import sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('<LAPTOP_IP>', username='<LAPTOP_USER>', password='<REDACTED>',
            timeout=15, look_for_keys=False, allow_agent=False)
try:
    # 杀干净 + 等句柄释放
    ssh.exec_command('powershell -NoProfile -Command "Get-Process llama-server -ErrorAction SilentlyContinue | Stop-Process -Force"', timeout=20)[1].read()
    time.sleep(4)
    # 删日志（验证是否成功）
    i, o, e = ssh.exec_command('cmd /c del D:\\llama_old\\server.log 2>&1', timeout=15)
    del_out = o.read().decode('gbk', errors='replace')
    print('DEL:', del_out.strip() or '(ok)')
    i, o, e = ssh.exec_command('cmd /c dir D:\\llama_old\\server.log 2>&1', timeout=15)
    print('LOG EXISTS:', o.read().decode('gbk', errors='replace').strip().splitlines()[-1] if o.read else '?')

    # 前台启动 196608
    cmd = ('D:\\llama_old\\bin\\llama-server.exe -m D:\\models\\ornith-1.0-35b-Q4_K_M.gguf '
           '-ngl 999 -cmoe --no-mmap -c 196608 -kvo -ctk q8_0 -ctv q8_0 -fit off --jinja --port 8080 2>&1')
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    buf = b''
    t0 = time.time()
    while time.time() - t0 < 240:
        if stdout.channel.recv_ready():
            buf += stdout.channel.recv(65536)
        else:
            time.sleep(0.3)
        low = buf.lower()
        if b'model loaded' in low or b'cuda error' in low or b'error' in low or b'failed' in low:
            time.sleep(3)
            while stdout.channel.recv_ready():
                buf += stdout.channel.recv(65536)
            break
    text = buf.decode('utf-8', errors='replace')
    print(f'--- {len(buf)} bytes, {time.time()-t0:.0f}s ---')
    for line in text.splitlines():
        if any(k in line.lower() for k in ['n_ctx', 'kv buffer', 'offloaded', 'model loaded', 'listening', 'cuda error', 'error', 'failed', 'buffer size', 'abort']):
            print(line)
    # 若成功则保持运行
    if b'model loaded' in buf.lower():
        print('=== SERVICE KEPT RUNNING (196608) ===')
        ssh.exec_command('powershell -NoProfile -Command "Start-Sleep -Seconds 2; $p=Get-Process llama-server; $p.PriorityClass=\'High\'"', timeout=20)[1].read()
        print('priority set to High')
    else:
        print('=== SERVICE FAILED / NOT READY ===')
finally:
    ssh.close()
