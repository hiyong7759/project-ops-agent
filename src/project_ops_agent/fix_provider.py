from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from .models import Comment, FixResult, Issue, IssueAnalysis, ProjectProfile


class ExternalFixProvider:
    def __init__(self, profile: ProjectProfile) -> None:
        self.profile = profile

    def apply(
        self,
        workspace: Path,
        issue: Issue,
        analysis: IssueAnalysis,
        comments: list[Comment],
    ) -> FixResult:
        if not self.profile.fix.command:
            return FixResult(
                success=False,
                skipped=True,
                summary="이 프로젝트에는 fix.command가 설정되어 있지 않습니다.",
            )

        context = {
            "issue": {
                "iid": issue.iid,
                "title": issue.title,
                "description": issue.description,
                "labels": issue.labels,
                "web_url": issue.web_url,
            },
            "analysis": analysis.to_dict(),
            "decision": analysis.decision,
            "comments": [comment.body for comment in comments[-20:]],
            "project": {
                "key": self.profile.key,
                "name": self.profile.name,
            },
        }

        result = subprocess.run(
            self.profile.fix.command,
            cwd=workspace,
            shell=True,
            input=json.dumps(context, ensure_ascii=False),
            text=True,
            capture_output=True,
            timeout=self.profile.fix.timeout_seconds,
            check=False,
        )
        if result.returncode != 0:
            return FixResult(
                success=False,
                summary="수정 명령이 실패했습니다.",
                stdout=result.stdout,
                stderr=result.stderr,
            )

        return _parse_fix_result(result.stdout, result.stderr)


def _parse_fix_result(stdout: str, stderr: str) -> FixResult:
    try:
        payload: dict[str, Any] = json.loads(stdout or "{}")
    except json.JSONDecodeError:
        return FixResult(success=True, summary=stdout.strip(), stdout=stdout, stderr=stderr)

    return FixResult(
        success=bool(payload.get("success", True)),
        skipped=bool(payload.get("skipped", False)),
        summary=str(payload.get("summary") or ""),
        files_changed=[str(item) for item in payload.get("files_changed") or []],
        commit_message=str(payload.get("commit_message") or ""),
        stdout=str(payload.get("stdout") or stdout),
        stderr=str(payload.get("stderr") or stderr),
    )
