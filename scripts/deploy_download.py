# -*- coding: utf-8 -*-
"""上传 download_ornith.bat 到 laptop 并用 wmic 启动独立后台下载（不依赖 SSH 会话）"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('<LAPTOP_IP>', username='<LAPTOP_USER>', password='<REDACTED>',
            timeout=15, look_for_keys=False, allow_agent=False)
try:
    sftp = ssh.open_sftp()
    sftp.put(r'<SCRIPT_DIR>\download_ornith.bat', 'D:/models/download_ornith.bat')
    sftp.close()
    print('BAT UPLOADED')

    stdin, stdout, stderr = ssh.exec_command(
        'wmic process call create "D:\\models\\download_ornith.bat"', timeout=30)
    out = stdout.read().decode('utf-8', errors='replace')
    print('WMIC OUT:', out)
    err = stderr.read().decode('utf-8', errors='replace')
    if err.strip():
        print('WMIC ERR:', err[:500])
finally:
    ssh.close()
