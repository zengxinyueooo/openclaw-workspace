#!/usr/bin/env python3
"""人脸一致性验证 - 使用 DeepFace/ArcFace"""

import os
import sys
import json
import requests
from pathlib import Path
from deepface import DeepFace
from supabase import create_client

# 配置
SUPABASE_URL = os.environ['SUPABASE_URL']
SUPABASE_KEY = os.environ['SUPABASE_SERVICE_KEY']
PERSONAS_DIR = Path("/Users/lipengyu/.openclaw/workspace/shared/personas")

# 阈值
FACE_THRESHOLD = 0.4  # cosine distance < 0.4 视为同一人
MIN_PASS_COUNT = 4   # 最少通过4张

def verify_face(ref_path, gen_path):
    """验证两张图的人脸一致性"""
    try:
        result = DeepFace.verify(
            img1_path=str(ref_path),
            img2_path=str(gen_path),
            model_name="ArcFace",
            distance_metric="cosine",
            enforce_detection=True
        )
        distance = result["distance"]
        return distance < FACE_THRESHOLD, distance
    except:
        return False, 1.0

def verify_task(task_id):
    """对任务的所有图片做人脸验证"""
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # 获取任务
    task = client.table('generation_tasks').select('*').eq('id', task_id).single().execute()
    if not task.data:
        print(f"❌ Task not found: {task_id}")
        return 0
    
    persona_name = task.data['persona_name']
    
    # 加载人设参考图URL
    ref_profile = PERSONAS_DIR / persona_name / "profile.json"
    with open(ref_profile) as f:
        profile = json.load(f)
    portrait_url = profile["persona"]["visual"]["portraitReference"]
    
    # 下载参考图
    ref_tmp = Path("/tmp/persona_ref.jpg")
    r = requests.get(portrait_url, timeout=30)
    ref_tmp.write_bytes(r.content)
    
    # 获取该任务的所有图片
    images = client.table('generated_images').select('*').eq('task_id', task_id).execute()
    
    passed = 0
    for img in images.data:
        gen_tmp = Path(f"/tmp/gen_{img['id'][:8]}.jpg")
        try:
            r = requests.get(img['image_url'], timeout=30)
            gen_tmp.write_bytes(r.content)
            
            is_pass, dist = verify_face(ref_tmp, gen_tmp)
            
            client.table('generated_images').update({
                'face_passed': is_pass,
                'face_distance': dist,
                'status': 'pending' if is_pass else 'rejected'
            }).eq('id', img['id']).execute()
            
            if is_pass:
                passed += 1
                print(f"  ✅ {img['id'][:8]} dist={dist:.3f}")
            else:
                print(f"  ❌ {img['id'][:8]} dist={dist:.3f}")
        except Exception as e:
            print(f"  ⚠️ {img['id'][:8]} error: {e}")
        finally:
            gen_tmp.unlink(missing_ok=True)
    
    # 更新任务状态
    status = 'scoring' if passed >= MIN_PASS_COUNT else 'failed'
    client.table('generation_tasks').update({
        'face_passed_count': passed,
        'status': status
    }).eq('id', task_id).execute()
    
    ref_tmp.unlink(missing_ok=True)
    print(f"\n总结: {passed}/{len(images.data)} 张通过人脸验证")
    return passed

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python face_verifier.py <task_id>")
        sys.exit(1)
    verify_task(sys.argv[1])
