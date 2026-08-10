# -*- coding: utf-8 -*-
"""上传 disable_services.ps1 并执行（安全禁用：Office更新服务 + Intel显卡中心服务 + 搜狗云/升级工具），读日志"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('<LAPTOP_IP>', username='<LAPTOP_USER>', password='<REDACTED>',
            timeout=15, look_for_keys=False, allow_agent=False)
try:
    sftp = ssh.open_sftp()
    sftp.put(r'<SCRIPT_DIR>\disable_services.ps1', 'C:/disable_services.ps1')
    sftp.close()
    stdin, stdout, stderr = ssh.exec_command(
        'powershell -NoProfile -ExecutionPolicy Bypass -File C:\\disable_services.ps1', timeout=120)
    stdout.read()
    err = stderr.read().decode('utf-8', errors='replace')
    if err.strip():
        print('[stderr]', err[:800])
    stdin, stdout, stderr = ssh.exec_command('cmd /c type C:\\disable_log.txt', timeout=30)
    print(stdout.read().decode('utf-8', errors='replace'))
finally:
    ssh.close()
