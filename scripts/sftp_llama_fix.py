# -*- coding: utf-8 -*-
"""诊断 D:\\llama 内容，改用 PowerShell Expand-Archive 解压并验证 llama-server"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

ZIP_NAME = 'llama-b10301-bin-win-cuda-12.4-x64.zip'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('<LAPTOP_IP>', username='<LAPTOP_USER>', password='<REDACTED>',
            timeout=15, look_for_keys=False, allow_agent=False)
try:
    print('=== DIR D:\\llama ===')
    stdin, stdout, stderr = ssh.exec_command('cmd /c dir D:\\llama', timeout=30)
    print(stdout.read().decode('utf-8', errors='replace'))

    print('=== EXPAND-ARCHIVE ===')
    cmd = ('powershell -NoProfile -Command "Expand-Archive -Path \'D:\\llama\\%s\' '
           '-DestinationPath \'D:\\llama\\llama-bins\' -Force"' % ZIP_NAME)
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=180)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    print('OUT:', out)
    if err.strip():
        print('[stderr] ' + err[:1500])

    print('=== AFTER dir D:\\llama\\llama-bins ===')
    stdin, stdout, stderr = ssh.exec_command('cmd /c dir /b D:\\llama\\llama-bins', timeout=30)
    print(stdout.read().decode('utf-8', errors='replace'))

    print('=== VERSION ===')
    stdin, stdout, stderr = ssh.exec_command('cmd /c D:\\llama\\llama-bins\\llama-server.exe --version', timeout=30)
    print('OUT:', stdout.read().decode('utf-8', errors='replace'))
    print('ERR:', stderr.read().decode('utf-8', errors='replace')[:1000])
finally:
    ssh.close()
