# -*- coding: utf-8 -*-
"""查 bat 内容 + server.log 崩溃原因"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('<LAPTOP_IP>', username='<LAPTOP_USER>', password='<REDACTED>',
            timeout=15, look_for_keys=False, allow_agent=False)
try:
    stdin, stdout, stderr = ssh.exec_command('cmd /c type D:\\llama_old\\start_ornith.bat', timeout=30)
    print('=== BAT ===')
    print(stdout.read().decode('utf-8', errors='replace'))
    stdin, stdout, stderr = ssh.exec_command(
        'cmd /c powershell -NoProfile -Command "Get-Content D:\\llama_old\\server.log -Tail 30"', timeout=30)
    print('=== LOG TAIL ===')
    print(stdout.read().decode('utf-8', errors='replace'))
finally:
    ssh.close()
