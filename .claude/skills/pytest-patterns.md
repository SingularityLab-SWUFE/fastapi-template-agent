# Pytest Patterns

## Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/server/test_auth.py

# Run with coverage
uv run pytest --cov

# Skip integration tests
uv run pytest -m "not integration"

# Skip tests that spawn processes
uv run pytest -m "not integration and not client_process"
```

## Test Organization

Tests mirror the `src/` directory structure:
- Code in `src/server/auth.py` → tests in `tests/server/test_auth.py`

## Test Requirements

### Single Behavior Per Test
Each test verifies exactly one behavior. When it fails, you know immediately what broke.

### Self-Contained Setup
Every test creates its own setup. Tests must be runnable in any order, in parallel, or in isolation.

### Clear Intent
Test names and assertions make the verified behavior obvious.

### Using Fixtures
Use fixtures for reusable data, server configurations, or resources.

**Important**: Do NOT open clients in fixtures - it creates hard-to-diagnose event loop issues.

### Effective Assertions
Assertions should be specific and provide context on failure:

```python
# Bad - minimal context
assert result.status == "success"

# Good - explains what was expected
assert result.status == "success", f"Expected successful operation, got {result.status}: {result.error}"
```

Try not to have too many assertions in a single test. Assertions of different behaviors should be in separate tests.

## Test Speed

Tests should complete in under 1 second unless marked as integration tests. This encourages running them frequently.

## Test Markers

Use pytest markers to categorize tests requiring special resources or longer run times.
