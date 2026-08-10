# -*- coding: utf-8 -*-
"""确认服务健康 + 内存/显存/进程状态"""
import sys, json, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

HOST = '<LAPTOP_IP>'
PORT = 8080

# 健康检查
try:
    req = urllib.request.Request(f'http://{HOST}:{PORT}/health', headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as resp:
        print('HEALTH:', resp.status, resp.read().decode())
except Exception as e:
    print('HEALTH ERR:', repr(e)[:200])

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username='<LAPTOP_USER>', password='<REDACTED>', timeout=15, look_for_keys=False, allow_agent=False)
try:
    stdin, stdout, stderr = ssh.exec_command('cmd /c nvidia-smi --query-gpu=memory.used --format=csv', timeout=30)
    print('GPU MEM:', stdout.read().decode('utf-8', errors='replace').strip())
    stdin, stdout, stderr = ssh.exec_command(
        'tasklist /fi "imagename eq llama-server.exe"', timeout=30)
    print('--- PROC ---')
    print(stdout.read().decode('utf-8', errors='replace'))
finally:
    ssh.close()
