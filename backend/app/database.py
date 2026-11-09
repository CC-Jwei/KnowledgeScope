"""数据库引擎与会话。"""

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


# 确保 SQLite 文件父目录存在，用在引擎创建前的路径准备
def _ensure_sqlite_parent_dir(database_url: str) -> None:
    # SQLite URL 前缀，用在判断是否需要建本地目录
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        return
    # 从连接串解析出的库文件路径，用在 mkdir
    db_path = Path(database_url.removeprefix(prefix))
    if db_path.parent != Path("."):
        db_path.parent.mkdir(parents=True, exist_ok=True)


# 模块级配置实例，用在创建引擎与建库目录
settings = get_settings()
_ensure_sqlite_parent_dir(settings.database_url)

# SQLAlchemy 引擎，用在 SessionLocal 与 init_db
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)
# 会话工厂，用在 get_db 为每个请求创建 Session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# FastAPI 依赖：产出并关闭 DB Session，用在各路由 Depends(get_db)
def get_db() -> Generator[Session, None, None]:
    # 当前请求的数据库会话，用在路由与 service 读写
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 根据 ORM 元数据建表，用在应用 lifespan 启动阶段
def init_db() -> None:
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
