---
name: backend-patterns
description: DDD structure, caching, auth, error handling, and common backend patterns
---

# Backend Patterns

## Architecture

### DDD Structure
- **Domain Modules**: Each domain (e.g., `auth/`, `users/`) contains models (SQLTable), schemas (Request/Response), services.
- **Representation Layer**: `http/` handles HTTP requests, routing, controllers.
- **Core Layer**: `core/` contains business-related domains.

### Shared Module Guidelines
Before adding code to `shared/`, verify it meets these criteria:

**Belongs in `shared/`:**
- Used by 3+ domains
- Pure utility with no business logic
- Infrastructure-level abstractions (error codes, mixins, cache keys)

**NOT belong in `shared/`:**
- Domain-specific logic (put in domain directory)
- Used by only 1-2 domains (co-locate with primary domain)
- Business rules or policies

## Patterns

### Structured Logging
Use loguru for logging with structured context:

```python
from loguru import logger

logger.bind(order_id=order.id, amount=order.total).info("Order completed")
logger.exception("Order processing failed")  # Auto-captures traceback
```

### Caching
Inject cache via dependency injection:

```python
from src.cache import CacheProtocol, get_cache

async def handler(cache: CacheProtocol = Depends(get_cache)):
    cached = await cache.get(f"key:{id}")
    if cached:
        return cached
    await cache.set(f"key:{id}", data, ttl=300)
```

### Response Format
All responses wrapped in `{code, msg, data}`:

```python
from src.http import Response

# Return raw data (middleware wraps)
return [{"id": 1}]

# Explicit wrapper
return Response.success(data=item, msg="Created", code=201)
```

### Error Handling
Define error codes in `src/shared/errors.py`:

```python
class ErrorCode(IntEnum):
    PRODUCT_OUT_OF_STOCK = 50101

ERROR_CODE_TO_HTTP = {
    ErrorCode.PRODUCT_OUT_OF_STOCK: 409,
}
```

Raise business exceptions:

```python
from src.exceptions import BusinessException

raise BusinessException(
    ErrorCode.PRODUCT_OUT_OF_STOCK,
    f"Only {stock} items available",
    data={"available": stock}
)
```

### Pagination
Use `fastapi-pagination` for query results:

```python
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import apaginate

@router.get("/users", response_model=Page[User])
async def list_users(session: AsyncSession = Depends(get_session)):
    return await apaginate(session, select(User))
```

### Authentication & Authorization
Use dependency injection for route protection:

```python
from src.auth import current_user, require_permissions, require_roles

# Require login
@router.get("/profile")
async def get_profile(user: User = Depends(current_user)):
    return user

# Require permission
@router.post("/users", dependencies=[Depends(require_permissions("user:create"))])
async def create_user(data: dict):
    pass

# Require role
@router.get("/admin/stats", dependencies=[Depends(require_roles("admin"))])
async def admin_stats():
    pass
```

### Dependency Injection
Inject settings and services:

```python
from src.config import Settings, get_settings

async def handler(settings: Settings = Depends(get_settings)):
    max_retries = settings.app.max_retries
```

### Retry Mechanism
Use tenacity for automatic retries:

```python
from src.retry import retry_on_network

@retry_on_network()
async def fetch_user(user_id: int):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.example.com/users/{user_id}")
        response.raise_for_status()
        return response.json()
```

### Timezone Handling
**Principle**: Store in UTC, query in UTC, convert to local time at presentation time.

```python
# Storage (models)
from datetime import UTC, datetime
from src.mixins import TimestampMixin

class Order(SQLModel, TimestampMixin, table=True):
    # created_at, updated_at stored in UTC
    pass

# Presentation (serializers)
from datetime import timedelta, timezone
from src.config import get_settings

class OrderResponse(BaseModel):
    created_at: datetime

    @field_serializer('created_at')
    def serialize_dt(self, dt: datetime, _info):
        tz_offset = get_settings().app.timezone
        local_tz = timezone(timedelta(hours=tz_offset))
        return dt.astimezone(local_tz)
```
