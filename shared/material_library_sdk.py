"""
蜜蜂素材召回 SDK
"""
import os
from supabase import create_client, Client
from typing import List, Dict, Optional


class MaterialLibrary:
    def __init__(self, url: str = None, key: str = None):
        self.url = url or os.environ.get('SUPABASE_URL')
        self.key = key or os.environ.get('SUPABASE_SERVICE_KEY') or os.environ.get('SUPABASE_ANON_KEY')
        self.client: Client = create_client(self.url, self.key)
    
    def recall(
        self,
        category: str,
        account_id: str,
        context_type: str = 'general',
        context_id: Optional[str] = None,
        style_tags: List[str] = None,
        limit: int = 9
    ) -> List[Dict]:
        """召回素材"""
        style_tags = style_tags or []
        
        query = (
            self.client.table('materials')
            .select('id,image_url,category,tags,style,score,used_count')
            .eq('status', 'approved')
            .eq('category', category)
            .eq('context_type', context_type)
            .not_.contains('used_by', [account_id])
            .order('used_count', desc=False)
            .order('score', desc=True)
            .limit(limit * 3)
        )
        
        if context_id:
            query = query.eq('context_id', context_id)
        else:
            query = query.is_('context_id', 'null')
        
        response = query.execute()
        materials = response.data or []
        
        if style_tags:
            materials = self._sort_by_tags(materials, style_tags)
        
        return materials[:limit]
    
    def _sort_by_tags(self, materials: List[Dict], target_tags: List[str]) -> List[Dict]:
        def score(m):
            m_tags = set(m.get('tags') or [])
            matches = len(m_tags & set(target_tags))
            return (-matches, m.get('used_count', 0), -(m.get('score') or 0))
        return sorted(materials, key=score)
    
    def mark_used(self, material_id: str, account_id: str):
        """标记已使用"""
        resp = self.client.table('materials').select('used_by').eq('id', material_id).single().execute()
        if not resp.data:
            return False
        
        used_by = resp.data.get('used_by', []) or []
        if account_id in used_by:
            return True
        
        used_by.append(account_id)
        self.client.table('materials').update({
            'used_count': len(used_by),
            'last_used_at': 'now()',
            'used_by': used_by
        }).eq('id', material_id).execute()
        return True


# 示例
if __name__ == '__main__':
    lib = MaterialLibrary()
    
    # 常态化: 甜妹账号要 face 素材
    faces = lib.recall(
        category='face',
        account_id='account_xhs_001',
        style_tags=['甜妹', '清新']
    )
    print(f"召回 {len(faces)} 张 face 素材")
    
    # 门店探店: 朝阳大悦城店需要 scene 素材
    scenes = lib.recall(
        category='scene',
        account_id='account_xhs_002',
        context_type='store',
        context_id='store_cdyuecheng'
    )
    print(f"召回 {len(scenes)} 张场景素材")
