# -*- coding: utf-8 -*-
"""抓 llama-server --help 完整输出到本地文件分析"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('<LAPTOP_IP>', username='<LAPTOP_USER>', password='<REDACTED>',
            timeout=15, look_for_keys=False, allow_agent=False)
try:
    stdin, stdout, stderr = ssh.exec_command('cmd /c D:\\llama\\llama-server.exe --help 2>&1', timeout=30)
    data = stdout.read().decode('utf-8', errors='replace')
    with open(r'<SCRIPT_DIR>\llama_help.txt', 'w', encoding='utf-8') as f:
        f.write(data)
    print('saved', len(data), 'chars to llama_help.txt')
finally:
    ssh.close()
