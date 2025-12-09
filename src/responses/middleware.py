from __future__ import annotations

import json
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse, Response as FastAPIResponse
from starlette.concurrency import iterate_in_threadpool
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .base import Response


class ResponseWrapperMiddleware(BaseHTTPMiddleware):
    """Wrap application JSON outputs into the unified Response[T] envelope."""

    DOC_PATH_PREFIXES = ("/docs", "/redoc")
    DOC_PATHS = {"/openapi.json", "/docs/oauth2-redirect"}
    SKIP_PATHS = {"/auth/jwt/login", "/auth/jwt/refresh", "/auth/jwt/logout"}

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> FastAPIResponse:
        api_response = await call_next(request)

        if self._should_skip(request, api_response):
            return api_response

        body_chunks = [chunk async for chunk in api_response.body_iterator]
        body = b"".join(body_chunks)

        # Rebuild iterator so subsequent middleware / response flow remains valid
        api_response.body_iterator = iterate_in_threadpool(iter(body_chunks))

        if not body:
            payload = None
        else:
            try:
                payload = json.loads(body.decode(api_response.charset or "utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return api_response

        if self._is_already_wrapped(payload):
            new_payload = payload
            status_code = api_response.status_code
        elif 200 <= api_response.status_code < 400:
            new_payload = Response.success(code=api_response.status_code, data=payload).model_dump()
            status_code = 200
        else:
            error_msg = self._extract_error_msg(payload)
            error_code = self._extract_error_code(payload, api_response.status_code)
            new_payload = Response.error(code=error_code, msg=error_msg, data=payload).model_dump()
            status_code = api_response.status_code

        unified = JSONResponse(
            content=new_payload,
            status_code=status_code,
            media_type=api_response.media_type,
            background=api_response.background,
            headers=dict(api_response.headers),
        )
        return unified

    def _should_skip(self, request: Request, response: FastAPIResponse) -> bool:
        content_type = (response.headers.get("content-type") or "").lower()
        if "application/json" not in content_type:
            return True

        path = request.url.path
        if path in self.DOC_PATHS or any(path.startswith(prefix) for prefix in self.DOC_PATH_PREFIXES):
            return True

        if path in self.SKIP_PATHS:
            return True

        return False

    @staticmethod
    def _is_already_wrapped(payload: Any) -> bool:
        if not isinstance(payload, dict):
            return False

        required = {"code", "msg", "data"}
        if not required.issubset(payload.keys()):
            return False

        return True

    @staticmethod
    def _extract_error_msg(payload: Any) -> str:
        if payload is None:
            return "error"

        if isinstance(payload, str):
            return payload

        if isinstance(payload, dict):
            detail = payload.get("detail") or payload.get("msg") or payload.get("message")
            if isinstance(detail, str):
                return detail
            if detail is not None:
                return json.dumps(detail, ensure_ascii=False)

        if isinstance(payload, list):
            return json.dumps(payload, ensure_ascii=False)

        return "error"

    @staticmethod
    def _extract_error_code(payload: Any, default_code: int) -> int:
        if isinstance(payload, dict):
            candidate = payload.get("code")
            if isinstance(candidate, int):
                return candidate
        return default_code
