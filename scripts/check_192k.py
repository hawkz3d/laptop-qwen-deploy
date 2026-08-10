# -*- coding: utf-8 -*-
"""诊断 192K 配置：/props + server.log + 进程"""
import sys, time, json, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

HOST = '<LAPTOP_IP>'
PORT = 8080
time.sleep(5)

try:
    req = urllib.request.Request(f'http://{HOST}:{PORT}/props', headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.load(resp)
    print('n_ctx:', data.get('default_generation_settings', {}).get('n_ctx'))
except Exception as e:
    print('PROPS ERR:', repr(e)[:120])

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username='<LAPTOP_USER>', password='<REDACTED>', timeout=15, look_for_keys=False, allow_agent=False)
try:
    stdin, stdout, stderr = ssh.exec_command(
        'cmd /c powershell -NoProfile -Command "Get-Content D:\\llama_old\\server.log -Tail 15"', timeout=30)
    print('--- LOG TAIL ---')
    print(stdout.read().decode('utf-8', errors='replace'))
    stdin, stdout, stderr = ssh.exec_command('tasklist /fi "imagename eq llama-server.exe"', timeout=30)
    print('--- PROC ---')
    print(stdout.read().decode('utf-8', errors='replace'))
    stdin, stdout, stderr = ssh.exec_command('cmd /c nvidia-smi --query-gpu=memory.used --format=csv', timeout=30)
    print('GPU:', stdout.read().decode('utf-8', errors='replace').strip())
finally:
    ssh.close()
