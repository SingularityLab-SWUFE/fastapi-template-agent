from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi_pagination import add_pagination
from starlette.middleware import Middleware

from src.api import auth_router, core_router, create_oauth_router
from src.cache import close_cache, init_cache
from src.config import get_settings
from src.handlers import register_exception_handlers
from src.logging import setup_logging
from src.responses.middleware import ResponseWrapperMiddleware

from .session import close_db, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    setup_logging(log_level=settings.log.level, json_logs=settings.log.json_logs)
    await init_db(settings.db.url, settings.db.echo)
    await init_cache(
        backend=settings.cache.backend,
        host=settings.cache.host,
        port=settings.cache.port,
        db=settings.cache.db,
        password=settings.cache.password,
        encoding=settings.cache.encoding,
        decode_responses=settings.cache.decode_responses,
        socket_timeout=settings.cache.socket_timeout,
        socket_connect_timeout=settings.cache.socket_connect_timeout,
        max_connections=settings.cache.max_connections,
        retry_on_timeout=settings.cache.retry_on_timeout,
    )
    yield
    await close_cache()
    await close_db()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app.name,
        version=settings.app.version,
        debug=settings.app.debug,
        lifespan=lifespan,
        middleware=[
            Middleware(ResponseWrapperMiddleware),
        ],
    )

    register_exception_handlers(app)

    app.include_router(auth_router, prefix="/auth", tags=["auth"])
    app.include_router(create_oauth_router(settings), prefix="/auth", tags=["auth"])
    app.include_router(core_router, tags=["core"])

    add_pagination(app)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "src.main:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.debug,
    )
