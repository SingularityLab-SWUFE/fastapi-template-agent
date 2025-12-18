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
- **Caching**: Pluggable caching system with built-in Redis support.
- **Standardized Responses**: Middleware for consistent, unified JSON response formatting across all endpoints.
- **Custom Error Codes**: Flexible handling of business-specific error codes and messages.

## Use

You can **clone or fork** the repo as it is, or use `copier` to create a new project from the template:

```bash
uvx copier copy gh:SingularityLab-SWUFE/fastapi-template-agent my-backend-project --trust  # will do some file mv
```

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
# src/core/schemas/error.py
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
from src.core.schemas.error import ErrorCode
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

### Protected Routes

```python
from fastapi import APIRouter, Depends
from src.auth import current_user, current_superuser
from src.core.schemas import User

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

<!-- TODO: RBAC -->

### Dependency Injection settings

`settings` can be injected into your path operation functions using `Depends`:

```python
from fastapi import Depends
from src.core.config import Settings, get_settings
from src.cache import CacheProtocol, get_cache

async def my_handler(
    settings: Settings = Depends(get_settings),
    cache: CacheProtocol = Depends(get_cache)
):
    max_retries = settings.app.max_retries
    await cache.set("config", settings.app.name)
```

This allows you to test different configurations by overriding the `get_settings` dependency in your tests.

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
