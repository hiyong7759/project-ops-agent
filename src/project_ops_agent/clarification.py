from __future__ import annotations

import re

from .models import Comment

AGENT_COMMENT_MARKER = "<!-- project-ops-agent:"
ANSWER_RE = re.compile(r"@agent\s+(?P<answer>A|B|C|proceed|approve)\b", re.IGNORECASE)
CUSTOM_DIRECTION_RE = re.compile(
    r"@agent\s+(?P<keyword>direction|custom|방향|지시|요청)\s*:?\s*(?P<direction>.+)",
    re.IGNORECASE | re.DOTALL,
)
USER_TEST_RE = re.compile(r"@agent\s+test-(?P<result>pass|fail)\b(?P<reason>.*)", re.IGNORECASE | re.DOTALL)


def latest_agent_decision(comments: list[Comment]) -> str:
    return _latest_agent_decision(comments)


def latest_agent_decision_after_marker(comments: list[Comment], marker: str) -> str:
    return _latest_agent_decision(comments, stop_marker=marker)


def latest_user_test_result(comments: list[Comment]) -> tuple[str, str]:
    return _latest_user_test_result(comments)


def latest_user_test_result_after_marker(comments: list[Comment], marker: str) -> tuple[str, str]:
    return _latest_user_test_result(comments, stop_marker=marker)


def has_marker(comments: list[Comment], marker: str) -> bool:
    return any(marker in comment.body for comment in comments)


def _latest_user_test_result(comments: list[Comment], stop_marker: str = "") -> tuple[str, str]:
    for comment in reversed(comments):
        if stop_marker and stop_marker in comment.body:
            return "", ""
        if _is_agent_comment(comment):
            continue
        match = USER_TEST_RE.search(comment.body)
        if match:
            result = match.group("result").lower()
            reason = match.group("reason").strip(" :-\r\n\t")
            return result, reason
    return "", ""


def _latest_agent_decision(comments: list[Comment], stop_marker: str = "") -> str:
    for comment in reversed(comments):
        if stop_marker and stop_marker in comment.body:
            return ""
        if _is_agent_comment(comment):
            continue
        match = ANSWER_RE.search(comment.body)
        if match:
            return _format_answer(match.group("answer"))
        custom_match = CUSTOM_DIRECTION_RE.search(comment.body)
        if custom_match:
            direction = _compact(custom_match.group("direction"))
            if direction:
                return f"@agent 방향: {direction}"
    return ""


def _format_answer(answer: str) -> str:
    lowered = answer.lower()
    if lowered in {"proceed", "approve"}:
        return f"@agent {lowered}"
    return f"@agent {answer.upper()}"


def _compact(text: str) -> str:
    return " ".join(text.strip().split())


def _is_agent_comment(comment: Comment) -> bool:
    return AGENT_COMMENT_MARKER in comment.body
