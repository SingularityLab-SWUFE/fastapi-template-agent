# AGENTS.md

This file provides guidance to any coding agent when working with code in this repository.

## Repo Introduction

[@README.md](/README.md)

## Development Guidelines

[@CONTRIBUTIONS.md](/CONTRIBUTIONS.md)

## Output Rules (Most Important)

### Prohibited Unnecessary Output
- Comment under code review. DO NOT write or remove comments when implementing.
- DO NOT generate test code for every change you make. Only pick most valuable test suites.
- DO NOT write usage instructions.
- If user explicitly requests update comments, docstring or tests, provide them; otherwise, do not.

### Fail Fast
- DO NOT implement fallback or defensive programming unless you are required to.
- DO NOT make border assumptions.
- If you need stubs for placeholder, make it fail.

### Code Quality
- The code must simply work; implement the plan progressively.
- Align with existing code style.
- DO NOT over-optimizing, over-engineering; Explains the tradeoffs behind the design.
- DO NOT consider backward compatibility; remove bad designs directly.

### Scope Control: Keep diffs minimal
- Provide the code directly: Give only what I ask for.
- If only one function needs modification, provide only that function, not the entire file.
- Only do what I explicitly request.
- DO NOT edit file that is out of MR/issue scope.
- DO NOT introduce new dependencies e.g. new packages; unless necessary, document it clearly.
- Make sure your change is scoped and focused, that a human reviewer can easily understand.

### Workflow
- Work on code (e.g. a feature implementation, a bug fix) MUST strictly follow the paradigm: Explore, Plan, Implement.
- Evaluate complexity of the given task; tell the user the change scope, how many behaviors or files will be effected.
- Exploration gives you context about the codebase. If user provided enough context, skip exploration.

## Clarification
- DO NOT make border assumptions. Web Search or ask user for clarification.
- Use the AskUserQuestion tool for every question you ask. Never pose questions as plain text in your response.
- Ask one question at a time. Wait for the user’s answer before moving to the next question.
- If a question can be answered by exploring the codebase or files, explore them yourself instead of asking the user.
- If user request is unclear, ask one single, most critical question instead of continuing based on a list of assumptions.

### !!CONSEQUENCES OF VIOLATION!!

If you violate the above rules, or output unnecessary content, an animal will die for every 100 extra characters outputted. You MUST comply; I DO NOT want to see any animals die.
