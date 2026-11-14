"""FastAPI 应用入口：创建应用、注册中间件、路由与全局异常处理。"""
import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.api.router import api_router
from app.common.response import ok
from app.core.config import settings
from app.core.database import engine
from app.core.exceptions import BizError
from app.core.logging import request_id_var, setup_logging
from app.core.redis import get_redis
from app.websocket.admin_notifications import router as ws_router

logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    level = logging.DEBUG if settings.app_debug else logging.INFO
    setup_logging(level)
    logger.info("应用启动 | env=%s", settings.app_env)

    # 定时关单仅在非测试环境启动（V1 单实例）
    scheduler_started = False
    if settings.app_env != "test":
        from app.tasks.order_tasks import start_scheduler, stop_scheduler

        start_scheduler()
        scheduler_started = True

    yield

    if scheduler_started:
        stop_scheduler()
    logger.info("应用关闭")


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None,
    openapi_url=None if settings.is_production else "/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.user_web_origin, settings.admin_web_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    rid = request.headers.get("X-Request-ID") or uuid.uuid4().hex
    request_id_var.set(rid)
    response = await call_next(request)
    response.headers["X-Request-ID"] = rid
    return response


@app.exception_handler(BizError)
async def biz_error_handler(request: Request, exc: BizError):
    return JSONResponse(
        status_code=exc.http_status,
        content={"code": exc.code, "message": exc.message, "data": exc.data},
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"code": 40001, "message": "参数校验失败", "data": jsonable_encoder(exc.errors())},
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    logger.exception("未处理异常 | path=%s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"code": 50000, "message": "服务异常", "data": None},
    )


@app.get("/health")
def health():
    """存活探针：进程可响应即返回 ok，不依赖外部组件。"""
    return ok({"status": "ok"})


@app.get("/health/ready")
def health_ready():
    """就绪探针：检查 MySQL 与 Redis 连通性。"""
    db_ok = redis_ok = False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception as exc:  # noqa: BLE001
        logger.warning("MySQL 就绪检查失败: %s", exc)
    try:
        get_redis().ping()
        redis_ok = True
    except Exception as exc:  # noqa: BLE001
        logger.warning("Redis 就绪检查失败: %s", exc)
    return JSONResponse(
        status_code=200 if (db_ok and redis_ok) else 503,
        content=ok({"db": db_ok, "redis": redis_ok}),
    )


app.include_router(api_router, prefix=settings.api_prefix)

# WebSocket 管理端提醒（独立于 /api/v1 前缀）
app.include_router(ws_router)

# 挂载上传目录为静态资源，供图片 URL 直接访问
settings.upload_path.mkdir(parents=True, exist_ok=True)
app.mount(
    settings.upload_base_url,
    StaticFiles(directory=str(settings.upload_path)),
    name="uploads",
)
