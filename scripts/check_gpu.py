# -*- coding: utf-8 -*-
"""查 laptop GPU 显存占用（确认 -ngl 35 offload 是否生效）+ llama-server 状态"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('<LAPTOP_IP>', username='<LAPTOP_USER>', password='<REDACTED>',
            timeout=15, look_for_keys=False, allow_agent=False)
try:
    stdin, stdout, stderr = ssh.exec_command('cmd /c nvidia-smi', timeout=30)
    print(stdout.read().decode('utf-8', errors='replace'))
    stdin, stdout, stderr = ssh.exec_command(
        'tasklist /fi "imagename eq llama-server.exe"', timeout=30)
    print('--- PROC ---')
    print(stdout.read().decode('utf-8', errors='replace'))
finally:
    ssh.close()
