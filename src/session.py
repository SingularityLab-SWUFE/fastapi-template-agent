from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.config import settings


# 在模块导入时根据配置初始化异步引擎和会话工厂
engine: AsyncEngine = create_async_engine(settings.db.url, echo=settings.db.echo)
async_session_factory: sessionmaker[AsyncSession] = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db(url: str, echo: bool = False) -> None:
    """初始化异步数据库引擎和会话工厂"""
    global engine, async_session_factory
    engine = create_async_engine(url, echo=echo)
    async_session_factory = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def close_db() -> None:
    """关闭数据库引擎连接"""
    await engine.dispose()


class SessionContextManager:
    """异步会话上下文管理器"""

    def __init__(self) -> None:
        self._session: AsyncSession | None = None

    async def __aenter__(self) -> AsyncSession:
        self._session = async_session_factory()
        await self._session.__aenter__()
        return self._session

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._session is not None:
            await self._session.__aexit__(exc_type, exc_val, exc_tb)


def get_session() -> SessionContextManager:
    """获取异步数据库会话（支持 async with）"""
    return SessionContextManager()
