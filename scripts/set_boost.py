# -*- coding: utf-8 -*-
"""尝试开启 Intel Turbo Boost：查 boost mode -> 设 Aggressive -> 重读 MaxClockSpeed + 满载采样"""
import sys, time, json, urllib.request, threading
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

HOST = '<LAPTOP_IP>'
PORT = 8080
BOOST_GUID = '3b04d4fd-1cc7-4f23-ab1c-d1337819c4e2'  # 处理器性能提升模式

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username='<LAPTOP_USER>', password='<REDACTED>', timeout=15, look_for_keys=False, allow_agent=False)
try:
    def run(c):
        i, o, e = ssh.exec_command(c, timeout=30)
        return o.read().decode('gbk', errors='replace')

    print('=== BEFORE boost settings (SUB_PROCESSOR around boost GUID) ===')
    out = run(f'powercfg /q SCHEME_CURRENT SUB_PROCESSOR')
    # 打印包含 boost GUID 附近的行
    lines = out.splitlines()
    for i, ln in enumerate(lines):
        if '3b04d4fd' in ln:
            for j in range(max(0, i-1), min(len(lines), i+8)):
                print(lines[j])
            break
    print('MaxClockSpeed:', run('wmic cpu get MaxClockSpeed /value').strip())

    # 设 Aggressive (2) 交流+直流
    print('=== SET boost mode aggressive ===')
    print(run(f'powercfg /setacvalueindex SCHEME_CURRENT SUB_PROCESSOR {BOOST_GUID} 2').strip() or '(ok ac)')
    print(run(f'powercfg /setdcvalueindex SCHEME_CURRENT SUB_PROCESSOR {BOOST_GUID} 2').strip() or '(ok dc)')
    print(run('powercfg /setactive SCHEME_CURRENT').strip() or '(ok active)')
    time.sleep(2)
    print('=== AFTER MaxClockSpeed ===')
    print(run('wmic cpu get MaxClockSpeed /value').strip())
    print(run('wmic cpu get CurrentClockSpeed /value').strip())
finally:
    ssh.close()

# 满载采样
freqs = []
def poll():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username='<LAPTOP_USER>', password='<REDACTED>', timeout=15, look_for_keys=False, allow_agent=False)
    try:
        for _ in range(15):
            i, o, e = ssh.exec_command('wmic cpu get CurrentClockSpeed /value', timeout=10)
            out = o.read().decode('utf-8', errors='replace')
            for line in out.splitlines():
                if 'CurrentClockSpeed' in line:
                    try:
                        freqs.append(int(line.split('=')[1].strip()))
                    except Exception:
                        pass
            time.sleep(0.5)
    finally:
        ssh.close()

def bench():
    url = f'http://{HOST}:{PORT}/v1/chat/completions'
    body = json.dumps({"model": "D:\\models\\ornith-1.0-35b-Q4_K_M.gguf",
                       "messages": [{"role": "user", "content": "Write a Python function for quicksort. Code only."}],
                       "max_tokens": 400, "temperature": 0.6}).encode()
    req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=300) as resp:
        json.load(resp)

th = threading.Thread(target=poll)
th.start()
bench()
th.join()
print('=== CPU freq during load ===')
print('samples:', len(freqs), 'min:', min(freqs) if freqs else 'n/a', 'max:', max(freqs) if freqs else 'n/a')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username='<LAPTOP_USER>', password='<REDACTED>', timeout=15, look_for_keys=False, allow_agent=False)
try:
    i, o, e = ssh.exec_command(
        'cmd /c powershell -NoProfile -Command "Select-String -Path D:\\llama_old\\server.log -Pattern \'eval time\' | Select-Object -Last 1 | ForEach-Object {$_.Line}"',
        timeout=30)
    print('--- latest eval ---')
    print(o.read().decode('utf-8', errors='replace'))
finally:
    ssh.close()
