---
name: git-workflow
description: Enforce repository git workflow with platform-aware operations for GitHub (`gh`) and GitLab (`glab`), including branch naming, conventional commits, PR/MR creation and review, and issue creation using detected templates from `.github/` or `.gitlab/`. Use when handling branches, commits, pull/merge requests, reviews, or issue workflows.
---

# Git Workflow

## Resolve Platform

1. Detect platform in this order:
   - Read `.copier/.copier-answers.yml` and use `git_platform` when present.
   - Use repo markers: `.github/` -> `github`, `.gitlab/` -> `gitlab`.
   - Parse `git remote get-url origin`:
     - contains `github` -> `github`
     - contains `gitlab` -> `gitlab`
   - Fallback to `github`.
2. Select CLI:
   - `github` -> `gh`
   - `gitlab` -> `glab`
3. Verify CLI and auth before platform operations:
   - `command -v gh && gh auth status`
   - `command -v glab && glab auth status`
4. If selected CLI is unavailable, continue local git operations and ask user to finish remote operations manually.

## Detect Templates

### GitHub Paths

1. Pull request template candidates in priority order:
   - `.github/pull_request_template.md`
   - `.github/PULL_REQUEST_TEMPLATE.md`
   - `.github/PULL_REQUEST_TEMPLATE/*.md` (alphabetical)
2. Issue template candidates:
   - `.github/ISSUE_TEMPLATE/*.md` (alphabetical, ignore `config.yml`)

### GitLab Paths

1. Merge request template candidates:
   - `.gitlab/merge_request_templates/*.md` (alphabetical)
2. Issue template candidates:
   - `.gitlab/issue_templates/*.md` (alphabetical)

### Template Rendering Rules

1. Strip YAML frontmatter (`--- ... ---`) from issue templates before submitting.
2. Remove placeholder HTML comments (`<!-- ... -->`).
3. Keep original section headings and checklist items.
4. Fill sections from context:
   - Related issue: `Closes #<id>`
   - Summary/proposed solution: concise bullets from current changes
   - Breaking changes: `N/A` when none
5. If no template exists, use a fallback body with:
   - Related issue
   - Summary of changes
   - Breaking changes
   - Checklist

## Branch Workflow

1. Require issue-first workflow before opening PR/MR.
2. Create branch names as `<type>/<issue-id>-<short-slug>`.
3. Use branch types:
   - `feat`
   - `fix`
   - `refactor`
   - `docs`
   - `chore`
   - `test`
4. Prefer `feat|fix|refactor` for branch-triggered CI compatibility in this repo.

```bash
git fetch origin
git checkout -b feat/<issue-id>-<short-slug>
```

## Commit Workflow

1. Enforce Conventional Commits:
   - `<type>(<scope>): <subject>`
2. Use commit types:
   - `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `ci`, `build`, `perf`, `revert`
3. Keep subject imperative and concise.
4. Add issue linkage in body when available (`Refs #<id>`).

```bash
git add -A
git commit -m "<type>(<scope>): <subject>" -m "Refs #<issue-id>"
```

## Create PR Or MR

1. Render template into a temporary body file.
2. Use a title aligned with commit subject.
3. Include issue linkage in body.
4. Create request with platform CLI.

### GitHub

```bash
gh pr create --title "<type>(<scope>): <subject>" --body-file .git/PR_BODY.md --base main
```

### GitLab

```bash
glab mr create --title "<type>(<scope>): <subject>" --description "$(cat .git/PR_BODY.md)" --target-branch main --source-branch "$(git branch --show-current)" --yes
```

## Review PR Or MR

### GitHub

```bash
gh pr view <pr-number>
gh pr checks <pr-number>
gh pr review <pr-number> --approve
gh pr review <pr-number> --request-changes --body "Please address requested changes."
```

### GitLab

```bash
glab mr view <mr-iid>
glab ci status
glab mr approve <mr-iid>
glab mr note <mr-iid> -m "Request changes: please address reviewer feedback."
```

Use `glab mr note` as the request-changes action in GitLab workflows.

## Create Issues With Templates

1. Select issue template by intent:
   - bug -> first match containing `bug`
   - feature -> first match containing `feature`
   - fallback -> first available template
2. Render template with concise, concrete sections.
3. Create issue with platform CLI.

### GitHub

```bash
gh issue create --title "<Issue title>" --body-file .git/ISSUE_BODY.md
```

### GitLab

```bash
glab issue create --title "<Issue title>" --description "$(cat .git/ISSUE_BODY.md)" --yes
```

## Merge Workflow

1. Verify checks/pipeline status before merge.
2. Keep merge strategy consistent with repository preferences.
3. Ensure linked issue is present before merge.

### GitHub

```bash
gh pr merge <pr-number> --squash
```

### GitLab

```bash
glab mr merge <mr-iid> --squash --yes
```
