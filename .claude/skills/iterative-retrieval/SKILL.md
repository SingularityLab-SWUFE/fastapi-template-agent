---
name: iterative-retrieval
description: Pattern for progressively refining context retrieval to solve the subagent context problem
---

# Iterative Retrieval Pattern

Gather relevant codebase context for a task in multi-agent workflows where subagents don't know what context they need until they start working.

## Cycle: DISPATCH → EVALUATE → REFINE → LOOP

### DISPATCH
Broad retrieval with initial query. Use Glob patterns and Grep keywords in parallel. Cast wide net (10-20 candidates).

### EVALUATE
Score each file (0-1):
- 0.8+ HIGH: Directly implements task-relevant code
- 0.5-0.7 MEDIUM: Related utilities, types, dependencies
- <0.5 LOW: False positive

Read contents to score. Don't score by filename alone.

### REFINE
- Extract terminology from high-relevance files
- Identify gaps: "missing: [schema | service | config | tests]"
- Build refined queries using discovered naming conventions

### LOOP
TERMINATE: ≥3 high-relevance files OR no critical gaps OR max iterations
CONTINUE: Critical context missing AND iterations remain

## Best Practices
1. Start broad, narrow progressively
2. Learn codebase terminology first cycle — initial query may miss if codebase uses "throttle" not "rate limit"
3. Track what's missing explicitly
4. Stop at "good enough" — 3 high-relevance beats 10 mediocre
5. Exclude confidently — low-relevance won't improve

## Example
```
Task: "Fix auth token expiry bug"
Cycle 1: Search "token", "auth", "expiry" → auth.ts (0.9), user.ts (0.3)
Cycle 2: Add "refresh", "jwt" from auth.ts → session-manager.ts (0.95)
→ Terminate: 2 high-relevance, no critical gaps
```

## Output
```
### High Relevance (0.8+)
- path: [why]

### Medium Relevance
- path: [why]

### Gaps
- [type]: [what's missing]

### Terminology
- [conventions discovered]
```
