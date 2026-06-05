from __future__ import annotations

import re

from .models import Comment

ANSWER_RE = re.compile(r"@agent\s+(?P<answer>A|B|C|proceed|approve)\b", re.IGNORECASE)
USER_TEST_RE = re.compile(r"@agent\s+test-(?P<result>pass|fail)\b(?P<reason>.*)", re.IGNORECASE | re.DOTALL)


def latest_agent_decision(comments: list[Comment]) -> str:
    for comment in reversed(comments):
        match = ANSWER_RE.search(comment.body)
        if match:
            return f"@agent {match.group('answer').upper()}"
    return ""


def latest_agent_decision_after_marker(comments: list[Comment], marker: str) -> str:
    for comment in reversed(comments):
        if marker in comment.body:
            return ""
        match = ANSWER_RE.search(comment.body)
        if match:
            return f"@agent {match.group('answer').upper()}"
    return ""


def latest_user_test_result(comments: list[Comment]) -> tuple[str, str]:
    for comment in reversed(comments):
        match = USER_TEST_RE.search(comment.body)
        if match:
            result = match.group("result").lower()
            reason = match.group("reason").strip(" :-\r\n\t")
            return result, reason
    return "", ""


def has_marker(comments: list[Comment], marker: str) -> bool:
    return any(marker in comment.body for comment in comments)
