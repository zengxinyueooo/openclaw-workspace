-- ============================================
-- Migration: Ralph Loop tasks 表创建
-- ============================================

CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT,
    agent TEXT NOT NULL CHECK (agent IN ('eagle', 'squirrel', 'bee', 'ant', 'main')),
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'done', 'failed', 'blocked')),
    priority INTEGER DEFAULT 3 CHECK (priority >= 1 AND priority <= 5),
    source TEXT DEFAULT 'self' CHECK (source IN ('pipi', 'zhuazhua', 'self') OR source LIKE 'agent:%'),
    source_message TEXT,
    parent_task_id UUID REFERENCES tasks(id),
    created_at TIMESTAMPTZ DEFAULT now(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    result TEXT,
    error TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    metadata JSONB DEFAULT '{}'
);

-- 索引
CREATE INDEX idx_tasks_agent_status ON tasks (agent, status);
CREATE INDEX idx_tasks_priority ON tasks (priority ASC);
CREATE INDEX idx_tasks_created_at ON tasks (created_at DESC);
CREATE INDEX idx_tasks_parent ON tasks (parent_task_id);

-- 注释
COMMENT ON TABLE tasks IS 'Ralph Loop 任务队列';
COMMENT ON COLUMN tasks.agent IS '负责执行的 Agent: eagle/squirrel/bee/ant/main';
COMMENT ON COLUMN tasks.status IS '任务状态: pending/running/done/failed/blocked';
COMMENT ON COLUMN tasks.source IS '任务来源: pipi(皮皮直达)/zhuazhua(爪爪拆解)/self(自产生)/agent:xxx(其他Agent委派)';
