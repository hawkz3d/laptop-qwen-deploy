# -*- coding: utf-8 -*-
"""测当前服务速度（发请求 + 读 timing + 显存/内存）"""
import sys, time, json, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

HOST = '<LAPTOP_IP>'
PORT = 8080

url = f'http://{HOST}:{PORT}/v1/chat/completions'
body = json.dumps({"model": "D:\\models\\ornith-1.0-35b-Q4_K_M.gguf",
                   "messages": [{"role": "user", "content": "Write a Python function to sort a list with quick sort. Code only."}],
                   "max_tokens": 250, "temperature": 0.6}).encode()
req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req, timeout=300) as resp:
        json.load(resp)
except Exception as e:
    print('REQ ERR:', repr(e)[:150])

time.sleep(2)
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username='<LAPTOP_USER>', password='<REDACTED>', timeout=15, look_for_keys=False, allow_agent=False)
try:
    stdin, stdout, stderr = ssh.exec_command(
        'cmd /c powershell -NoProfile -Command "Select-String -Path D:\\llama_old\\server.log -Pattern \'eval time\' | Select-Object -Last 2 | ForEach-Object {$_.Line}"',
        timeout=30)
    print('--- TIMING ---')
    print(stdout.read().decode('utf-8', errors='replace'))
    stdin, stdout, stderr = ssh.exec_command('cmd /c nvidia-smi --query-gpu=memory.used --format=csv', timeout=30)
    print('GPU:', stdout.read().decode('utf-8', errors='replace').strip())
    stdin, stdout, stderr = ssh.exec_command(
        'powershell -NoProfile -Command "$os=Get-CimInstance Win32_OperatingSystem; Write-Output (\'Free: \'+[math]::Round($os.FreePhysicalMemory/1MB,1)+\'GB\')"',
        timeout=30)
    print('MEM:', stdout.read().decode('utf-8', errors='replace').strip())
finally:
    ssh.close()
