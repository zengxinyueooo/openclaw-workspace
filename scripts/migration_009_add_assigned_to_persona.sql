-- =============================================
-- migration_009: materials 表加 assigned_to_persona 字段
-- 2026-03-25
-- 用于锁定某张素材被分配给了哪个 persona，避免同一张图重复分配给多个人设
-- =============================================

ALTER TABLE materials
  ADD COLUMN IF NOT EXISTS assigned_to_persona TEXT;

COMMENT ON COLUMN materials.assigned_to_persona IS '锁定分配给的 persona 名称，分配后不可再分配给其他人设';

-- 已有数据的兼容性：used_by 里有值的说明已使用，设为 used_by[1]
UPDATE materials
SET assigned_to_persona = used_by[1]
WHERE used_by IS NOT NULL
  AND array_length(used_by, 1) > 0
  AND assigned_to_persona IS NULL;
