# -*- coding: utf-8 -*-
"""诊断当前 llama-server 状态：进程/端口/server.log 尾部"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('<LAPTOP_IP>', username='<LAPTOP_USER>', password='<REDACTED>',
            timeout=15, look_for_keys=False, allow_agent=False)
try:
    cmds = [
        'tasklist /fi "imagename eq llama-server.exe"',
        'netstat -ano | findstr :8080',
        'cmd /c powershell -NoProfile -Command "Get-Content D:\\llama\\server.log -Tail 50"',
        'dir D:\\llama\\server.log',
    ]
    for i, c in enumerate(cmds):
        print(f'===== CMD[{i}] =====')
        stdin, stdout, stderr = ssh.exec_command('cmd /c "' + c + '"', timeout=30)
        print(stdout.read().decode('utf-8', errors='replace'))
finally:
    ssh.close()
