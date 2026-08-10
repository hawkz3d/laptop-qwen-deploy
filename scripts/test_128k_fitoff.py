# -*- coding: utf-8 -*-
"""实测 128K + -fit off：重启 b8600 服务为 -c 131072 -fit off，测速对比 192K"""
import sys, time, json, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

HOST = '<LAPTOP_IP>'
PORT = 8080

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username='<LAPTOP_USER>', password='<REDACTED>', timeout=15, look_for_keys=False, allow_agent=False)
try:
    ssh.exec_command('powershell -NoProfile -Command "Get-Process llama-server -ErrorAction SilentlyContinue | Stop-Process -Force"', timeout=20)[1].read()
    ssh.exec_command('cmd /c del D:\\llama_old\\server.log 2>nul', timeout=15)[1].read()
    # bat：128K + fit off（其余同 192K 最优配置）
    bat = ('@echo off\r\ncd /d D:\\llama_old\\bin\r\n'
           'llama-server.exe -m D:\\models\\ornith-1.0-35b-Q4_K_M.gguf -ngl 999 -cmoe --no-mmap '
           '-c 131072 -kvo -ctk q8_0 -ctv q8_0 -fit off --jinja --host 0.0.0.0 --port 8080 > D:\\llama_old\\server.log 2>&1\r\n')
    sftp = ssh.open_sftp()
    with sftp.open('D:/llama_old/start_ornith.bat', 'w') as f:
        f.write(bat)
    sftp.close()
    stdin, stdout, stderr = ssh.exec_command('wmic process call create "D:\\llama_old\\start_ornith.bat"', timeout=30)
    print('WMIC:', stdout.read().decode('utf-8', errors='replace')[:120])

    # 拉 High 优先级
    time.sleep(6)
    stdin, stdout, stderr = ssh.exec_command(
        "powershell -NoProfile -Command \"Start-Sleep -Seconds 3; $p=Get-Process llama-server -ErrorAction SilentlyContinue; if($p){$p.PriorityClass='High'}\"",
        timeout=30)
    stdout.read()

    def get_log():
        i, o, e = ssh.exec_command('cmd /c type D:\\llama_old\\server.log', timeout=20)
        return o.read().decode('utf-8', errors='replace')

    t0 = time.time(); log = ''
    while time.time() - t0 < 400:
        log = get_log()
        if 'model loaded' in log or 'CUDA error' in log or 'error:' in log:
            break
        time.sleep(8)
    print('--- load status ---')
    for line in log.splitlines():
        if any(k in line.lower() for k in ['offloaded', 'buffer size', 'model loaded', 'listening', 'cuda error', 'kv buffer', 'recurrent', 'n_ctx']):
            print(line)
finally:
    ssh.close()

time.sleep(2)
try:
    req = urllib.request.Request(f'http://{HOST}:{PORT}/health', headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as resp:
        print('HEALTH:', resp.status, resp.read().decode())
except Exception as e:
    print('HEALTH ERR:', repr(e)[:150])

# 测速 3 次取平均
def bench(label):
    url = f'http://{HOST}:{PORT}/v1/chat/completions'
    body = json.dumps({"model": "D:\\models\\ornith-1.0-35b-Q4_K_M.gguf",
                       "messages": [{"role": "user", "content": "Write a Python function for quicksort. Code only."}],
                       "max_tokens": 300, "temperature": 0.6}).encode()
    req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=300) as resp:
        json.load(resp)
    time.sleep(2)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username='<LAPTOP_USER>', password='<REDACTED>', timeout=15, look_for_keys=False, allow_agent=False)
    try:
        i, o, e = ssh.exec_command(
            'cmd /c powershell -NoProfile -Command "Select-String -Path D:\\llama_old\\server.log -Pattern \'eval time\' | Select-Object -Last 1 | ForEach-Object {$_.Line}"',
            timeout=30)
        line = o.read().decode('utf-8', errors='replace')
        print(f'{label}: {line.strip()}')
    finally:
        ssh.close()

for k in range(3):
    bench(f'run{k+1}')
