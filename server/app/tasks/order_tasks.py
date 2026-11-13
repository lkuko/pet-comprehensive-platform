"""定时任务：超时未支付订单自动关单（V1 单实例）。

任务复用订单 Service 的 close_expired_orders，不绕过 Service 自行改状态；
通过状态条件更新保证幂等，重复执行不会重复返还库存。
"""
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.database import SessionLocal
from app.services import mall as mall_service

logger = logging.getLogger("app.tasks.order")

scheduler = BackgroundScheduler()


def close_expired_orders_job() -> None:
    """每分钟扫描并关闭超时未支付订单，返还库存。"""
    db = SessionLocal()
    try:
        closed = mall_service.close_expired_orders(db)
        if closed:
            logger.info("超时关单完成 | closed=%d", closed)
    finally:
        db.close()


def start_scheduler() -> None:
    """启动调度器（幂等：重复调用不重复启动）。"""
    if scheduler.running:
        return
    scheduler.add_job(
        close_expired_orders_job,
        "interval",
        minutes=1,
        id="close_expired_orders",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    logger.info("订单关单定时任务已启动（每 1 分钟）")


def stop_scheduler() -> None:
    """停止调度器。"""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("订单关单定时任务已停止")
