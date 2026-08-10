# -*- coding: utf-8 -*-
"""加载模型头确认 llama.cpp 识别架构（-c 512 最小上下文，16GB 内存可完成）"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('<LAPTOP_IP>', username='<LAPTOP_USER>', password='<REDACTED>',
            timeout=15, look_for_keys=False, allow_agent=False)
try:
    cmd = ('D:\\llama\\llama-cli.exe -m D:\\models\\ornith-1.0-35b-Q4_K_M.gguf '
           '-p "hi" -n 1 -c 512 --no-warmup')
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=90)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    text = err + '\n' + out
    lines = text.splitlines()
    for line in lines[:90]:
        print(line)
    if len(lines) > 90:
        print('... (truncated)', len(lines), 'total lines')
finally:
    ssh.close()
