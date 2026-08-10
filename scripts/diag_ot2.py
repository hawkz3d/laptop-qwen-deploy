# -*- coding: utf-8 -*-
"""后台启动 -ot 配置，等 60s 读日志 + 查进程，判断是崩溃还是加载中"""
import sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('<LAPTOP_IP>', username='<LAPTOP_USER>', password='<REDACTED>',
            timeout=15, look_for_keys=False, allow_agent=False)
try:
    ssh.exec_command('cmd /c del C:\\ot_test.log 2>nul', timeout=15)[1].read()
    cmd = ('cmd /c D:\\llama\\llama-server.exe -m D:\\models\\ornith-1.0-35b-Q4_K_M.gguf '
           '-ngl 999 -ot "exps=CPU" --no-mmap --no-kv-offload -ctk q8_0 -ctv q8_0 '
           '-c 32768 --jinja --host 0.0.0.0 --port 8080 > C:\\ot_test.log 2>&1')
    stdin, stdout, stderr = ssh.exec_command('wmic process call create "' + cmd + '"', timeout=30)
    print('WMIC:', stdout.read().decode('utf-8', errors='replace')[:200])
    ssh.close()
finally:
    pass

print('waiting 60s...')
time.sleep(60)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('<LAPTOP_IP>', username='<LAPTOP_USER>', password='<REDACTED>',
            timeout=15, look_for_keys=False, allow_agent=False)
try:
    stdin, stdout, stderr = ssh.exec_command('cmd /c type C:\\ot_test.log', timeout=30)
    print('--- OT LOG ---')
    print(stdout.read().decode('utf-8', errors='replace'))
    stdin, stdout, stderr = ssh.exec_command(
        'tasklist /fi "imagename eq llama-server.exe"', timeout=30)
    print('--- PROC ---')
    print(stdout.read().decode('utf-8', errors='replace'))
    stdin, stdout, stderr = ssh.exec_command('cmd /c nvidia-smi --query-gpu=memory.used --format=csv', timeout=30)
    print('--- GPU ---')
    print(stdout.read().decode('utf-8', errors='replace').strip())
finally:
    ssh.close()
