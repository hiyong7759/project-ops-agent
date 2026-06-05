from __future__ import annotations

from html import escape

from .models import CommandResult, FixResult, Issue, IssueAnalysis, MergeRequest

ANALYSIS_MARKER = "<!-- project-ops-agent:analysis -->"
NEEDS_INFO_MARKER = "<!-- project-ops-agent:needs-info -->"
BLOCKED_MARKER = "<!-- project-ops-agent:blocked -->"
MR_COMMENT_MARKER = "<!-- project-ops-agent:mr-created -->"
USER_TEST_MARKER = "<!-- project-ops-agent:user-test -->"


def render_issue_analysis(analysis: IssueAnalysis) -> str:
    return f"""{ANALYSIS_MARKER}
## Agent Analysis

- Summary: {escape(analysis.summary)}
- Risk: `{analysis.risk}`
- Expected behavior: {escape(analysis.expected_behavior or "not found")}
- Observed behavior: {escape(analysis.observed_behavior or "not found")}
- Reproduction: {escape(analysis.reproduction or "not found")}
- Ambiguity: {_comma_or_none(analysis.ambiguity_reasons)}
- Policy flags: {_comma_or_none(analysis.policy_flags)}
"""


def render_needs_info(analysis: IssueAnalysis) -> str:
    reasons = analysis.ambiguity_reasons or analysis.policy_flags
    return f"""{NEEDS_INFO_MARKER}
## Agent Needs Info

I need human direction before changing code.

### What I understood
- {escape(analysis.summary)}

### Ambiguous or approval-required points
{_bullet_lines(reasons)}

### Options
- A: Keep current policy and fix only the reported exception.
- B: Change the behavior policy intentionally.
- C: Stop after root-cause analysis and do not create a code fix yet.

### Reply format
`@agent A`
"""


def render_blocked(reason: str) -> str:
    return f"""{BLOCKED_MARKER}
## Agent Blocked

{escape(reason)}
"""


def render_mr_issue_comment(mr: MergeRequest) -> str:
    return f"""{MR_COMMENT_MARKER}
## Agent MR Created

- MR: {mr.web_url}
"""


def render_user_test_request(mr: MergeRequest) -> str:
    return f"""{USER_TEST_MARKER}
## Agent User Test Required

The MR/PR is ready for human user testing.

- MR/PR: {mr.web_url}

After testing, reply in this issue:

- `@agent test-pass`
- `@agent test-fail <reason>`
"""


def render_mr_report(
    issue: Issue,
    analysis: IssueAnalysis,
    fix: FixResult,
    verification: list[CommandResult],
    changed_files: list[str],
    decision_log: list[str],
) -> str:
    tests_ok = all(result.ok for result in verification) if verification else False
    status = "Ready for review" if tests_ok else "Review required - verification incomplete"
    decision = analysis.decision or "No human decision required"
    issue_link = f"#{issue.iid}"
    if issue.web_url:
        issue_link = f'<a href="{escape(issue.web_url)}">#{issue.iid}</a>'

    return f"""# Agent Report

<table>
<tr><td><b>Issue</b></td><td>{issue_link}</td></tr>
<tr><td><b>Risk</b></td><td>{escape(analysis.risk)}</td></tr>
<tr><td><b>Status</b></td><td>{escape(status)}</td></tr>
<tr><td><b>Decision</b></td><td>{escape(decision)}</td></tr>
<tr><td><b>User Test</b></td><td>Required before merge</td></tr>
</table>

## Reviewer Summary

- Cause: {escape(analysis.observed_behavior or analysis.summary)}
- Change: {escape(fix.summary or "See changed files")}
- Verification: {escape(_verification_summary(verification))}
- User test: required; reply on the linked issue with `@agent test-pass` or `@agent test-fail <reason>`
- Attention: {escape(_attention_summary(analysis, verification))}

<details>
<summary>Issue Analysis</summary>

- Summary: {escape(analysis.summary)}
- Expected behavior: {escape(analysis.expected_behavior or "not found")}
- Observed behavior: {escape(analysis.observed_behavior or "not found")}
- Reproduction: {escape(analysis.reproduction or "not found")}
- Related keywords: {_comma_or_none(analysis.related_keywords)}
- Ambiguity reasons: {_comma_or_none(analysis.ambiguity_reasons)}
- Policy flags: {_comma_or_none(analysis.policy_flags)}

</details>

<details>
<summary>Implementation Details</summary>

- Changed files:
{_bullet_lines(changed_files or fix.files_changed)}
- Fix summary: {escape(fix.summary or "not provided")}

</details>

<details>
<summary>Verification</summary>

{_verification_details(verification)}

</details>

<details>
<summary>User Test Gate</summary>

- This MR/PR is not considered done until user testing is recorded.
- Pass format: `@agent test-pass`
- Fail format: `@agent test-fail <reason>`
- The reply should be written on the linked issue so the issue remains the decision source.

</details>

<details>
<summary>Agent Decision Log</summary>

{_bullet_lines(decision_log)}

</details>

Closes #{issue.iid}
"""


def _comma_or_none(items: list[str]) -> str:
    return ", ".join(f"`{escape(item)}`" for item in items) if items else "none"


def _bullet_lines(items: list[str]) -> str:
    if not items:
        return "- none"
    return "\n".join(f"- {escape(item)}" for item in items)


def _verification_summary(results: list[CommandResult]) -> str:
    if not results:
        return "not configured"
    failed = [result.command for result in results if not result.ok]
    if failed:
        return f"failed: {', '.join(failed)}"
    return "all configured commands passed"


def _attention_summary(analysis: IssueAnalysis, results: list[CommandResult]) -> str:
    if any(not result.ok for result in results):
        return "verification failed or incomplete"
    if analysis.risk == "high":
        return "high-risk area, review carefully"
    return "no special attention flagged"


def _verification_details(results: list[CommandResult]) -> str:
    if not results:
        return "- No verification command was configured."
    lines: list[str] = []
    for result in results:
        state = "passed" if result.ok else "failed"
        lines.append(f"### `{escape(result.command)}`")
        lines.append("")
        lines.append(f"- Result: {state}")
        if result.stdout:
            lines.append("")
            lines.append("```text")
            lines.append(result.stdout[-2000:])
            lines.append("```")
        if result.stderr:
            lines.append("")
            lines.append("```text")
            lines.append(result.stderr[-2000:])
            lines.append("```")
        lines.append("")
    return "\n".join(lines).strip()
