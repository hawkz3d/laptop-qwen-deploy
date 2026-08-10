# -*- coding: utf-8 -*-
"""诊断睿频：CPU 型号/MaxClockSpeed + 电源计划处理器设置 + 满载时 %Processor Performance + 电池状态"""
import sys, time, json, urllib.request, threading
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

HOST = '<LAPTOP_IP>'
PORT = 8080

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username='<LAPTOP_USER>', password='<REDACTED>', timeout=15, look_for_keys=False, allow_agent=False)
try:
    def run(c):
        i, o, e = ssh.exec_command(c, timeout=30)
        return o.read().decode('utf-8', errors='replace')

    print('=== CPU ===')
    print(run('wmic cpu get Name,MaxClockSpeed,CurrentClockSpeed,NumberofCores,NumberofLogicalProcessors /value'))
    print('=== POWER SUB_PROCESSOR ===')
    print(run('powercfg /q SCHEME_CURRENT SUB_PROCESSOR')[:3000])
    print('=== BATTERY ===')
    print(run('WMIC Path Win32_Battery Get BatteryStatus,EstimatedChargeRemaining /value'))
finally:
    ssh.close()

# 满载时采样 % Processor Performance
pct = []
def poll():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username='<LAPTOP_USER>', password='<REDACTED>', timeout=15, look_for_keys=False, allow_agent=False)
    try:
        for _ in range(15):
            i, o, e = ssh.exec_command(
                'powershell -NoProfile -Command "(Get-Counter \'\\\\Processor Information(_Total)\\\\% Processor Performance\' -ErrorAction SilentlyContinue).CounterSamples[0].CookedValue"',
                timeout=10)
            out = o.read().decode('utf-8', errors='replace').strip()
            try:
                pct.append(float(out.splitlines()[-1].strip()))
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
print('=== % Processor Performance during load (100=base, >100=turbo) ===')
print('samples:', len(pct), 'max:', max(pct) if pct else 'n/a', 'avg:', (sum(pct)//len(pct)) if pct else 'n/a')
