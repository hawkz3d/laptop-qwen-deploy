# -*- coding: utf-8 -*-
"""验证下载完整性：laptop 文件大小 vs HF API 目标大小，检查 curl 退出码"""
import sys, json, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

url = 'https://huggingface.co/api/models/deepreinforce-ai/Ornith-1.0-35B-GGUF/tree/main'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=20) as r:
    files = json.load(r)
TARGET = next(f['size'] for f in files if f['path'] == 'ornith-1.0-35b-Q4_K_M.gguf')
print('TARGET:', TARGET, '=', round(TARGET/1024/1024/1024, 2), 'GB')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('<LAPTOP_IP>', username='<LAPTOP_USER>', password='<REDACTED>',
            timeout=15, look_for_keys=False, allow_agent=False)
try:
    stdin, stdout, stderr = ssh.exec_command(
        'powershell -NoProfile -Command "(Get-Item \'D:\\models\\ornith-1.0-35b-Q4_K_M.gguf\').Length"', timeout=30)
    mlen = int(stdout.read().decode('utf-8', errors='replace').strip())
    print('ACTUAL:', mlen, '=', round(mlen/1024/1024/1024, 2), 'GB')
    print('MATCH:', mlen == TARGET, '| DIFF:', mlen - TARGET)

    stdin, stdout, stderr = ssh.exec_command('cmd /c type D:\\models\\dl_log.txt', timeout=30)
    print('--- DL_LOG ---')
    print(stdout.read().decode('utf-8', errors='replace'))
finally:
    ssh.close()
