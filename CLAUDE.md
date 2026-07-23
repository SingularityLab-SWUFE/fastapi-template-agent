# Claude Code Configuration

This file provides guidance to Claude Code when working with code in this repository.

## Configuration

Claude Code uses configuration files in `.claude/` directory:

- **Rules**: [@.claude/rules.md](/.claude/rules.md) (Always loaded)
- **Skills**: Available task-specific workflows (auto-discovered via `.claude/skills/*/SKILL.md` and `.claude/commands/*.md`)
- **Agents**: Subagent configurations (spawn when needed via `.claude/agents/`)
- **Knowledge**: Project-specific context (via `README.md`, and `.claude/knowledge/`)
