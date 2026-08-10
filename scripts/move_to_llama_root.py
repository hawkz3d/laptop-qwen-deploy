# -*- coding: utf-8 -*-
"""把 D:\\llama\\llama-bins 下的文件移到 D:\\llama 根目录，删空目录和 zip，验证 llama-server"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('<LAPTOP_IP>', username='<LAPTOP_USER>', password='<REDACTED>',
            timeout=15, look_for_keys=False, allow_agent=False)
try:
    cmds = [
        'move /y D:\\llama\\llama-bins\\* D:\\llama\\',
        'rmdir D:\\llama\\llama-bins',
        'del /q D:\\llama\\llama-b10301-bin-win-cuda-12.4-x64.zip',
        'dir /b D:\\llama',
        'D:\\llama\\llama-server.exe --version',
    ]
    combined = ' && '.join(cmds)
    stdin, stdout, stderr = ssh.exec_command('cmd /c "' + combined + '"', timeout=60)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    print('--- STDOUT ---')
    print(out)
    print('--- STDERR ---')
    print(err[:1500])
finally:
    ssh.close()
