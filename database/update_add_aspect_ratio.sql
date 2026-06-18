-- ============================================
-- 添加 aspect_ratio 字段到 model_price_configs 和 generation_tasks 表
-- ============================================

-- 1. model_price_configs 表添加 aspect_ratio 字段
ALTER TABLE model_price_configs
ADD COLUMN aspect_ratio VARCHAR(16) DEFAULT NULL COMMENT '宽高比，例如 1:1, 16:9, 9:16' AFTER image_count;

-- 2. generation_tasks 表添加 aspect_ratio 字段
ALTER TABLE generation_tasks
ADD COLUMN aspect_ratio VARCHAR(16) DEFAULT NULL COMMENT '宽高比' AFTER image_count;


ALTER TABLE model_configs DROP INDEX uk_model_provider;
ALTER TABLE model_configs
ADD UNIQUE KEY uk_model_provider_capability (model_key, provider_key, capability_type);


ALTER TABLE model_price_configs DROP INDEX uk_model_price;
ALTER TABLE model_price_configs
ADD UNIQUE KEY uk_model_price (
    model_id,
    image_size,
    image_count,
    aspect_ratio,
    video_duration,
    video_resolution
);