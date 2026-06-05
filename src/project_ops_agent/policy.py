from __future__ import annotations

from fnmatch import fnmatch

from .models import IssueAnalysis, PolicySettings


class PolicyEngine:
    def __init__(self, settings: PolicySettings) -> None:
        self.settings = settings

    def requires_human_direction(self, analysis: IssueAnalysis) -> bool:
        if analysis.decision:
            return False
        configured = set(self.settings.require_info_when)
        if any(reason in configured for reason in analysis.ambiguity_reasons):
            return True
        approval_required = set(self.settings.require_approval_before_fix_when)
        return any(flag in approval_required for flag in analysis.policy_flags)

    def forbidden_changed_paths(self, paths: list[str]) -> list[str]:
        forbidden: list[str] = []
        for path in paths:
            normalized = path.replace("\\", "/")
            if any(fnmatch(normalized, pattern) for pattern in self.settings.forbidden_paths):
                forbidden.append(path)
        return forbidden


def classify_risk(text: str, policy_flags: list[str]) -> str:
    lowered = text.lower()
    high_keywords = (
        "payment",
        "billing",
        "auth",
        "permission",
        "migration",
        "schema",
        "production",
        "secret",
        "결제",
        "인증",
        "권한",
        "마이그레이션",
        "운영",
    )
    medium_keywords = ("cache", "batch", "timeout", "retry", "api", "장애", "배치", "타임아웃")
    if policy_flags or any(keyword in lowered for keyword in high_keywords):
        return "high"
    if any(keyword in lowered for keyword in medium_keywords):
        return "medium"
    return "low"

