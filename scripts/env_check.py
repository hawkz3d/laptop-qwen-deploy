# -*- coding: utf-8 -*-
"""检查 laptop 部署 llama.cpp 前置环境：GPU驱动/CUDA、磁盘、架构、解压/下载工具、代理"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('<LAPTOP_IP>', username='<LAPTOP_USER>', password='<REDACTED>',
            timeout=15, look_for_keys=False, allow_agent=False)

try:
    cmds = [
        'nvidia-smi',
        'wmic logicaldisk get DeviceID,FreeSpace,Size /format:csv',
        'echo ARCH=%PROCESSOR_ARCHITECTURE%',
        'where 7z & where curl & where tar & where powershell',
        'echo ---D-DIR---',
        'dir D:\\ /b',
        'echo ---NET-PROXY---',
        'reg query "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings" /v ProxyServer',
    ]
    combined = ' && echo ===NEXT=== && '.join(cmds)
    stdin, stdout, stderr = ssh.exec_command('cmd /c "' + combined + '"', timeout=90)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    print(out)
    if err.strip():
        print('[stderr] ' + err[:1000])
finally:
    ssh.close()
