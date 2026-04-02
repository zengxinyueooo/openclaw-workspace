-- Migration 002: AI Review Pipeline
-- generated_images + generation_tasks + note_drafts + reviewers

-- 1. 生成任务追踪
CREATE TABLE IF NOT EXISTS generation_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    persona_name TEXT NOT NULL,
    requested_count INT DEFAULT 8,
    generated_count INT DEFAULT 0,
    face_passed_count INT DEFAULT 0,
    retry_count INT DEFAULT 0,
    max_retries INT DEFAULT 3,
    status TEXT DEFAULT 'generating' CHECK (status IN ('generating','verifying','scoring','done','failed')),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- 2. 生成图片记录
CREATE TABLE IF NOT EXISTS generated_images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    persona_name TEXT NOT NULL,
    task_id UUID REFERENCES generation_tasks(id),
    batch_id TEXT,
    image_url TEXT NOT NULL,
    local_path TEXT,
    face_distance FLOAT,
    face_passed BOOLEAN DEFAULT false,
    aesthetic_score FLOAT,
    aesthetic_reason TEXT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending','selected','rejected')),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_generated_images_persona ON generated_images(persona_name);
CREATE INDEX IF NOT EXISTS idx_generated_images_task ON generated_images(task_id);
CREATE INDEX IF NOT EXISTS idx_generated_images_status ON generated_images(status);

-- 3. 笔记草稿
CREATE TABLE IF NOT EXISTS note_drafts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    persona_name TEXT NOT NULL,
    account_id TEXT,
    candidate_titles TEXT[],
    title TEXT,
    candidate_contents TEXT[],
    content TEXT,
    candidate_tags TEXT[],
    tags TEXT[],
    image_ids UUID[],
    cover_image_id UUID,
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft','content_ready','pending_review','approved','published')),
    scheduled_at TIMESTAMPTZ,
    published_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_note_drafts_persona ON note_drafts(persona_name);
CREATE INDEX IF NOT EXISTS idx_note_drafts_status ON note_drafts(status);

-- 4. 审核人员
CREATE TABLE IF NOT EXISTS reviewers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    auth_code TEXT NOT NULL,
    role TEXT DEFAULT 'reviewer' CHECK (role IN ('admin','reviewer')),
    permissions TEXT[] DEFAULT ARRAY['material_review','image_select','draft_review'],
    persona_scope TEXT[],
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 5. 插入默认管理员
INSERT INTO reviewers (name, auth_code, role, permissions)
VALUES ('皮皮', 'pipi2026', 'admin', ARRAY['material_review','image_select','draft_review','publish'])
ON CONFLICT (name) DO NOTHING;

