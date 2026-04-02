-- =============================================
-- migration_006: note_drafts 关联 sub_requirement
-- 2026-03-19
-- =============================================

-- note_drafts 加 sub_requirement_id 字段
ALTER TABLE note_drafts
  ADD COLUMN IF NOT EXISTS sub_requirement_id UUID REFERENCES sub_requirement(id);

-- 索引：方便按 sub_requirement_id 查草稿
CREATE INDEX IF NOT EXISTS idx_note_drafts_sub_requirement_id
  ON note_drafts(sub_requirement_id)
  WHERE sub_requirement_id IS NOT NULL;

-- 修复 migration_005 的表名不一致（如果之前用了 requirements/sub_requirements 复数名）
-- 如果报错说表不存在，忽略即可
