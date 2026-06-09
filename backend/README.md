# AI创作平台后端

基于 FastAPI 的 AI 创作平台后端服务。

## 项目结构

```
backend/
├── app/
│   ├── main.py                 # FastAPI 入口
│   ├── core/
│   │   ├── config.py           # 配置读取
│   │   ├── security.py         # JWT、密码加密
│   │   └── deps.py             # 依赖注入
│   ├── db/
│   │   ├── database.py         # 数据库连接
│   │   └── base.py             # SQLAlchemy Base
│   ├── models/                 # ORM 模型
│   │   ├── user.py
│   │   ├── point.py
│   │   ├── recharge.py
│   │   ├── model_price.py
│   │   ├── generation_task.py
│   │   └── admin_user.py
│   ├── schemas/                # Pydantic 模型
│   │   ├── auth.py
│   │   ├── point.py
│   │   ├── model_price.py
│   │   └── generation.py
│   ├── api/
│   │   ├── router.py           # 总路由
│   │   └── routes/             # 各模块路由
│   │       ├── auth.py
│   │       ├── points.py
│   │       ├── model_prices.py
│   │       ├── image.py
│   │       └── tasks.py
│   ├── services/               # 业务逻辑
│   │   ├── auth_service.py
│   │   ├── point_service.py
│   │   ├── model_price_service.py
│   │   └── generation_service.py
│   ├── providers/              # 外部 API 调用
│   │   ├── base.py
│   │   └── api_gateway_provider.py
│   └── utils/                  # 工具函数
│       ├── id_generator.py
│       ├── logger.py
│       └── validators.py
├── alembic/                    # 数据库迁移
├── tests/                      # 测试
├── .env                        # 环境变量配置
├── requirements.txt            # 依赖
└── alembic.ini                 # Alembic 配置
```

## 环境要求

- Python 3.9.11
- MySQL 5.7+

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置环境变量

编辑 `.env` 文件，配置以下内容：

```env
# 数据库配置
DATABASE_URL=mysql+pymysql://root:your_password@localhost:3306/ai_creation_platform

# JWT 配置
JWT_SECRET_KEY=change-this-to-a-random-secret-key

# API 中转站配置
API_GATEWAY_BASE_URL=https://your-api-gateway.com/v1
API_GATEWAY_API_KEY=sk-your-api-key
```

## 初始化数据库

```bash
# 1. 创建数据库
mysql -u root -p
CREATE DATABASE ai_creation_platform DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 2. 执行建表脚本
mysql -u root -p ai_creation_platform < ../database/create_tables.sql

# 3. 导入初始数据（可选）
mysql -u root -p ai_creation_platform < ../database/init_data.sql
```

## 运行数据库迁移

```bash
# 生成迁移文件
alembic revision --autogenerate -m "init"

# 执行迁移
alembic upgrade head
```

## 启动服务

```bash
# 开发模式
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 或者
python -m app.main
```

## API 文档

启动服务后，访问以下地址查看 API 文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 已完成的接口

### 认证模块
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `GET /api/auth/me` - 获取当前用户信息

### 积分模块
- `GET /api/user/points` - 查询积分余额
- `GET /api/user/point-logs` - 查询积分流水

### 模型价格模块
- `GET /api/model-prices` - 查询模型价格配置

### 生图模块
- `POST /api/image/generate` - 创建生图任务（Mock）
- `GET /api/tasks` - 查询我的任务列表
- `GET /api/tasks/{task_id}` - 查询任务详情

## 待完成的功能

- [ ] 充值订单与支付
- [ ] 后台管理接口
- [ ] 接入真实生图 API
- [ ] 视频生成
