-- 素材库升级 Migration
-- 执行方式: Supabase Dashboard -> SQL Editor -> New query -> 粘贴执行

-- ============================================
-- 1. 给 materials 表添加新字段
-- ============================================

ALTER TABLE materials 
ADD COLUMN IF NOT EXISTS category text,
ADD COLUMN IF NOT EXISTS context_type text DEFAULT 'general',
ADD COLUMN IF NOT EXISTS context_id text,
ADD COLUMN IF NOT EXISTS context_name text,
ADD COLUMN IF NOT EXISTS used_count integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_used_at timestamptz,
ADD COLUMN IF NOT EXISTS used_by text[] DEFAULT '{}';

-- 给 category 添加约束（可选，推荐）
-- ALTER TABLE materials ADD CONSTRAINT chk_category 
-- CHECK (category IN ('face', 'nail', 'nail-face', 'outfit', 'scene', 'food', 'product'));

-- ============================================
-- 2. 创建 contexts 表（门店/活动管理）
-- ============================================

CREATE TABLE IF NOT EXISTS contexts (
    id text PRIMARY KEY,
    type text NOT NULL CHECK (type IN ('store', 'campaign')),
    name text NOT NULL,
    status text DEFAULT 'active' CHECK (status IN ('active', 'archived')),
    metadata jsonb DEFAULT '{}',
    created_at timestamptz DEFAULT now()
);

-- 启用 RLS
ALTER TABLE contexts ENABLE ROW LEVEL SECURITY;

-- 创建公开读取策略
CREATE POLICY "Allow public read contexts"
    ON contexts FOR SELECT
    USING (true);

-- ============================================
-- 3. 创建 available_materials 视图（干净素材池）
-- ============================================

DROP VIEW IF EXISTS available_materials;

CREATE VIEW available_materials AS
SELECT 
    id,
    image_url,
    storage_path,
    category,
    context_type,
    context_id,
    context_name,
    tags,
    style,
    mood,
    score,
    face_ratio,
    sharpness,
    resolution,
    used_count,
    last_used_at,
    used_by,
    source_note_id,
    source_keyword,
    batch_id,
    created_at,
    reviewed_at
FROM materials
WHERE status = 'approved'
  AND category IS NOT NULL
ORDER BY used_count ASC, score DESC;

-- ============================================
-- 4. 创建索引加速查询
-- ============================================

CREATE INDEX IF NOT EXISTS idx_materials_category ON materials(category);
CREATE INDEX IF NOT EXISTS idx_materials_status ON materials(status);
CREATE INDEX IF NOT EXISTS idx_materials_context ON materials(context_type, context_id);
CREATE INDEX IF NOT EXISTS idx_materials_used ON materials(used_count);
CREATE INDEX IF NOT EXISTS idx_materials_tags ON materials USING GIN(tags);

-- ============================================
-- 5. 迁移现有数据
-- ============================================

-- batch_1139 是颜值采集，补标为 face
UPDATE materials 
SET category = 'face' 
WHERE category IS NULL AND batch_id = 'batch_1139';

-- ============================================
-- 6. 创建常用查询函数（可选）
-- ============================================

-- 蜜蜂召回素材的函数
CREATE OR REPLACE FUNCTION get_materials_for_bee(
    p_category text,
    p_context_type text DEFAULT 'general',
    p_context_id text DEFAULT NULL,
    p_account_id text DEFAULT NULL,
    p_style_tags text[] DEFAULT '{}',
    p_limit integer DEFAULT 9
)
RETURNS TABLE (
    id uuid,
    image_url text,
    category text,
    tags text[],
    style text,
    score integer,
    used_count integer
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        m.id,
        m.image_url,
        m.category,
        m.tags,
        m.style,
        m.score,
        m.used_count
    FROM materials m
    WHERE m.status = 'approved'
      AND m.category = p_category
      AND m.context_type = p_context_type
      AND (p_context_id IS NULL OR m.context_id = p_context_id)
      AND (p_account_id IS NULL OR NOT (p_account_id = ANY(m.used_by)))
    ORDER BY 
        CASE WHEN p_style_tags && m.tags THEN 1 ELSE 0 END DESC,
        m.used_count ASC,
        m.score DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 7. 标记素材已使用的函数
-- ============================================

CREATE OR REPLACE FUNCTION mark_material_used(
    p_material_id uuid,
    p_account_id text
)
RETURNS void AS $$
BEGIN
    UPDATE materials
    SET 
        used_count = used_count + 1,
        last_used_at = now(),
        used_by = array_append(used_by, p_account_id)
    WHERE id = p_material_id
      AND NOT (p_account_id = ANY(used_by));
END;
$$ LANGUAGE plpgsql;