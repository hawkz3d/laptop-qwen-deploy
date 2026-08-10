# -*- coding: utf-8 -*-
"""只查 laptop 磁盘分区与剩余空间"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('<LAPTOP_IP>', username='<LAPTOP_USER>', password='<REDACTED>',
            timeout=15, look_for_keys=False, allow_agent=False)

try:
    stdin, stdout, stderr = ssh.exec_command(
        'wmic logicaldisk get Name,Size,FreeSpace,VolumeName /format:list', timeout=30)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    if 'wmic' in err.lower() or 'not recognized' in out.lower():
        # wmic 失效，fallback powershell
        stdin, stdout, stderr = ssh.exec_command(
            'powershell -Command "Get-Volume | Where-Object DriveLetter | Select-Object DriveLetter,FileSystemLabel,@{n=\"SizeGB\";e={[math]::Round($_.Size/1GB,1)}},@{n=\"FreeGB\";e={[math]::Round($_.SizeRemaining/1GB,1)}} | Format-Table -AutoSize"',
            timeout=30)
        out = stdout.read().decode('utf-8', errors='replace')
    print(out)
    if err.strip():
        print('[stderr] ' + err[:500])
finally:
    ssh.close()
