# -*- coding: utf-8 -*-
"""从 -lv 6 日志提取层分配统计 + offload 决策行"""
import json, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

path = r'<PROJECT_DIR>\<SESSION_ID>\tool-results\mcp-desktop-commander-start_process-1786193536738.txt'
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)
text = data[0]['text']
lines = text.splitlines()

assign = [l for l in lines if 'assigned to device' in l]
cpu = sum(1 for l in assign if 'device CPU' in l)
cuda = sum(1 for l in assign if 'CUDA' in l)
other = [l for l in assign if 'device CPU' not in l and 'CUDA' not in l]
print(f'layer assigned lines: {len(assign)} | CPU: {cpu} | CUDA: {cuda} | other: {len(other)}')
for l in other[:10]:
    print('  OTHER:', l)

print()
print('=== DECISION / OFFLOAD LINES ===')
seen = set()
for l in lines:
    low = l.lower()
    if 'assigned to device' in low:
        continue
    if any(k in low for k in ['prepare_model', 'n_gpu_layers', 'gpu_layers', 'repeating layers',
                               'not offload', 'cannot offload', 'unsupported', 'no cuda', 'cuda not',
                               'offload', 'buffer type', 'op_offload', 'resolve_fused', 'fused',
                               'moexpert', 'moefused', 'ssm', 'force']):
        if l not in seen:
            seen.add(l)
            print(l)
