# -*- coding: utf-8 -*-
"""监控 llama-server 启动（-ngl 999 -cmoe）：轮询 server.log 直到 listening/error/超时"""
import sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('<LAPTOP_IP>', username='<LAPTOP_USER>', password='<REDACTED>',
            timeout=15, look_for_keys=False, allow_agent=False)

def get_log():
    stdin, stdout, stderr = ssh.exec_command('cmd /c type D:\\llama\\server.log', timeout=20)
    return stdout.read().decode('utf-8', errors='replace')

def proc_alive():
    stdin, stdout, stderr = ssh.exec_command(
        'tasklist /fi "imagename eq llama-server.exe" | findstr llama-server', timeout=20)
    return 'llama-server' in stdout.read().decode('utf-8', errors='replace')

try:
    ssh.exec_command('cmd /c del D:\\llama\\server.log 2>nul', timeout=15)[1].read()
    stdin, stdout, stderr = ssh.exec_command(
        'wmic process call create "D:\\llama\\server_start.bat"', timeout=30)
    print('WMIC:', stdout.read().decode('utf-8', errors='replace')[:200])

    last_len = 0
    t0 = time.time()
    deadline = t0 + 360
    done = False
    while time.time() < deadline:
        log = get_log()
        if len(log) > last_len:
            new = log[last_len:]
            last_len = len(log)
            for line in new.splitlines():
                print(f'{time.time()-t0:6.0f}s | {line}')
        low = log.lower()
        if 'listening' in low:
            print('== LISTENING ==')
            done = True
            break
        if 'error' in low or 'failed' in low or 'out of memory' in low:
            print('== ERROR DETECTED ==')
            done = True
            break
        time.sleep(6)
    print('--- elapsed:', round(time.time()-t0, 1), 's | listening:', done, '| alive:', proc_alive())
finally:
    ssh.close()
