# -*- coding: utf-8 -*-
"""诊断 laptop llama-server 进程/端口/日志状态"""
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
        'dir D:\\llama\\server.log',
        'tasklist /fi "imagename eq cmd.exe"',
    ]
    for i, c in enumerate(cmds):
        print(f'===== CMD[{i}] {c[:50]} =====')
        stdin, stdout, stderr = ssh.exec_command('cmd /c "' + c + '"', timeout=30)
        print(stdout.read().decode('utf-8', errors='replace'))
finally:
    ssh.close()
