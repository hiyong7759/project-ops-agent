from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .models import Comment, Issue, MergeRequest


class GitHubError(RuntimeError):
    pass


@dataclass(slots=True)
class GitHubClient:
    api_url: str
    owner: str
    repo: str
    token: str

    def list_issues_by_label(self, label: str, limit: int = 20) -> list[Issue]:
        payload = self._request(
            "GET",
            "/issues",
            query={"labels": label, "state": "open", "per_page": str(limit)},
        )
        issues = [item for item in payload if "pull_request" not in item]
        return [Issue.from_github(item) for item in issues]

    def get_issue(self, iid: int) -> Issue:
        return Issue.from_github(self._request("GET", f"/issues/{iid}"))

    def get_issue_comments(self, iid: int) -> list[Comment]:
        payload = self._request(
            "GET",
            f"/issues/{iid}/comments",
            query={"per_page": "100"},
        )
        return [Comment.from_github(item) for item in payload]

    def list_labels(self) -> list[str]:
        payload = self._request("GET", "/labels", query={"per_page": "100"})
        return [str(item.get("name")) for item in payload or [] if item.get("name")]

    def post_issue_comment(self, iid: int, body: str) -> None:
        self._request("POST", f"/issues/{iid}/comments", data={"body": body})

    def update_issue_labels(self, iid: int, labels: list[str]) -> None:
        self._request("PUT", f"/issues/{iid}/labels", data={"labels": labels})

    def create_label(
        self,
        name: str,
        color: str = "ededed",
        description: str = "",
    ) -> None:
        data = {"name": name, "color": color.lstrip("#")}
        if description:
            data["description"] = description
        self._request("POST", "/labels", data=data)

    def create_merge_request(
        self,
        source_branch: str,
        target_branch: str,
        title: str,
        description: str,
        remove_source_branch: bool = True,
    ) -> MergeRequest:
        payload = self._request(
            "POST",
            "/pulls",
            data={
                "head": source_branch,
                "base": target_branch,
                "title": title,
                "body": description,
            },
        )
        return MergeRequest(
            iid=int(payload["number"]),
            web_url=str(payload.get("html_url") or ""),
            title=str(payload.get("title") or title),
        )

    def get_repo_http_url(self) -> str:
        payload = self._request("GET", "")
        return str(payload.get("clone_url") or "")

    def _request(
        self,
        method: str,
        path: str,
        data: dict[str, Any] | None = None,
        query: dict[str, str] | None = None,
    ) -> Any:
        url = f"{self.api_url.rstrip('/')}/repos/{self.owner}/{self.repo}{path}"
        if query:
            url = f"{url}?{urlencode(query)}"

        body = None
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "project-ops-agent",
        }
        if data is not None:
            body = json.dumps(data).encode("utf-8")

        request = Request(url, data=body, headers=headers, method=method)
        try:
            with urlopen(request, timeout=60) as response:
                text = response.read().decode("utf-8")
        except Exception as exc:  # pragma: no cover - exercised against real GitHub.
            raise GitHubError(f"GitHub {method} {path} failed: {exc}") from exc

        if not text:
            return None
        return json.loads(text)
