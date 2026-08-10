# -*- coding: utf-8 -*-
"""诊断：bat 内容 + llama-server 进程 + 命令行"""
import sys
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

    print('=== start_ornith.bat ===')
    print(run('cmd /c type D:\\llama_old\\start_ornith.bat'))
    print('=== llama-server procs ===')
    print(run('tasklist /fi "imagename eq llama-server.exe"'))
    print('=== commandline ===')
    print(run('wmic process where "name=\'llama-server.exe\'" get ProcessId,CommandLine /format:list'))
finally:
    ssh.close()
