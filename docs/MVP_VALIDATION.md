# MVP Validation

This document maps the implementation to the agreed MVP.

## Requirement Checklist

| Requirement | Implemented By |
| --- | --- |
| Issue platform as source of truth | `GitLabClient` or `GitHubClient`, label/comment/MR/PR operations |
| No PostgreSQL | no database package or module |
| Issue state via label | `state.py` |
| Human answers in issue comments | `clarification.py` |
| Stop on ambiguous issue | `IssueAnalyzer`, `PolicyEngine`, `Orchestrator` |
| MR report with expandable details | `templates.py` |
| User testing gate after MR/PR | `agent:needs-user-test`, `@agent test-pass`, `@agent test-fail` |
| Project-specific config | `ProjectProfile`, TOML config |
| External code-fix boundary | `ExternalFixProvider` |
| Verification commands | `CommandRunner` |
| No auto merge | no merge method is implemented in either platform client |

## Local Verification

Run:

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests
```

The tests verify:

- an e2e issue lifecycle from queued, clarification, MR/PR creation, user testing, and done
- agent labels are mutually exclusive
- ambiguous issues move to `agent:needs-info`
- Issue comments are used for clarification
- answered issues can proceed to MR creation with injected runners
- MR creation moves the issue to user testing instead of done
- user test pass/fail comments move the issue to done or changes-requested
- MR reports use compact summary and expandable details

## Operational Verification

Before connecting to a real GitLab or GitHub project:

1. Create labels listed in `docs/OPERATING_RULES.md`.
2. Create a project access token with the minimum required scope.
3. Set `GITLAB_TOKEN`.
4. Create one issue labeled `agent:queued`.
5. Run `scan`.
6. Confirm the issue receives `agent:analyzing`.
7. Confirm ambiguous issues receive `agent:needs-info`.
8. Reply in the issue with `@agent A`.
9. Configure a safe `fix.command`.
10. Confirm the MR report has table and details sections.
11. Confirm the issue is labeled `agent:needs-user-test`.
12. Reply `@agent test-pass`.
13. Confirm the issue moves to `agent:done`.
