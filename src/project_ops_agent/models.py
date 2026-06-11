from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class Issue:
    iid: int
    title: str
    description: str = ""
    labels: list[str] = field(default_factory=list)
    web_url: str = ""
    state: str = "opened"

    @classmethod
    def from_gitlab(cls, payload: dict[str, Any]) -> "Issue":
        return cls(
            iid=int(payload["iid"]),
            title=str(payload.get("title", "")),
            description=str(payload.get("description") or ""),
            labels=list(payload.get("labels") or []),
            web_url=str(payload.get("web_url") or ""),
            state=str(payload.get("state") or "opened"),
        )

    @classmethod
    def from_github(cls, payload: dict[str, Any]) -> "Issue":
        raw_labels = payload.get("labels") or []
        labels = [
            str(label.get("name") if isinstance(label, dict) else label)
            for label in raw_labels
        ]
        return cls(
            iid=int(payload["number"]),
            title=str(payload.get("title", "")),
            description=str(payload.get("body") or ""),
            labels=labels,
            web_url=str(payload.get("html_url") or ""),
            state=str(payload.get("state") or "open"),
        )


@dataclass(slots=True)
class Comment:
    id: int
    body: str
    author_username: str = ""
    created_at: str = ""

    @classmethod
    def from_gitlab(cls, payload: dict[str, Any]) -> "Comment":
        author = payload.get("author") or {}
        return cls(
            id=int(payload["id"]),
            body=str(payload.get("body") or ""),
            author_username=str(author.get("username") or ""),
            created_at=str(payload.get("created_at") or ""),
        )

    @classmethod
    def from_github(cls, payload: dict[str, Any]) -> "Comment":
        user = payload.get("user") or {}
        return cls(
            id=int(payload["id"]),
            body=str(payload.get("body") or ""),
            author_username=str(user.get("login") or ""),
            created_at=str(payload.get("created_at") or ""),
        )


@dataclass(slots=True)
class GitLabSettings:
    url: str
    project_id: str
    default_branch: str
    repo_http_url: str = ""


@dataclass(slots=True)
class GitHubSettings:
    owner: str
    repo: str
    default_branch: str
    repo_http_url: str = ""
    api_url: str = "https://api.github.com"


@dataclass(slots=True)
class AgentSettings:
    branch_prefix: str = "agent"
    can_push_branch: bool = True
    can_create_mr: bool = True
    can_merge: bool = False


@dataclass(slots=True)
class CommandsSettings:
    install: str = ""
    lint: str = ""
    test: str = ""


@dataclass(slots=True)
class FixSettings:
    command: str = ""
    timeout_seconds: int = 1800


@dataclass(slots=True)
class PolicySettings:
    require_info_when: list[str] = field(default_factory=list)
    require_approval_before_fix_when: list[str] = field(default_factory=list)
    forbidden_paths: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ReviewSettings:
    reviewers: list[str] = field(default_factory=list)


@dataclass(slots=True)
class WorkspaceSettings:
    root: Path = Path("workspaces")
    use_current_checkout: bool = False


@dataclass(slots=True)
class ProjectProfile:
    key: str
    name: str
    platform: str = "gitlab"
    gitlab: GitLabSettings | None = None
    github: GitHubSettings | None = None
    agent: AgentSettings = field(default_factory=AgentSettings)
    commands: CommandsSettings = field(default_factory=CommandsSettings)
    fix: FixSettings = field(default_factory=FixSettings)
    policy: PolicySettings = field(default_factory=PolicySettings)
    policy_file: str = ""
    review: ReviewSettings = field(default_factory=ReviewSettings)
    workspace: WorkspaceSettings = field(default_factory=WorkspaceSettings)

    @property
    def default_branch(self) -> str:
        if self.platform == "github":
            if not self.github:
                raise ValueError("GitHub profile is missing")
            return self.github.default_branch
        if not self.gitlab:
            raise ValueError("GitLab profile is missing")
        return self.gitlab.default_branch

    @property
    def repo_http_url(self) -> str:
        if self.platform == "github":
            if not self.github:
                raise ValueError("GitHub profile is missing")
            return self.github.repo_http_url or f"https://github.com/{self.github.owner}/{self.github.repo}.git"
        if not self.gitlab:
            raise ValueError("GitLab profile is missing")
        return self.gitlab.repo_http_url


@dataclass(slots=True)
class IssueAnalysis:
    issue_iid: int
    summary: str
    observed_behavior: str
    expected_behavior: str
    reproduction: str
    ambiguity_reasons: list[str]
    policy_flags: list[str]
    risk: str
    related_keywords: list[str]
    decision: str = ""

    @property
    def needs_info(self) -> bool:
        return bool(self.ambiguity_reasons or self.policy_flags)

    def to_dict(self) -> dict[str, Any]:
        return {
            "issue_iid": self.issue_iid,
            "summary": self.summary,
            "observed_behavior": self.observed_behavior,
            "expected_behavior": self.expected_behavior,
            "reproduction": self.reproduction,
            "ambiguity_reasons": self.ambiguity_reasons,
            "policy_flags": self.policy_flags,
            "risk": self.risk,
            "related_keywords": self.related_keywords,
            "decision": self.decision,
        }


@dataclass(slots=True)
class CommandResult:
    command: str
    exit_code: int
    stdout: str = ""
    stderr: str = ""

    @property
    def ok(self) -> bool:
        return self.exit_code == 0


@dataclass(slots=True)
class FixResult:
    success: bool
    skipped: bool = False
    summary: str = ""
    files_changed: list[str] = field(default_factory=list)
    commit_message: str = ""
    stdout: str = ""
    stderr: str = ""


@dataclass(slots=True)
class MergeRequest:
    iid: int
    web_url: str
    title: str


@dataclass(slots=True)
class ProcessResult:
    status: str
    message: str
    issue_iid: int
    mr_url: str = ""
