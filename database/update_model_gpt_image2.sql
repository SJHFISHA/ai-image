-- 更新模型价格配置为 gpt-image-2
-- 先删除旧的配置
DELETE FROM model_price_configs;

-- 插入新的 gpt-image-2 配置
INSERT INTO model_price_configs (model_key, model_name, capability_type, image_size, image_count, points, cost_amount, sort_order)
VALUES
    ('gpt-image-2', 'GPT Image 2', 'image', '1024x1024', 1, 100, 0.400000, 1),
    ('gpt-image-2', 'GPT Image 2', 'image', '1536x1024', 1, 120, 0.500000, 2),
    ('gpt-image-2', 'GPT Image 2', 'image', '1024x1536', 1, 120, 0.500000, 3);
