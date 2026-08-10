# -*- coding: utf-8 -*-
"""读 start_ornith.bat + 测试 b8600 -c 上限"""
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
finally:
    ssh.close()
