-- Migration 011: 添加 append_sub_requirement_progress RPC 函数（原子追加 progress）
-- 解决多 agent 并发写入 progress 互相覆盖的问题
-- 使用方式：SELECT append_sub_requirement_progress('sub_requirement_uuid', '{"agent":"bee","action":"生图完成","at":"2026-04-01T12:00:00Z"}'::jsonb);

CREATE OR REPLACE FUNCTION append_sub_requirement_progress(
  sub_req_id UUID,
  entry JSONB
) RETURNS VOID AS $$
  UPDATE sub_requirement
  SET 
    progress = progress || entry::jsonb,
    updated_at = NOW()
  WHERE id = sub_req_id;
$$ LANGUAGE SQL;

-- 验证函数存在
-- SELECT append_sub_requirement_progress('test_uuid', '{"test":1}'::jsonb);
