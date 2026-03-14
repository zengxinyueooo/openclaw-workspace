#!/usr/bin/env python3
"""
通过 CDP 编辑学城文档
"""
import json
import time
import urllib.request
import websocket

def get_cdp_url():
    tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json/list", timeout=5).read())
    for t in tabs:
        if t.get('type') == 'page' and 'km.sankuai.com' in t.get('url', ''):
            return t['webSocketDebuggerUrl']
    return None

def eval_js(ws, js, msg_id=1):
    cmd = {"id": msg_id, "method": "Runtime.evaluate", "params": {
        "expression": js, "returnByValue": True, "awaitPromise": True
    }}
    ws.send(json.dumps(cmd))
    while True:
        resp = json.loads(ws.recv())
        if resp.get('id') == msg_id:
            return resp

ws_url = get_cdp_url()
if not ws_url:
    print("❌ 找不到浏览器 tab")
    exit(1)

print(f"✅ 连接到 KM 页面")
ws = websocket.create_connection(ws_url, timeout=60)

# 检查页面 & 编辑状态
result = eval_js(ws, """
JSON.stringify({
  url: location.href,
  editBtn: !!document.querySelector('.doc-mode-switch-item.edit'),
  isEditing: document.querySelectorAll('[contenteditable="true"]').length,
  hasEditor: !!document.querySelector('.ct-editor-content')
})
""", msg_id=1)
state = json.loads(result.get('result', {}).get('result', {}).get('value', '{}'))
print("页面状态:", state)

# 点击编辑按钮
if not state.get('isEditing'):
    print("点击编辑按钮...")
    result = eval_js(ws, """
    (function() {
        const btn = document.querySelector('.doc-mode-switch-item.edit');
        if (btn) { btn.click(); return 'ok'; }
        const all = Array.from(document.querySelectorAll('*'));
        const eb = all.find(e => e.textContent.trim() === '编辑' && e.offsetParent);
        if (eb) { eb.click(); return 'clicked by text'; }
        return 'not found';
    })()
    """, msg_id=2)
    print("编辑按钮:", result.get('result', {}).get('result', {}).get('value'))
    time.sleep(2)

# 获取标题结构
result = eval_js(ws, """
JSON.stringify(
  Array.from(document.querySelectorAll('h1,h2,h3,h4,h5')).map(h => ({
    tag: h.tagName, text: h.textContent.trim().substring(0,100)
  }))
)
""", msg_id=3)
headings = json.loads(result.get('result', {}).get('result', {}).get('value', '[]'))
print(f"\n找到 {len(headings)} 个标题:")
for h in headings:
    print(f"  {h['tag']}: {h['text']}")

# 检查编辑器
result = eval_js(ws, """
JSON.stringify({
  editable: document.querySelectorAll('[contenteditable="true"]').length,
  editorSelector: '.ct-editor-content',
  hasEditor: !!document.querySelector('.ct-editor-content')
})
""", msg_id=4)
print("\n编辑器状态:", result.get('result', {}).get('result', {}).get('value'))

ws.close()
