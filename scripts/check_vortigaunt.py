# -*- coding: utf-8 -*-
"""查 Vortigaunt-35B GGUF：文件列表 + Range 头检查 fused metadata"""
import json, urllib.request, sys, struct, io
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

repo = 'xero0000/Vortigaunt-35B-mixed-q2k-imat'

def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.load(r)

try:
    data = fetch(f'https://huggingface.co/api/models/{repo}/tree/main')
    print(f'===== {repo} =====')
    for f in data:
        if f.get('type') == 'file':
            size = f.get('size')
            gb = f'{size/1024**3:.2f} GB' if size else ''
            print(f"  {f['path']}  {gb}")
except Exception as e:
    print(f'{repo} ERR: {repr(e)[:200]}')
    sys.exit(0)

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

# Range 下载头部检查
REMOTE_HEAD = 'D:/models/vort_head.gguf'
files = [f for f in data if f.get('type') == 'file' and f['path'].endswith('.gguf')]
if not files:
    print('NO GGUF'); sys.exit(0)
gguf = files[0]['path']
print('checking:', gguf)
url = f'https://hf-mirror.com/{repo}/resolve/main/{gguf}'
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('<LAPTOP_IP>', username='<LAPTOP_USER>', password='<REDACTED>', timeout=15, look_for_keys=False, allow_agent=False)
try:
    cmd = f'curl -L --connect-timeout 15 -r 0-16777215 -sS -o {REMOTE_HEAD} "{url}"'
    stdin, stdout, stderr = ssh.exec_command('cmd /c ' + cmd, timeout=120)
    stdout.read()
    err = stderr.read().decode('utf-8', errors='replace')
    if err.strip(): print('CURL ERR:', err[:200])
    sftp = ssh.open_sftp()
    with sftp.open(REMOTE_HEAD, 'rb') as f:
        head = f.read(16 * 1024 * 1024)
    sftp.close()
    print('head bytes:', len(head))
    b = io.BytesIO(head)
    assert b.read(4) == b'GGUF'
    read_u32(b)
    tensor_count = read_u64(b)
    kv_count = read_u64(b)
    print(f'tensors={tensor_count} kv={kv_count}')
    keys = []
    for i in range(kv_count):
        key = read_str(b)
        t = read_u32(b)
        read_value(b, t)
        keys.append(key)
    print('HAS fuse key:', any('fuse' in k.lower() for k in keys))
    print('HAS chat_template:', any('chat_template' in k for k in keys))
    names = []
    for _ in range(tensor_count):
        name = read_str(b)
        n_dims = read_u32(b)
        for _ in range(n_dims): read_u64(b)
        read_u32(b); read_u64(b)
        names.append(name)
    fused_t = [n for n in names if 'gate_up' in n or 'up_gate' in n or 'fused' in n or 'updown' in n]
    print(f'tensor fused={len(fused_t)}')
    for n in fused_t[:10]:
        print('  FUSED TENSOR:', n)
    # 专家张量模式
    gate = [n for n in names if 'gate' in n and 'exp' in n]
    up = [n for n in names if 'up' in n and 'exp' in n]
    print(f'gate_exps={len(gate)} up_exps={len(up)}')
finally:
    ssh.close()
