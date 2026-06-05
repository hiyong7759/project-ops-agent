from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from .models import (
    AgentSettings,
    CommandsSettings,
    FixSettings,
    GitHubSettings,
    GitLabSettings,
    PolicySettings,
    ProjectProfile,
    ReviewSettings,
    WorkspaceSettings,
)


def load_project_profile(path: str | Path) -> ProjectProfile:
    config_path = Path(path)
    data = tomllib.loads(config_path.read_text(encoding="utf-8"))

    project = _required_table(data, "project")
    platform = str(project.get("platform") or ("github" if "github" in data else "gitlab")).lower()
    if platform not in {"gitlab", "github"}:
        raise ValueError("project.platform must be either 'gitlab' or 'github'")

    gitlab_settings = None
    github_settings = None
    if platform == "gitlab":
        gitlab = _required_table(data, "gitlab")
        gitlab_settings = GitLabSettings(
            url=str(gitlab["url"]).rstrip("/"),
            project_id=str(gitlab["project_id"]),
            default_branch=str(gitlab.get("default_branch") or "main"),
            repo_http_url=str(gitlab.get("repo_http_url") or ""),
        )
    else:
        github = _required_table(data, "github")
        github_settings = GitHubSettings(
            owner=str(github["owner"]),
            repo=str(github["repo"]),
            default_branch=str(github.get("default_branch") or "main"),
            repo_http_url=str(github.get("repo_http_url") or ""),
            api_url=str(github.get("api_url") or "https://api.github.com").rstrip("/"),
        )

    return ProjectProfile(
        key=str(project["key"]),
        name=str(project.get("name") or project["key"]),
        platform=platform,
        gitlab=gitlab_settings,
        github=github_settings,
        agent=AgentSettings(**_table(data, "agent")),
        commands=CommandsSettings(**_table(data, "commands")),
        fix=FixSettings(**_table(data, "fix")),
        policy=PolicySettings(**_table(data, "policy")),
        review=ReviewSettings(**_table(data, "review")),
        workspace=WorkspaceSettings(
            root=Path(_table(data, "workspace").get("root", "workspaces")),
            use_current_checkout=bool(_table(data, "workspace").get("use_current_checkout", False)),
        ),
    )


def _required_table(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"Missing [{key}] table")
    return value


def _table(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"[{key}] must be a table")
    return value
