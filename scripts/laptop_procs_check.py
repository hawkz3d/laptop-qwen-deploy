# -*- coding: utf-8 -*-
"""只读检查 laptop 进程（按内存占用降序 Top 30）+ 内存总量/空闲。不做任何禁用。"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('<LAPTOP_IP>', username='<LAPTOP_USER>', password='<REDACTED>',
            timeout=15, look_for_keys=False, allow_agent=False)
try:
    sftp = ssh.open_sftp()
    sftp.put(r'<SCRIPT_DIR>\procs.ps1', 'C:/procs.ps1')
    sftp.close()
    print('[uploaded procs.ps1]')

    stdin, stdout, stderr = ssh.exec_command(
        'powershell -NoProfile -ExecutionPolicy Bypass -File C:\\procs.ps1', timeout=90)
    stdout.read()
    err = stderr.read().decode('utf-8', errors='replace')
    if err.strip():
        print('[stderr]', err[:500])

    stdin, stdout, stderr = ssh.exec_command('cmd /c type C:\\procs.txt', timeout=30)
    print(stdout.read().decode('utf-8', errors='replace'))
finally:
    ssh.close()
