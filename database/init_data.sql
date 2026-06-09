-- ============================================
-- AI创作平台初始数据
-- ============================================

-- ============================================
-- 充值套餐示例数据
-- ============================================
INSERT INTO recharge_packages (package_name, amount, base_points, bonus_points, total_points, sort_order)
VALUES
    ('10元套餐', 10.00, 1000, 0, 1000, 1),
    ('50元套餐', 50.00, 5000, 500, 5500, 2),
    ('100元套餐', 100.00, 10000, 2000, 12000, 3),
    ('500元套餐', 500.00, 50000, 15000, 65000, 4);


-- ============================================
-- 图片模型价格配置示例数据
-- ============================================
INSERT INTO model_price_configs (model_key, model_name, capability_type, image_size, image_count, points, cost_amount, sort_order)
VALUES
    ('gpt-image-2', 'GPT Image 2', 'image', '1024x1024', 1, 100, 0.400000, 1),
    ('gpt-image-2', 'GPT Image 2', 'image', '1536x1024', 1, 120, 0.500000, 2),
    ('gpt-image-2', 'GPT Image 2', 'image', '1024x1536', 1, 120, 0.500000, 3);


-- ============================================
-- 后台管理员初始账号（密码: admin123）
-- 注意：password_hash 需要在应用中生成，这里只是示例
-- ============================================
-- INSERT INTO admin_users (username, password_hash, nickname, role)
-- VALUES ('admin', '$2b$12$xxx', '超级管理员', 'super_admin');
