# -*- coding: utf-8 -*-
"""诊断：1) GGUF 头全部 KV key（找 fused/experts metadata） 2) 推理期间 GPU util"""
import sys, struct, io, time, json, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

HOST = '<LAPTOP_IP>'
REMOTE = 'D:/models/ornith-1.0-35b-Q4_K_M.gguf'

# ---------- 1) GGUF 头 KV keys ----------
def read_u32(f): return struct.unpack('<I', f.read(4))[0]
def read_u64(f): return struct.unpack('<Q', f.read(8))[0]
def read_str(f):
    n = read_u64(f)
    return f.read(n).decode('utf-8', errors='replace')
def read_value(f, t):
    if t == 0: return f.read(1)[0]
    if t == 1: return struct.unpack('<b', f.read(1))[0]
    if t == 2: return struct.unpack('<H', f.read(2))[0]
    if t == 3: return struct.unpack('<h', f.read(2))[0]
    if t == 4: return read_u32(f)
    if t == 5: return struct.unpack('<i', f.read(4))[0]
    if t == 6: return struct.unpack('<f', f.read(4))[0]
    if t == 7: return f.read(1)[0] != 0
    if t == 8: return read_str(f)
    if t == 9:
        et = read_u32(f); n = read_u64(f)
        for _ in range(n): read_value(f, et)
        return None
    if t == 10: return read_u64(f)
    if t == 11: return struct.unpack('<q', f.read(8))[0]
    if t == 12: return struct.unpack('<d', f.read(8))[0]
    raise ValueError(f'type {t}')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username='<LAPTOP_USER>', password='<REDACTED>', timeout=15, look_for_keys=False, allow_agent=False)
try:
    sftp = ssh.open_sftp()
    with sftp.open(REMOTE, 'rb') as f:
        head = f.read(16 * 1024 * 1024)
    sftp.close()
    b = io.BytesIO(head)
    assert b.read(4) == b'GGUF'
    read_u32(b)  # version
    tensor_count = read_u64(b)
    kv_count = read_u64(b)
    print(f'tensors={tensor_count} kv={kv_count}')
    fused = []
    for i in range(kv_count):
        key = read_str(b)
        t = read_u32(b)
        read_value(b, t)
        if 'fuse' in key.lower() or 'expert' in key.lower() or 'gate' in key.lower() or 'up' in key.lower() or 'delta' in key.lower():
            fused.append(key)
    print('--- fused/expert related keys ---')
    for k in fused:
        print(' ', k)
finally:
    ssh.close()

# ---------- 2) GPU util during inference ----------
print()
print('=== GPU UTIL DURING INFERENCE ===')
# 启动 nvidia-smi 采样（后台，1s 间隔，20s）
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username='<LAPTOP_USER>', password='<REDACTED>', timeout=15, look_for_keys=False, allow_agent=False)
try:
    ssh.exec_command(
        'powershell -NoProfile -Command "Start-Process nvidia-smi -ArgumentList \'--query-gpu=utilization.gpu,memory.used --format=csv -lms 1000\' -RedirectStandardOutput C:\\gpu_util.txt -WindowStyle Hidden"',
        timeout=20)[1].read()
    time.sleep(2)
finally:
    ssh.close()

# 发请求（~60s 生成）
url = f'http://{HOST}:8080/v1/chat/completions'
body = json.dumps({"model": "D:\\models\\ornith-1.0-35b-Q4_K_M.gguf",
                   "messages": [{"role": "user", "content": "Write Python code for binary search. Code only."}],
                   "max_tokens": 300, "temperature": 0.6}).encode()
req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=180) as resp:
    json.load(resp)

# 停采样，读结果
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username='<LAPTOP_USER>', password='<REDACTED>', timeout=15, look_for_keys=False, allow_agent=False)
try:
    ssh.exec_command('powershell -NoProfile -Command "Get-Process nvidia-smi -ErrorAction SilentlyContinue | Stop-Process -Force"', timeout=20)[1].read()
    time.sleep(1)
    stdin, stdout, stderr = ssh.exec_command('cmd /c type C:\\gpu_util.txt', timeout=20)
    print(stdout.read().decode('utf-8', errors='replace'))
finally:
    ssh.close()
