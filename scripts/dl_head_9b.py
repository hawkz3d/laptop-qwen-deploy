# -*- coding: utf-8 -*-
"""Range 下载 jessteru 9B 头部，检查架构/fused/chat_template"""
import sys, struct, io
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

URL = 'https://hf-mirror.com/jessteru/Ornith-1.0-9B-Ollama-fixed-GGUX/resolve/main/ornith-1.0-9b-Q8_0-fixed.gguf'
REMOTE_HEAD = 'D:/models/jes_head.gguf'

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
    cmd = f'curl -L --connect-timeout 15 -r 0-16777215 -sS -o {REMOTE_HEAD} "{URL}"'
    stdin, stdout, stderr = ssh.exec_command('cmd /c ' + cmd, timeout=120)
    print('CURL:', stdout.read().decode('utf-8', errors='replace'))
    err = stderr.read().decode('utf-8', errors='replace')
    if err.strip(): print('CURL ERR:', err[:300])

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
    print('HAS chat_template:', any('chat_template' in k for k in keys))
    print('HAS fuse key:', any('fuse' in k.lower() for k in keys))
    print('arch:', [k for k in keys if 'architecture' in k])
    # tensor 名 fused 检查
    names = []
    for _ in range(tensor_count):
        name = read_str(b)
        n_dims = read_u32(b)
        for _ in range(n_dims): read_u64(b)
        read_u32(b); read_u64(b)
        names.append(name)
    fused_t = [n for n in names if 'gate_up' in n or 'up_gate' in n or 'fused' in n]
    gate = [n for n in names if 'gate' in n and 'exp' in n]
    print(f'tensor fused={len(fused_t)} gate_exps={len(gate)}')
    # 打印前 15 个 tensor 名样本
    print('--- sample tensors ---')
    for n in names[:15]:
        print('  ', n)
finally:
    ssh.close()
