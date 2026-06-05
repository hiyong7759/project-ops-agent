# Architecture

## Purpose

The agent exists to reduce production maintenance effort without hiding operational decisions.

The reviewer-facing MR is the primary output. The MR must be short by default and expandable on demand.

## Source of Truth

The selected issue platform is the only source of truth in the MVP. GitLab is the primary production target, while GitHub is supported for personal validation.

| Concern | Platform Object |
| --- | --- |
| Work request | Issue |
| Agent state | Issue label |
| Human decision | Issue comment |
| Agent analysis log | Issue comment |
| Code review | Merge Request or Pull Request |
| Reviewer report | MR or PR description |
| Code history | Commit message |

## Components

```text
Issue Platform
  -> GitLabClient or GitHubClient
  -> Orchestrator
  -> IssueAnalyzer
  -> PolicyEngine
  -> ClarificationGate
  -> Workspace GitRunner
  -> ExternalFixProvider
  -> CommandRunner
  -> MRReportBuilder
  -> MR or PR
```

## Runtime Flow

```text
agent:queued
  -> agent:analyzing
  -> agent:needs-info
  -> wait for @agent answer
  -> agent:fixing
  -> agent:verifying
  -> agent:needs-user-test
  -> agent:done
```

The agent never edits code while an issue is in `agent:needs-info`.

The agent never treats MR/PR creation as user testing. MR/PR creation only opens the review and user-test gate. The issue remains active until `@agent test-pass` is recorded on the linked issue.

## Why No Database

The MVP uses GitLab labels and comments as durable state.

This keeps operations simple:

- no state synchronization problem
- no separate audit database
- no messenger-to-issue answer mapping
- every decision remains visible next to the issue and MR

A database can be added later for dashboards, metrics, and multi-project scheduling. It is not required for the first operational loop.

## Fix Execution Boundary

The agent does not hard-code project-specific source changes.

Instead, the project profile can provide a `fix.command`. That command receives a normalized JSON context and is responsible for editing files in the checked-out workspace.

This gives each project control over how fixes are produced:

- Codex CLI wrapper
- internal LLM tool
- rule-based repair script
- manual patch generator

The orchestrator still controls labels, policy gates, tests, commits, pushes, and MR reports.
