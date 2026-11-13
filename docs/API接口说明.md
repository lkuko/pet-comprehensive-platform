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

## 当前已实现接口

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/health` | 存活探针 |
| GET | `/health/ready` | 就绪探针（MySQL + Redis 连通性） |
| GET | `/api/v1/ping` | 冒烟接口，验证统一响应与路由挂载 |
| POST | `/api/v1/user/auth/register` | 用户注册（返回 JWT） |
| POST | `/api/v1/user/auth/login` | 用户登录（返回 JWT） |
| POST | `/api/v1/admin/auth/login` | 管理员登录（仅 ADMIN 角色） |
| GET | `/api/v1/user/profile` | 当前用户资料（USER/ADMIN） |
| PUT | `/api/v1/user/profile` | 修改个人资料（USER/ADMIN） |
| GET | `/api/v1/user/pets` | 我的宠物列表（USER） |
| POST | `/api/v1/user/pets` | 新增宠物档案（USER） |
| GET | `/api/v1/user/pets/{id}` | 宠物档案详情（所属 USER） |
| PUT | `/api/v1/user/pets/{id}` | 修改宠物档案（所属 USER） |
| DELETE | `/api/v1/user/pets/{id}` | 删除宠物档案（软删除/停用，所属 USER） |
| GET | `/api/v1/public/pet-categories` | 领养分类列表（游客） |
| GET | `/api/v1/public/adoption-pets` | 领养宠物分页/筛选（游客，仅可领养） |
| GET | `/api/v1/public/adoption-pets/{id}` | 领养宠物详情（游客，仅可领养） |
| POST | `/api/v1/upload/image` | 图片上传（任意登录用户；subdir=pets/products/avatars） |
| GET | `/api/v1/admin/adoption-pets` | 宠物管理列表（ADMIN） |
| POST | `/api/v1/admin/adoption-pets` | 新增领养宠物（ADMIN） |
| GET | `/api/v1/admin/adoption-pets/{id}` | 宠物详情（ADMIN，任意状态） |
| PUT | `/api/v1/admin/adoption-pets/{id}` | 编辑领养宠物（ADMIN） |
| PATCH | `/api/v1/admin/adoption-pets/{id}/status` | 上下架（ADMIN） |
| POST | `/api/v1/user/adoption-applications` | 提交领养申请（USER，仅 AVAILABLE 宠物、同一用户同一宠物仅一条待审核） |
| GET | `/api/v1/user/adoption-applications` | 我的申请列表（USER） |
| GET | `/api/v1/user/adoption-applications/{id}` | 申请详情（所属 USER） |
| POST | `/api/v1/user/adoption-applications/{id}/cancel` | 撤回待审核申请（所属 USER） |
| GET | `/api/v1/admin/adoption-applications` | 申请审核列表（ADMIN，支持 status/pet_id/keyword 筛选） |
| POST | `/api/v1/admin/adoption-applications/{id}/approve` | 审核通过（ADMIN；宠物→已领养，同宠物其他待审核申请→关闭） |
| POST | `/api/v1/admin/adoption-applications/{id}/reject` | 审核拒绝（ADMIN；必须填写原因） |
| GET | `/api/v1/public/medical/locations` | 医疗点列表（游客，仅启用） |
| GET | `/api/v1/public/medical/doctors` | 医生列表（游客，仅启用，可按医疗点过滤） |
| GET | `/api/v1/public/medical/services` | 医疗项目列表（游客，仅启用） |
| GET | `/api/v1/public/medical/schedules` | 可预约时段（游客，仅启用/未满额/未过期） |
| POST | `/api/v1/user/medical/appointments` | 提交医疗预约（USER；FOR UPDATE 锁排班防超卖，同一时段防重复） |
| GET | `/api/v1/user/medical/appointments` | 我的医疗预约（USER） |
| GET | `/api/v1/user/medical/appointments/{id}` | 预约详情（所属 USER） |
| POST | `/api/v1/user/medical/appointments/{id}/cancel` | 取消待确认预约（所属 USER；释放名额） |
| GET/POST/PUT/DELETE | `/api/v1/admin/medical/locations` | 医疗点 CRUD（ADMIN；删除前检查医生关联） |
| GET/POST/PUT/DELETE | `/api/v1/admin/medical/doctors` | 医生 CRUD（ADMIN；删除前检查排班关联） |
| GET/POST/PUT/DELETE | `/api/v1/admin/medical/services` | 医疗项目 CRUD（ADMIN；删除前检查预约引用） |
| GET/POST/PUT/DELETE | `/api/v1/admin/medical/schedules` | 排班 CRUD（ADMIN；同医生同天时段重叠校验；有未完成预约只能停用） |
| GET | `/api/v1/admin/medical/appointments` | 预约列表（ADMIN，支持 status/doctor_id/location_id/keyword 筛选） |
| POST | `/api/v1/admin/medical/appointments/{id}/confirm` | 确认预约（ADMIN） |
| POST | `/api/v1/admin/medical/appointments/{id}/reject` | 拒绝预约（ADMIN；必须填原因；释放名额） |
| POST | `/api/v1/admin/medical/appointments/{id}/complete` | 完成预约（ADMIN；仅已确认可完成） |

## 认证

- JWT 认证，请求头 `Authorization: Bearer <token>`。
- 角色 `USER` / `ADMIN`；JWT 仅存 `sub`（用户 ID），角色与状态由依赖实时查库校验（禁用用户立即失效）。
- 管理员账号由 seed 脚本创建（密码走环境变量），不允许公开注册管理员。
