from __future__ import annotations

from html import escape

from .models import CommandResult, FixResult, Issue, IssueAnalysis, MergeRequest

ANALYSIS_MARKER = "<!-- project-ops-agent:analysis -->"
NEEDS_INFO_MARKER = "<!-- project-ops-agent:needs-info -->"
BLOCKED_MARKER = "<!-- project-ops-agent:blocked -->"
MR_COMMENT_MARKER = "<!-- project-ops-agent:mr-created -->"
USER_TEST_MARKER = "<!-- project-ops-agent:user-test -->"
USER_TEST_RESULT_MARKER = "<!-- project-ops-agent:user-test-result -->"
AGENT_VISIBLE_NOTICE = """> **작성 주체:** Project Ops Agent
> 작성 계정이 사용자와 같아 보여도 이 표식이 있으면 에이전트가 작성한 운영 댓글입니다.
"""

AMBIGUITY_LABELS = {
    "requirement_ambiguous": "요구사항이 모호함",
    "expected_behavior_missing": "기대 동작 누락",
    "reproduction_missing": "재현 조건 누락",
    "multiple_solution_paths": "해결 방향이 여러 갈래임",
}
POLICY_FLAG_LABELS = {
    "db_migration": "DB 마이그레이션",
    "auth_change": "인증/권한 변경",
    "payment_change": "결제 변경",
    "production_config_change": "운영 설정 변경",
    "destructive_change": "삭제/파괴적 변경",
}
RISK_LABELS = {
    "low": "낮음",
    "medium": "중간",
    "high": "높음",
}


def render_issue_analysis(analysis: IssueAnalysis) -> str:
    return f"""{ANALYSIS_MARKER}
{AGENT_VISIBLE_NOTICE}
## 에이전트 분석

- 요약: {escape(analysis.summary)}
- 위험도: `{_risk_label(analysis.risk)}`
- 기대 동작: {escape(analysis.expected_behavior or "확인되지 않음")}
- 현재 동작: {escape(analysis.observed_behavior or "확인되지 않음")}
- 재현 조건: {escape(analysis.reproduction or "확인되지 않음")}
- 모호한 지점: {_comma_or_none(analysis.ambiguity_reasons, AMBIGUITY_LABELS)}
- 정책 확인 필요: {_comma_or_none(analysis.policy_flags, POLICY_FLAG_LABELS)}
"""


def render_needs_info(analysis: IssueAnalysis) -> str:
    reasons = analysis.ambiguity_reasons or analysis.policy_flags
    return f"""{NEEDS_INFO_MARKER}
{AGENT_VISIBLE_NOTICE}
## 에이전트 추가 정보 필요

코드를 변경하기 전에 사용자의 방향 결정이 필요합니다.

### 제가 이해한 내용
- {escape(analysis.summary)}

### 모호하거나 승인 확인이 필요한 지점
{_bullet_lines(reasons, {**AMBIGUITY_LABELS, **POLICY_FLAG_LABELS})}

### 선택지
- A: 현재 정책은 유지하고 보고된 예외만 수정합니다.
- B: 동작 정책을 의도적으로 변경합니다.
- C: 원인 분석까지만 진행하고 코드 수정은 만들지 않습니다.

### 답변 형식
제시된 선택지를 그대로 고를 수 있습니다.

```text
@agent A
```

선택지 밖의 방향이 더 맞다면 직접 지시할 수 있습니다.

```text
@agent 방향: 현재 정책은 유지하되 로그인 실패 메시지만 사용자가 이해하기 쉽게 바꿔주세요.
```
"""


def render_blocked(reason: str) -> str:
    return f"""{BLOCKED_MARKER}
{AGENT_VISIBLE_NOTICE}
## 에이전트 중단

{escape(reason)}
"""


def render_mr_issue_comment(mr: MergeRequest) -> str:
    return f"""{MR_COMMENT_MARKER}
{AGENT_VISIBLE_NOTICE}
## 에이전트 MR/PR 생성됨

- MR: {mr.web_url}
"""


def render_user_test_request(
    mr: MergeRequest,
    analysis: IssueAnalysis | None = None,
    changed_files: list[str] | None = None,
    verification: list[CommandResult] | None = None,
) -> str:
    checklist = ""
    if analysis:
        checklist = f"""
### 먼저 확인할 것
{_user_test_checklist(analysis, changed_files or [], verification or [])}
"""
    return f"""{USER_TEST_MARKER}
{AGENT_VISIBLE_NOTICE}
## 사용자 테스트 필요

MR/PR이 생성되었습니다. 병합 전 실제 사용자 테스트 결과를 이 이슈 댓글에 남겨야 합니다.

- MR/PR: {mr.web_url}
{checklist}

테스트 후 이 이슈에 아래 형식으로 답변하세요.

- `@agent test-pass`
- `@agent test-fail <사유>`
"""


def render_user_test_pass_confirmation() -> str:
    return f"""{USER_TEST_RESULT_MARKER}
{AGENT_VISIBLE_NOTICE}
## 사용자 테스트 통과 확인

이슈 댓글에서 `@agent test-pass`가 확인되었습니다.
"""


def render_user_test_fail_confirmation(reason: str) -> str:
    return f"""{USER_TEST_RESULT_MARKER}
{AGENT_VISIBLE_NOTICE}
## 변경 요청됨

사용자 테스트 실패가 기록되었습니다: {escape(reason)}
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
    status = "검토 준비됨" if tests_ok else "검토 필요 - 검증이 완료되지 않음"
    decision = analysis.decision or "사용자 결정 불필요"
    issue_link = f"#{issue.iid}"
    review_files = changed_files or fix.files_changed
    if issue.web_url:
        issue_link = f'<a href="{escape(issue.web_url)}">#{issue.iid}</a>'

    return f"""# 에이전트 보고서

{AGENT_VISIBLE_NOTICE}
<table>
<tr><td><b>이슈</b></td><td>{issue_link}</td></tr>
<tr><td><b>위험도</b></td><td>{escape(_risk_label(analysis.risk))}</td></tr>
<tr><td><b>상태</b></td><td>{escape(status)}</td></tr>
<tr><td><b>사용자 결정</b></td><td>{escape(decision)}</td></tr>
<tr><td><b>사용자 테스트</b></td><td>병합 전 필요</td></tr>
</table>

## 사용자가 먼저 확인할 것

{_user_test_checklist(analysis, review_files, verification)}

## 코드 리뷰 참고

{_code_review_hints(analysis, review_files, verification)}

## 검토 요약

- 원인/현상: {escape(analysis.observed_behavior or analysis.summary)}
- 변경 요약: {escape(fix.summary or "변경 파일을 확인하세요.")}
- 검증: {escape(_verification_summary(verification))}
- 사용자 테스트: 필요합니다. 연결된 이슈에 `@agent test-pass` 또는 `@agent test-fail <사유>`로 답변하세요.
- 주의 사항: {escape(_attention_summary(analysis, verification))}

<details>
<summary>이슈 분석</summary>

- 요약: {escape(analysis.summary)}
- 기대 동작: {escape(analysis.expected_behavior or "확인되지 않음")}
- 현재 동작: {escape(analysis.observed_behavior or "확인되지 않음")}
- 재현 조건: {escape(analysis.reproduction or "확인되지 않음")}
- 관련 키워드: {_comma_or_none(analysis.related_keywords)}
- 모호한 지점: {_comma_or_none(analysis.ambiguity_reasons, AMBIGUITY_LABELS)}
- 정책 확인 필요: {_comma_or_none(analysis.policy_flags, POLICY_FLAG_LABELS)}

</details>

<details>
<summary>구현 상세</summary>

- 변경 파일:
{_bullet_lines(review_files)}
- 수정 요약: {escape(fix.summary or "제공되지 않음")}

</details>

<details>
<summary>검증</summary>

{_verification_details(verification)}

</details>

<details>
<summary>사용자 테스트 게이트</summary>

- 이 MR/PR은 사용자 테스트 결과가 기록되기 전까지 완료로 간주하지 않습니다.
- 통과 형식: `@agent test-pass`
- 실패 형식: `@agent test-fail <사유>`
- 이슈가 의사결정의 단일 기준으로 남도록 답변은 반드시 연결된 이슈 댓글에 작성해야 합니다.

</details>

<details>
<summary>에이전트 결정 로그</summary>

{_bullet_lines(decision_log)}

</details>

관련 이슈: #{issue.iid}
"""


def _comma_or_none(items: list[str], labels: dict[str, str] | None = None) -> str:
    if not items:
        return "없음"
    return ", ".join(f"`{escape(_label(item, labels))}`" for item in items)


def _bullet_lines(items: list[str], labels: dict[str, str] | None = None) -> str:
    if not items:
        return "- 없음"
    return "\n".join(f"- {escape(_label(item, labels))}" for item in items)


def _verification_summary(results: list[CommandResult]) -> str:
    if not results:
        return "검증 명령이 설정되지 않음"
    failed = [result.command for result in results if not result.ok]
    if failed:
        return f"실패: {', '.join(failed)}"
    return "설정된 모든 검증 명령 통과"


def _user_test_checklist(analysis: IssueAnalysis, changed_files: list[str], results: list[CommandResult]) -> str:
    lines: list[str] = []
    if analysis.reproduction:
        lines.append(f"- 재현 조건으로 다시 확인: {escape(analysis.reproduction)}")
    else:
        lines.append("- 이슈에 적힌 문제 상황이 더 이상 발생하지 않는지 확인합니다.")
    if analysis.expected_behavior:
        lines.append(f"- 기대 동작 확인: {escape(analysis.expected_behavior)}")
    else:
        lines.append("- 사용자가 기대하는 정상 동작과 실제 결과가 맞는지 확인합니다.")
    if changed_files:
        lines.append(f"- 변경 범위 확인: {_inline_items(changed_files)}")
    lines.append(f"- 검증 결과 확인: {escape(_verification_summary(results))}")
    if any(not result.ok for result in results):
        lines.append("- 실패한 검증이 있으면 통과 댓글을 남기기 전에 원인을 확인합니다.")
    return "\n".join(lines)


def _code_review_hints(analysis: IssueAnalysis, changed_files: list[str], results: list[CommandResult]) -> str:
    lines: list[str] = []
    if changed_files:
        lines.append(f"- 우선 볼 파일: {_inline_items(changed_files)}")
    else:
        lines.append("- 변경 파일 목록이 비어 있으면 PR Files changed 탭에서 실제 diff를 확인합니다.")
    lines.append("- 리뷰 관점: 변경이 이슈 범위와 사용자 결정에 맞는지 확인합니다.")
    if analysis.risk != "low":
        lines.append(f"- 위험도: {escape(_risk_label(analysis.risk))}. 정책 변경이나 영향 범위를 더 신중히 봅니다.")
    if any(not result.ok for result in results):
        lines.append("- 검증 실패가 있으면 실패 로그를 먼저 보고 merge를 보류합니다.")
    lines.append("- 상세 구현과 로그는 아래 접이식 섹션을 펼쳐 확인합니다.")
    return "\n".join(lines)


def _inline_items(items: list[str], limit: int = 5) -> str:
    visible = items[:limit]
    rendered = ", ".join(f"`{escape(item)}`" for item in visible)
    if len(items) > limit:
        rendered = f"{rendered} 외 {len(items) - limit}개"
    return rendered


def _attention_summary(analysis: IssueAnalysis, results: list[CommandResult]) -> str:
    if any(not result.ok for result in results):
        return "검증 실패 또는 미완료"
    if analysis.risk == "high":
        return "고위험 영역이므로 신중한 검토 필요"
    return "특별한 주의 사항 없음"


def _verification_details(results: list[CommandResult]) -> str:
    if not results:
        return "- 검증 명령이 설정되지 않았습니다."
    lines: list[str] = []
    for result in results:
        state = "통과" if result.ok else "실패"
        lines.append(f"### `{escape(result.command)}`")
        lines.append("")
        lines.append(f"- 결과: {state}")
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


def _risk_label(risk: str) -> str:
    label = RISK_LABELS.get(risk, risk)
    return f"{label} ({risk})" if label != risk else risk


def _label(item: str, labels: dict[str, str] | None) -> str:
    if not labels:
        return item
    label = labels.get(item, item)
    return f"{label} ({item})" if label != item else item
