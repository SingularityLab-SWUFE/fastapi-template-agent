from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from src.cache import close_cache, init_cache
from src.core.config import settings
from src.core.handlers.exceptions import (
    HTTPExceptionHandler,
    ValueErrorHandler,
    BusinessExceptionHandler,
    BusinessException,
)
from src.core.middleware.exception_middleware import ExceptionMiddleware
from src.core.responses.schemas import ErrorResponse
from src.routers import users

from .session import close_db, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
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

app.include_router(users.router)

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
