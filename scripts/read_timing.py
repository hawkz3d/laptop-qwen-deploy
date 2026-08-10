# -*- coding: utf-8 -*-
"""读 b8600 server.log 的 print_timing（准确 tg），确认稳态生成速度"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('<LAPTOP_IP>', username='<LAPTOP_USER>', password='<REDACTED>',
            timeout=15, look_for_keys=False, allow_agent=False)
try:
    stdin, stdout, stderr = ssh.exec_command(
        'cmd /c powershell -NoProfile -Command "Select-String -Path D:\\llama_old\\server.log -Pattern \'print_timing|eval time|model loaded|listening\' | Select-Object -Last 15 | ForEach-Object {$_.Line}"',
        timeout=30)
    print(stdout.read().decode('utf-8', errors='replace'))
finally:
    ssh.close()
