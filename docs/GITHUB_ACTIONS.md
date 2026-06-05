# GitHub Actions MVP

Personal GitHub repositories can validate the same operations loop without a company GitLab runner. This repository includes `.github/workflows/project-ops-agent.yml` for the `hiyong7759/project-ops-agent` MVP validation target.

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

The workflow name shown in GitHub Actions is:

```text
Project Ops Agent MVP
```

It supports manual runs with `workflow_dispatch`. A 10-minute schedule is included in the workflow file as a commented option so the MVP can start with explicit runs.

The workflow runs this command:

```bash
python -m project_ops_agent.cli scan --config configs/projects/github.sample.project.toml
```

with these repository permissions:

```yaml
permissions:
  contents: write
  issues: write
  pull-requests: write
```

The sample GitHub profile uses:

```toml
[github]
owner = "hiyong7759"
repo = "project-ops-agent"
repo_http_url = "https://github.com/hiyong7759/project-ops-agent.git"

[workspace]
use_current_checkout = true
```

That makes the agent operate on the repository already checked out by `actions/checkout`, avoiding a second clone and private-repository credential issues.

## Manual Validation

1. Push the workflow and sample config changes to `main`.
2. In GitHub, open **Actions**.
3. Select **Project Ops Agent MVP**.
4. Click **Run workflow**.
5. Keep the branch as `main`.
6. Click **Run workflow** again in the dialog.

The included sample profile keeps `fix.command = ""`, so the first live run is best used to verify GitHub issue discovery, analysis comments, labels, and the `agent:needs-info` loop. To validate branch push, PR creation, and `agent:needs-user-test`, configure a safe project-specific `fix.command` first.

Before running against real issues, verify locally from WSL:

```bash
cd ~/workspace/project-ops-agent
export PYTHONPATH=src
export PYTHONDONTWRITEBYTECODE=1
python3 -m unittest discover -s tests
```

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

## Test Issue Example

Create an issue and add the `agent:queued` label:

```markdown
Title: Add a smoke test for the agent CLI

Body:
현재 GitHub Actions에서 project-ops-agent CLI가 기본 테스트 경로로 실행되는지 확인하고 싶습니다.

기대 동작:
- `python -m unittest discover -s tests`가 성공해야 합니다.
- PR 본문에는 table과 details 기반 Agent Report가 있어야 합니다.

재현/검증:
- GitHub Actions의 Project Ops Agent MVP workflow를 수동 실행합니다.
```

If the agent asks for clarification, answer in the issue comment:

```text
@agent A
```

After the PR is created and the issue moves to `agent:needs-user-test`, test the PR manually. Record the result on the linked issue:

```text
@agent test-pass
```

or:

```text
@agent test-fail workflow still fails during unittest discovery
```

## Token Notes

The default `GITHUB_TOKEN` is enough for the MVP when workflow permissions include:

```yaml
permissions:
  contents: write
  issues: write
  pull-requests: write
```

For stricter organizations or cross-repository tests, use a fine-grained personal access token with repository contents, issues, and pull request write access.
