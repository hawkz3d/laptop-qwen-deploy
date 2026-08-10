# -*- coding: utf-8 -*-
"""快速状态检查：/props + 进程 + GPU + 内存"""
import sys, json, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

HOST = '<LAPTOP_IP>'
PORT = 8080

try:
    req = urllib.request.Request(f'http://{HOST}:{PORT}/props', headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=8) as resp:
        data = json.load(resp)
    print('HEALTH OK, n_ctx:', data.get('default_generation_settings', {}).get('n_ctx'))
except Exception as e:
    print('SERVER:', 'DOWN' if 'Bad Gateway' in repr(e) or 'timed out' in repr(e) or 'refused' in repr(e) else repr(e)[:100])

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username='<LAPTOP_USER>', password='<REDACTED>', timeout=15, look_for_keys=False, allow_agent=False)
try:
    stdin, stdout, stderr = ssh.exec_command('tasklist /fi "imagename eq llama-server.exe" | findstr llama-server', timeout=30)
    proc = stdout.read().decode('utf-8', errors='replace').strip()
    print('PROC:', proc if proc else 'none')
    stdin, stdout, stderr = ssh.exec_command('cmd /c nvidia-smi --query-gpu=memory.used --format=csv', timeout=30)
    print('GPU:', stdout.read().decode('utf-8', errors='replace').strip())
    stdin, stdout, stderr = ssh.exec_command(
        'powershell -NoProfile -Command "$os=Get-CimInstance Win32_OperatingSystem; Write-Output (\'Free: \'+[math]::Round($os.FreePhysicalMemory/1MB,1)+\'GB\')"',
        timeout=30)
    print('MEM:', stdout.read().decode('utf-8', errors='replace').strip())
finally:
    ssh.close()
