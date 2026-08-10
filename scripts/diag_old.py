# -*- coding: utf-8 -*-
"""诊断 b8600 CUDA：对比 D:\\llama dll，补齐后重测 --list-devices"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('<LAPTOP_IP>', username='<LAPTOP_USER>', password='<REDACTED>',
            timeout=15, look_for_keys=False, allow_agent=False)
try:
    print('=== D:\\llama dlls ===')
    stdin, stdout, stderr = ssh.exec_command('cmd /c dir /b D:\\llama\\*.dll', timeout=30)
    llama_dlls = stdout.read().decode('utf-8', errors='replace').split()
    print(llama_dlls)
    print('=== D:\\llama_old\\bin dlls ===')
    stdin, stdout, stderr = ssh.exec_command('cmd /c dir /b D:\\llama_old\\bin\\*.dll', timeout=30)
    old_dlls = stdout.read().decode('utf-8', errors='replace').split()
    print(old_dlls)
    # 复制缺失的
    missing = [d for d in llama_dlls if d not in old_dlls]
    print('missing to copy:', missing)
    for d in missing:
        ssh.exec_command(f'cmd /c copy /y D:\\llama\\{d} D:\\llama_old\\bin\\', timeout=15)[1].read()
    print('copied all')
    # 重测
    stdin, stdout, stderr = ssh.exec_command('cmd /c D:\\llama_old\\bin\\llama-server.exe --list-devices', timeout=30)
    print('--- DEVICES ---')
    print(stdout.read().decode('utf-8', errors='replace'))
    print(stderr.read().decode('utf-8', errors='replace')[:500])
finally:
    ssh.close()
