# -*- coding: utf-8 -*-
"""看 server.log 尾部 + 8080 端口占用 + 相关进程"""
import sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('<LAPTOP_IP>', username='<LAPTOP_USER>', password='<REDACTED>',
            timeout=15, look_for_keys=False, allow_agent=False)
try:
    def run(c):
        i, o, e = ssh.exec_command(c, timeout=30)
        return o.read().decode('gbk', errors='replace')

    print('=== server.log size/mtime ===')
    print(run('cmd /c dir D:\\llama_old\\server.log'))
    print('=== server.log tail 30 ===')
    print(run('cmd /c powershell -NoProfile -Command "Get-Content D:\\llama_old\\server.log -Tail 30"'))
    print('=== port 8080 ===')
    print(run('netstat -ano | findstr :8080'))
    print('=== cmd procs (start_ornith) ===')
    print(run('tasklist /fi "imagename eq cmd.exe" | findstr cmd'))
finally:
    ssh.close()
