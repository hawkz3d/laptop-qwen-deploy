# -*- coding: utf-8 -*-
"""等服务稳定后查：实际上下文 + 内存占用"""
import sys, time, json, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

HOST = '<LAPTOP_IP>'
PORT = 8080
time.sleep(10)

# /props
try:
    req = urllib.request.Request(f'http://{HOST}:{PORT}/props', headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.load(resp)
    print('n_ctx:', data.get('default_generation_settings', {}).get('n_ctx'))
    print('total_slots:', data.get('total_slots'))
except Exception as e:
    print('PROPS ERR:', repr(e)[:150])

# 内存
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username='<LAPTOP_USER>', password='<REDACTED>', timeout=15, look_for_keys=False, allow_agent=False)
try:
    stdin, stdout, stderr = ssh.exec_command(
        'powershell -NoProfile -Command "$os=Get-CimInstance Win32_OperatingSystem; Write-Output (\'Free: \'+[math]::Round($os.FreePhysicalMemory/1MB,1)+\'GB / \'+[math]::Round($os.TotalVisibleMemorySize/1MB,1)+\'GB\')"',
        timeout=30)
    print('MEM:', stdout.read().decode('utf-8', errors='replace').strip())
    stdin, stdout, stderr = ssh.exec_command(
        'tasklist /fi "imagename eq llama-server.exe"', timeout=30)
    print('--- PROC ---')
    print(stdout.read().decode('utf-8', errors='replace'))
    stdin, stdout, stderr = ssh.exec_command('cmd /c nvidia-smi --query-gpu=memory.used --format=csv', timeout=30)
    print('GPU:', stdout.read().decode('utf-8', errors='replace').strip())
finally:
    ssh.close()
