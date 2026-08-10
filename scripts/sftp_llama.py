# -*- coding: utf-8 -*-
"""SFTP 上传 llama.cpp zip 到 laptop D:\\llama -> 解压 -> 验证 llama-server"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

LOCAL = r'<TEMP_DIR>\llama-b10301-bin-win-cuda-12.4-x64.zip'
ZIP_NAME = os.path.basename(LOCAL)
REMOTE_DIR = 'D:/llama'
REMOTE_ZIP = f'D:/llama/{ZIP_NAME}'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('<LAPTOP_IP>', username='<LAPTOP_USER>', password='<REDACTED>',
            timeout=15, look_for_keys=False, allow_agent=False)
try:
    stdin, stdout, stderr = ssh.exec_command('cmd /c if not exist D:\\llama mkdir D:\\llama', timeout=30)
    stdout.read()

    sftp = ssh.open_sftp()
    sftp.put(LOCAL, REMOTE_ZIP)
    sftp.close()
    print('UPLOAD DONE:', REMOTE_ZIP, round(os.path.getsize(LOCAL)/1024/1024, 1), 'MB')

    cmd = f'cmd /c cd /d D:\\llama && tar -xf {ZIP_NAME} && echo EXTRACT_OK && dir /b D:\\llama'
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=180)
    print(stdout.read().decode('utf-8', errors='replace'))
    err = stderr.read().decode('utf-8', errors='replace')
    if err.strip():
        print('[stderr] ' + err[:1000])

    stdin, stdout, stderr = ssh.exec_command('cmd /c D:\\llama\\llama-server.exe --version', timeout=30)
    out = stdout.read().decode('utf-8', errors='replace')
    err2 = stderr.read().decode('utf-8', errors='replace')
    print('--- VERSION STDOUT ---')
    print(out)
    print('--- VERSION STDERR ---')
    print(err2[:1000])
finally:
    ssh.close()
