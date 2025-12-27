# fastapi-template-agent

[![GitHub stars](https://img.shields.io/github/stars/SingularityLab-SWUFE/fastapi-template-agent?style=social)](https://github.com/SingularityLab-SWUFE/fastapi-template-agent/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/SingularityLab-SWUFE/fastapi-template-agent?style=social)](https://github.com/SingularityLab-SWUFE/fastapi-template-agent/network/members)
[![GitHub license](https://img.shields.io/github/license/SingularityLab-SWUFE/fastapi-template-agent)](https://github.com/SingularityLab-SWUFE/fastapi-template-agent/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-005571?logo=fastapi)](https://fastapi.tiangolo.com/)

Modern FastAPI Boilerplate for Agent Coding

## Features

### Agent

Have you ever been bothered by coding agent consistently wasting token usage? This repo summarizes few patterns (e.g. outputing unnecessary documentation rubbish), and offer a ready-to-use solution:

- **Cost-Effective Instructions**: Well-crafted prompts and guidelines optimized for efficient and economical agent usage.
- **Unified Instruction for all agents**: Instructions that different coding agents can consistently follow, and automatic sync in precommit hook.

| Agent product | Instruction file |
| --- | --- |
| Codex | `AGENTS.md` (source of truth) |
| Claude Code | `CLAUDE.md` |
| Cline | `.clinerules` |
| Cursor | `.cursorrules` |
| GitHub Copilot | `.github/copilot-instructions.md` |

You can use the same pattern to your any other project that uses coding agent as well.

### Backend

This repo also provides a full-featured, best-practiced backend template for building a robust/modern FastAPI application:

- **Modern Tooling Stack**: State-of-the-art setup with `uv` for package management, `just` as task runner, `pre-commit` for git hooks, `pytest` for testing, and more.
- **Authentication & Authorization**: Secure JWT-based authentication with role-based access control (RBAC).
- **Structured Logging**: Production-ready logging with loguru - colored console output with clickable file:line references for development, JSON logs for production.
- **Caching**: Pluggable caching system with built-in Redis support.
- **Retry Mechanism**: Automatic retry for network errors and transient failures with exponential backoff using `tenacity`.
- **Standardized Responses**: Middleware for consistent, unified JSON response formatting across all endpoints.
- **Custom Error Codes**: Flexible handling of business-specific error codes and messages.
- **Pagination**: Built-in support for paginating query results using `fastapi-pagination`.

### DDD guidelines

This repo follows **Domain-Driven Design (DDD)** principles to structure the codebase for better maintainability and scalability:

- **Domain Modules**: Each domain (e.g., `auth/`, `users/`) has its own module containing models(SQLTable), schemas (Request/Response), services.
- **Representation Layer**: `api/` module handles HTTP requests, routing, and controllers. You can add `grpc`, `graphql` in this layer as needed.
- **Core Layer**: `core/` module contains business-related domains.

The `shared/` module contains **cross-cutting concerns** used by multiple domains. Before adding code to `shared/`, it must meet these criteria:

**✅ Belongs in `shared/`:**
- Used by 3+ domains
- Pure utility with no business logic
- Infrastructure-level abstractions (error codes, mixins, cache keys)

**❌ Does NOT belong in `shared/`:**
- Domain-specific logic (put in domain directory)
- Used by only 1-2 domains (co-locate with primary domain)
- Business rules or policies

## Use

You can **clone or fork** the repo as it is, or use `copier` to create a new project from the template:

```bash
uvx copier copy gh:SingularityLab-SWUFE/fastapi-template-agent my-backend-project --trust  # will do some file mv
```

This repo is also a public template on GitHub, you can directly use the "Use this template" button on the repo page, and vibing with Copilot!

## CI

The CI workflow runs tests on pull requests with branch names starting with `fix/`, `feat/`, or `refactor/`.

To enables/configures ci, create repository variables and secrets as needed:

- `CI_JWT_SECRET`
- `CI_APP_NAME`
- `CI_CACHE_BACKEND`
- `CI_DB_DATABASE`
- `CI_DB_DRIVER`

## Deploy

### Docker Setup

- Start services (production):

```bash
docker compose -f docker/docker-compose.yml up --build
```

- Start services for development (mounts project and enables hot reload):

```bash
docker compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml up --build
```

The compose files read environment variables from the repository root `.env` file. Adjust that file for DB and cache settings as needed.

**Note**: the docker compose setup will run database migrations automatically before the app starts (the app image's entrypoint runs `alembic upgrade head` against the `db` service). The repository `.env` has been updated to use a local Postgres instance (`DB__DRIVER=postgresql`, host `db`).

## Agent instructing

This repo keeps a single source of truth for agent rules in `AGENTS.md`, and syncs it to:

- `CLAUDE.md`
- `.clinerules`
- `.cursorrules`
- `.github/copilot-instructions.md`

Update `AGENTS.md`, then run:

```bash
just agent-rules-sync
```

The `pre-commit` hook `agent-rules` runs the same check on commit.

## Usage Examples

### Structured Logging

Logging system built with [loguru](https://github.com/Delgan/loguru) provides colored console output with clickable file:line references for development and JSON logs for production.

```python
from loguru import logger # just import loguru

@router.post("/orders")
async def create_order(order: Order):
    logger.info(f"Creating order {order.id}")
    try:
        result = await process_order(order)
        logger.bind(order_id=order.id, amount=order.total).info("Order completed")
        return result
    except Exception as e:
        logger.exception("Order processing failed")  # Auto-captures traceback
        raise
```

### Using Cache

```python
from src.cache import CacheProtocol, get_cache

@router.get("/user/{user_id}")
async def get_user(user_id: int, cache: CacheProtocol = Depends(get_cache)):
    # Try cache first
    cached = await cache.get(f"user:{user_id}")
    if cached:
        return {"source": "cache", "data": cached}

    # Fetch from DB
    user_data = fetch_user_from_db(user_id)

    # Cache for 5 minutes
    await cache.set(f"user:{user_id}", user_data, ttl=300)

    return {"source": "db", "data": user_data}
```

### Response Middleware

All JSON responses automatically wrapped in `{code, msg, data}` format:

```python
from fastapi import APIRouter
from src.responses import Response

router = APIRouter()

# Option 1: Return raw data (middleware wraps it)
@router.get("/items")
async def list_items():
    return [{"id": 1, "name": "Item 1"}]
    # Response: {"code": 200, "msg": "success", "data": [...]}

# Option 2: Explicit Response wrapper
@router.get("/items/{item_id}")
async def get_item(item_id: int):
    return Response.success(data={"id": item_id, "name": "Item"})
    # Response: {"code": 200, "msg": "success", "data": {...}}

# Custom success message
@router.post("/items")
async def create_item(item: dict):
    return Response.success(data=item, msg="Item created", code=201)
```

### Custom Error Codes

**1. Define error codes:**
```python
# src/shared/errors.py
class ErrorCode(IntEnum):
    # Your custom codes
    PRODUCT_OUT_OF_STOCK = 50101
    PAYMENT_DECLINED = 50201
    SHIPPING_UNAVAILABLE = 50301

# mapping to HTTP status code
ERROR_CODE_TO_HTTP = {
    ErrorCode.PRODUCT_OUT_OF_STOCK: 409,
    ErrorCode.PAYMENT_DECLINED: 402,
    ErrorCode.SHIPPING_UNAVAILABLE: 503,
}
```

**2. Raise business exceptions:**
```python
from src.shared.errors import ErrorCode
from src.exceptions import BusinessException

@router.post("/orders")
async def create_order(product_id: int, quantity: int):
    stock = get_stock(product_id)
    if stock < quantity:
        raise BusinessException(
            ErrorCode.PRODUCT_OUT_OF_STOCK,
            f"Only {stock} items available",
            data={"available": stock, "requested": quantity}
        )

    # Response:
    # HTTP 409
    # {"code": 50101, "msg": "Only 3 items available", "data": {...}}
```

**3. Custom exception classes:**
```python
# src/exceptions.py
class OutOfStockException(BusinessException):
    def __init__(self, product_id: int, available: int):
        super().__init__(
            code=ErrorCode.PRODUCT_OUT_OF_STOCK,
            msg=f"Product {product_id} out of stock",
            data={"product_id": product_id, "available": available}
        )

# Usage
raise OutOfStockException(product_id=123, available=0)
```

`BusinessException` can be addressed globally by the exception handlers, so you don't need to catch it in every endpoint.

### Pagination

Paginate query results with built-in [`fastapi-pagination`](https://github.com/uriyyo/fastapi-pagination) support.

**Usage:**
```python
from fastapi import APIRouter, Depends
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import apaginate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.schemas import User
from src.session import get_session

router = APIRouter()

@router.get("/users", response_model=Page[User])
async def list_users(session: AsyncSession = Depends(get_session)):
    return await apaginate(session, select(User))
    # Response: {"code": 200, "msg": "success", "data": {"items": [...], "total": 100, "page": 1, "size": 50}}
```

### Protected Routes

Authentication is well-implemented by `fastapi-users`, so use `current_user` and `current_superuser` dependencies to register route login or superuser access:

```python
from fastapi import APIRouter, Depends
from src.auth import current_user, current_superuser
from src.auth.schemas import User

router = APIRouter()

@router.get("/profile")
async def get_profile(user: User = Depends(current_user)):
    return {"username": user.username, "email": user.email}

@router.delete("/users/{user_id}")
async def delete_user(user_id: int, admin: User = Depends(current_superuser)):
    # Only superusers can access
    delete_user_from_db(user_id)
    return {"deleted": user_id}
```

We recommend you use RBAC related dependencies for permission control. Try avoid use `current_superuser`.

### RBAC (Role-Based Access Control)

If your views require more fine-grained permission control, use the `require_permissions`, `require_roles`, and `owner_or_perm` dependencies:

```python
from fastapi import APIRouter, Depends
from src.auth import require_permissions, require_roles, owner_or_perm

router = APIRouter()

# Require specific permission
# Note: you do not need to set current_user dependency here, as require_permissions does it internally
@router.post("/users", dependencies=[Depends(require_permissions("user:create"))])
async def create_user(data: dict):
    return {"created": True}

# Require multiple permissions (all)
@router.delete(
    "/users/{user_id}",
    dependencies=[Depends(require_permissions("user:delete", "audit:log", match="all"))]
)
async def delete_user(user_id: int):
    return {"deleted": user_id}

# Require any of multiple permissions
@router.get(
    "/users/{user_id}",
    dependencies=[Depends(require_permissions("user:read", "user:write", match="any"))]
)
async def get_user(user_id: int):
    return {"id": user_id}

# Require specific role
# You can register an endpoint that both needs permission check and role check
@router.get("/admin/stats", dependencies=[Depends(require_roles("admin"))])
async def admin_stats():
    return {"stats": "..."}

# Owner or permission check
async def get_post_owner_id(post_id: int) -> int:
    # Fetch owner_id from database
    return fetch_post_owner(post_id)

@router.put(
    "/posts/{post_id}",
    dependencies=[Depends(owner_or_perm(get_post_owner_id, ["post:edit"]))]
)
async def update_post(post_id: int, data: dict):
    # User can edit if they own the post OR have "post:edit" permission
    return {"updated": True}
```

**Permission Format:**
- `required_perm` must be `module:action` (e.g., `"user:read"`, `"post:delete"`)
- `user_perm` can be `module` (full module access) or `module:action` (specific action)
- `user_perm="user"` matches any `required_perm="user:*"`
- Use `bypass_superuser=True` to allow superusers to bypass checks

### Dependency Injection settings

`settings` can be injected into your path operation functions using `Depends`:

```python
from fastapi import Depends
from src.config import Settings, get_settings
from src.cache import CacheProtocol, get_cache

async def my_handler(
    settings: Settings = Depends(get_settings),
    cache: CacheProtocol = Depends(get_cache)
):
    max_retries = settings.app.max_retries
    await cache.set("config", settings.app.name)
```

This allows you to test different configurations by overriding the `get_settings` dependency in your tests.

### Retry

Automatic retry for network errors, timeouts, and 5xx responses using [tenacity](https://github.com/jd/tenacity). Retries up to 3 times with exponential backoff (1-10 seconds).

```python
import httpx
from src.retry import retry_on_network, async_retry_on_network

# Decorator for sync functions
@retry_on_network()
def fetch_data():
    response = httpx.get("https://api.example.com/data")
    response.raise_for_status()
    return response.json()

# Decorator for async functions
@retry_on_network()
async def fetch_user(user_id: int):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.example.com/users/{user_id}")
        response.raise_for_status()
        return response.json()

# Manual retry control (async)
async def fetch_with_manual_retry():
    async for attempt in async_retry_on_network():
        with attempt:
            async with httpx.AsyncClient() as client:
                response = await client.get("https://api.example.com/data")
                response.raise_for_status()
                return response.json()
```

## Development Setup

- Python >= 3.12
- [uv](https://github.com/astral-sh/uv)
- [just](https://github.com/casey/just)

### Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Install just

`just` is used to simplify command execution. You can also refer to commands in `justfile` directly. Installation options:

```bash
cargo install just
```

Or

```bash
curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to ~/.local/bin
```

## Contributing

**Read [CONTRIBUTIONS.md](/CONTRIBUTIONS.md) before contributing.**

### Quick Start for Contributors

1. **Install dependencies**
   ```bash
   just dev
   ```

2. **Install pre-commit hooks**
   ```bash
   just hooks
   ```

3. **Create an issue first**
   - Every PR requires a corresponding issue
   - Discuss approach and scope before writing code

4. **Run checks before submitting PR**
   ```bash
   just check
   just test
   ```

For Chinese contributors, since this is a open-source project, please ensure that your commit messages or issues/PRs can be understood by the global community. It's recommended to write in English or provide English version alongside Chinese descriptions.
