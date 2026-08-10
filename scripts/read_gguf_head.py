# -*- coding: utf-8 -*-
"""只读 laptop 上 GGUF 文件头（前 16MB）解析关键元数据，不加载模型。
完整解析 KV 保证字节流推进正确。"""
import sys, struct, io
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

REMOTE = 'D:/models/ornith-1.0-35b-Q4_K_M.gguf'

def read_u8(f): return f.read(1)[0]
def read_u32(f): return struct.unpack('<I', f.read(4))[0]
def read_u64(f): return struct.unpack('<Q', f.read(8))[0]
def read_str(f):
    n = read_u64(f)
    return f.read(n).decode('utf-8', errors='replace')
def read_value(f, t):
    if t == 0: return read_u8(f)
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
        return [read_value(f, et) for _ in range(n)]
    if t == 10: return read_u64(f)
    if t == 11: return struct.unpack('<q', f.read(8))[0]
    if t == 12: return struct.unpack('<d', f.read(8))[0]
    raise ValueError(f'unknown type {t}')

INTEREST = {
    'general.architecture', 'general.name', 'general.file_type',
    'general.size_label', 'general.context_length', 'general.tensor_count',
    'qwen3_5_moe.expert_count', 'qwen3_5_moe.attention.head_count_kv',
    'qwen3_5_moe.block_count', 'qwen3_5_moe.expert_used_count',
    'tokenizer.ggml.model', 'general.quantization_version',
}

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('<LAPTOP_IP>', username='<LAPTOP_USER>', password='<REDACTED>',
            timeout=15, look_for_keys=False, allow_agent=False)
try:
    stdin, stdout, stderr = ssh.exec_command(
        'powershell -NoProfile -Command "Get-Process llama-cli -ErrorAction SilentlyContinue | Stop-Process -Force"', timeout=20)
    stdout.read()
    print('[cleaned stray llama-cli processes]')

    sftp = ssh.open_sftp()
    with sftp.open(REMOTE, 'rb') as f:
        head = f.read(16 * 1024 * 1024)  # 16MB
    sftp.close()
    print(f'[read {len(head)/1024/1024:.1f} MB head]')

    b = io.BytesIO(head)
    magic = b.read(4)
    print('MAGIC:', magic)
    if magic != b'GGUF':
        print('NOT a GGUF file'); sys.exit(1)
    version = read_u32(b)
    tensor_count = read_u64(b)
    kv_count = read_u64(b)
    print(f'GGUF version={version} tensor_count={tensor_count} kv_count={kv_count}')

    parsed = {}
    skipped_big = []
    for i in range(kv_count):
        key = read_str(b)
        t = read_u32(b)
        val = read_value(b, t)
        if key in INTEREST:
            parsed[key] = val
        elif isinstance(val, list) and len(val) > 1000:
            skipped_big.append(f'{key}:{len(val)}')
    for k, v in parsed.items():
        print(f'{k} = {v}')
    if skipped_big:
        print('SKIPPED BIG ARRAYS:', skipped_big)
    # 剩余字节（确认头是否读完）
    remaining = len(head) - b.tell()
    print(f'[remaining in 16MB buffer: {remaining} bytes]')
finally:
    ssh.close()
