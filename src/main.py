from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.core.config import settings
from .session import close_db, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db(settings.db.url, settings.db.echo)
    yield
    await close_db()


app = FastAPI(
    title=settings.app.name,
    version=settings.app.version,
    debug=settings.app.debug,
    lifespan=lifespan,
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.debug,
    )
