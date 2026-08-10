# -*- coding: utf-8 -*-
"""给 laptop 防火墙加 8080 入站规则，测试端口 + API 健康检查"""
import sys, time, socket, urllib.request, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import paramiko

HOST = '<LAPTOP_IP>'
PORT = 8080

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username='<LAPTOP_USER>', password='<REDACTED>',
            timeout=15, look_for_keys=False, allow_agent=False)
try:
    stdin, stdout, stderr = ssh.exec_command(
        'netsh advfirewall firewall add rule name="llama-server-8080" dir=in action=allow protocol=TCP localport=8080',
        timeout=30)
    print('FW:', stdout.read().decode('utf-8', errors='replace'))
    err = stderr.read().decode('utf-8', errors='replace')
    if err.strip():
        print('FW ERR:', err[:300])

    # 确认规则
    stdin, stdout, stderr = ssh.exec_command(
        'netsh advfirewall firewall show rule name="llama-server-8080"', timeout=30)
    fw = stdout.read().decode('utf-8', errors='replace')
    print('--- FW RULE ---')
    print(fw[:400])
finally:
    ssh.close()

# 本机测端口
s = socket.socket()
s.settimeout(5)
r = s.connect_ex((HOST, PORT))
s.close()
print('PORT CONNECT:', 'OPEN' if r == 0 else f'CLOSED({r})')

# 本机测 API（等几秒让防火墙生效）
time.sleep(2)
try:
    req = urllib.request.Request(f'http://{HOST}:{PORT}/health', headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as resp:
        print('HEALTH:', resp.status, resp.read().decode())
except Exception as e:
    print('HEALTH ERR:', repr(e)[:300])
try:
    req = urllib.request.Request(f'http://{HOST}:{PORT}/v1/models', headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as resp:
        print('MODELS:', resp.status, resp.read().decode()[:500])
except Exception as e:
    print('MODELS ERR:', repr(e)[:300])
