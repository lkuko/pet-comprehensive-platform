# API 接口说明

> 完整接口清单见 `docs/计划初稿.md` 第 7.4 节。本文记录已落地的接口与统一规范。

## 统一约定

- 前缀：`/api/v1`
- 用户接口：`/api/v1/user/...`；管理接口：`/api/v1/admin/...`；公开接口：`/api/v1/public/...`
- 分页：`page` 从 1 开始，`page_size` 默认 10，最大 100；列表返回 `items/total/page/page_size`

## 统一响应

```json
{ "code": 0, "message": "success", "data": {} }
```

## 业务错误码

| code | HTTP | 含义 |
|---|---|---|
| 0 | 200 | 成功 |
| 40001 | 400/422 | 参数错误 |
| 40100 | 401 | 未登录 / Token 失效 |
| 40300 | 403 | 无权限 |
| 40400 | 404 | 资源不存在 |
| 40900 | 409 | 状态冲突 |
| 50000 | 500 | 服务异常 |

## 当前已实现接口（Day 1）

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/health` | 存活探针 |
| GET | `/health/ready` | 就绪探针（MySQL + Redis 连通性） |
| GET | `/api/v1/ping` | 冒烟接口，验证统一响应与路由挂载 |

## 认证

JWT 认证与 `USER`/`ADMIN` 角色校验在 Day 2 落地；请求头 `Authorization: Bearer <token>`。
