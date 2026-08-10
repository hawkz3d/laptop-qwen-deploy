# -*- coding: utf-8 -*-
"""在 laptop 启动 llama-server 跑 Ornith Q4_K_M（内存到位后执行）。
检查内存>=32GB 再启动，五参数命令，OpenAI 兼容端口 8080。
用 wmic 后台启动，独立于 SSH 会话。
"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('<LAPTOP_IP>', username='<LAPTOP_USER>', password='<REDACTED>',
            timeout=15, look_for_keys=False, allow_agent=False)
try:
    # 1) 检查内存
    stdin, stdout, stderr = ssh.exec_command(
        'wmic ComputerSystem get TotalPhysicalMemory /value', timeout=30)
    total_bytes = None
    for line in stdout.read().decode('utf-8', errors='replace').splitlines():
        if 'TotalPhysicalMemory' in line and '=' in line:
            try:
                total_bytes = int(line.split('=')[1].strip())
            except Exception:
                pass
    gb = round(total_bytes / 1024**3, 1) if total_bytes else None
    print('TOTAL MEMORY:', gb, 'GB')
    if not total_bytes or total_bytes < 30 * 1024**3:
        print('WARN: 内存 < 32GB，模型 19.71GB + KV 可能不够，仍尝试启动')

    # 2) 检查模型文件
    stdin, stdout, stderr = ssh.exec_command(
        'powershell -NoProfile -Command "(Get-Item \'D:\\models\\ornith-1.0-35b-Q4_K_M.gguf\').Length"', timeout=30)
    mlen = stdout.read().decode('utf-8', errors='replace').strip()
    print('MODEL SIZE bytes:', mlen)

    # 3) 后台启动 llama-server（五参数命令）
    server_cmd = ('cmd /c D:\\llama\\llama-server.exe -m D:\\models\\ornith-1.0-35b-Q4_K_M.gguf '
                  '--no-moe-offload --no-mmap -ngl 35 --turbo-key 4 --turbo-values 4 '
                  '-c 32768 --jinja --port 8080')
    stdin, stdout, stderr = ssh.exec_command(
        'wmic process call create "' + server_cmd + '"', timeout=30)
    print('WMIC OUT:', stdout.read().decode('utf-8', errors='replace'))
    err = stderr.read().decode('utf-8', errors='replace')
    if err.strip():
        print('WMIC ERR:', err[:500])
finally:
    ssh.close()
