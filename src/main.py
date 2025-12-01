from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from src.cache import close_cache, init_cache, get_cache
from src.core.config import settings
from src.core.config.auth import jwt_settings
from src.core.handlers.exceptions import (
    HTTPExceptionHandler,
    ValueErrorHandler,
    BusinessExceptionHandler,
    BusinessException,
)
from src.core.middleware.exception_middleware import ExceptionMiddleware
from src.core.responses.schemas import ErrorResponse
from src.routers import users, auth, roles, users_roles
from src.auth.token_manager import TokenManager
from src.auth.cache_token_store import CacheTokenStore
from src.auth.dependencies import set_token_manager

from .session import close_db, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 初始化数据库
    await init_db(settings.db.url, settings.db.echo)

    # 初始化缓存
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

    # 初始化认证
    token_manager = TokenManager(
        secret_key=jwt_settings.secret_key,
        algorithm=jwt_settings.algorithm,
        access_token_expire_minutes=jwt_settings.access_token_expire_minutes,
        refresh_token_expire_days=jwt_settings.refresh_token_expire_days,
    )

    # 设置缓存存储的缓存实例
    cache_token_store = CacheTokenStore()
    cache_instance = await get_cache()
    cache_token_store.set_cache(cache_instance)
    token_manager.cache_store = cache_token_store

    # 设置全局 Token 管理器
    set_token_manager(token_manager)

    yield

    # 关闭资源
    await close_cache()
    await close_db()


app = FastAPI(
    title=settings.app.name,
    version=settings.app.version,
    debug=settings.app.debug,
    lifespan=lifespan,
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse.error(exc.status_code, exc.detail).model_dump()
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content=ErrorResponse.error(400, str(exc)).model_dump()
    )


@app.exception_handler(BusinessException)
async def business_exception_handler(request: Request, exc: BusinessException) -> JSONResponse:
    return JSONResponse(
        status_code=200,
        content=ErrorResponse.error(exc.code, exc.message).model_dump()
    )


app.add_middleware(ExceptionMiddleware)

# 注册路由
app.include_router(users.router)
app.include_router(auth.router)
app.include_router(roles.router)
app.include_router(users_roles.router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.debug,
    )
