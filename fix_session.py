#!/usr/bin/env python3
# OpenClaw 会话修复工具
# 用法:
# curl -fsSL <url>/fix_session.py | python3 # 扫描并修复
# curl -fsSL <url>/fix_session.py | python3 - --scan # 仅扫描
import json
import os
import shutil
import sys
from pathlib import Path

D = '/root/.openclaw/agents/main/sessions'
T = 4  # ← 改这里，原来是 16

def _chk(t):
    s = t.strip()
    return (s.startswith('[') or s.startswith('{')) and t.count('```') >= T

def _fix(t):
    return t.replace('```', '`\u200b`\u200b`')

def _proc(fp, dr=False):
    with open(fp, 'r') as f:
        lines = f.readlines()
    n = 0
    fixed = 0
    out = []
    for line in lines:
        try:
            d = json.loads(line.strip())
        except:
            out.append(line.rstrip('\n'))
            continue
        if d.get('type') == 'message' and 'message' in d and d['message'].get('role') == 'toolResult':
            c = d['message'].get('content', [])
            if isinstance(c, list):
                for b in c:
                    if b.get('type') == 'text' and _chk(b['text']):
                        n += 1
                        if not dr:
                            b['text'] = _fix(b['text'])
                            fixed += 1
        out.append(json.dumps(d, ensure_ascii=False))
    if fixed > 0:
        bk = fp + '.bak'
        if not os.path.exists(bk):
            shutil.copy2(fp, bk)
        with open(fp, 'w') as f:
            f.write('\n'.join(out) + '\n')
    return n, fixed

def main():
    dr = '--scan' in sys.argv
    p = Path(D)
    if not p.exists():
        print(f'[错误] 目录不存在: {D}')
        sys.exit(1)
    fs = sorted(p.glob('*.jsonl'))
    print(f'正在扫描 {len(fs)} 个会话...\n')
    ti = 0
    tf = 0
    pf = 0
    for f in fs:
        i, x = _proc(str(f), dr=dr)
        if i > 0:
            pf += 1
            ti += i
            tf += x
            st = '(仅扫描)' if dr else '已修复'
            print(f' [!] {f.name}: 需要修复 - {st}')
    print(f'\n{"="*40}')
    print(f'会话总数: {len(fs)}')
    print(f'存在问题: {pf} 个')
    if dr:
        print(f'\n当前为扫描模式，去掉 --scan 参数执行修复')
    elif tf > 0:
        print(f'已修复: {tf} 处')
    if ti == 0:
        print('\n✅ 所有会话状态正常')

if __name__ == '__main__':
    main()
