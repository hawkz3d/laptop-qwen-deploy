# -*- coding: utf-8 -*-
"""查 b8600 llama-server 的 moe/cpu/ngl 参数"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('<LAPTOP_IP>', username='<LAPTOP_USER>', password='<REDACTED>',
            timeout=15, look_for_keys=False, allow_agent=False)
try:
    stdin, stdout, stderr = ssh.exec_command(
        'cmd /c D:\\llama_old\\bin\\llama-server.exe --help 2>&1 | findstr /i "moe cpu gpu-layers ngl"', timeout=30)
    print(stdout.read().decode('utf-8', errors='replace'))
finally:
    ssh.close()
