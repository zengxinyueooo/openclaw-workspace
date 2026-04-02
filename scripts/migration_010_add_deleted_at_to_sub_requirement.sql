-- =============================================
-- migration_010: sub_requirement 表加 deleted_at 字段
-- 2026-03-25
-- 用于软删除：审核页删除时打时间戳，不物理删除
-- 已删除的子需求子蜜蜂可查询到，会优雅退出
-- =============================================

ALTER TABLE sub_requirement
  ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;

COMMENT ON COLUMN sub_requirement.deleted_at IS '软删除标记，删除时写入当前时间；有值的记录视为已废弃';
