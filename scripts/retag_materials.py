#!/usr/bin/env python3
"""批量用AI重新打标签（覆盖假数据）"""
import os, json, subprocess, re, time
from supabase import create_client

ZHIPU_KEY = os.environ['ZHIPU_API_KEY']
client = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_ANON_KEY'])

PROMPT = 'JSON描述图片风格：{"tags":[],"style":"","mood":"","score":0}。tags从[甜妹,纯欲,清冷,韩系,日系,复古,文艺,街拍,氛围感,自拍,写真,户外,室内,特写,全身,半身]选3-5个。style从[甜妹,纯欲,清冷,韩系,日系,复古,文艺,性感]选1。mood从[清新,温暖,冷调,梦幻,自然,都市]选1。score是颜值+质量0-100。只返回JSON不要代码块。'

def tag_one(url):
    payload = {"model":"glm-4v-flash","messages":[{"role":"user","content":[
        {"type":"image_url","image_url":{"url":url}},
        {"type":"text","text":PROMPT}
    ]}],"max_tokens":200,"temperature":0.3}
    r = subprocess.run(['curl','-s','--max-time','15',
        'https://open.bigmodel.cn/api/paas/v4/chat/completions',
        '-H','Content-Type: application/json',
        '-H',f'Authorization: Bearer {ZHIPU_KEY}',
        '-d',json.dumps(payload,ensure_ascii=False)],
        capture_output=True,text=True)
    resp = json.loads(r.stdout)
    c = resp['choices'][0]['message']['content']
    c = re.sub(r'```json\s*','',c)
    c = re.sub(r'```\s*','',c).strip()
    p = json.loads(c)
    return {
        'tags': p.get('tags',[])[:5],
        'style': p.get('style',''),
        'mood': p.get('mood',''),
        'score': min(100,max(0,int(p.get('score',50))))
    }

# 取所有 manual_import 的（假标签数据）
resp = client.table('materials').select('id,image_url').eq('source_keyword','manual_import').execute()
items = resp.data or []
print(f"需要重新打标: {len(items)} 张")

ok = 0
fail = 0
for i, m in enumerate(items, 1):
    try:
        result = tag_one(m['image_url'])
        client.table('materials').update({
            'tags': result['tags'],
            'style': result['style'],
            'mood': result['mood'],
            'score': result['score']
        }).eq('id', m['id']).execute()
        ok += 1
        print(f"[{i}/{len(items)}] {result['tags']} s={result['score']} ✅")
    except Exception as e:
        fail += 1
        print(f"[{i}/{len(items)}] ❌ {e}")
    if i % 14 == 0:
        time.sleep(1)

print(f"\n完成: {ok} 成功 / {fail} 失败")
