# -*- coding: utf-8 -*-
"""测速同时抓 CPU 满载频率，确认睿频/降频"""
import sys, time, json, urllib.request, threading
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

HOST = '<LAPTOP_IP>'
PORT = 8080
freqs = []

def poll_freq():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username='<LAPTOP_USER>', password='<REDACTED>', timeout=15, look_for_keys=False, allow_agent=False)
    try:
        for _ in range(20):
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
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=300) as resp:
        json.load(resp)
    print(f'REQ took {time.time()-t0:.1f}s')

th = threading.Thread(target=poll_freq)
th.start()
bench()
th.join()

print('--- CPU freq during load ---')
print('samples:', len(freqs))
print('min:', min(freqs), 'max:', max(freqs), 'avg:', sum(freqs)//max(1,len(freqs)))

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
