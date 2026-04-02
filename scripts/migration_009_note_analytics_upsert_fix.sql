-- migration_009: Fix note_analytics upsert
-- Problem: Prefer: resolution=merge-duplicates requires a UNIQUE constraint
-- on the conflict columns. Without it, PostgREST can't do proper upsert.
--
-- Solution: Add UNIQUE constraint on (persona_name, note_title) so that
-- same note re-collected will UPDATE existing row instead of being silently ignored.

-- First, check for any duplicates and keep only the latest
DELETE FROM note_analytics a
USING note_analytics b
WHERE a.persona_name = b.persona_name
  AND a.note_title = b.note_title
  AND a.collected_at < b.collected_at;

-- Add unique constraint
ALTER TABLE note_analytics
  ADD CONSTRAINT note_analytics_persona_title_unique
  UNIQUE (persona_name, note_title);
