from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def main() -> int:
    payload = json.loads(sys.stdin.read() or "{}")
    issue = payload.get("issue") or {}
    analysis = payload.get("analysis") or {}

    iid = int(issue.get("iid") or 0)
    if not iid:
        print(
            json.dumps(
                {
                    "success": False,
                    "summary": "demo fix.command 입력에 issue.iid가 없습니다.",
                },
                ensure_ascii=False,
            )
        )
        return 1

    title = str(issue.get("title") or "untitled")
    summary = str(analysis.get("summary") or title)

    output_dir = Path(".agent-demo")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / f"issue-{iid or 'unknown'}-{_slug(title)}.md"
    output_path.write_text(
        "\n".join(
            [
                "# 에이전트 데모 수정 결과",
                "",
                f"- 이슈: #{iid}",
                f"- 제목: {title}",
                f"- 분석 요약: {summary}",
                "- 목적: GitHub Actions에서 branch push, PR 생성, 사용자 테스트 게이트를 검증합니다.",
                "",
                "이 파일은 실제 업무 수정이 아니라 demo fix.command가 만든 검증용 산출물입니다.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    result = {
        "success": True,
        "summary": "demo fix.command가 검증용 산출물을 생성했습니다.",
        "files_changed": [str(output_path)],
        "commit_message": f"이슈 #{iid} 데모 수정 생성\n\nRefs #{iid}",
    }
    print(json.dumps(result, ensure_ascii=False))
    return 0


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9가-힣]+", "-", value.lower()).strip("-")
    return (slug[:48] or "demo")


if __name__ == "__main__":
    raise SystemExit(main())
