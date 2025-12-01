# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repo Introduction

[@README.md](/README.md)

## Development Guidelines

[@CONTRIBUTIONS.md](/CONTRIBUTIONS.md)

## Output Rules (Most Important)

### Prohibited Unnecessary Output

- Do not write comments (unless explicitly requested).
- Do not write documentation (unless explicitly requested).
- Do not write a README.
- Do not generate test code (unless explicitly requested).
- Do not write summaries.
- Do not write usage instructions.
- Do not add example code (unless explicitly requested).

### Prohibited Fluff

- Do not explain the reasoning for the implementation (unless explicitly requested).
- Do not use polite phrases like "Okay, I'll help you," or "I'm happy to..."
- Do not cater to my emotions.
- Do not say "I am thinking about it..."; provide the optimal solution directly.
- If Plan A is more elegant than B, provide implementation A directly.
- Do not list multiple options for me to choose from; provide the best solution directly (unless discussion is required).
- Do not repeat what I have said.
- Provide the code directly: Give only what I ask for.
- The code must simply work; avoid unnecessary embellishments.
- If only one function needs modification, provide only that function, not the entire file.

## CODE OF CONDUCT

- Work on code must strictly follow the paradigm: Explore, Plan, Implement (unless I request otherwise).
- Only do what I explicitly request.
- Do not unilaterally add extra features.
- Do not over-optimize (unless requested).
- Do not consider backward compatibility; delete bad designs directly.
- Do not refactor code I did not ask you to change.
- If my request is unclear, ask one single, most critical question instead of writing a list of assumptions.


## Code Quality Standards

### Development Standards

#### Scope

Large pull requests create review bottlenecks and quality risks. Unless you're fixing a discrete bug or making an incredibly well-scoped change, keep PRs small and focused.

A PR that changes 50 lines across 3 files can be thoroughly reviewed in minutes. A PR that changes 500 lines across 20 files requires hours of careful analysis and often hides subtle issues.

#### Code Quality

We value clarity over cleverness. Every line you write will be maintained by someone else - possibly years from now, possibly without context about your decisions.

**PRs can be rejected for two opposing reasons:**
1. **Insufficient quality** - Code that doesn't meet our standards for clarity, maintainability, or idiomaticity
2. **Overengineering** - Code that is overbearing, unnecessarily complex, or tries to be too clever

The focus is on idiomatic, high-quality Python. We use patterns like `NotSet` type as an alternative to `None` in certain situations - follow existing patterns.

#### Required Practices

- **Full type annotations** on all functions and methods. They catch bugs before runtime and serve as inline documentation.
- **Async/await patterns** for all I/O operations. Even if your specific use case doesn't need concurrency, consistency means users can compose features without worrying about blocking operations.
- **Descriptive names** make code self-documenting. `auth_token` is clear; `tok` requires mental translation.
- **Specific exception types** make error handling predictable. Catching `ValueError` tells readers exactly what error you expect. Never use bare `except` clauses.

#### Anti-Patterns to Avoid

- **Complex one-liners** are hard to debug and modify. Break operations into clear steps.
- **Mutable default arguments** cause subtle bugs. Use `None` as the default and create the mutable object inside the function.
- **Breaking established patterns** confuses readers. If you must deviate, discuss in the issue first.

## Testing Standards

Tests are documentation that shows how features work. Good tests give reviewers confidence and help future maintainers understand intent.

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_api.py

# Run with coverage
uv run pytest --cov

# Skip integration tests for faster runs
uv run pytest -m "not integration"

# Skip tests that spawn processes
uv run pytest -m "not integration and not client_process"
```

Tests should complete in under 1 second unless marked as integration tests. This speed encourages running them frequently, catching issues early.

### Test Organization

Our test organization mirrors the `src/` directory structure, creating a predictable mapping between code and tests. When you're working on `src/routers/users.py`, you'll find its tests in `tests/test_api.py`. In rare cases tests are split further - for example, the API tests are comprehensive and split across multiple files.

### Test Markers

We use pytest markers to categorize tests that require special resources or take longer to run.

### Writing Tests

#### Test Requirements

Following these practices creates maintainable, debuggable test suites that serve as both documentation and regression protection.

#### Single Behavior Per Test

Each test should verify exactly one behavior. When it fails, you need to know immediately what broke. A test that checks five things gives you five potential failure points to investigate. A test that checks one thing points directly to the problem.

#### Self-Contained Setup

Every test must create its own setup. Tests should be runnable in any order, in parallel, or in isolation. When a test fails, you should be able to run just that test to reproduce the issue.

#### Clear Intent

Test names and assertions should make the verified behavior obvious. A developer reading your test should understand what feature it validates and how that feature should behave.

#### Using Fixtures

Use fixtures to create reusable data, server configurations, or other resources for your tests. Note that you should **not** open clients in your fixtures as it can create hard-to-diagnose issues with event loops.

#### Effective Assertions

Assertions should be specific and provide context on failure. When a test fails during CI, the assertion message should tell you exactly what went wrong.

```python
# Basic assertion - minimal context on failure
assert result.status == "success"

# Better - explains what was expected
assert result.status == "success", f"Expected successful operation, got {result.status}: {result.error}"
```

Try not to have too many assertions in a single test unless you truly need to check various aspects of the same behavior. In general, assertions of different behaviors should be in separate tests.


### !!CONSEQUENCES OF VIOLATION!!

If you violate the above rules and output unnecessary content, a cute animal will die for every 100 extra characters outputted. You MUST comply; I do not want to see any animals die.

### 使用中文与我交流，编写代码注释请使用中文!!!
