# GitHub Actions MVP

Personal GitHub repositories can validate the same operations loop without a company GitLab runner.

## Flow

```text
GitHub Issue labeled agent:queued
  -> scheduled or manual GitHub Actions workflow
  -> project_ops_agent scan
  -> issue analysis comment
  -> agent:needs-info if unclear
  -> human replies @agent A in the issue
  -> next workflow run resumes
  -> branch push
  -> Pull Request with expandable Agent Report
  -> issue labeled agent:needs-user-test
  -> human replies @agent test-pass or @agent test-fail
```

## Workflow

Create `.github/workflows/project-ops-agent.yml` in the personal test repository:

```yaml
name: Project Ops Agent

on:
  workflow_dispatch:
  schedule:
    - cron: "*/10 * * * *"

permissions:
  contents: write
  issues: write
  pull-requests: write

jobs:
  agent:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: python -m pip install -e .
      - run: python -m project_ops_agent.cli scan --config configs/projects/github.sample.project.toml
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          PYTHONDONTWRITEBYTECODE: "1"
```

The sample GitHub profile uses:

```toml
[workspace]
use_current_checkout = true
```

That makes the agent operate on the repository already checked out by `actions/checkout`, avoiding a second clone and private-repository credential issues.

## Labels

Create these labels in the repository before running the workflow:

```text
agent:queued
agent:analyzing
agent:needs-info
agent:fixing
agent:verifying
agent:mr-created
agent:needs-user-test
agent:changes-requested
agent:blocked
agent:done
risk:low
risk:medium
risk:high
```

The name `agent:mr-created` is kept for compatibility with the GitLab flow. In GitHub it means a Pull Request was created.

## Token Notes

The default `GITHUB_TOKEN` is enough for the MVP when workflow permissions include:

```yaml
permissions:
  contents: write
  issues: write
  pull-requests: write
```

For stricter organizations or cross-repository tests, use a fine-grained personal access token with repository contents, issues, and pull request write access.
