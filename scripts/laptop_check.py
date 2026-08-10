# -*- coding: utf-8 -*-
"""检查 laptop (<LAPTOP_IP>) 硬件与引擎现状"""
import paramiko

host = '<LAPTOP_IP>'
user = '<LAPTOP_USER>'
pwd = '<REDACTED>'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=pwd, timeout=15,
            look_for_keys=False, allow_agent=False)

cmds = [
    'wmic OS get TotalVisibleMemorySize,FreePhysicalMemory /format:list',
    'wmic logicaldisk get Name,Size,FreeSpace /format:list',
    'nvidia-smi',
    'where llama-server 2>nul & where llama-cli 2>nul & where ollama 2>nul & echo ---end---',
]

for c in cmds:
    print('===== ' + c + ' =====')
    try:
        stdin, stdout, stderr = ssh.exec_command(c, timeout=60)
        out = stdout.read().decode('utf-8', errors='replace')
        err = stderr.read().decode('utf-8', errors='replace')
        print(out)
        if err.strip():
            print('[stderr] ' + err[:800])
    except Exception as e:
        print('[ERR] ' + str(e))

ssh.close()
