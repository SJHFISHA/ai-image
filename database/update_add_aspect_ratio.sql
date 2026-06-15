-- ============================================
-- 添加 aspect_ratio 字段到 model_price_configs 和 generation_tasks 表
-- ============================================

-- 1. model_price_configs 表添加 aspect_ratio 字段
ALTER TABLE model_price_configs
ADD COLUMN aspect_ratio VARCHAR(16) DEFAULT NULL COMMENT '宽高比，例如 1:1, 16:9, 9:16' AFTER image_count;

-- 2. generation_tasks 表添加 aspect_ratio 字段
ALTER TABLE generation_tasks
ADD COLUMN aspect_ratio VARCHAR(16) DEFAULT NULL COMMENT '宽高比' AFTER image_count;