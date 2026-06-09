# AI 创作平台开发顺序与后端目录结构

## 1. 项目目标

本项目是一个带用户体系和积分系统的 AI 创作平台。

核心能力包括：

1. 用户注册、登录、JWT 鉴权。
2. 用户充值兑换平台积分。
3. 用户选择固定模型规格进行生图、生视频。
4. 不同模型、尺寸、数量、时长对应固定积分。
5. 后端统一使用平台自己的 API 中转站 Key 调用模型。
6. API 中转站余额由平台自己维护，不由本项目自动充值。
7. 任务开始前冻结积分。
8. 任务成功后正式扣除积分。
9. 任务失败后退回冻结积分。
10. 所有积分变化都需要写入积分流水。

整体闭环：

```text
注册 → 登录 → 创建积分账户 → 测试加积分 → 查询模型价格 → 创建生成任务
→ 冻结积分 → 调用模型 API → 成功扣积分 / 失败退积分 → 返回结果
```

---

## 2. 推荐总体开发顺序

建议不要一开始就直接做完整前端，也不要一开始就接真实支付。

推荐顺序是：

```text
后端基础能力
    ↓
积分与任务闭环
    ↓
Mock 模型调用
    ↓
真实生图 API 接入
    ↓
前端页面联调
    ↓
视频模型接入
    ↓
真实支付接入
    ↓
后台管理完善
```

---

## 3. 第一阶段：后端用户体系

### 目标

先完成用户注册、登录、JWT 鉴权。

### 需要完成的内容

1. 创建 `users` 表。
2. 创建 `user_point_accounts` 表。
3. 实现用户注册接口。
4. 注册时自动创建积分账户。
5. 实现用户登录接口。
6. 登录成功后返回 JWT token。
7. 实现获取当前用户信息接口。
8. 实现 JWT 鉴权依赖。

### 接口

```http
POST /api/auth/register
POST /api/auth/login
GET  /api/auth/me
```

### 关键规则

1. 密码不能明文保存，必须保存 `password_hash`。
2. 推荐使用 `bcrypt`。
3. 注册用户时必须同时创建积分账户。
4. 注册用户和创建积分账户必须放在同一个数据库事务中。
5. 前端后续请求通过 `Authorization: Bearer <token>` 携带登录状态。

---

## 4. 第二阶段：积分账户与流水

### 目标

完成积分账户基础能力。

### 需要完成的内容

1. 查询我的积分余额。
2. 查询我的积分流水。
3. 封装增加积分方法。
4. 封装冻结积分方法。
5. 封装成功扣除冻结积分方法。
6. 封装失败解冻积分方法。
7. 所有积分变化都写入 `point_transactions`。

### 接口

```http
GET /api/user/points
GET /api/user/point-logs
```

### 核心积分状态

```text
balance_points：可用积分
frozen_points：冻结积分
total_recharged_points：累计充值积分
total_consumed_points：累计消费积分
```

### 积分流水类型

```text
recharge      充值到账
freeze        创建任务冻结积分
consume       任务成功扣除积分
unfreeze      任务失败解冻积分
refund        退款或补偿
admin_adjust  后台人工调整
```

---

## 5. 第三阶段：模型价格配置

### 目标

先把模型、尺寸、数量、积分价格配置好。

### 需要完成的内容

1. 创建 `model_price_configs` 表。
2. 写入第一批测试模型价格。
3. 实现查询模型价格接口。
4. 前端后续只能选择后端返回的模型价格配置。
5. 创建任务时前端只传 `price_config_id`。

### 接口

```http
GET /api/model-prices?capability_type=image
```

### 示例配置

```text
Flux Pro / 1024x1024 / 1 张 / 80 积分
Flux Pro / 1024x1024 / 4 张 / 300 积分
GPT Image / 1024x1024 / 1 张 / 120 积分
```

### 关键规则

错误做法：

```json
{
  "model": "flux-pro",
  "size": "1024x1024",
  "points": 1
}
```

正确做法：

```json
{
  "price_config_id": 1,
  "prompt": "一个赛博朋克风格的女孩"
}
```

后端根据 `price_config_id` 查询真实模型、尺寸、数量和积分。

---

## 6. 第四阶段：生成任务与 Mock 模型调用

### 目标

先不用真实模型 API，用假结果跑通任务和扣费闭环。

### 需要完成的内容

1. 创建 `generation_tasks` 表。
2. 实现创建生图任务接口。
3. 创建任务前检查积分是否足够。
4. 积分足够则冻结积分。
5. 创建任务记录。
6. 使用 Mock 函数模拟生成成功。
7. 成功后扣除冻结积分。
8. 失败后退回冻结积分。
9. 保存任务结果或错误信息。

### 接口

```http
POST /api/image/generate
GET  /api/tasks/{task_id}
GET  /api/tasks
```

### Mock 生成函数示例

```python
def mock_generate_image(prompt: str):
    return {
        "images": [
            "https://example.com/test-image.png"
        ]
    }
```

### 为什么先用 Mock？

因为要先验证以下逻辑是否正确：

1. 积分是否正确冻结。
2. 任务是否正确创建。
3. 成功后是否正确扣积分。
4. 失败后是否正确退积分。
5. 积分流水是否正确记录。
6. 任务状态是否正确更新。

只有这个闭环稳定后，再接真实模型 API。

---

## 7. 第五阶段：接入真实生图 API

### 目标

把 Mock 生图替换成真实 API 中转站调用。

### 需要完成的内容

1. 配置 API 中转站地址。
2. 配置 API 中转站 Key。
3. 创建 `providers/api_gateway_provider.py`。
4. 实现真实生图调用方法。
5. 将 `mock_generate_image()` 替换成 `api_gateway_provider.generate_image()`。
6. 保存中转站原始返回。
7. 统一处理接口异常。
8. 成功扣积分，失败退积分。

### 环境变量

```env
API_GATEWAY_BASE_URL=https://xxx.com/v1
API_GATEWAY_API_KEY=sk-xxxx
```

### 生图调用流程

```text
用户提交生图任务
    ↓
后端根据 price_config_id 查询模型配置
    ↓
冻结积分
    ↓
调用 API 中转站
    ↓
返回图片结果
    ↓
任务成功，扣除冻结积分
```

### 第一版只建议接一个模型

例如：

curl https://api.jiguangmanying.xyz/v1/images/generations   -H "Content-Type: application/json"   -H "Authorization: Bearer sk-YOUR_TOKEN"   -d '{
    "model": "gpt-image-2",
    "prompt": "A futuristic city skyline at sunset with neon lights",
    "n": 1,
    "size": "1024x1024",
    "quality": "low",
    "format": "jpeg"
  }'

不要一开始接太多模型。

---

## 8. 第六阶段：前端页面联调

### 目标

后端闭环稳定后，再开发前端页面。

### 用户端页面

```text
/login
/register
/dashboard
/recharge
/points/logs
/image-generate
/tasks
```

### 前端重点

1. 登录成功后保存 token。
2. Axios 请求拦截器自动带上 `Authorization`。
3. 生图页面从后端获取模型价格配置。
4. 用户只能选择后端返回的模型规格。
5. 创建任务时只提交 `price_config_id` 和 `prompt`。
6. 展示积分余额。
7. 展示任务状态。
8. 展示生成结果。
9. 失败时提示积分已退回。

### Axios 拦截器示例

```javascript
axios.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')

  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  return config
})
```

---

## 9. 第七阶段：接入视频生成 API

### 目标

生图稳定后，再扩展视频生成。

### 为什么视频要后做？

视频生成通常比生图复杂，可能涉及：

1. 异步任务。
2. 轮询结果。
3. 首帧图。
4. 尾帧图。
5. 视频时长。
6. 视频比例。
7. 视频分辨率。
8. 更长的等待时间。
9. 更高的失败概率。

### 新增字段可以复用 generation_tasks

建议不要单独创建 `image_tasks` 和 `video_tasks`。

直接使用通用表：

```text
generation_tasks
```

通过 `capability_type` 区分：

```text
image
video
audio
text
```

### 视频价格配置示例

```text
视频模型 A / 5 秒 / 720p / 1000 积分
视频模型 A / 10 秒 / 720p / 2000 积分
视频模型 B / 5 秒 / 1080p / 3000 积分
```

### 视频接口

```http
POST /api/video/generate
GET  /api/tasks/{task_id}
```

---

## 10. 第八阶段：充值订单与支付

### 目标

在积分和模型调用稳定后，再接真实支付。

### 需要完成的内容

1. 创建 `recharge_packages` 表。
2. 创建 `recharge_orders` 表。
3. 查询充值套餐。
4. 创建充值订单。
5. 对接支付平台。
6. 支付成功回调。
7. 回调成功后给用户增加积分。
8. 写充值积分流水。
9. 支付回调幂等处理。

### 接口

```http
GET  /api/recharge/packages
POST /api/recharge/create
GET  /api/recharge/orders
POST /api/pay/callback
```

### 支付回调幂等逻辑

```text
根据 order_no 查询订单
    ↓
如果订单已经 paid
    ↓
直接返回成功，不重复加积分

如果订单未 paid
    ↓
校验支付状态和签名
    ↓
更新订单为 paid
    ↓
给用户增加积分
    ↓
写积分流水
```

---

## 11. 第九阶段：后台管理

### 目标

完成平台运营需要的管理功能。

### 后台页面

```text
/admin/login
/admin/users
/admin/recharge-packages
/admin/model-prices
/admin/orders
/admin/tasks
/admin/point-logs
```

### 后台功能

1. 用户管理。
2. 查看用户积分。
3. 手动加积分。
4. 手动扣积分。
5. 充值套餐管理。
6. 模型价格配置管理。
7. 充值订单查询。
8. 生成任务查询。
9. 积分流水查询。
10. 失败任务排查。

---

## 12. 后端推荐目录结构

推荐 FastAPI 后端目录如下：

```text
app/
  main.py                         # FastAPI 入口
  core/
    config.py                     # 配置读取，例如 .env
    security.py                   # JWT、密码加密、权限相关
    deps.py                       # 通用依赖，例如获取当前用户
    exceptions.py                 # 自定义异常
    response.py                   # 统一响应结构，可选

  db/
    database.py                   # 数据库连接、Session 管理
    base.py                       # SQLAlchemy Base
    init_db.py                    # 初始化数据，可选

  models/
    user.py                       # users、admin_users
    point.py                      # user_point_accounts、point_transactions
    recharge.py                   # recharge_packages、recharge_orders
    model_price.py                # model_price_configs
    generation_task.py            # generation_tasks

  schemas/
    auth.py                       # 注册、登录、Token 响应模型
    user.py                       # 用户信息响应模型
    point.py                      # 积分余额、积分流水响应模型
    recharge.py                   # 充值套餐、充值订单请求响应模型
    model_price.py                # 模型价格配置响应模型
    generation.py                 # 生图、生视频任务请求响应模型

  api/
    router.py                     # 总路由汇总
    routes/
      auth.py                     # 注册、登录、当前用户
      users.py                    # 用户信息
      points.py                   # 积分查询、流水查询
      recharge.py                 # 充值套餐、充值订单
      model_prices.py             # 模型价格查询
      image.py                    # 生图接口
      video.py                    # 视频接口
      tasks.py                    # 任务查询
      admin.py                    # 后台管理接口，可后做

  services/
    auth_service.py               # 注册、登录业务
    user_service.py               # 用户相关业务
    point_service.py              # 积分增加、冻结、扣除、解冻
    recharge_service.py           # 充值订单、支付回调
    model_price_service.py        # 模型价格查询和管理
    generation_service.py         # 创建任务、调度生成、任务结算
    billing_service.py            # 扣费结算逻辑，可与 point_service 配合
    task_service.py               # 任务查询、任务状态更新

  providers/
    base.py                       # 供应商基类
    api_gateway_provider.py       # API 中转站调用
    image_provider.py             # 生图能力封装，可选
    video_provider.py             # 视频能力封装，可选

  utils/
    id_generator.py               # 订单号、任务 ID、流水号生成
    time.py                       # 时间工具
    logger.py                     # 日志工具
    validators.py                 # 通用校验

  tests/
    test_auth.py
    test_points.py
    test_generation.py

alembic/
  versions/                       # 数据库迁移文件

.env
requirements.txt
alembic.ini
README.md
```

---

## 13. 核心目录职责说明

### app/main.py

负责创建 FastAPI 应用，挂载总路由。

主要职责：

1. 创建 FastAPI 实例。
2. 配置 CORS。
3. 注册 API 路由。
4. 注册异常处理。
5. 启动项目。

---

### app/core/config.py

负责读取配置。

包括：

1. 数据库地址。
2. JWT 配置。
3. API 中转站地址。
4. API 中转站 Key。
5. 环境变量。

示例配置：

```python
class Settings:
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 10080

    API_GATEWAY_BASE_URL: str
    API_GATEWAY_API_KEY: str
```

---

### app/core/security.py

负责安全相关能力。

包括：

1. 密码 hash。
2. 密码校验。
3. JWT 创建。
4. JWT 解析。
5. token 过期校验。

---

### app/core/deps.py

负责公共依赖。

常见方法：

```python
get_db()
get_current_user()
get_current_admin()
```

其中 `get_current_user()` 用于所有需要登录的接口。

---

### app/models/

负责数据库 ORM 模型。

建议按业务拆分：

```text
user.py
point.py
recharge.py
model_price.py
generation_task.py
```

不要把所有 ORM 都放到一个文件里。

---

### app/schemas/

负责 Pydantic 请求和响应结构。

例如：

```text
RegisterRequest
LoginRequest
TokenResponse
PointBalanceResponse
ImageGenerateRequest
TaskDetailResponse
```

作用：

1. 校验请求参数。
2. 统一接口响应结构。
3. 让接口文档更清晰。

---

### app/api/routes/

负责接口层。

接口层只做：

1. 接收请求。
2. 调用 service。
3. 返回响应。

不要在 routes 里写大量业务逻辑。

错误做法：

```text
routes/image.py 里面直接写积分扣除、任务创建、模型调用
```

正确做法：

```text
routes/image.py 调用 generation_service.create_image_task()
```

---

### app/services/

负责核心业务逻辑。

重点文件：

```text
auth_service.py
point_service.py
generation_service.py
billing_service.py
```

#### point_service.py

负责：

1. 增加积分。
2. 冻结积分。
3. 扣除冻结积分。
4. 解冻积分。
5. 写积分流水。

#### generation_service.py

负责：

1. 创建生成任务。
2. 查询模型价格配置。
3. 调用积分冻结。
4. 调用模型 provider。
5. 成功结算。
6. 失败退积分。

#### billing_service.py

可以专门负责结算逻辑。

如果项目不复杂，也可以先合并到 `point_service.py`。

---

### app/providers/

负责外部模型供应商调用。

这里放 API 中转站调用逻辑。

#### api_gateway_provider.py

负责：

1. 读取 API 中转站配置。
2. 调用生图接口。
3. 调用视频接口。
4. 统一处理返回。
5. 统一处理异常。

示例方法：

```python
class ApiGatewayProvider:
    def generate_image(self, model: str, prompt: str, size: str, count: int):
        pass

    def generate_video(self, model: str, prompt: str, duration: int, resolution: str):
        pass
```

---

## 14. 重点业务流程伪代码

### 创建生图任务

```python
def create_image_task(user_id: int, price_config_id: int, prompt: str):
    # 1. 查询模型价格配置
    price_config = model_price_service.get_enabled_config(
        price_config_id=price_config_id,
        capability_type="image"
    )

    # 2. 获取需要消耗的积分
    points = price_config.points

    # 3. 冻结积分并创建任务
    with db.transaction():
        point_service.freeze_points(
            user_id=user_id,
            points=points,
            related_task_id=task_id,
            remark="生图任务冻结积分"
        )

        task = task_service.create_task(
            user_id=user_id,
            price_config=price_config,
            prompt=prompt,
            frozen_points=points
        )

    # 4. 调用模型
    try:
        result = api_gateway_provider.generate_image(
            model=price_config.model_key,
            prompt=prompt,
            size=price_config.image_size,
            count=price_config.image_count
        )

        # 5. 成功结算
        generation_service.settle_success(
            task_id=task.task_id,
            result=result
        )

        return task

    except Exception as e:
        # 6. 失败退积分
        generation_service.settle_failed(
            task_id=task.task_id,
            error_message=str(e)
        )

        return task
```

---

### 成功结算

```python
def settle_success(task_id: str, result: dict):
    with db.transaction():
        task = task_service.lock_task(task_id)

        if task.status == "success":
            return

        point_service.consume_frozen_points(
            user_id=task.user_id,
            points=task.frozen_points,
            related_task_id=task.task_id,
            remark="生成任务成功扣除积分"
        )

        task.status = "success"
        task.consumed_points = task.frozen_points
        task.result_json = result
        task.finished_at = now()
```

---

### 失败结算

```python
def settle_failed(task_id: str, error_message: str):
    with db.transaction():
        task = task_service.lock_task(task_id)

        if task.status in ["success", "failed"]:
            return

        point_service.unfreeze_points(
            user_id=task.user_id,
            points=task.frozen_points,
            related_task_id=task.task_id,
            remark="生成任务失败退回积分"
        )

        task.status = "failed"
        task.refunded_points = task.frozen_points
        task.error_message = error_message
        task.finished_at = now()
```

---

## 15. 开发时的优先级建议

### 必须先做

```text
用户注册登录
JWT 鉴权
积分账户
积分流水
模型价格配置
生成任务
Mock 生图
真实生图 API
```

### 可以后做

```text
真实支付
后台管理
视频生成
语音生成
文本模型
会员系统
优惠券系统
多供应商路由
API 中转站余额监控
```

---

## 16. 最终建议

最稳的开发路线是：

```text
1. 后端先跑通注册登录。
2. 注册时创建积分账户。
3. 做一个测试加积分能力。
4. 配置一个生图模型价格。
5. 创建生图任务时冻结积分。
6. 先用 Mock 假结果测试成功扣积分、失败退积分。
7. Mock 流程稳定后接真实生图 API。
8. 生图 API 稳定后做前端页面。
9. 前端联调完成后再扩展视频生成。
10. 最后再接真实支付和后台管理。
```

一句话总结：

```text
先后端，后前端；先 Mock，后真实模型；先生图，后视频；先积分闭环，后真实支付。
```
