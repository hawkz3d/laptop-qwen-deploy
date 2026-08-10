# -*- coding: utf-8 -*-
"""监控 laptop 模型下载进度：查 HF API 目标大小，轮询 laptop 文件字节数直到完成/超时"""
import sys, time, json, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

# 目标大小（本机查 HF API）
url = 'https://huggingface.co/api/models/deepreinforce-ai/Ornith-1.0-35B-GGUF/tree/main'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=20) as r:
    files = json.load(r)
TARGET = next(f['size'] for f in files if f['path'] == 'ornith-1.0-35b-Q4_K_M.gguf')
print('TARGET:', TARGET, '=', round(TARGET/1024/1024/1024, 2), 'GB', flush=True)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('<LAPTOP_IP>', username='<LAPTOP_USER>', password='<REDACTED>',
            timeout=15, look_for_keys=False, allow_agent=False)

def size():
    stdin, stdout, stderr = ssh.exec_command(
        'powershell -NoProfile -Command "(Get-Item \'D:\\models\\ornith-1.0-35b-Q4_K_M.gguf\').Length"',
        timeout=30)
    try:
        return int(stdout.read().decode().strip())
    except Exception:
        return -1

deadline = time.time() + 2700  # 45 分钟
while time.time() < deadline:
    s = size()
    if s < 0:
        print(f'{time.strftime("%H:%M:%S")} (file not ready yet)', flush=True)
    else:
        pct = s / TARGET * 100
        print(f'{time.strftime("%H:%M:%S")} {s/1024/1024/1024:.2f}/{TARGET/1024/1024/1024:.2f} GB ({pct:.1f}%)', flush=True)
        if s >= TARGET:
            print('DOWNLOAD COMPLETE', flush=True)
            break
    time.sleep(45)
else:
    print('TIMEOUT waiting download', flush=True)

ssh.close()
