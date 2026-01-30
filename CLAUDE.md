# Claude Code Configuration

This file provides guidance to Claude Code when working with code in this repository.

## Configuration

Claude Code uses configuration files in `.claude/` directory:

- **Rules**: [@.claude/rules.md](/.claude/rules.md) (Always loaded)
- **Skills**: Available task-specific workflows (load on-demand via `.claude/skills/`)
  - `backend-patterns` - DDD, caching, auth, error handling
  - `pytest-patterns` - Testing guidelines
- **Agents**: Subagent configurations (spawn when needed via `.claude/agents/`)
  - `code-reviewer` - Code review criteria
  - `planner` - Planning workflow
- **Knowledge**: Project-specific context (via `.claude/knowledge/`)
