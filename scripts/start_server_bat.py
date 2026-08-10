# -*- coding: utf-8 -*-
"""上传 server_start.bat 并 wmic 启动，轮询端口 8080，打印日志和进程状态"""
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
    sftp = ssh.open_sftp()
    sftp.put(r'<SCRIPT_DIR>\server_start.bat', 'D:/llama/server_start.bat')
    sftp.close()
    print('[bat uploaded]')

    stdin, stdout, stderr = ssh.exec_command(
        'powershell -NoProfile -Command "Get-Process llama-server -ErrorAction SilentlyContinue | Stop-Process -Force"', timeout=20)
    stdout.read()
    print('[cleaned old llama-server]')

    stdin, stdout, stderr = ssh.exec_command(
        'wmic process call create "D:\\llama\\server_start.bat"', timeout=30)
    print('WMIC:', stdout.read().decode('utf-8', errors='replace')[:300])

    print('Waiting for port 8080 ...')
    t0 = time.time()
    ok = False
    while time.time() - t0 < 480:
        s = socket.socket()
        s.settimeout(3)
        if s.connect_ex((HOST, PORT)) == 0:
            print('PORT OPEN after', round(time.time() - t0, 1), 's')
            ok = True
            s.close()
            break
        s.close()
        time.sleep(5)
    if not ok:
        print('TIMEOUT waiting port')

    stdin, stdout, stderr = ssh.exec_command(
        'cmd /c powershell -NoProfile -Command "Get-Content D:\\llama\\server.log -Tail 60"', timeout=30)
    print('--- LOG TAIL ---')
    print(stdout.read().decode('utf-8', errors='replace'))

    stdin, stdout, stderr = ssh.exec_command(
        'tasklist /fi "imagename eq llama-server.exe"', timeout=30)
    print('--- PROC ---')
    print(stdout.read().decode('utf-8', errors='replace'))
finally:
    ssh.close()
