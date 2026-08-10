# -*- coding: utf-8 -*-
"""收尾：建 D:\\models 目录，验证 CUDA 设备可见性（--list-devices），确认 D:\\llama 状态"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('<LAPTOP_IP>', username='<LAPTOP_USER>', password='<REDACTED>',
            timeout=15, look_for_keys=False, allow_agent=False)
try:
    cmds = [
        'if not exist D:\\models mkdir D:\\models',
        'D:\\llama\\llama-cli.exe --list-devices',
        'dir D:\\llama\\llama-server.exe D:\\models',
    ]
    combined = ' && '.join(cmds)
    stdin, stdout, stderr = ssh.exec_command('cmd /c "' + combined + '"', timeout=60)
    print('--- STDOUT ---')
    print(stdout.read().decode('utf-8', errors='replace'))
    print('--- STDERR ---')
    print(stderr.read().decode('utf-8', errors='replace')[:1500])
finally:
    ssh.close()
