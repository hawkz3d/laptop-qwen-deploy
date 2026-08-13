# -*- coding: utf-8 -*-
"""一键启动 Ornith（b8600 + -cmoe）：上传 bat -> wmic 后台启动 -> 等加载 -> 健康检查"""
import sys, time, json, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

HOST = '<LAPTOP_IP>'
PORT = 8080
MODEL = 'D:\\models\\ornith-1.0-35b-Q4_K_M.gguf'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username='<LAPTOP_USER>', password='<REDACTED>', timeout=15, look_for_keys=False, allow_agent=False)
try:
    # 杀旧进程（等 4s 让 cmd.exe 句柄释放，否则 server.log 删不掉、新进程写日志失败）
    ssh.exec_command('powershell -NoProfile -Command "Get-Process llama-server -ErrorAction SilentlyContinue | Stop-Process -Force"', timeout=20)[1].read()
    time.sleep(4)
    ssh.exec_command('cmd /c del D:\\llama_old\\server.log 2>nul', timeout=15)[1].read()
    # bat：b8600 + -cmoe（专家 CPU，non-expert/SSM GPU）——GTX1060 最优配置
    bat = ('@echo off\r\ncd /d D:\\llama_old\\bin\r\n'
           'llama-server.exe -m D:\\models\\ornith-1.0-35b-Q4_K_M.gguf -ngl 999 -cmoe --no-mmap '
           '-c 196608 -kvo -ctk q8_0 -ctv q8_0 -fa on -fit off --jinja --host 0.0.0.0 --port 8080 > D:\\llama_old\\server.log 2>&1\r\n')
    sftp = ssh.open_sftp()
    with sftp.open('D:/llama_old/start_ornith.bat', 'w') as f:
        f.write(bat)
    sftp.close()
    stdin, stdout, stderr = ssh.exec_command('wmic process call create "D:\\llama_old\\start_ornith.bat"', timeout=30)
    print('WMIC:', stdout.read().decode('utf-8', errors='replace')[:150])

    # 进程起来后拉 High 优先级（内存带宽瓶颈下实测 +9% 速度）
    time.sleep(6)
    stdin, stdout, stderr = ssh.exec_command(
        "powershell -NoProfile -Command \"Start-Sleep -Seconds 3; $p=Get-Process llama-server -ErrorAction SilentlyContinue; if($p){$p.PriorityClass='High'}\"",
        timeout=30)
    stdout.read()
    stdin, stdout, stderr = ssh.exec_command(
        'powershell -NoProfile -Command "(Get-Process llama-server -ErrorAction SilentlyContinue).PriorityClass"', timeout=30)
    print('PRIORITY:', stdout.read().decode('utf-8', errors='replace').strip() or '(not found)')

    # 等加载
    def get_log():
        stdin, stdout, stderr = ssh.exec_command('cmd /c type D:\\llama_old\\server.log', timeout=20)
        return stdout.read().decode('utf-8', errors='replace')

    t0 = time.time(); log = ''
    while time.time() - t0 < 400:
        log = get_log()
        if 'model loaded' in log or 'CUDA error' in log or 'error:' in log:
            break
        time.sleep(8)
    print('--- load status ---')
    for line in log.splitlines():
        if any(k in line.lower() for k in ['offloaded', 'buffer size', 'model loaded', 'listening', 'cuda error', 'kv buffer', 'recurrent']):
            print(line)
finally:
    ssh.close()

# 健康检查
time.sleep(2)
try:
    req = urllib.request.Request(f'http://{HOST}:{PORT}/health', headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as resp:
        print('HEALTH:', resp.status, resp.read().decode())
except Exception as e:
    print('HEALTH ERR:', repr(e)[:150])
