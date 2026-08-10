# -*- coding: utf-8 -*-
"""请求后确认：空闲显存回落 + server.log 无 CUDA error"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('<LAPTOP_IP>', username='<LAPTOP_USER>', password='<REDACTED>',
            timeout=15, look_for_keys=False, allow_agent=False)
try:
    stdin, stdout, stderr = ssh.exec_command('cmd /c nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv', timeout=30)
    print('GPU NOW:', stdout.read().decode('utf-8', errors='replace').strip())
    stdin, stdout, stderr = ssh.exec_command(
        'cmd /c powershell -NoProfile -Command "Select-String -Path D:\\llama_old\\server.log -Pattern \'CUDA error|error:|OOM|out of memory\' | ForEach-Object {$_.Line}"',
        timeout=30)
    errs = stdout.read().decode('utf-8', errors='replace').strip()
    print('CUDA ERRORS:', errs if errs else 'NONE')
    stdin, stdout, stderr = ssh.exec_command(
        'cmd /c powershell -NoProfile -Command "Select-String -Path D:\\llama_old\\server.log -Pattern \'eval time\' | Select-Object -Last 2 | ForEach-Object {$_.Line}"',
        timeout=30)
    print('--- LAST TIMING ---')
    print(stdout.read().decode('utf-8', errors='replace'))
finally:
    ssh.close()
