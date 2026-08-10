# -*- coding: utf-8 -*-
"""验证 CUDA 后端：llama-server/llama-bench --list-devices，及 device 相关参数"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('<LAPTOP_IP>', username='<LAPTOP_USER>', password='<REDACTED>',
            timeout=15, look_for_keys=False, allow_agent=False)
try:
    cmds = [
        'D:\\llama\\llama-server.exe --list-devices',
        'D:\\llama\\llama-bench.exe --list-devices',
        'D:\\llama\\llama-cli.exe --help | findstr /i "device cuda gpu"',
    ]
    for i, c in enumerate(cmds):
        print(f'===== CMD[{i}] =====')
        stdin, stdout, stderr = ssh.exec_command('cmd /c "' + c + '"', timeout=60)
        print('--- STDOUT ---')
        print(stdout.read().decode('utf-8', errors='replace'))
        print('--- STDERR ---')
        print(stderr.read().decode('utf-8', errors='replace')[:800])
finally:
    ssh.close()
