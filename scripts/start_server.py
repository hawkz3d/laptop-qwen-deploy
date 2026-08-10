# -*- coding: utf-8 -*-
"""确认内存 32GB -> 启动 llama-server（五参数，日志重定向 server.log）-> 轮询端口 8080 -> 打印启动日志"""
import sys, time, socket
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

HOST = '<LAPTOP_IP>'
PORT = 8080

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username='<LAPTOP_USER>', password='<REDACTED>',
            timeout=15, look_for_keys=False, allow_agent=False)
try:
    # 1) 内存确认
    stdin, stdout, stderr = ssh.exec_command(
        'wmic ComputerSystem get TotalPhysicalMemory /value', timeout=30)
    total = None
    for line in stdout.read().decode('utf-8', errors='replace').splitlines():
        if 'TotalPhysicalMemory' in line and '=' in line:
            try:
                total = int(line.split('=')[1].strip())
            except Exception:
                pass
    print('TOTAL MEMORY:', round(total / 1024**3, 1), 'GB' if total else '?')

    # 2) 模型文件确认
    stdin, stdout, stderr = ssh.exec_command(
        'powershell -NoProfile -Command "(Get-Item \'D:\\models\\ornith-1.0-35b-Q4_K_M.gguf\').Length"', timeout=30)
    mlen = stdout.read().decode('utf-8', errors='replace').strip()
    print('MODEL bytes:', mlen)

    # 3) 清理残留 llama-server，启动新版（-cmoe 替代 --no-moe-offload；-ctk/-ctv 替代 turbo-key）
    stdin, stdout, stderr = ssh.exec_command(
        'powershell -NoProfile -Command "Get-Process llama-server -ErrorAction SilentlyContinue | Stop-Process -Force"', timeout=20)
    stdout.read()
    server_cmd = ('cmd /c D:\\llama\\llama-server.exe -m D:\\models\\ornith-1.0-35b-Q4_K_M.gguf '
                  '-cmoe --no-mmap -ngl 35 --no-kv-offload '
                  '-ctk q8_0 -ctv q8_0 -c 32768 --jinja '
                  '--host 0.0.0.0 --port 8080 > D:\\llama\\server.log 2>&1')
    stdin, stdout, stderr = ssh.exec_command(
        'wmic process call create "' + server_cmd + '"', timeout=30)
    print('WMIC:', stdout.read().decode('utf-8', errors='replace')[:300])

    # 4) 轮询端口 8080
    print('Waiting for port 8080 ...')
    t0 = time.time()
    deadline = t0 + 420
    ok = False
    while time.time() < deadline:
        s = socket.socket()
        s.settimeout(3)
        r = s.connect_ex((HOST, PORT))
        s.close()
        if r == 0:
            print('PORT OPEN after', round(time.time() - t0, 1), 's')
            ok = True
            break
        time.sleep(5)
    if not ok:
        print('TIMEOUT waiting port (420s)')

    # 5) 打印 server.log 尾部（架构识别/offload/加载信息）
    stdin, stdout, stderr = ssh.exec_command(
        'cmd /c powershell -NoProfile -Command "Get-Content D:\\llama\\server.log -Tail 50"', timeout=30)
    print('--- SERVER LOG TAIL ---')
    print(stdout.read().decode('utf-8', errors='replace'))
finally:
    ssh.close()
