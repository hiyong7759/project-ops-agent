from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


DEFAULT_TIMEOUT_SECONDS = 1800


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError as exc:
        _emit(False, f"fix.command 입력 JSON을 읽을 수 없습니다: {exc}")
        return 1

    issue = _as_dict(payload.get("issue"))
    analysis = _as_dict(payload.get("analysis"))
    iid = int(issue.get("iid") or 0)
    title = str(issue.get("title") or "제목 없음")
    if not iid:
        _emit(False, "fix.command 입력에 issue.iid가 없습니다.")
        return 1

    command = shlex.split(os.getenv("CODEX_FIX_COMMAND", "codex"))
    if not command:
        _emit(False, "CODEX_FIX_COMMAND가 비어 있습니다.")
        return 1

    prompt = _build_prompt(payload)
    timeout = int(os.getenv("CODEX_FIX_TIMEOUT_SECONDS") or DEFAULT_TIMEOUT_SECONDS)

    with tempfile.TemporaryDirectory(prefix="project-ops-agent-codex-") as tmpdir:
        output_path = Path(tmpdir) / "codex-final-message.md"
        args = [
            *command,
            "exec",
            "--sandbox",
            os.getenv("CODEX_FIX_SANDBOX", "workspace-write"),
            "--output-last-message",
            str(output_path),
            "--ephemeral",
            prompt,
        ]
        result = subprocess.run(
            args,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        final_message = output_path.read_text(encoding="utf-8") if output_path.exists() else result.stdout

    if result.returncode != 0:
        _emit(
            False,
            _summarize_failure("Codex fix.command 실행이 실패했습니다.", result.stdout, result.stderr),
        )
        return result.returncode or 1

    changed_files = _changed_files()
    if not changed_files:
        _emit(False, "Codex fix.command는 완료됐지만 변경된 파일이 없습니다.", stdout=final_message, stderr=result.stderr)
        return 1

    _emit(
        True,
        _summary(final_message) or "Codex fix.command가 소스 변경을 생성했습니다.",
        files_changed=changed_files,
        commit_message=f"이슈 #{iid} 수정: {title}\n\nRefs #{iid}",
        stdout=final_message,
        stderr=result.stderr,
    )
    return 0


def _build_prompt(payload: dict[str, Any]) -> str:
    issue = _as_dict(payload.get("issue"))
    analysis = _as_dict(payload.get("analysis"))
    decision = str(payload.get("decision") or "")
    comments = payload.get("comments") or []
    context = {
        "issue": issue,
        "analysis": analysis,
        "decision": decision,
        "comments": comments[-20:] if isinstance(comments, list) else [],
        "project": _as_dict(payload.get("project")),
    }
    context_json = json.dumps(context, ensure_ascii=False, indent=2)
    return "\n".join(
        [
            "Project Ops Agent가 전달한 Issue 기반 작업을 처리하세요.",
            "",
            "규칙:",
            "- 현재 checkout된 저장소 안에서만 필요한 파일을 수정하세요.",
            "- AGENTS.md와 저장소의 기존 스타일을 따르세요.",
            "- 자동 merge, branch push, commit 생성은 하지 마세요. Project Ops Agent가 후속 처리합니다.",
            "- 사용자에게 보이는 문구, 문서, 테스트 설명은 한국어로 작성하세요.",
            "- 요구사항이 부족하면 추측으로 큰 변경을 만들지 말고 최소 변경 또는 명확한 실패 사유를 남기세요.",
            "- 작업 후 가능한 검증 명령을 직접 실행하고, 최종 응답에 변경 요약과 검증 결과를 한국어로 적으세요.",
            "",
            "Issue context JSON:",
            "```json",
            context_json,
            "```",
        ]
    )


def _changed_files() -> list[str]:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return []

    files: list[str] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        path = path.strip()
        if path.endswith("/") or Path(path).is_dir():
            files.extend(_untracked_files(path))
        else:
            files.append(path)
    return _stable_unique(files)


def _untracked_files(path: str) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "--", path],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return [path.rstrip("/")]
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _emit(
    success: bool,
    summary: str,
    files_changed: list[str] | None = None,
    commit_message: str = "",
    stdout: str = "",
    stderr: str = "",
) -> None:
    print(
        json.dumps(
            {
                "success": success,
                "summary": summary,
                "files_changed": files_changed or [],
                "commit_message": commit_message,
                "stdout": stdout,
                "stderr": stderr,
            },
            ensure_ascii=False,
        )
    )


def _summary(message: str) -> str:
    lines = [line.strip() for line in message.splitlines() if line.strip()]
    return "\n".join(lines[:12])


def _summarize_failure(prefix: str, stdout: str, stderr: str) -> str:
    detail = "\n".join(part.strip() for part in [stdout, stderr] if part.strip())
    if not detail:
        return prefix
    return f"{prefix}\n{detail[-4000:]}"


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _stable_unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
