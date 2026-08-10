# -*- coding: utf-8 -*-
"""打印官方 Ornith GGUF 头全部 KV key 名（确认 fused metadata 是否存在）"""
import sys, struct, io
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

REMOTE = 'D:/models/ornith-1.0-35b-Q4_K_M.gguf'

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
    sftp = ssh.open_sftp()
    with sftp.open(REMOTE, 'rb') as f:
        head = f.read(16 * 1024 * 1024)
    sftp.close()
    b = io.BytesIO(head)
    assert b.read(4) == b'GGUF'
    read_u32(b)
    read_u64(b)  # tensor_count
    kv_count = read_u64(b)
    print(f'kv_count={kv_count}')
    keys = []
    for i in range(kv_count):
        key = read_str(b)
        t = read_u32(b)
        read_value(b, t)
        keys.append(f'{i}: {key}')
    for k in keys:
        print(' ', k)
    has_fused = any('fuse' in k.lower() for k in keys)
    print('HAS FUSED KEY:', has_fused)
finally:
    ssh.close()
