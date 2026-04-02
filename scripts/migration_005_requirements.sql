-- =============================================
-- 需求表 & 子需求表
-- 2026-03-18 v2
-- =============================================

-- 需求表：记录运营需求
CREATE TABLE IF NOT EXISTS requirement (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  scene_type TEXT NOT NULL CHECK (scene_type IN ('常态化运营', 'BigDay活动运营', '新店运营', '其他')),
  description TEXT NOT NULL,              -- 原始需求描述
  start_time TIMESTAMPTZ,                 -- 需求开始时间
  end_time TIMESTAMPTZ,                   -- 需求结束时间
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'success')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 子需求表：需求拆分后的单账号任务
CREATE TABLE IF NOT EXISTS sub_requirement (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  requirement_id UUID NOT NULL REFERENCES requirements(id) ON DELETE CASCADE,
  account_id INTEGER NOT NULL,            -- 账号 ID（shared/accounts 里的数字 id，如 13, 17）
  persona_name TEXT NOT NULL,             -- 账号名（冗余，方便查看）
  content_description TEXT NOT NULL,      -- 发布什么内容，如「常态化颜值运营」
  draft_id UUID,                          -- 关联 note_drafts.id（蜜蜂生成笔记后回填）
  material_ids UUID[],                    -- 关联使用的素材 id 列表（松鼠采集的素材）
  job_id TEXT,                            -- 蚂蚁发布后回填的 gui_agent_job_id
  progress JSONB DEFAULT '[]'::jsonb,     -- 进展记录，爪爪全局视角写入各 agent 执行动态
  -- 格式: [{"agent":"eagle","action":"拆分子需求","at":"2026-03-18T05:00:00Z"},
  --        {"agent":"bee","action":"生成笔记","at":"..."},
  --        {"agent":"pipi","action":"审核通过","at":"..."},
  --        {"agent":"ant","action":"创建资产","at":"..."},
  --        {"agent":"ant","action":"发布成功","at":"..."}]
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'success')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_requirements_status ON requirements(status);
CREATE INDEX IF NOT EXISTS idx_requirements_scene_type ON requirements(scene_type);
CREATE INDEX IF NOT EXISTS idx_sub_requirements_requirement_id ON sub_requirements(requirement_id);
CREATE INDEX IF NOT EXISTS idx_sub_requirements_status ON sub_requirements(status);
CREATE INDEX IF NOT EXISTS idx_sub_requirements_account_id ON sub_requirements(account_id);

-- RLS 策略（允许 anon key 读写）
ALTER TABLE requirements ENABLE ROW LEVEL SECURITY;
ALTER TABLE sub_requirements ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow all for requirements" ON requirements FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for sub_requirements" ON sub_requirements FOR ALL USING (true) WITH CHECK (true);

-- 授权
GRANT ALL ON requirements TO anon, authenticated;
GRANT ALL ON sub_requirements TO anon, authenticated;
