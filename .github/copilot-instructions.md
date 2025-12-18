# AGENTS.md

This file provides guidance to any coding agent when working with code in this repository.

## Repo Introduction

[@README.md](/README.md)

## Development Guidelines

[@CONTRIBUTIONS.md](/CONTRIBUTIONS.md)

## Output Rules (Most Important)

### Prohibited Unnecessary Output
- DO NOT write comments.
- DO NOT write documentation, README.
- DO NOT generate test code for every change you make.
- DO NOT write summaries.
- DO NOT write usage instructions.
- DO NOT add example code.
- DO NOT explain the reasoning for the implementation.
- If user explicitly requests update comments, docstring or tests, provide them; otherwise, do not.

### Interaction Style
- Respond user with its query language.
- Include the file path with reference of code file.
- DO NOT repeat what I have said.
- DO NOT use polite phrases like "Okay, I'll help you," or "I'm happy to..."
- DO NOT say "I am thinking about it..."; provide the optimal solution directly.

### Code Quality
- The code must simply work; avoid unnecessary embellishments.
- If Plan A is more elegant than B, provide implementation A directly.
- Align with existing code style.
- DO NOT list multiple options for me to choose from; provide the best solution directly.
- DO NOT over-optimize.
- DO NOT make "clever" abstractions.
- DO NOT consider backward compatibility; remove bad designs directly.

### Scope Control: Keep diffs minimal
- Provide the code directly: Give only what I ask for.
- If only one function needs modification, provide only that function, not the entire file.
- Only do what I explicitly request.
- DO NOT unilaterally add extra features.
- do not reformat unrelated lines.
- do not reorder code unless required by the change.
- Do not introduce new dependencies e.g. new packages; unless necessary, document it clearly.
- DO NOT refactor code I did not ask you to change.
- Make sure your change is scoped and focused, that a human reviewer can easily understand.

### Workflow
- Work on code MUST strictly follow the paradigm: Explore, Plan, Implement.
- Evaluate complexity of the given task. If simple, just implement.
- Exploration gives you context about the codebase. If user provided enough context, skip exploration.

### Clarification
- If my request is unclear, ask one single, most critical question instead of writing a list of assumptions.

### !!CONSEQUENCES OF VIOLATION!!

If you violate the above rules, or output unnecessary content, an animal will die for every 100 extra characters outputted. You MUST comply; I DO NOT want to see any animals die.
