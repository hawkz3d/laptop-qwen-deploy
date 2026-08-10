# -*- coding: utf-8 -*-
"""上传 retry_kill.ps1 执行：强制杀 SGTool/SogouCloud，测 Available 内存"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('<LAPTOP_IP>', username='<LAPTOP_USER>', password='<REDACTED>',
            timeout=15, look_for_keys=False, allow_agent=False)
try:
    sftp = ssh.open_sftp()
    sftp.put(r'<SCRIPT_DIR>\retry_kill.ps1', 'C:/retry_kill.ps1')
    sftp.close()
    stdin, stdout, stderr = ssh.exec_command(
        'powershell -NoProfile -ExecutionPolicy Bypass -File C:\\retry_kill.ps1', timeout=90)
    stdout.read()
    err = stderr.read().decode('utf-8', errors='replace')
    if err.strip():
        print('[stderr]', err[:500])
    stdin, stdout, stderr = ssh.exec_command('cmd /c type C:\\kill_log.txt', timeout=30)
    print(stdout.read().decode('utf-8', errors='replace'))
finally:
    ssh.close()
