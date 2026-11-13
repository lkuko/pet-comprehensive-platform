"""分环境配置：Pydantic Settings 统一读取环境变量。

禁止在源码中写数据库密码、JWT 密钥、管理员真实密码、固定公网地址。
env_file 依次尝试 server/.env 与项目根 .env，均不存在时仅从进程环境变量读取（Docker 场景）。
"""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_SERVER_DIR = Path(__file__).resolve().parents[2]  # server/


def _find_env_file() -> str | None:
    for candidate in (_SERVER_DIR / ".env", _SERVER_DIR.parent / ".env"):
        if candidate.exists():
            return str(candidate)
    return None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_find_env_file(),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- 应用 ---
    app_name: str = "pet-comprehensive-platform"
    app_env: str = "development"  # development / test / production
    app_debug: bool = True
    app_timezone: str = "Asia/Shanghai"
    api_prefix: str = "/api/v1"

    # --- MySQL ---
    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3307
    mysql_database: str = "pet_platform"
    mysql_user: str = "pet_user"
    mysql_password: str = "change_me"

    # --- Redis ---
    redis_host: str = "127.0.0.1"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""

    # --- JWT ---
    jwt_secret_key: str = "replace_with_a_long_random_secret_key_32bytes"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 120

    # --- 上传 ---
    upload_dir: str = "./uploads"
    upload_base_url: str = "/uploads"
    max_upload_size_mb: int = 5

    # --- 订单 ---
    order_pay_timeout_minutes: int = 30

    # --- Seed 管理员（仅 development/test 创建；密码走环境变量，禁止写死） ---
    admin_seed_username: str = "admin"
    admin_seed_password: str = ""

    # --- CORS 白名单 ---
    user_web_origin: str = "http://localhost:5173"
    admin_web_origin: str = "http://localhost:5174"

    @property
    def upload_path(self) -> Path:
        """上传目录的绝对路径（相对路径基于 server/ 目录解析）。"""
        p = Path(self.upload_dir)
        if not p.is_absolute():
            p = _SERVER_DIR / p
        return p

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}?charset=utf8mb4"
        )

    @property
    def redis_url(self) -> str:
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
