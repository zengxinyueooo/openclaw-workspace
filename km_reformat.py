#!/usr/bin/env python3
"""
学城文档格式化脚本：
1. 给 H2 大标题加"一、二、三…"序号
2. 给 H3 小标题加"（一）（二）…"序号（按章节重置）
3. 在 Session 章节末尾补充 Sub-agent/Cron Session 生命周期内容
"""
import json
import time
import urllib.request
import websocket

CHINESE_NUM = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十',
               '十一', '十二', '十三', '十四', '十五']
CHINESE_SUB = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十',
               '十一', '十二', '十三', '十四', '十五']

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
    print("❌ 找不到 KM 页面")
    exit(1)

ws = websocket.create_connection(ws_url, timeout=60)
print("✅ 已连接到 KM 页面")

# 确保处于编辑模式
result = eval_js(ws, """
JSON.stringify({
  isEditing: document.querySelectorAll('[contenteditable="true"]').length > 0
})
""", msg_id=1)
state = json.loads(result.get('result', {}).get('result', {}).get('value', '{}'))
if not state.get('isEditing'):
    print("点击编辑按钮...")
    eval_js(ws, """
    (function() {
        const btn = document.querySelector('.doc-mode-switch-item.edit');
        if (btn) btn.click();
    })()
    """, msg_id=2)
    time.sleep(2)

print("✅ 处于编辑模式")

# ============================================================
# Step 1: 格式化所有标题
# ============================================================
# 定义标题映射：原始文本 -> 新文本
# H2 大标题（按顺序）
h2_titles = [
    "安装配置",
    "常用命令",
    "踩坑点",
    "架构",
    "Tool",
    "文件分类",
    "一些命令",
    "Session",
    "Memory",
    "Context Window 管理",
    "四、总结：一张图看懂",
    "定期清理",
    "多agent",
    "宠物科普skill",
]

# H2 新标题（加序号，跳过已有序号的）
h2_new = [
    "一、安装配置",
    "二、常用命令",
    "三、踩坑点",
    "四、架构",
    "五、Tool",
    "六、文件分类",
    "七、一些命令",
    "八、Session",
    "九、Memory",
    "十、Context Window 管理",
    "十一、总结：一张图看懂",
    "十二、定期清理",
    "十三、多 Agent",
    "十四、宠物科普 Skill",
]

# H3 小标题映射（原文 -> 新文本）
h3_map = {
    "引擎拆解：Pi Agent": "（一）引擎拆解：Pi Agent",
    'OpenClaw的"平台化"增强': '（二）OpenClaw 的"平台化"增强',
    "对比Claude code": "（三）对比 Claude Code",
    '📋 核心工具列表（System Prompt 中的 "Tooling")': '（一）📋 核心工具列表（System Prompt 中的 "Tooling"）',
    "Session 的生命周期与重置": "（一）Session 的生命周期与重置",
    "Session 的几种类型": "（二）Session 的几种类型",
    "新会话时加载什么": "（三）新会话时加载什么",
    "1. Memory 的存储位置": "（一）Memory 的存储位置",
    "2. Memory 的加载时机": "（二）Memory 的加载时机",
    "3. Memory Search（语义搜索）": "（三）Memory Search（语义搜索）",
    "定期清理": "（一）定期清理",
}

# H4 小标题映射
h4_map = {
    "1. Session Pruning（修剪）": "（一）Session Pruning（修剪）",
    "2. Compaction（压缩）": "（二）Compaction（压缩）",
    "3. Memory Flush（记忆刷新）": "（三）Memory Flush（记忆刷新）",
}

# 构造完整映射（escape 用于 JS）
all_renames = {}
for old, new in zip(h2_titles, h2_new):
    all_renames[old] = new
all_renames.update(h3_map)
all_renames.update(h4_map)

print(f"\n📝 准备重命名 {len(all_renames)} 个标题...")

# 用 JS 批量修改标题文本
# 学城富文本编辑器中，标题内容在 <h2>/<h3> 的 innerText 里
# 需要修改其文本节点，而不是 innerHTML（避免破坏格式）
rename_js = f"""
(function() {{
    const renames = {json.dumps(all_renames, ensure_ascii=False)};
    let changed = 0;
    let errors = [];
    
    document.querySelectorAll('h1,h2,h3,h4,h5').forEach(h => {{
        const text = h.textContent.trim();
        // 精确匹配
        if (renames[text] !== undefined) {{
            // 找到第一个文本节点并修改
            const walker = document.createTreeWalker(h, NodeFilter.SHOW_TEXT);
            let node = walker.nextNode();
            if (node) {{
                // 清空所有子节点，直接设文本
                h.textContent = renames[text];
                changed++;
            }} else {{
                errors.push('no text node: ' + text);
            }}
        }}
    }});
    
    return JSON.stringify({{changed, errors}});
}})()
"""

result = eval_js(ws, rename_js, msg_id=10)
rename_result = json.loads(result.get('result', {}).get('result', {}).get('value', '{}'))
print(f"✅ 标题重命名完成: {rename_result}")

time.sleep(1)

# ============================================================
# Step 2: 在「八、Session」章节末尾插入新内容
# ============================================================
print("\n📝 Step 2: 在 Session 章节末尾插入新内容...")

new_content_js = """
(function() {
    // 找到 Session 章节
    const allHeadings = Array.from(document.querySelectorAll('h1,h2,h3,h4,h5'));
    let sessionH2 = null;
    let nextH2 = null;
    
    for (let i = 0; i < allHeadings.length; i++) {
        const h = allHeadings[i];
        if (h.tagName === 'H2' && h.textContent.includes('Session')) {
            sessionH2 = h;
            // 找下一个 H2
            for (let j = i + 1; j < allHeadings.length; j++) {
                if (allHeadings[j].tagName === 'H2') {
                    nextH2 = allHeadings[j];
                    break;
                }
            }
            break;
        }
    }
    
    if (!sessionH2) return JSON.stringify({error: 'Session H2 not found'});
    
    // 检查是否已经有「Session 生命周期详解」
    const existing = Array.from(document.querySelectorAll('h3')).find(
        h => h.textContent.includes('生命周期详解') || h.textContent.includes('Sub-agent Session')
    );
    if (existing) return JSON.stringify({skip: 'already exists'});
    
    // 在 nextH2 前面（即 Session 章节末尾）插入新内容
    // 学城是富文本，通过 document.execCommand 或直接 DOM 操作
    const insertBefore = nextH2;
    const parent = insertBefore ? insertBefore.parentNode : sessionH2.parentNode;
    
    // 创建新的 H3 标题
    function insertH3(text, beforeNode) {
        const h3 = document.createElement('h3');
        h3.textContent = text;
        beforeNode ? parent.insertBefore(h3, beforeNode) : parent.appendChild(h3);
        return h3;
    }
    
    function insertP(text, beforeNode) {
        const p = document.createElement('p');
        p.textContent = text;
        beforeNode ? parent.insertBefore(p, beforeNode) : parent.appendChild(p);
        return p;
    }
    
    const ref = insertBefore;
    
    // （四）Sub-agent Session 与 Cron Session 的生命周期
    const h3_4 = insertH3('（四）Sub-agent Session 与 Cron Session 的生命周期', ref);
    insertP('理解 Session 的生命周期，是避免数据丢失、任务失败的关键。', ref);
    
    // Sub-agent Session
    const h4_sub = document.createElement('h4');
    h4_sub.textContent = '1. Sub-agent Session';
    parent.insertBefore(h4_sub, ref);
    
    insertP('默认模式（mode="run"）：任务完成后自动关闭，不能再对话；历史记录默认保留（cleanup="keep"），可用 sessions_history 查看；关闭后无法再发消息。', ref);
    insertP('持久模式（mode="session" 或 thread: true）：任务完成后不自动关闭，可以继续 sessions_send 追加指令；适合 ACP 编码 Agent（CatPaw、Claude Code）长期开发任务；需手动 subagents(action="kill") 结束。', ref);
    insertP('cleanup="delete" 模式：任务完成后立即删除所有记录，连历史都查不到；一般不推荐，除非处理敏感数据。', ref);
    
    // Cron Session
    const h4_cron = document.createElement('h4');
    h4_cron.textContent = '2. Cron Session';
    parent.insertBefore(h4_cron, ref);
    
    insertP('执行完毕后自动关闭，历史记录有保留，可通过 sessions_list 找到并用 sessions_history 查看；不能继续对话（Cron Session 没有绑定 channel，没有接收消息的入口）；下次 Cron 触发时是全新的 Session，和上次完全独立。', ref);
    
    // 对比表说明
    const h4_compare = document.createElement('h4');
    h4_compare.textContent = '3. 对比总结';
    parent.insertBefore(h4_compare, ref);
    
    insertP('Sub-agent (run)：任务完成自动关闭 ✅，可继续对话 ❌，历史记录保留 ✅，下次复用 Session ❌', ref);
    insertP('Sub-agent (session)：任务完成自动关闭 ❌，可继续对话 ✅，历史记录保留 ✅，下次复用 Session ❌', ref);
    insertP('Cron：任务完成自动关闭 ✅，可继续对话 ❌，历史记录保留 ✅，下次复用 Session ❌（永远新建）', ref);
    
    // 关键原则
    const h4_key = document.createElement('h4');
    h4_key.textContent = '4. 关键原则';
    parent.insertBefore(h4_key, ref);
    
    insertP('⚠️ Cron 和 run 模式的子 Agent，成果必须写入文件！Session 关闭后，脑内思考消失，只有写到 memory/*.md 或其他文件里的内容才是真正持久化的。这也是每次 Cron 任务执行完都要把结果写进 MEMORY.md 的原因。', ref);
    
    return JSON.stringify({success: true, inserted: 'Session lifecycle section'});
})()
"""

result = eval_js(ws, new_content_js, msg_id=20)
insert_result = json.loads(result.get('result', {}).get('result', {}).get('value', '{}'))
print(f"✅ 内容插入结果: {insert_result}")

time.sleep(1)

# ============================================================
# Step 3: 触发自动保存
# ============================================================
print("\n💾 Step 3: 触发自动保存...")
save_js = """
(function() {
    // 触发 input 事件让编辑器感知到变化，触发自动保存
    const editor = document.querySelector('[contenteditable="true"]');
    if (editor) {
        editor.dispatchEvent(new Event('input', {bubbles: true}));
        editor.dispatchEvent(new Event('keyup', {bubbles: true}));
        // 模拟 Ctrl+S
        const event = new KeyboardEvent('keydown', {
            key: 's', code: 'KeyS', ctrlKey: true, bubbles: true
        });
        editor.dispatchEvent(event);
        return 'triggered save events';
    }
    return 'no editor found';
})()
"""
result = eval_js(ws, save_js, msg_id=30)
print(f"保存触发: {result.get('result', {}).get('result', {}).get('value')}")

time.sleep(3)

# Step 4: 截图验证
print("\n📸 截图验证...")
import base64
cmd = {"id": 40, "method": "Page.captureScreenshot", "params": {"format": "png"}}
ws.send(json.dumps(cmd))
while True:
    resp = json.loads(ws.recv())
    if resp.get('id') == 40:
        img_data = base64.b64decode(resp['result']['data'])
        with open('/root/.openclaw/workspace/km_after.png', 'wb') as f:
            f.write(img_data)
        print(f"✅ 截图已保存: km_after.png ({len(img_data)} bytes)")
        break

ws.close()
print("\n🎉 全部完成！")
