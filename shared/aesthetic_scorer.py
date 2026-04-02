#!/usr/bin/env python3
"""AI 美感评分 - 使用智谱 GLM-4V-Flash"""

import os
import json
import subprocess
from supabase import create_client

SUPABASE_URL = os.environ['SUPABASE_URL']
SUPABASE_KEY = os.environ['SUPABASE_SERVICE_KEY']
ZHIPU_API_KEY = os.environ.get('ZHIPU_API_KEY', '')

SCORE_PROMPT = """对这张图片的美感和吸引力进行评分。
格式：{"score": 85, "reason": "光线自然，构图优秀，氛围感强"}
score: 0-100 的综合吸引力分，考虑颜值、光线、构图、质感。
reason: 简要说明得分理由，10字以内。
只返回JSON，不要markdown代码块。"""

def score_image(image_url):
    """调用 GLM-4V 打分"""
    if not ZHIPU_API_KEY:
        return 50, "no_api_key"
    
    payload = {
        "model": "glm-4v-flash",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": image_url}},
                {"type": "text", "text": SCORE_PROMPT}
            ]
        }],
        "max_tokens": 100,
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
        # 清理 markdown
        content = content.replace('```json', '').replace('```', '').strip()
        parsed = json.loads(content)
        return int(parsed.get('score', 50)), parsed.get('reason', '')
    except Exception as e:
        print(f"  ⚠️ 打分失败: {e}")
        return 50, "error"

def score_task(task_id):
    """对任务中所有通过人脸验证的图片打分"""
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # 获取通过人脸验证的图片
    images = client.table('generated_images').select('*').eq('task_id', task_id).eq('face_passed', True).execute()
    
    if not images.data:
        print("❌ 没有通过人脸验证的图片")
        return
    
    print(f"🎨 开始为 {len(images.data)} 张图片打美感分...")
    
    for img in images.data:
        score, reason = score_image(img['image_url'])
        client.table('generated_images').update({
            'aesthetic_score': score,
            'aesthetic_reason': reason
        }).eq('id', img['id']).execute()
        print(f"  {img['id'][:8]}: score={score} ({reason})")
    
    # 更新任务状态为完成
    client.table('generation_tasks').update({'status': 'done'}).eq('id', task_id).execute()
    print("✅ 评分完成")

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python aesthetic_scorer.py <task_id>")
        sys.exit(1)
    score_task(sys.argv[1])
