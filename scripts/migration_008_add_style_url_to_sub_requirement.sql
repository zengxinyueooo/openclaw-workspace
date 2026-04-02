-- =============================================
-- migration_008: sub_requirement 加 style_url 字段
-- 2026-03-20
-- 用于锁定子需求的风格参考图，避免多波蜜蜂选不同素材
-- =============================================

ALTER TABLE sub_requirement
  ADD COLUMN IF NOT EXISTS style_url TEXT;

COMMENT ON COLUMN sub_requirement.style_url IS '锁定的风格参考图URL，父蜜蜂首次分配后写入，后续生图必须使用此URL';
