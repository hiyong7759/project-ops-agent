from __future__ import annotations

import json
import tomllib
import re
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

    policy = _policy_from_source(config_path, project.get("policy_file"), _table(data, "policy"))

    return ProjectProfile(
        key=str(project["key"]),
        name=str(project.get("name") or project["key"]),
        platform=platform,
        gitlab=gitlab_settings,
        github=github_settings,
        agent=AgentSettings(**_table(data, "agent")),
        commands=CommandsSettings(**_table(data, "commands")),
        fix=FixSettings(**_table(data, "fix")),
        policy=policy,
        policy_file=str(_resolve_policy_file(config_path, project.get("policy_file"))),
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


def _policy_from_source(config_path: Path, policy_file: Any, base_policy: dict[str, Any]) -> PolicySettings:
    if not policy_file:
        return PolicySettings(**base_policy)
    if not isinstance(policy_file, str):
        raise ValueError("project.policy_file must be a string")

    policy_overrides = _load_policy_overrides(_resolve_policy_path(config_path, policy_file))
    merged = _merge_policy(base_policy, policy_overrides)
    return PolicySettings(**merged)


def _resolve_policy_file(config_path: Path, policy_file: Any) -> str:
    if not policy_file:
        return ""
    return str(_resolve_policy_path(config_path, policy_file))


def _resolve_policy_path(config_path: Path, policy_file: Any) -> Path:
    path = Path(policy_file)
    if path.is_absolute():
        return path

    config_relative = config_path.parent / path
    if config_relative.exists():
        return config_relative

    for parent in config_path.parent.parents:
        candidate = parent / path
        if candidate.exists():
            return candidate

    return config_relative


def _merge_policy(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = {
        "require_info_when": list(base.get("require_info_when", [])),
        "require_approval_before_fix_when": list(base.get("require_approval_before_fix_when", [])),
        "forbidden_paths": list(base.get("forbidden_paths", [])),
    }

    for key in merged:
        if key not in override:
            continue
        merged[key] = _merge_unique_list(merged[key], override[key], key)

    return merged


def _merge_unique_list(base_list: list[Any], override_list: Any, key: str) -> list[str]:
    if not isinstance(override_list, list):
        raise ValueError(f"[policy.{key}] must be an array")
    seen = set[str]()
    merged: list[str] = []
    for value in [*base_list, *override_list]:
        if not isinstance(value, str):
            value = str(value)
        if value in seen:
            continue
        seen.add(value)
        merged.append(value)
    return merged


def _load_policy_overrides(policy_path: Path) -> dict[str, Any]:
    if not policy_path.exists():
        raise ValueError(f"Policy file not found: {policy_path}")

    raw = policy_path.read_text(encoding="utf-8")
    parsed: dict[str, Any] = {}
    suffix = policy_path.suffix.lower()

    if suffix in {".toml", ".tml"}:
        parsed = _ensure_dict(tomllib.loads(raw), policy_path)
    elif suffix == ".json":
        parsed = _ensure_dict(json.loads(raw), policy_path)
    elif suffix == ".md":
        parsed = _extract_policy_from_markdown(raw, policy_path)
    else:
        raise ValueError(f"Unsupported policy file extension: {policy_path.suffix}")

    if "policy" in parsed:
        parsed = _ensure_dict(parsed["policy"], policy_path, "policy block")
    return parsed


def _extract_policy_from_markdown(raw: str, policy_path: Path) -> dict[str, Any]:
    block_re = re.compile(r"```(?P<kind>toml|json)\s*\n(?P<body>.*?)```", re.S | re.I)
    match = block_re.search(raw)
    if not match:
        raise ValueError(
            f"Policy markdown has no readable policy block. Add a ```toml or ```json code block in {policy_path}"
        )

    kind = match.group("kind").lower()
    body = match.group("body").strip()
    if kind == "toml":
        return _ensure_dict(tomllib.loads(body), policy_path, f"{policy_path} toml block")
    try:
        return _ensure_dict(json.loads(body), policy_path, f"{policy_path} json block")
    except json.JSONDecodeError as exc:
        if kind == "json":
            raise ValueError(f"Invalid JSON in {policy_path}") from exc
        raise ValueError(f"Invalid TOML in {policy_path}") from exc


def _ensure_dict(value: Any, policy_path: Path, source: str = "policy file") -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{source} in {policy_path} must be a table/dictionary")
    return value
