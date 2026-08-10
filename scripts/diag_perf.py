# -*- coding: utf-8 -*-
"""诊断提速潜力：电源计划 / 内存频率 / MAA-MuMu 进程"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('<LAPTOP_IP>', username='<LAPTOP_USER>', password='<REDACTED>',
            timeout=15, look_for_keys=False, allow_agent=False)
try:
    cmds = [
        'powercfg /getactivescheme',
        'wmic memorychip get BankLabel,DeviceLocator,Speed,Capacity /format:csv',
        'tasklist /fi "imagename eq MAA.exe" | findstr MAA',
        'tasklist /fi "imagename eq MuMuNxMain.exe" | findstr MuMu',
        'wmic cpu get LoadPercentage /value',
    ]
    for i, c in enumerate(cmds):
        print(f'===== CMD[{i}] =====')
        stdin, stdout, stderr = ssh.exec_command('cmd /c "' + c + '"', timeout=30)
        out = stdout.read().decode('utf-8', errors='replace')
        print(out if out.strip() else '(none)')
finally:
    ssh.close()
