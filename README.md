# AI创作平台

带用户体系和积分系统的AI创作平台。

## 项目结构

```
项目/
├── backend/          # FastAPI 后端
├── database/         # 数据库SQL脚本
└── vue/              # Vue3 前端
```

## 快速开始

### 1. 数据库配置

```bash
# 登录 MySQL
mysql -u root -p

# 创建数据库
CREATE DATABASE ai_creation_platform DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 退出后导入建表脚本
mysql -u root -p ai_creation_platform < database/create_tables.sql

# 导入初始数据（可选）
mysql -u root -p ai_creation_platform < database/init_data.sql
```

### 2. 后端配置

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置环境变量（编辑 .env 文件）
# 主要配置：
# - DATABASE_URL: 数据库连接地址
# - JWT_SECRET_KEY: JWT密钥
# - API_GATEWAY_BASE_URL: API中转站地址
# - API_GATEWAY_API_KEY: API中转站密钥

# 启动后端服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 前端配置

```bash
cd vue

# 安装依赖
npm install

# 安装 axios（用于HTTP请求）
npm install axios

# 启动前端服务
npm run dev
```

### 4. 访问应用

- 前端地址: http://localhost:3000
- 后端API文档: http://localhost:8000/docs

## 功能说明

### 已完成的功能

#### 用户认证
- 用户注册
- 用户登录
- JWT鉴权
- 获取当前用户信息

#### 积分系统
- 查询积分余额
- 查询积分流水
- 冻结积分（创建任务时）
- 扣除冻结积分（任务成功时）
- 退回冻结积分（任务失败时）

#### 模型价格
- 查询模型价格配置
- 支持按能力类型筛选

#### 生图任务
- 创建生图任务（Mock）
- 查询任务列表
- 查询任务详情
- 轮询任务状态

### 待完成的功能

- [ ] 充值订单与支付
- [ ] 后台管理接口
- [ ] 接入真实生图API
- [ ] 视频生成

## 开发说明

### 后端开发

后端使用 FastAPI + SQLAlchemy + MySQL，主要模块：

- `app/core/` - 核心配置、安全、依赖注入
- `app/models/` - ORM模型
- `app/schemas/` - Pydantic请求响应模型
- `app/api/routes/` - API路由
- `app/services/` - 业务逻辑
- `app/providers/` - 外部API调用

### 前端开发

前端使用 Vue3 + TypeScript + Ant Design Vue，主要模块：

- `src/api/` - API接口封装
- `src/stores/` - Pinia状态管理
- `src/views/` - 页面组件
- `src/router/` - 路由配置
- `src/utils/` - 工具函数

## 注意事项

1. API中转站密钥只能放在后端，不能暴露给前端
2. 所有需要登录的接口都需要携带 JWT token
3. 前端不能传 user_id，后端从 token 中解析
4. 积分扣减使用数据库事务和行锁保证并发安全
