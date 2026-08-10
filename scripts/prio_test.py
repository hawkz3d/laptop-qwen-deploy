# -*- coding: utf-8 -*-
"""进程优先级 High + CPU 频率检查 + 测速对比"""
import sys, time, json, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

HOST = '<LAPTOP_IP>'
PORT = 8080

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username='<LAPTOP_USER>', password='<REDACTED>', timeout=15, look_for_keys=False, allow_agent=False)
try:
    def run(c):
        i, o, e = ssh.exec_command(c, timeout=30)
        return o.read().decode('utf-8', errors='replace')

    # 1) 当前优先级 + CPU 频率
    print('=== BEFORE ===')
    print('PRIORITY:', run('powershell -NoProfile -Command "(Get-Process llama-server -ErrorAction SilentlyContinue).PriorityClass"').strip())
    print('CPU:', run('wmic cpu get LoadPercentage,CurrentClockSpeed,MaxClockSpeed /value').strip())
    print('--- baseline eval (last 2) ---')
    print(run('cmd /c powershell -NoProfile -Command "Select-String -Path D:\\llama_old\\server.log -Pattern \'eval time\' | Select-Object -Last 2 | ForEach-Object {$_.Line}"'))

    # 2) 设 High
    out = run('powershell -NoProfile -Command "(Get-Process llama-server -ErrorAction SilentlyContinue).PriorityClass=\'High\'"')
    time.sleep(1)
    print('=== AFTER SET ===')
    print('PRIORITY:', run('powershell -NoProfile -Command "(Get-Process llama-server -ErrorAction SilentlyContinue).PriorityClass"').strip())
finally:
    ssh.close()

# 3) 测速
def bench(label):
    url = f'http://{HOST}:{PORT}/v1/chat/completions'
    body = json.dumps({"model": "D:\\models\\ornith-1.0-35b-Q4_K_M.gguf",
                       "messages": [{"role": "user", "content": "Write a Python function for quicksort. Code only."}],
                       "max_tokens": 250, "temperature": 0.6}).encode()
    req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=300) as resp:
        json.load(resp)
    time.sleep(2)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username='<LAPTOP_USER>', password='<REDACTED>', timeout=15, look_for_keys=False, allow_agent=False)
    try:
        i, o, e = ssh.exec_command(
            'cmd /c powershell -NoProfile -Command "Select-String -Path D:\\llama_old\\server.log -Pattern \'eval time\' | Select-Object -Last 1 | ForEach-Object {$_.Line}"',
            timeout=30)
        print(f'--- {label} (latest eval) ---')
        print(o.read().decode('utf-8', errors='replace'))
    finally:
        ssh.close()

bench('HIGH PRIORITY')
