#!/usr/bin/env python3
"""
素材上传脚本模板（v2 版）
支持自动打上 category 和 context
"""
import os
import sys
from supabase import create_client
from datetime import datetime

# ============ 配置区域 ============
# 素材类型: face / nail / outfit / scene / food / product
CATEGORY = "face"

# 归属类型: general / store / campaign
CONTEXT_TYPE = "general"

# 归属ID（如果是 store/campaign）
CONTEXT_ID = None  # 例如: "store_cdyuecheng" 或 "campaign_feb_bath"
CONTEXT_NAME = None  # 例如: "朝阳大悦城店" 或 "2月洗浴bigday"

# 批次ID
BATCH_ID = f"batch_{datetime.now().strftime('%H%M')}"

# ===================================

def upload_materials(image_paths: list, category: str = "face",
                     context_type: str = "general", context_id: str = None,
                     context_name: str = None):
    """
    上传素材到 Supabase
    
    Args:
        image_paths: 本地图片路径列表
        category: 素材类型 (face/nail/outfit/scene/food)
        context_type: 归属类型 (general/store/campaign)
        context_id: 归属ID
        context_name: 归属名称
    """
    url = os.environ['SUPABASE_URL']
    key = os.environ['SUPABASE_SERVICE_KEY']
    client = create_client(url, key)
    
    uploaded = []
    
    for img_path in image_paths:
        filename = os.path.basename(img_path)
        storage_path = f"{BATCH_ID}/{filename}"
        
        # 1. 上传文件到 Storage
        with open(img_path, 'rb') as f:
            client.storage.from_('materials').upload(storage_path, f)
        
        # 2. 获取公网URL
        image_url = client.storage.from_('materials').get_public_url(storage_path)
        
        # 3. 写入数据库（带上 category 和 context）
        data = {
            'image_url': image_url,
            'storage_path': storage_path,
            'category': category,
            'context_type': context_type,
            'context_id': context_id,
            'context_name': context_name,
            'status': 'pending',
            'batch_id': BATCH_ID,
            'score': 0,  # 预筛时计算
            # ... 其他字段
        }
        
        result = client.table('materials').insert(data).execute()
        uploaded.append(result.data[0]['id'])
    
    print(f"✅ 上传完成: {len(uploaded)} 张")
    print(f"   Category: {category}")
    print(f"   Context: {context_type} / {context_id or 'general'}")
    return uploaded


if __name__ == '__main__':
    # 示例用法
    if len(sys.argv) < 2:
        print("Usage: python upload_materials.py <image_dir>")
        sys.exit(1)
    
    image_dir = sys.argv[1]
    images = [os.path.join(image_dir, f) for f in os.listdir(image_dir)
              if f.endswith(('.jpg', '.png'))]
    
    upload_materials(
        images,
        category=CATEGORY,
        context_type=CONTEXT_TYPE,
        context_id=CONTEXT_ID,
        context_name=CONTEXT_NAME
    )
