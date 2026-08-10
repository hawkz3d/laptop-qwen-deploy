# -*- coding: utf-8 -*-
"""测试 laptop 直连 GitHub / hf-mirror / objects.githubusercontent 的连通性（HTTP HEAD 状态码+耗时）"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('<LAPTOP_IP>', username='<LAPTOP_USER>', password='<REDACTED>',
            timeout=15, look_for_keys=False, allow_agent=False)
try:
    cmd = ('curl -sI -m 15 https://github.com -o NUL -w "GITHUB:%{http_code} %{time_total}s\\n" '
           '&& curl -sI -m 15 https://hf-mirror.com -o NUL -w "HFMIRROR:%{http_code} %{time_total}s\\n" '
           '&& curl -sI -m 15 https://objects.githubusercontent.com -o NUL -w "GHOBJ:%{http_code} %{time_total}s\\n"')
    stdin, stdout, stderr = ssh.exec_command('cmd /c ' + cmd, timeout=90)
    print(stdout.read().decode('utf-8', errors='replace'))
    err = stderr.read().decode('utf-8', errors='replace')
    if err.strip():
        print('[stderr] ' + err[:500])
finally:
    ssh.close()
