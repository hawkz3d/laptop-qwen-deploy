# -*- coding: utf-8 -*-
"""查 laptop 内存条物理配置（单条/双条、频率、容量）"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('<LAPTOP_IP>', username='<LAPTOP_USER>', password='<REDACTED>',
            timeout=15, look_for_keys=False, allow_agent=False)

try:
    cmd = ('powershell -Command "Get-CimInstance Win32_PhysicalMemory | '
           'Select-Object BankLabel,DeviceLocator,Manufacturer,PartNumber,'
           '@{n=\'GB\';e={$_.Capacity/1GB}},Speed | Format-Table -AutoSize"')
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=40)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    print(out)
    if err.strip():
        print('[stderr] ' + err[:500])
finally:
    ssh.close()
