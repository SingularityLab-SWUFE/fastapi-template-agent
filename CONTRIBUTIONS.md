## Issues

### Issue First, Code Second

**Every pull request requires a corresponding issue - no exceptions.** This requirement creates a collaborative space where approach, scope, and alignment are established before code is written. Issues serve as design documents where maintainers and contributors discuss implementation strategy, identify potential conflicts with existing patterns.

Use issues to understand scope BEFORE opening PRs. The issue discussion determines whether a feature belongs in core, contrib, or not at all.

### Writing Good Issues

Issues that appear to transfer burden to maintainers without any effort to validate the problem will be closed. Please help the maintainers help you by always providing a minimal reproducible example and clearly describing the problem.

**LLM-generated issues will be closed immediately.** Issues that contain paragraphs of unnecessary explanation, verbose problem descriptions, or obvious LLM authorship patterns obfuscate the actual problem and transfer burden to maintainers.

Write clear, concise issues that:

- State the problem directly
- Provide a minimal reproducible example
- Skip unnecessary background or context
- Take responsibility for clear communication

Issues may be labeled "Invalid" simply due to confusion caused by verbosity or not adhering to the guidelines outlined here.

## Pull Requests

PRs that deviate from the project's core principles will be rejected regardless of implementation quality. **PRs are NOT for iterating on ideas** - they should only be opened for ideas that already have a bias toward acceptance based on issue discussion.

### Development Standards

#### Scope

Large pull requests create review bottlenecks and quality risks. Unless you're fixing a discrete bug or making an incredibly well-scoped change, keep PRs small and focused. 

A PR that changes 50 lines across 3 files can be thoroughly reviewed in minutes. A PR that changes 500 lines across 20 files requires hours of careful analysis and often hides subtle issues.

Breaking large features into smaller PRs:

- Creates better review experiences
- Makes git history clear
- Simplifies debugging with bisect
- Reduces merge conflicts
- Gets your code merged faster

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

### Testing

Tests are documentation that shows how features work. Good tests give reviewers confidence and help future maintainers understand intent.

```bash
# Run specific test directory
uv run pytest tests/server/ -v

# Run all tests before submitting PR
uv run pytest
```

Good tests are the foundation of reliable software. We treat tests as first-class documentation that demonstrates how features work while protecting against regressions. Every new capability needs comprehensive tests that demonstrate correctness.

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/server/test_auth.py

# Run with coverage
uv run pytest --cov

# Skip integration tests for faster runs
uv run pytest -m "not integration"

# Skip tests that spawn processes
uv run pytest -m "not integration and not client_process"
```

Tests should complete in under 1 second unless marked as integration tests. This speed encourages running them frequently, catching issues early.

### Test Organization

Our test organization mirrors the `src/` directory structure, creating a predictable mapping between code and tests. When you're working on `src/server/auth.py`, you'll find its tests in `tests/server/test_auth.py`. In rare cases tests are split further - for example, the OpenAPI tests are so comprehensive they're split across multiple files.

### Test Markers

We use pytest markers to categorize tests that require special resources or take longer to run.

## Writing Tests

### Test Requirements

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

### Mocking External Dependencies

### Submitting Your PR

#### Before Submitting

1. **Run all checks**: `uv run pre-commit run --all-files && uv run pytest`
2. **Keep scope small**: One feature or fix per PR
3. **Write clear description**: Your PR description becomes permanent documentation
4. **Update docs**: Include documentation for API changes

#### PR Description

Write PR descriptions that explain:
- What problem you're solving
- Why you chose this approach  
- Any trade-offs or alternatives considered
- Migration path for breaking changes

Focus on the "why" - the code shows the "what". Keep it concise but complete.

#### What We Look For

**Framework Philosophy**: The project is NOT trying to do all things or provide all shortcuts. Features are rejected when they don't align with the project's vision, even if perfectly implemented. The burden of proof is on the PR to demonstrate value.
**Code Quality**: We verify code follows existing patterns. Consistency reduces cognitive load. When every module works similarly, developers understand new code quickly.
**Test Coverage**: Not every line needs testing, but every behavior does. Tests document intent and protect against regressions.
**Breaking Changes**: May be acceptable in minor versions but must be clearly documented.

## Acknowledgments

We derived this contribution guide from best practices in [FastMCP](https://github.com/jlowin/fastmcp). Thanks to FastMCP maintainers for their excellent guidelines!
