-- Migration 004: Add original_url column to generated_images
-- 用于存储生成图片的原始API返回URL（在上传Venus之前的URL）
-- 执行方式：Supabase Dashboard → SQL Editor → 粘贴执行

ALTER TABLE generated_images ADD COLUMN IF NOT EXISTS original_url TEXT;
ALTER TABLE generated_images ADD COLUMN IF NOT EXISTS scene TEXT;

COMMENT ON COLUMN generated_images.original_url IS '生成API返回的原始图片URL（Venus上传前）';
COMMENT ON COLUMN generated_images.scene IS '生成场景名称（如咖啡店、街拍等）';
