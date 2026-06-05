from __future__ import annotations

import argparse
import json
import os
import sys

from .config import load_project_profile
from .github_client import GitHubClient
from .gitlab_client import GitLabClient
from .issue_analyzer import IssueAnalyzer
from .models import Comment, Issue, FixResult, CommandResult
from .orchestrator import Orchestrator
from .templates import render_mr_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="gitlab-project-ops-agent")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan = subparsers.add_parser("scan", help="Process issues labeled agent:queued")
    scan.add_argument("--config", required=True)
    scan.add_argument("--limit", type=int, default=20)

    process = subparsers.add_parser("process", help="Process a single issue IID")
    process.add_argument("--config", required=True)
    process.add_argument("--issue", type=int, required=True)

    render = subparsers.add_parser("render-report", help="Render a local MR report from a fixture")
    render.add_argument("--config", required=True)
    render.add_argument("--fixture", required=True)

    args = parser.parse_args(argv)

    if args.command == "render-report":
        profile = load_project_profile(args.config)
        fixture = json.loads(open(args.fixture, encoding="utf-8").read())
        issue = Issue(**fixture["issue"])
        comments = [Comment(**item) for item in fixture.get("comments", [])]
        analysis = IssueAnalyzer().analyze(issue, comments)
        report = render_mr_report(
            issue,
            analysis,
            FixResult(success=True, summary=fixture.get("fix_summary", "Example fix summary.")),
            [CommandResult(command="example", exit_code=0, stdout="ok")],
            fixture.get("changed_files", []),
            ["로컬 보고서 렌더링", f"프로젝트 설정 로드: {profile.key}"],
        )
        print(report)
        return 0

    profile = load_project_profile(args.config)
    client = _client_from_profile(profile)
    orchestrator = Orchestrator(client, profile)

    if args.command == "scan":
        results = orchestrator.process_queued(limit=args.limit)
        for result in results:
            print(f"#{result.issue_iid}: {result.status} - {result.message} {result.mr_url}".strip())
        return 0

    if args.command == "process":
        issue = client.get_issue(args.issue)
        result = orchestrator.process_issue(issue)
        print(f"#{result.issue_iid}: {result.status} - {result.message} {result.mr_url}".strip())
        return 0

    return 2


def _client_from_profile(profile):
    if profile.platform == "github":
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            raise SystemExit("GITHUB_TOKEN is required")
        if not profile.github:
            raise SystemExit("[github] settings are required")
        return GitHubClient(
            api_url=profile.github.api_url,
            owner=profile.github.owner,
            repo=profile.github.repo,
            token=token,
        )

    token = os.getenv("GITLAB_TOKEN")
    if not token:
        raise SystemExit("GITLAB_TOKEN is required")
    if not profile.gitlab:
        raise SystemExit("[gitlab] settings are required")
    return GitLabClient(base_url=profile.gitlab.url, project_id=profile.gitlab.project_id, token=token)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
