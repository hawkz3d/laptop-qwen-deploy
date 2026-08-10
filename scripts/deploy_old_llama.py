# -*- coding: utf-8 -*-
"""本机下载 llama.cpp b8600 -> SFTP 传 laptop D:\\llama_old -> 解压 -> 复制 cudart -> 测 CUDA"""
import urllib.request, sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

url = 'https://github.com/ggml-org/llama.cpp/releases/download/b8600/llama-b8600-bin-win-cuda-12.4-x64.zip'
local = r'<TEMP_DIR>\llama-b8600-bin-win-cuda-12.4-x64.zip'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=60) as r, open(local, 'wb') as f:
    total = int(r.headers.get('Content-Length', 0)); done = 0
    while True:
        chunk = r.read(1 << 20)
        if not chunk: break
        f.write(chunk); done += len(chunk)
        print(f'\r{done/1024/1024:.0f}/{total/1024/1024:.0f}MB', end='', flush=True)
print('\ndownloaded', round(os.path.getsize(local)/1024/1024, 1), 'MB')

import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('<LAPTOP_IP>', username='<LAPTOP_USER>', password='<REDACTED>',
            timeout=15, look_for_keys=False, allow_agent=False)
try:
    ssh.exec_command('cmd /c if not exist D:\\llama_old mkdir D:\\llama_old', timeout=20)[1].read()
    sftp = ssh.open_sftp()
    sftp.put(local, 'D:/llama_old/llama.zip')
    sftp.close()
    print('uploaded')
    ssh.exec_command(
        'powershell -NoProfile -Command "Expand-Archive -Path \'D:\\llama_old\\llama.zip\' -DestinationPath \'D:\\llama_old\\bin\' -Force"',
        timeout=180)[1].read()
    print('extracted')
    ssh.exec_command(
        'cmd /c copy /y D:\\llama\\cublas64_12.dll D:\\llama\\cublasLt64_12.dll D:\\llama\\cudart64_12.dll D:\\llama_old\\bin\\',
        timeout=20)[1].read()
    print('copied cudart')
    stdin, stdout, stderr = ssh.exec_command(
        'cmd /c D:\\llama_old\\bin\\llama-server.exe --list-devices', timeout=30)
    print('--- DEVICES ---')
    print(stdout.read().decode('utf-8', errors='replace'))
    print(stderr.read().decode('utf-8', errors='replace')[:500])
finally:
    ssh.close()
