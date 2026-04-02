-- Migration 007: Add sub_requirement_id to generated_images
-- Purpose: 关联生成图与子需求，支持精确去重

ALTER TABLE generated_images
ADD COLUMN IF NOT EXISTS sub_requirement_id UUID REFERENCES sub_requirement(id);

-- 索引：按子需求查图 + 审核状态过滤
CREATE INDEX IF NOT EXISTS idx_generated_images_sub_req_id
ON generated_images(sub_requirement_id)
WHERE sub_requirement_id IS NOT NULL;

COMMENT ON COLUMN generated_images.sub_requirement_id IS '关联的子需求ID，手动派活的生图为NULL';
