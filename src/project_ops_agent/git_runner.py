from __future__ import annotations

import re
import subprocess
from pathlib import Path

from .models import Issue, ProjectProfile


class GitRunner:
    def __init__(self, profile: ProjectProfile, repo_url: str | None = None) -> None:
        self.profile = profile
        self.repo_url = repo_url or profile.repo_http_url

    def prepare_workspace(self) -> Path:
        if self.profile.workspace.use_current_checkout:
            return Path.cwd().resolve()

        if not self.repo_url:
            raise RuntimeError("No repository URL configured")

        root = self.profile.workspace.root
        root.mkdir(parents=True, exist_ok=True)
        workspace = root / self.profile.key

        if not workspace.exists():
            self._run(["git", "clone", self.repo_url, str(workspace)], cwd=root)
        else:
            self._run(["git", "fetch", "origin"], cwd=workspace)
        return workspace

    def create_branch(self, workspace: Path, issue: Issue) -> str:
        branch = self.branch_name(issue)
        base = self.profile.default_branch
        self._run(["git", "fetch", "origin", base], cwd=workspace)
        self._run(["git", "checkout", "-B", base, f"origin/{base}"], cwd=workspace)
        self._run(["git", "checkout", "-B", branch], cwd=workspace)
        return branch

    def branch_name(self, issue: Issue) -> str:
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", issue.title.lower()).strip("-")
        slug = slug[:48] or "issue"
        return f"{self.profile.agent.branch_prefix}/{self.profile.key}-{issue.iid}-{slug}"

    def changed_files(self, workspace: Path) -> list[str]:
        result = self._run(["git", "diff", "--name-only", "--cached"], cwd=workspace, check=False)
        staged = _lines(result.stdout)
        result = self._run(["git", "diff", "--name-only"], cwd=workspace, check=False)
        unstaged = _lines(result.stdout)
        return _stable_unique([*staged, *unstaged])

    def commit_all(self, workspace: Path, message: str) -> bool:
        if not self.has_changes(workspace):
            return False
        self._run(["git", "add", "-A"], cwd=workspace)
        self._run(["git", "commit", "-m", message], cwd=workspace)
        return True

    def push_branch(self, workspace: Path, branch: str) -> None:
        self._run(["git", "push", "--force-with-lease", "-u", "origin", branch], cwd=workspace)

    def has_changes(self, workspace: Path) -> bool:
        result = self._run(["git", "status", "--porcelain"], cwd=workspace, check=False)
        return bool(result.stdout.strip())

    def _run(self, args: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            args,
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
        )
        if check and result.returncode != 0:
            raise RuntimeError(f"{' '.join(args)} failed\n{result.stderr}")
        return result


def _lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def _stable_unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result
