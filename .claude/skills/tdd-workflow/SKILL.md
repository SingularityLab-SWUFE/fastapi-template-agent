---
name: tdd-workflow
description: TDD cycle phases (RED → GREEN → REFACTOR → REVIEW) and agent orchestration
---

# TDD Workflow

## Phases

### Phase 1: RED (Write Failing Test)

1. **Understand requirement** from task description
2. **Find test location**:
   - Search existing tests in `tests/` directory
   - Match structure: `src/server/auth.py` → `tests/server/test_auth.py`
3. **Write test that fails**:
   - Test behavior, not implementation
   - Use descriptive test names
   - Follow `pytest-patterns` conventions
4. **Run test to verify failure**:
   ```bash
   uv run pytest path/to/test_file.py::test_name -v
   ```

### Phase 2: GREEN (Minimal Implementation)

**For complex implementations** (multi-file changes, architectural decisions, unclear scope):
- Use the `planner` agent to create implementation plan
- Follow the plan to implement minimal code

**For simple implementations** (single function, obvious change):
- Implement minimal code directly

**Verify test passes**:
```bash
uv run pytest path/to/test_file.py::test_name -v
```

### Phase 3: REFACTOR (Improve Code)

1. **Use `refactor-cleaner` agent** to identify:
   - Dead code to remove
   - Duplicated logic to consolidate
   - Cleanup opportunities

2. **Apply refactorings** while keeping tests green:
   ```bash
   uv run pytest path/to/test_file.py -v
   ```

3. **Verify coverage**:
   ```bash
   uv run pytest path/to/test_file.py --cov=src/module/being/tested --cov-report=term-missing
   ```

### Phase 4: REVIEW (Quality Check)

**Use `code-reviewer` agent** to verify:
- Security concerns
- Code quality
- Test coverage adequacy
- Adherence to project patterns

## Agent Orchestration

- **planner**: Complex implementations in GREEN phase
- **refactor-cleaner**: Cleanup in REFACTOR phase
- **code-reviewer**: Final quality check in REVIEW phase
