# -*- coding: utf-8 -*-
"""读 vort_head.gguf 全部 KV keys，找 delta_net_gpu_compat / gpu_compat 标记"""
import sys, struct, io
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

REMOTE = 'D:/models/vort_head.gguf'

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
    tensor_count = read_u64(b)
    kv_count = read_u64(b)
    print(f'tensors={tensor_count} kv={kv_count}')
    for i in range(kv_count):
        key = read_str(b)
        t = read_u32(b)
        val = read_value(b, t)
        if 'compat' in key.lower() or 'delta' in key.lower() or 'gpu' in key.lower() or 'fused' in key.lower() or 'fuse' in key.lower():
            print(f'  ** {key} = {val}')
        else:
            print(f'  {key}')
finally:
    ssh.close()
