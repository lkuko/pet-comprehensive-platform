# 智能宠物综合服务平台（Intelligent Pet Comprehensive Service Platform）

基于前后端分离架构的宠物综合服务平台，覆盖宠物领养、宠物医疗预约、洗护/寄养服务预约、宠物用品商城四条核心业务线。

> 开发基线以 `docs/计划初稿.md` 为唯一依据。当前进度：Day 1 工程骨架 + Day 2 认证 + Day 3 宠物档案/领养 + Day 4 领养申请与审核已完成，业务模块将在后续阶段增量落地。

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Python 3.11+ · FastAPI · SQLAlchemy 2.x · Alembic · Pydantic 2 · PyMySQL |
| 数据库 | MySQL 8.0（主库） · Redis（缓存/购物车） |
| 前端 | Vue 3 · Vite · Element Plus · Pinia · Vue Router · Axios |
| 部署 | Docker Compose · Nginx |

## 目录结构

```
pet-comprehensive-platform/
├── server/            # FastAPI 后端（分层：api/schemas/services/repositories/models/core）
├── admin-web/         # 管理端（Vue 3）
├── user-web/          # 用户端（Vue 3）
├── deploy/            # Nginx 与 Dockerfile（部署阶段补充）
├── docs/              # 计划基线、API、数据库、部署文档
└── docker-compose.yml # MySQL 8.0 + Redis
```

## 快速开始

### 1. 启动基础设施（MySQL 8.0 + Redis）

```bash
cp .env.example .env          # 按需修改密码
docker compose up -d mysql redis
```

### 2. 后端

```bash
cd server
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env         # 后端本地开发读取 server/.env
alembic upgrade head            # 初始化数据库结构
# 初始化管理员（仅开发/测试环境；密码通过环境变量注入，禁止写死）
ADMIN_SEED_PASSWORD=你的密码 python -m scripts.seed
uvicorn app.main:app --reload   # 默认 http://localhost:8000
```

- 存活探针：`GET /health`
- 就绪探针：`GET /health/ready`（校验 MySQL + Redis 连通）
- 接口文档：`http://localhost:8000/docs`
- 管理员账号：`admin`（密码为 seed 时设置的 `ADMIN_SEED_PASSWORD`）；普通用户通过注册接口自行注册

### 3. 前端

```bash
cd admin-web && npm install && npm run dev   # 管理端 http://localhost:5173
cd user-web  && npm install && npm run dev   # 用户端 http://localhost:5174
```

Vite 已配置 `/api`、`/uploads`、`/ws` 代理到 `http://localhost:8000`。

### 4. 运行测试

```bash
cd server
pytest
```

## 统一响应规范

```json
{ "code": 0, "message": "success", "data": { } }
```

业务码：`0` 成功；`40001` 参数错误；`40100` 未登录；`40300` 无权限；`40400` 资源不存在；`40900` 状态冲突；`50000` 服务异常。HTTP 状态码表达协议层结果，业务码表达业务结果。

## 当前进度

- [x] Day 1 工程骨架：配置分环境、MySQL/Redis 连接、SQLAlchemy Base/Session、Alembic 迁移、统一响应/异常/日志/请求 ID、pytest 基建、双前端壳
- [x] Day 2 认证：User 模型、注册/登录/管理员登录、密码哈希（bcrypt）、JWT + 角色依赖、seed 管理员、两端登录页/路由守卫/个人中心
- [x] Day 3 宠物档案与领养：用户宠物 CRUD、领养分类/宠物/图片模型、图片上传（本地存储 + 静态访问）、公开领养列表/筛选/详情、管理端宠物维护、seed 3 分类 + 10 条演示宠物
- [x] Day 4 领养申请与审核：提交/撤回申请、重复申请受控、管理端审核通过/拒绝、审核通过后宠物状态→已领养并关闭同宠物其他待审核申请（事务 + 行锁）
- [ ] Day 5+ 医疗预约、洗护寄养、商城等业务模块

详细开发计划见 `docs/项目计划与结构.md`。
