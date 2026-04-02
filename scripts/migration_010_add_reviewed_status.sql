-- migration_010: 添加 reviewed 状态到 sub_requirement
-- 生图审核页人审完成后需要标记为 reviewed，然后从列表隐藏

-- 先删除旧约束，再添加新约束（包含 reviewed）
ALTER TABLE sub_requirement 
  DROP CONSTRAINT IF EXISTS sub_requirement_status_check,
  ADD CONSTRAINT sub_requirement_status_check 
  CHECK (status IN ('pending', 'reviewed', 'success'));
