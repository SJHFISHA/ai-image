-- ============================================
-- AI创作平台数据库建表脚本
-- ============================================

-- 创建数据库（如果不存在）
-- CREATE DATABASE IF NOT EXISTS ai_creation_platform DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- USE ai_creation_platform;

-- ============================================
-- 1. 用户表
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,

    username VARCHAR(64) DEFAULT NULL COMMENT '用户名',
    email VARCHAR(128) DEFAULT NULL COMMENT '邮箱',
    phone VARCHAR(32) DEFAULT NULL COMMENT '手机号',

    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',

    nickname VARCHAR(64) DEFAULT NULL COMMENT '昵称',
    avatar_url VARCHAR(255) DEFAULT NULL COMMENT '头像',

    status VARCHAR(32) NOT NULL DEFAULT 'normal' COMMENT '状态: normal, disabled',

    last_login_at DATETIME DEFAULT NULL COMMENT '最后登录时间',
    last_login_ip VARCHAR(64) DEFAULT NULL COMMENT '最后登录IP',

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    UNIQUE KEY uk_username (username),
    UNIQUE KEY uk_email (email),
    UNIQUE KEY uk_phone (phone),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';


-- ============================================
-- 2. 用户积分账户表
-- ============================================
CREATE TABLE IF NOT EXISTS user_point_accounts (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL UNIQUE COMMENT '用户ID',

    balance_points BIGINT NOT NULL DEFAULT 0 COMMENT '可用积分',
    frozen_points BIGINT NOT NULL DEFAULT 0 COMMENT '冻结积分',

    total_recharged_points BIGINT NOT NULL DEFAULT 0 COMMENT '累计充值积分',
    total_consumed_points BIGINT NOT NULL DEFAULT 0 COMMENT '累计消费积分',

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户积分账户表';


-- ============================================
-- 3. 积分流水表
-- ============================================
CREATE TABLE IF NOT EXISTS point_transactions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,

    transaction_no VARCHAR(64) NOT NULL UNIQUE COMMENT '积分流水号',
    user_id BIGINT NOT NULL COMMENT '用户ID',

    type VARCHAR(32) NOT NULL COMMENT '类型: recharge, freeze, consume, refund, unfreeze, admin_adjust',
    direction VARCHAR(16) NOT NULL COMMENT '方向: income, expense, freeze, unfreeze',

    points BIGINT NOT NULL COMMENT '变动积分',

    balance_before BIGINT NOT NULL COMMENT '变动前可用积分',
    balance_after BIGINT NOT NULL COMMENT '变动后可用积分',

    frozen_before BIGINT NOT NULL DEFAULT 0 COMMENT '变动前冻结积分',
    frozen_after BIGINT NOT NULL DEFAULT 0 COMMENT '变动后冻结积分',

    related_order_no VARCHAR(64) DEFAULT NULL COMMENT '关联充值订单号',
    related_task_id VARCHAR(64) DEFAULT NULL COMMENT '关联生成任务ID',

    remark VARCHAR(255) DEFAULT NULL COMMENT '备注',

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    INDEX idx_user_id_created_at (user_id, created_at),
    INDEX idx_related_order_no (related_order_no),
    INDEX idx_related_task_id (related_task_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='积分流水表';


-- ============================================
-- 4. 充值套餐表
-- ============================================
CREATE TABLE IF NOT EXISTS recharge_packages (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,

    package_name VARCHAR(64) NOT NULL COMMENT '套餐名称',

    amount DECIMAL(10,2) NOT NULL COMMENT '充值金额',
    base_points BIGINT NOT NULL COMMENT '基础积分',
    bonus_points BIGINT NOT NULL DEFAULT 0 COMMENT '赠送积分',
    total_points BIGINT NOT NULL COMMENT '总积分',

    enabled TINYINT NOT NULL DEFAULT 1 COMMENT '是否启用: 1=启用, 0=禁用',
    sort_order INT NOT NULL DEFAULT 0 COMMENT '排序',

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='充值套餐表';


-- ============================================
-- 5. 充值订单表
-- ============================================
CREATE TABLE IF NOT EXISTS recharge_orders (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,

    order_no VARCHAR(64) NOT NULL UNIQUE COMMENT '充值订单号',
    user_id BIGINT NOT NULL COMMENT '用户ID',

    package_id BIGINT NOT NULL COMMENT '充值套餐ID',
    package_name VARCHAR(64) NOT NULL COMMENT '套餐名称',

    amount DECIMAL(10,2) NOT NULL COMMENT '支付金额',
    currency VARCHAR(16) NOT NULL DEFAULT 'CNY' COMMENT '货币类型',

    base_points BIGINT NOT NULL COMMENT '基础积分',
    bonus_points BIGINT NOT NULL DEFAULT 0 COMMENT '赠送积分',
    total_points BIGINT NOT NULL COMMENT '总到账积分',

    pay_channel VARCHAR(32) DEFAULT NULL COMMENT '支付渠道: alipay, wechat, stripe',
    pay_status VARCHAR(32) NOT NULL DEFAULT 'pending' COMMENT '支付状态: pending, paid, failed, closed, refunded',

    pay_trade_no VARCHAR(128) DEFAULT NULL COMMENT '第三方支付流水号',

    paid_at DATETIME DEFAULT NULL COMMENT '支付成功时间',

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    INDEX idx_user_id_created_at (user_id, created_at),
    INDEX idx_pay_status (pay_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='充值订单表';


-- ============================================
-- 6. 模型价格配置表
-- ============================================
CREATE TABLE IF NOT EXISTS model_price_configs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,

    model_key VARCHAR(128) NOT NULL COMMENT '模型标识',
    model_name VARCHAR(128) NOT NULL COMMENT '前端展示名称',

    capability_type VARCHAR(32) NOT NULL COMMENT '能力类型: image, video, text, audio',

    provider_key VARCHAR(64) NOT NULL DEFAULT 'api_gateway' COMMENT '供应商/中转站标识',

    billing_mode VARCHAR(32) NOT NULL DEFAULT 'fixed' COMMENT '计费方式: fixed',

    image_size VARCHAR(32) DEFAULT NULL COMMENT '图片尺寸，例如 1024x1024',
    image_count INT DEFAULT 1 COMMENT '生成图片数量',

    video_duration INT DEFAULT NULL COMMENT '视频时长，单位秒',
    video_resolution VARCHAR(32) DEFAULT NULL COMMENT '视频分辨率',

    points BIGINT NOT NULL COMMENT '用户消耗积分',

    cost_amount DECIMAL(12,6) DEFAULT NULL COMMENT '预估真实成本，可选',
    cost_currency VARCHAR(16) DEFAULT 'CNY' COMMENT '成本货币',

    enabled TINYINT NOT NULL DEFAULT 1 COMMENT '是否启用: 1=启用, 0=禁用',
    sort_order INT NOT NULL DEFAULT 0 COMMENT '排序',

    remark VARCHAR(255) DEFAULT NULL COMMENT '备注',

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    UNIQUE KEY uk_model_price (
        model_key,
        capability_type,
        image_size,
        image_count,
        video_duration,
        video_resolution
    ),

    INDEX idx_capability_enabled (capability_type, enabled),
    INDEX idx_model_key (model_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='模型价格配置表';


-- ============================================
-- 7. 生成任务表
-- ============================================
CREATE TABLE IF NOT EXISTS generation_tasks (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,

    task_id VARCHAR(64) NOT NULL UNIQUE COMMENT '任务ID',
    user_id BIGINT NOT NULL COMMENT '用户ID',

    price_config_id BIGINT NOT NULL COMMENT '模型价格配置ID',

    model_key VARCHAR(128) NOT NULL COMMENT '模型标识',
    model_name VARCHAR(128) NOT NULL COMMENT '模型名称',
    capability_type VARCHAR(32) NOT NULL COMMENT '能力类型: image, video, text, audio',

    image_size VARCHAR(32) DEFAULT NULL COMMENT '图片尺寸',
    image_count INT DEFAULT NULL COMMENT '图片数量',

    video_duration INT DEFAULT NULL COMMENT '视频时长',
    video_resolution VARCHAR(32) DEFAULT NULL COMMENT '视频分辨率',

    status VARCHAR(32) NOT NULL DEFAULT 'pending' COMMENT '状态: pending, running, success, failed',

    frozen_points BIGINT NOT NULL DEFAULT 0 COMMENT '冻结积分',
    consumed_points BIGINT NOT NULL DEFAULT 0 COMMENT '实际消耗积分',
    refunded_points BIGINT NOT NULL DEFAULT 0 COMMENT '退回积分',

    prompt TEXT DEFAULT NULL COMMENT '用户提示词',

    request_json JSON DEFAULT NULL COMMENT '请求参数',
    provider_response_json JSON DEFAULT NULL COMMENT '中转站返回原始数据',
    result_json JSON DEFAULT NULL COMMENT '最终返回给前端的数据',

    error_message TEXT DEFAULT NULL COMMENT '错误信息',

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    started_at DATETIME DEFAULT NULL COMMENT '开始执行时间',
    finished_at DATETIME DEFAULT NULL COMMENT '完成时间',

    INDEX idx_user_id_created_at (user_id, created_at),
    INDEX idx_status (status),
    INDEX idx_price_config_id (price_config_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='生成任务表';


-- ============================================
-- 8. 后台管理员表
-- ============================================
CREATE TABLE IF NOT EXISTS admin_users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,

    username VARCHAR(64) NOT NULL UNIQUE COMMENT '管理员用户名',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',

    nickname VARCHAR(64) DEFAULT NULL COMMENT '昵称',
    role VARCHAR(32) NOT NULL DEFAULT 'admin' COMMENT '角色: admin, super_admin',

    status VARCHAR(32) NOT NULL DEFAULT 'normal' COMMENT '状态: normal, disabled',

    last_login_at DATETIME DEFAULT NULL COMMENT '最后登录时间',
    last_login_ip VARCHAR(64) DEFAULT NULL COMMENT '最后登录IP',

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='后台管理员表';



-- ============================================
-- 9. 会话表
-- ============================================

CREATE TABLE conversation_sessions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    session_id VARCHAR(64) NOT NULL UNIQUE COMMENT '会话ID',
    user_id BIGINT NOT NULL COMMENT '用户ID',

    title VARCHAR(255) DEFAULT NULL COMMENT '会话标题',
    session_type VARCHAR(32) NOT NULL DEFAULT 'mixed' COMMENT 'chat,image,video,mixed',

    last_message_preview VARCHAR(500) DEFAULT NULL COMMENT '最后一条消息预览',
    last_message_at DATETIME DEFAULT NULL COMMENT '最后消息时间',

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_user_updated (user_id, updated_at),
    INDEX idx_user_type (user_id, session_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='会话表';



-- ============================================
-- 10. 会话消息表表
-- ============================================
CREATE TABLE conversation_messages (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    message_id VARCHAR(64) NOT NULL UNIQUE COMMENT '消息ID',
    session_id VARCHAR(64) NOT NULL COMMENT '会话ID',
    user_id BIGINT NOT NULL COMMENT '用户ID',

    role VARCHAR(32) NOT NULL COMMENT 'user, assistant, system',
    content_type VARCHAR(32) NOT NULL COMMENT 'text,image,video,mixed',
    content_text TEXT DEFAULT NULL COMMENT '文本内容或提示词',

    task_id VARCHAR(64) DEFAULT NULL COMMENT '关联 generation_tasks.task_id',
    status VARCHAR(32) NOT NULL DEFAULT 'success' COMMENT 'pending,running,success,failed',

    metadata_json JSON DEFAULT NULL COMMENT '模型、尺寸、时长、积分等扩展信息',

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_session_created (session_id, created_at),
    INDEX idx_user_created (user_id, created_at),
    INDEX idx_task_id (task_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='会话消息表';




-- ============================================
-- 11. 媒体资源表
-- ============================================

CREATE TABLE media_assets (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    asset_id VARCHAR(64) NOT NULL UNIQUE COMMENT '资源ID',

    user_id BIGINT NOT NULL COMMENT '用户ID',
    session_id VARCHAR(64) DEFAULT NULL COMMENT '会话ID',
    message_id VARCHAR(64) DEFAULT NULL COMMENT '消息ID',
    task_id VARCHAR(64) DEFAULT NULL COMMENT '关联任务ID',

    media_type VARCHAR(32) NOT NULL COMMENT 'image,video,audio,file',
    provider VARCHAR(32) NOT NULL DEFAULT 'qiniu' COMMENT 'qiniu,local,s3',
    bucket VARCHAR(128) DEFAULT NULL COMMENT '存储桶',
    object_key VARCHAR(512) DEFAULT NULL COMMENT '云端对象key',
    url VARCHAR(1024) NOT NULL COMMENT '公开访问URL',

    mime_type VARCHAR(128) DEFAULT NULL,
    file_size BIGINT DEFAULT NULL,
    width INT DEFAULT NULL,
    height INT DEFAULT NULL,
    duration_seconds INT DEFAULT NULL,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_user_created (user_id, created_at),
    INDEX idx_session_id (session_id),
    INDEX idx_message_id (message_id),
    INDEX idx_task_id (task_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='媒体资源表';