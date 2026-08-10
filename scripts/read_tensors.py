# -*- coding: utf-8 -*-
"""解析官方 + APEX GGUF 的 tensor 名，对比专家张量是否 fused（gate/up/down 分离 vs 融合）"""
import sys, struct, io, collections
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

FILES = {
    'OFFICIAL': 'D:/models/ornith-1.0-35b-Q4_K_M.gguf',
    'APEX_HEAD': 'D:/models/apex_mini_head.gguf',
}

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
    for tag, path in FILES.items():
        print(f'===== {tag}: {path} =====')
        with sftp.open(path, 'rb') as f:
            head = f.read(16 * 1024 * 1024)
        b = io.BytesIO(head)
        assert b.read(4) == b'GGUF'
        read_u32(b)
        tensor_count = read_u64(b)
        kv_count = read_u64(b)
        for _ in range(kv_count):
            read_str(b)
            read_value(b, read_u32(b))
        # tensor info
        names = []
        for _ in range(tensor_count):
            name = read_str(b)
            n_dims = read_u32(b)
            for _ in range(n_dims): read_u64(b)
            read_u32(b)  # ggml_type
            read_u64(b)  # offset
            names.append(name)
        print(f'tensors parsed: {len(names)}')
        # 统计专家张量模式
        gate = [n for n in names if 'gate' in n and 'exp' in n]
        up = [n for n in names if 'up' in n and 'exp' in n]
        down = [n for n in names if 'down' in n and 'exp' in n]
        fused = [n for n in names if 'gate_up' in n or 'up_down' in n or 'gateup' in n]
        print(f'gate_exps: {len(gate)}  up_exps: {len(up)}  down_exps: {len(down)}  fused: {len(fused)}')
        # 打印 blk.0 的专家相关 tensor 名样本
        print('  blk.0 sample:')
        for n in names[:40]:
            if any(k in n for k in ('ffn', 'exp', 'ssm', 'attn')):
                print('   ', n)
    sftp.close()
finally:
    ssh.close()
