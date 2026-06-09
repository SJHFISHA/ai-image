# AI创作平台数据库

## 文件说明

- `create_tables.sql` - 建表脚本，包含所有数据表的创建语句
- `init_data.sql` - 初始数据，包含充值套餐和模型价格配置示例数据

## 使用方法

### 1. 创建数据库

```sql
CREATE DATABASE IF NOT EXISTS ai_creation_platform
DEFAULT CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
```

### 2. 执行建表脚本

```bash
mysql -u root -p ai_creation_platform < create_tables.sql
```

或者登录MySQL后执行：

```sql
USE ai_creation_platform;
SOURCE /path/to/create_tables.sql;
```

### 3. 导入初始数据（可选）

```bash
mysql -u root -p ai_creation_platform < init_data.sql
```

## 数据表说明

| 表名 | 说明 |
|------|------|
| users | 用户表 |
| user_point_accounts | 用户积分账户表 |
| point_transactions | 积分流水表 |
| recharge_packages | 充值套餐表 |
| recharge_orders | 充值订单表 |
| model_price_configs | 模型价格配置表 |
| generation_tasks | 生成任务表 |
| admin_users | 后台管理员表 |

## 积分流水类型说明

| type | 说明 |
|------|------|
| recharge | 充值到账 |
| freeze | 创建任务冻结积分 |
| consume | 任务成功扣除积分 |
| unfreeze | 任务失败解冻积分 |
| refund | 退款或补偿 |
| admin_adjust | 后台人工调整 |

## 任务状态说明

| status | 说明 |
|------|------|
| pending | 待处理 |
| running | 执行中 |
| success | 成功 |
| failed | 失败 |

## 能力类型说明

| capability_type | 说明 |
|------|------|
| image | 图片生成 |
| video | 视频生成 |
| text | 文本生成 |
| audio | 音频生成 |
