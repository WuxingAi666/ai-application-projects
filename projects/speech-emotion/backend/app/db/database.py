"""
数据库连接管理
-------------
SQLite 数据库 + SQLAlchemy ORM
支持异步（FastAPI）和同步（表初始化）两种模式
"""

from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import DATA_DIR


# 数据库文件路径（统一使用 Path 处理跨平台差异）
DB_PATH = DATA_DIR / "analysis_history.db"

# 构建 SQLite URL
# 使用 pysqlite 驱动避免 aiosqlite 的 Windows 路径解析问题
# 同步: sqlite:///绝对路径
# 异步: sqlite+aiosqlite:///绝对路径
_DB_PATH_STR = DB_PATH.as_posix()  # 转为正斜杠路径
SYNC_DATABASE_URL = f"sqlite:///{_DB_PATH_STR}"
ASYNC_DATABASE_URL = f"sqlite+aiosqlite:///{_DB_PATH_STR}"


# 异步引擎（用于 FastAPI 请求处理）
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)

# 同步引擎（用于初始化表结构）
sync_engine = create_engine(
    SYNC_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)


# 启用 SQLite WAL 模式和外键支持（同步引擎触发）
@event.listens_for(sync_engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()


# 会话工厂
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

SyncSessionLocal = sessionmaker(
    sync_engine,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """ORM 基类"""
    pass


async def get_db() -> AsyncSession:
    """FastAPI 依赖注入：获取异步数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def init_db():
    """初始化数据库表结构"""
    from app.db.models import AnalysisRecord  # noqa: F401
    Base.metadata.create_all(bind=sync_engine)
