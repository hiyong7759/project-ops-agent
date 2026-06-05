# Project Ops Agent

This repository contains an MVP implementation of a single-project operations agent.

The agent treats the selected issue platform as the only source of truth. GitLab is the primary target, and GitHub is supported for personal MVP validation.

- Issue: work request and human decisions
- Label: agent state and risk
- Issue Comment: analysis, clarification request, and progress log
- Merge Request or Pull Request: code review unit and reviewer-facing report
- Git Commit: code change history only

The MVP deliberately does not use PostgreSQL, Jira, or messenger-based replies.

## Goal

Reduce the amount of human effort required to operate production source code while keeping reviewer trust high.

A reviewer should be able to open the MR and quickly understand:

- which issue triggered the work
- what the agent analyzed
- why the selected fix path was used
- what changed
- how the change was verified
- which details can be expanded only when needed

## What This MVP Does

- Finds issues labeled `agent:queued`
- Moves one issue through `agent:*` labels
- Analyzes issue text and comments for ambiguity
- Stops and asks for direction when the issue is unclear
- Accepts answers only from issue comments such as `@agent A`
- Runs a project-specific external fix command when the issue is actionable
- Runs configured verification commands
- Creates an MR or PR with a structured, expandable report
- Waits for user testing to be recorded with `@agent test-pass` or `@agent test-fail`

## What This MVP Does Not Do

- It does not merge MRs
- It does not accept answers from Naver Works
- It does not store state in a database
- It does not read production logs directly
- It does not invent project-specific fixes by itself unless a `fix.command` is configured

## Quick Start

Create a project profile:

```toml
[project]
key = "order-api"
name = "Order API"
platform = "gitlab"

[gitlab]
url = "https://gitlab.company.local"
project_id = "123"
default_branch = "main"
repo_http_url = "https://gitlab.company.local/group/order-api.git"

[agent]
branch_prefix = "agent"
can_push_branch = true
can_create_mr = true
can_merge = false

[commands]
install = "npm ci"
lint = "npm run lint"
test = "npm test"

[fix]
command = "codex-fix-issue"
timeout_seconds = 1800

[policy]
require_info_when = [
  "requirement_ambiguous",
  "expected_behavior_missing",
  "reproduction_missing",
  "multiple_solution_paths"
]
require_approval_before_fix_when = [
  "db_migration",
  "auth_change",
  "payment_change",
  "production_config_change",
  "destructive_change"
]
forbidden_paths = [
  ".gitlab-ci.yml",
  "infra/**",
  "secrets/**"
]

[review]
reviewers = ["backend-lead"]

[workspace]
root = "workspaces"
```

Run against queued issues:

```powershell
$env:GITLAB_TOKEN = "..."
python -m project_ops_agent.cli scan --config configs/projects/sample.project.toml
```

For GitHub:

```powershell
$env:GITHUB_TOKEN = "..."
python -m project_ops_agent.cli scan --config configs/projects/github.sample.project.toml
```

Process a single issue:

```powershell
$env:GITLAB_TOKEN = "..."
python -m project_ops_agent.cli process --config configs/projects/sample.project.toml --issue 123
```

Run local tests:

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests
```

## External Fix Command Contract

The agent sends JSON to the configured `fix.command` through stdin. The command runs inside the checked-out project workspace.

Input shape:

```json
{
  "issue": {
    "iid": 123,
    "title": "...",
    "description": "...",
    "labels": []
  },
  "analysis": {
    "summary": "...",
    "risk": "low",
    "ambiguity_reasons": []
  },
  "decision": "@agent A",
  "project": {
    "key": "order-api",
    "name": "Order API"
  }
}
```

Output shape:

```json
{
  "success": true,
  "summary": "Added null guard and regression test.",
  "files_changed": ["src/order/status.ts", "test/order/status.test.ts"],
  "commit_message": "Fix order status null handling\n\nRefs #123"
}
```

If no `fix.command` is configured, the agent can still analyze issues and ask for clarification, but it blocks before code modification.

## User Testing Gate

The MR or PR is not treated as user testing by itself. It is the review and test entry point.

After the MR/PR is created, the issue moves to:

```text
agent:needs-user-test
```

The user or approver tests the change, then replies on the linked issue:

```text
@agent test-pass
```

or:

```text
@agent test-fail still fails when updating order status
```

The agent then moves the issue to `agent:done` or `agent:changes-requested`.
