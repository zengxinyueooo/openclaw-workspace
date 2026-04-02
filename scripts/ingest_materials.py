#!/usr/bin/env python3
"""
本地素材入库脚本
1. 上传图片获取URL
2. AI打标签
3. 写入Supabase
"""
import os
import sys
import json
import subprocess
import time
import re
from datetime import datetime
from supabase import create_client

# 配置
SUPABASE_URL = os.environ['SUPABASE_URL']
SUPABASE_KEY = os.environ['SUPABASE_ANON_KEY']
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_KEY', SUPABASE_KEY)
ZHIPU_API_KEY = os.environ.get('ZHIPU_API_KEY', '')

def upload_image(image_path):
    """使用美团内网服务上传图片"""
    cmd = [
        'curl', '-s', '--location', '--request', 'POST',
        'https://mdz.dzu.test.sankuai.com/api/dzusergrowth/assistant/image/gen/upload',
        '--header', 'swimlane: 3792-tsgru',
        '--form', f'file=@{image_path}'
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        resp = json.loads(result.stdout)
        if resp.get('code') == 200:
            return resp['data']
    except:
        pass
    return None

TAGGING_PROMPT = """用JSON描述这张图片的风格。格式：{"tags":[],"style":"","mood":"","score":0}
tags从[甜妹,纯欲,清冷,韩系,日系,复古,文艺,街拍,氛围感,自拍,写真,户外,室内,特写,全身,半身]选3-5个。
style从[甜妹,纯欲,清冷,韩系,日系,复古,文艺,性感]选1个最匹配的。
mood从[清新,温暖,冷调,梦幻,自然,都市]选1个。
score是颜值吸引力+质量0-100分。只返回JSON，不要markdown代码块。"""

FALLBACK_RESULT = {'tags': [], 'style': '', 'mood': '', 'score': 50}

def ai_tag_image(image_url):
    """使用智谱 GLM-4V-Flash 分析图片打标签"""
    if not ZHIPU_API_KEY:
        return FALLBACK_RESULT.copy()

    payload = {
        "model": "glm-4v-flash",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": image_url}},
                {"type": "text", "text": TAGGING_PROMPT}
            ]
        }],
        "max_tokens": 200,
        "temperature": 0.3
    }

    try:
        result = subprocess.run(
            ['curl', '-s', '--max-time', '15',
             'https://open.bigmodel.cn/api/paas/v4/chat/completions',
             '-H', 'Content-Type: application/json',
             '-H', f'Authorization: Bearer {ZHIPU_API_KEY}',
             '-d', json.dumps(payload, ensure_ascii=False)],
            capture_output=True, text=True
        )
        resp = json.loads(result.stdout)
        content = resp['choices'][0]['message']['content']
        # 去掉可能的 markdown 代码块
        content = re.sub(r'```json\s*', '', content)
        content = re.sub(r'```\s*', '', content)
        content = content.strip()
        parsed = json.loads(content)
        # 校验字段
        tags = parsed.get('tags', [])[:5]
        style = parsed.get('style', '')
        mood = parsed.get('mood', '')
        score = min(100, max(0, int(parsed.get('score', 50))))
        return {'tags': tags, 'style': style, 'mood': mood, 'score': score}
    except Exception as e:
        print(f"  ⚠️ AI打标签失败: {e}")
        return FALLBACK_RESULT.copy()

def ingest_material(image_path, category='face', context_type='general', 
                    context_id=None, context_name=None, status='pending'):
    """入库单张素材"""
    client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
    # 1. 上传图片
    print(f"  上传: {os.path.basename(image_path)}")
    image_url = upload_image(image_path)
    if not image_url:
        print(f"  ❌ 上传失败")
        return None
    print(f"  ✅ URL: {image_url[:60]}...")
    
    # 2. AI打标签
    ai_result = ai_tag_image(image_url)
    print(f"  🏷️ {ai_result['tags']} style={ai_result['style']} mood={ai_result['mood']} score={ai_result['score']}")
    
    # 3. 写入数据库
    batch_id = f"manual_{datetime.now().strftime('%Y%m%d')}"
    data = {
        'image_url': image_url,
        'storage_path': image_url.split('/')[-1],  # 简化存储路径
        'category': category,
        'context_type': context_type,
        'context_id': context_id,
        'context_name': context_name,
        'status': status,
        'batch_id': batch_id,
        'tags': ai_result['tags'],
        'style': ai_result['style'],
        'mood': ai_result['mood'],
        'score': ai_result['score'],
        'source_note_id': None,
        'source_keyword': 'manual_import',
    }
    
    result = client.table('materials').insert(data).execute()
    if result.data:
        print(f"  ✅ 入库成功: {result.data[0]['id'][:8]}...")
        return result.data[0]
    else:
        print(f"  ❌ 入库失败")
        return None

def register_batch(batch_id, keyword='', total_collected=0, total_passed=0, total_uploaded=0):
    """在 batches 表注册批次，已存在则更新 total_uploaded"""
    client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    # upsert: 存在则更新，不存在则插入
    data = {
        'id': batch_id,
        'keyword': keyword,
        'total_collected': total_collected,
        'total_passed': total_passed,
        'total_uploaded': total_uploaded,
    }
    try:
        client.table('batches').upsert(data, on_conflict='id').execute()
        print(f"📋 批次已注册: {batch_id} (uploaded={total_uploaded})")
    except Exception as e:
        print(f"⚠️ 批次注册失败: {e}")


def batch_ingest(directory, category='face', status='pending', limit=None):
    """批量入库目录下的图片"""
    image_files = []
    for ext in ['*.jpg', '*.png', '*.jpeg']:
        import glob
        image_files.extend(glob.glob(os.path.join(directory, ext)))
    
    image_files.sort()
    if limit:
        image_files = image_files[:limit]
    
    print(f"\n📦 批量入库: {directory}")
    print(f"   发现 {len(image_files)} 张图片")
    print(f"   Category: {category}, Status: {status}")
    print("=" * 60)
    
    success = 0
    for i, img_path in enumerate(image_files, 1):
        print(f"\n[{i}/{len(image_files)}]")
        result = ingest_material(
            img_path, 
            category=category,
            status=status
        )
        if result:
            success += 1
    
    print(f"\n{'=' * 60}")
    print(f"✅ 完成: {success}/{len(image_files)} 张入库成功")

    # 自动注册批次到 batches 表（审核页依赖此表展示列表）
    if success > 0:
        batch_id = f"manual_{datetime.now().strftime('%Y%m%d')}"
        register_batch(
            batch_id=batch_id,
            keyword=os.path.basename(directory),
            total_collected=len(image_files),
            total_passed=len(image_files),
            total_uploaded=success,
        )

    return success

if __name__ == '__main__':
    import glob
    
    if len(sys.argv) < 2:
        print("Usage: python ingest_materials.py <directory> [category] [status] [limit]")
        print("Example: python ingest_materials.py ./shared/content-assets/face/approved face approved 10")
        sys.exit(1)
    
    directory = sys.argv[1]
    category = sys.argv[2] if len(sys.argv) > 2 else 'face'
    status = sys.argv[3] if len(sys.argv) > 3 else 'pending'
    limit = int(sys.argv[4]) if len(sys.argv) > 4 else None
    
    batch_ingest(directory, category, status, limit)
