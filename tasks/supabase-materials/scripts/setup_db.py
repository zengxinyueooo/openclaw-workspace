#!/usr/bin/env python3
import sys
from pathlib import Path

SQL = """
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS materials (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  image_url TEXT NOT NULL,
  storage_path TEXT,
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
  score INTEGER DEFAULT 0,
  face_ratio REAL,
  sharpness REAL,
  resolution TEXT,
  source_note_id TEXT,
  source_keyword TEXT,
  batch_id TEXT,
  tags TEXT[] DEFAULT '{}',
  style TEXT,
  mood TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  reviewed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_materials_status ON materials(status);
CREATE INDEX IF NOT EXISTS idx_materials_score ON materials(score DESC);
CREATE INDEX IF NOT EXISTS idx_materials_created ON materials(created_at DESC);

ALTER TABLE materials ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow all for anon" ON materials;
CREATE POLICY "Allow all for anon" ON materials FOR ALL USING (true) WITH CHECK (true);

CREATE TABLE IF NOT EXISTS batches (
  id TEXT PRIMARY KEY,
  keyword  TEXT,
  total_collected INTEGER DEFAULT 0,
  total_passed INTEGER DEFAULT 0,
  total_uploaded INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE batches ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow all for anon" ON batches;
CREATE POLICY "Allow all for anon" ON batches FOR ALL USING (true) WITH CHECK (true);
"""


def load_env(env_path: Path) -> dict:
    data = {}
    if not env_path.exists():
        raise FileNotFoundError(f"Missing env file: {env_path}")
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip()
    return data


def main() -> int:
    env_path = Path(__file__).resolve().parents[3] / ".env.supabase"
    env = load_env(env_path)

    required = [
        "SUPABASE_DB_HOST",
        "SUPABASE_DB_PORT",
        "SUPABASE_DB_USER",
        "SUPABASE_DB_PASSWORD",
        "SUPABASE_DB_NAME",
    ]
    missing = [k for k in required if k not in env]
    if missing:
        print(f"Missing keys in .env.supabase: {', '.join(missing)}", file=sys.stderr)
        return 1

    try:
        import psycopg2
    except Exception as exc:
        print("psycopg2 is required to run this script.")
        print("Install with: pip install psycopg2-binary")
        print(f"Import error: {exc}")
        return 1

    conn = psycopg2.connect(
        host=env["SUPABASE_DB_HOST"],
        port=int(env["SUPABASE_DB_PORT"]),
        user=env["SUPABASE_DB_USER"],
        password=env["SUPABASE_DB_PASSWORD"],
        dbname=env["SUPABASE_DB_NAME"],
        sslmode="require",
    )

    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(SQL)
        print("Database setup complete.")
    finally:
        conn.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
