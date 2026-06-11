from __future__ import annotations

AGENT_STATES = (
    "agent:queued",
    "agent:analyzing",
    "agent:needs-info",
    "agent:fixing",
    "agent:verifying",
    "agent:mr-created",
    "agent:needs-user-test",
    "agent:changes-requested",
    "agent:blocked",
    "agent:done",
)

PROCESSABLE_STATES = (
    "agent:queued",
    "agent:needs-info",
    "agent:blocked",
    "agent:needs-user-test",
)

RISK_LABELS = ("risk:low", "risk:medium", "risk:high")
REQUIRED_LABELS = AGENT_STATES + RISK_LABELS


def current_agent_state(labels: list[str]) -> str:
    for label in labels:
        if label in AGENT_STATES:
            return label
    return ""


def with_agent_state(labels: list[str], next_state: str) -> list[str]:
    if next_state not in AGENT_STATES:
        raise ValueError(f"Unknown agent state: {next_state}")
    cleaned = [label for label in labels if label not in AGENT_STATES]
    return _stable_unique([*cleaned, next_state])


def with_risk_label(labels: list[str], risk: str) -> list[str]:
    risk_label = f"risk:{risk}"
    if risk_label not in RISK_LABELS:
        raise ValueError(f"Unknown risk: {risk}")
    cleaned = [label for label in labels if label not in RISK_LABELS]
    return _stable_unique([*cleaned, risk_label])


def _stable_unique(labels: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for label in labels:
        if label and label not in seen:
            seen.add(label)
            result.append(label)
    return result
