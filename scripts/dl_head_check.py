# -*- coding: utf-8 -*-
"""Range 下载 APEX-I-Mini 前 16MB，检查 GGUF 头是否带 fused metadata"""
import sys, struct, io
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

URL = 'https://hf-mirror.com/mudler/Ornith-1.0-35B-APEX-GGUF/resolve/main/Ornith-1.0-35B-APEX-I-Mini.gguf'
REMOTE_HEAD = 'D:/models/apex_mini_head.gguf'

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
ssh.connect('<LAPTOP_IP>', username='<LAPTOP_USER>', password='<REDACTED>',
            timeout=15, look_for_keys=False, allow_agent=False)
try:
    # 1) curl Range 下载前 16MB
    cmd = f'curl -L --connect-timeout 15 -r 0-16777215 -sS -o {REMOTE_HEAD} "{URL}"'
    stdin, stdout, stderr = ssh.exec_command('cmd /c ' + cmd, timeout=120)
    print('CURL OUT:', stdout.read().decode('utf-8', errors='replace'))
    err = stderr.read().decode('utf-8', errors='replace')
    if err.strip():
        print('CURL ERR:', err[:300])

    # 2) 读头
    sftp = ssh.open_sftp()
    with sftp.open(REMOTE_HEAD, 'rb') as f:
        head = f.read(16 * 1024 * 1024)
    sftp.close()
    print('downloaded head bytes:', len(head))
    b = io.BytesIO(head)
    magic = b.read(4)
    print('MAGIC:', magic)
    if magic != b'GGUF':
        print('NOT GGUF'); sys.exit(1)
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
    fused = [k for k in keys if 'fuse' in k.lower()]
    print('HAS FUSED KEY:', bool(fused))
    for k in fused:
        print('  FUSED:', k)
    print('--- all keys ---')
    for k in keys:
        print(' ', k)
finally:
    ssh.close()
