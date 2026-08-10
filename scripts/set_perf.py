# -*- coding: utf-8 -*-
"""切高性能电源计划 + 测速对比"""
import sys, time, json, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

HOST = '<LAPTOP_IP>'
PORT = 8080
HIGH_PERF = '8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username='<LAPTOP_USER>', password='<REDACTED>', timeout=15, look_for_keys=False, allow_agent=False)
try:
    stdin, stdout, stderr = ssh.exec_command(f'powercfg /setactive {HIGH_PERF}', timeout=30)
    print('SET:', stdout.read().decode('utf-8', errors='replace'))
    stdin, stdout, stderr = ssh.exec_command('powercfg /getactivescheme', timeout=30)
    print('ACTIVE:', stdout.read().decode('utf-8', errors='replace'))
finally:
    ssh.close()

# 测速（发请求 + 读 timing）
url = f'http://{HOST}:{PORT}/v1/chat/completions'
body = json.dumps({"model": "D:\\models\\ornith-1.0-35b-Q4_K_M.gguf",
                   "messages": [{"role": "user", "content": "Write a Python function for fibonacci. Code only."}],
                   "max_tokens": 250, "temperature": 0.6}).encode()
req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=300) as resp:
    json.load(resp)
time.sleep(2)
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username='<LAPTOP_USER>', password='<REDACTED>', timeout=15, look_for_keys=False, allow_agent=False)
try:
    stdin, stdout, stderr = ssh.exec_command(
        'cmd /c powershell -NoProfile -Command "Select-String -Path D:\\llama_old\\server.log -Pattern \'eval time\' | Select-Object -Last 2 | ForEach-Object {$_.Line}"',
        timeout=30)
    print('--- TIMING (high perf) ---')
    print(stdout.read().decode('utf-8', errors='replace'))
finally:
    ssh.close()
