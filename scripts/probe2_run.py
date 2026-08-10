# -*- coding: utf-8 -*-
"""上传 probe2.ps1 并执行，读取第二轮侦查结果"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('<LAPTOP_IP>', username='<LAPTOP_USER>', password='<REDACTED>',
            timeout=15, look_for_keys=False, allow_agent=False)
try:
    sftp = ssh.open_sftp()
    sftp.put(r'<SCRIPT_DIR>\probe2.ps1', 'C:/probe2.ps1')
    sftp.close()
    stdin, stdout, stderr = ssh.exec_command(
        'powershell -NoProfile -ExecutionPolicy Bypass -File C:\\probe2.ps1', timeout=90)
    stdout.read()
    err = stderr.read().decode('utf-8', errors='replace')
    if err.strip():
        print('[stderr]', err[:500])
    stdin, stdout, stderr = ssh.exec_command('cmd /c type C:\\probe2.txt', timeout=30)
    print(stdout.read().decode('utf-8', errors='replace'))
finally:
    ssh.close()
