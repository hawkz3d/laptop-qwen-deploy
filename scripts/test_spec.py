# -*- coding: utf-8 -*-
"""测试 ngram 投机解码（--spec-ngram）：无需额外模型，测速"""
import sys, time, json, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

HOST = '<LAPTOP_IP>'
PORT = 8080
print('=== ngram speculative decoding test ===')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username='<LAPTOP_USER>', password='<REDACTED>', timeout=15, look_for_keys=False, allow_agent=False)
try:
    ssh.exec_command('powershell -NoProfile -Command "Get-Process llama-server -ErrorAction SilentlyContinue | Stop-Process -Force"', timeout=20)[1].read()
    ssh.exec_command('cmd /c del D:\\llama_old\\server.log 2>nul', timeout=15)[1].read()
    bat = ('@echo off\r\ncd /d D:\\llama_old\\bin\r\n'
           'llama-server.exe -m D:\\models\\ornith-1.0-35b-Q4_K_M.gguf -ngl 999 -cmoe --no-mmap '
           '-c 131072 -kvo -ctk q8_0 -ctv q8_0 --spec-ngram-size-n 1 --spec-ngram-size-m 48 '
           '--jinja --host 0.0.0.0 --port 8080 > D:\\llama_old\\server.log 2>&1\r\n')
    sftp = ssh.open_sftp()
    with sftp.open('D:/llama_old/start_spec.bat', 'w') as f:
        f.write(bat)
    sftp.close()
    stdin, stdout, stderr = ssh.exec_command('wmic process call create "D:\\llama_old\\start_spec.bat"', timeout=30)
    print('WMIC:', stdout.read().decode('utf-8', errors='replace')[:120])

    def get_log():
        stdin, stdout, stderr = ssh.exec_command('cmd /c type D:\\llama_old\\server.log', timeout=20)
        return stdout.read().decode('utf-8', errors='replace')

    t0 = time.time(); log = ''
    while time.time() - t0 < 300:
        log = get_log()
        if 'model loaded' in log or 'CUDA error' in log or 'error:' in log:
            break
        time.sleep(8)
    print('--- loaded in', round(time.time()-t0), 's ---')
    for line in log.splitlines():
        if any(k in line.lower() for k in ['buffer size', 'model loaded', 'listening', 'spec', 'ngram', 'draft', 'cuda error']):
            print(line)
finally:
    ssh.close()

# 测速（用代码生成长 prompt 更能体现 ngram 优势）
url = f'http://{HOST}:{PORT}/v1/chat/completions'
prompt = ('Write a Python module with functions: bubble_sort, insertion_sort, merge_sort, quick_sort, '
          'heap_sort, selection_sort, shell_sort, radix_sort. Each function should take a list and return '
          'sorted list. Use consistent style.')
body = json.dumps({"model": "D:\\models\\ornith-1.0-35b-Q4_K_M.gguf",
                   "messages": [{"role": "user", "content": prompt}],
                   "max_tokens": 400, "temperature": 0.6}).encode()
req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req, timeout=400) as resp:
        json.load(resp)
except Exception as e:
    print('REQ ERR:', repr(e)[:150])
time.sleep(2)
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username='<LAPTOP_USER>', password='<REDACTED>', timeout=15, look_for_keys=False, allow_agent=False)
try:
    stdin, stdout, stderr = ssh.exec_command(
        'cmd /c powershell -NoProfile -Command "Select-String -Path D:\\llama_old\\server.log -Pattern \'eval time|draft|accept\' | Select-Object -Last 6 | ForEach-Object {$_.Line}"',
        timeout=30)
    print('--- TIMING ---')
    print(stdout.read().decode('utf-8', errors='replace'))
finally:
    ssh.close()
