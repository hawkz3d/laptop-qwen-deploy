# -*- coding: utf-8 -*-
"""上传 cudart 包到 laptop D:\\llama 并解压，验证 CUDA 后端加载"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

LOCAL = r'<TEMP_DIR>\cudart-llama-bin-win-cuda-12.4-x64.zip'
ZIP_NAME = os.path.basename(LOCAL)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('<LAPTOP_IP>', username='<LAPTOP_USER>', password='<REDACTED>',
            timeout=15, look_for_keys=False, allow_agent=False)
try:
    sftp = ssh.open_sftp()
    sftp.put(LOCAL, f'D:/llama/{ZIP_NAME}')
    sftp.close()
    print('UPLOAD DONE:', round(os.path.getsize(LOCAL)/1024/1024, 1), 'MB')

    ex = ('powershell -NoProfile -Command "Expand-Archive -Path \'D:\\llama\\%s\' '
          '-DestinationPath \'D:\\llama\' -Force"' % ZIP_NAME)
    stdin, stdout, stderr = ssh.exec_command(ex, timeout=300)
    print('EXTRACT OUT:', stdout.read().decode('utf-8', errors='replace'))
    err = stderr.read().decode('utf-8', errors='replace')
    if err.strip():
        print('EXTRACT ERR:', err[:1000])

    cmds = [
        'del /q D:\\llama\\%s' % ZIP_NAME,
        'dir /b D:\\llama | findstr /i "cudart cublas cublasLt cusolver cusparse nvrtc cufft curand cusolverLt cublasLt"',
        'D:\\llama\\llama-bench.exe --list-devices',
    ]
    for i, c in enumerate(cmds):
        print(f'===== CMD[{i}] =====')
        stdin, stdout, stderr = ssh.exec_command('cmd /c "' + c + '"', timeout=60)
        print(stdout.read().decode('utf-8', errors='replace'))
        print('[stderr]', stderr.read().decode('utf-8', errors='replace')[:800])
finally:
    ssh.close()
