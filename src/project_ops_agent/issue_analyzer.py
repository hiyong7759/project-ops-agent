from __future__ import annotations

import re

from .models import Comment, Issue, IssueAnalysis
from .policy import classify_risk


EXPECTED_MARKERS = ("expected", "기대", "원하는", "되어야", "해야", "정상")
OBSERVED_MARKERS = ("actual", "현재", "실제", "오류", "에러", "버그", "안됨", "실패", "장애")
REPRO_MARKERS = ("reproduce", "repro", "steps", "재현", "단계", "환경", "조건")
MULTIPLE_PATH_MARKERS = ("또는", "혹은", "아니면", "선택", "정책", "방향", "or ")

POLICY_KEYWORDS = {
    "db_migration": ("migration", "schema", "table", "column", "db ", "database", "마이그레이션", "스키마", "테이블", "컬럼"),
    "auth_change": ("auth", "login", "permission", "role", "인증", "로그인", "권한", "역할"),
    "payment_change": ("payment", "billing", "invoice", "결제", "청구", "정산"),
    "production_config_change": ("production", "prod", ".env", "config", "운영 설정", "환경변수"),
    "destructive_change": ("delete", "drop", "truncate", "remove", "삭제", "제거", "폐기"),
}


class IssueAnalyzer:
    def analyze(self, issue: Issue, comments: list[Comment] | None = None, decision: str = "") -> IssueAnalysis:
        comments = comments or []
        text = _combined_text(issue, comments)
        lowered = text.lower()
        ambiguity: list[str] = []

        if len(_words(text)) < 8 and len(text) < 80:
            ambiguity.append("requirement_ambiguous")
        if not _has_any(lowered, EXPECTED_MARKERS):
            ambiguity.append("expected_behavior_missing")
        if not _has_any(lowered, REPRO_MARKERS):
            ambiguity.append("reproduction_missing")
        if _has_any(lowered, MULTIPLE_PATH_MARKERS):
            ambiguity.append("multiple_solution_paths")

        policy_flags = [
            flag
            for flag, keywords in POLICY_KEYWORDS.items()
            if _has_any(lowered, keywords)
        ]

        if decision:
            ambiguity = []

        return IssueAnalysis(
            issue_iid=issue.iid,
            summary=_first_sentence(issue.title, issue.description),
            observed_behavior=_extract_line(text, OBSERVED_MARKERS),
            expected_behavior=_extract_line(text, EXPECTED_MARKERS),
            reproduction=_extract_line(text, REPRO_MARKERS),
            ambiguity_reasons=ambiguity,
            policy_flags=policy_flags,
            risk=classify_risk(text, policy_flags),
            related_keywords=_related_keywords(text),
            decision=decision,
        )


def _combined_text(issue: Issue, comments: list[Comment]) -> str:
    comment_text = "\n".join(comment.body for comment in comments)
    return f"{issue.title}\n{issue.description}\n{comment_text}".strip()


def _has_any(text: str, markers: tuple[str, ...]) -> bool:
    return any(marker.lower() in text for marker in markers)


def _words(text: str) -> list[str]:
    return re.findall(r"[\w가-힣]+", text)


def _first_sentence(title: str, description: str) -> str:
    if title:
        return title.strip()
    first = re.split(r"[\r\n.]", description.strip())[0]
    return first or "No issue summary"


def _extract_line(text: str, markers: tuple[str, ...]) -> str:
    for line in text.splitlines():
        lowered = line.lower()
        if any(marker.lower() in lowered for marker in markers):
            return line.strip("-: \t")
    return ""


def _related_keywords(text: str) -> list[str]:
    words = _words(text.lower())
    skip = {"the", "and", "with", "for", "from", "this", "that", "입니다", "합니다"}
    result: list[str] = []
    for word in words:
        if len(word) < 3 or word in skip:
            continue
        if word not in result:
            result.append(word)
        if len(result) >= 8:
            break
    return result

