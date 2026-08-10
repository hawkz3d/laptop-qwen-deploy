# -*- coding: utf-8 -*-
"""查当前服务上下文长度（/props 端点）"""
import sys, json, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HOST = '<LAPTOP_IP>'
PORT = 8080
try:
    req = urllib.request.Request(f'http://{HOST}:{PORT}/props', headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.load(resp)
    dgs = data.get('default_generation_settings', {})
    print('model_path:', data.get('model_path'))
    print('n_ctx (context size):', dgs.get('n_ctx'))
    print('n_parallel (slots):', dgs.get('n_parallel'))
    print('total slots:', data.get('total_slots'))
    print('--- all props keys ---')
    print(json.dumps({k: v for k, v in data.items() if k != 'default_generation_settings'}, ensure_ascii=False, indent=1)[:800])
except Exception as e:
    print('ERR:', repr(e)[:200])
