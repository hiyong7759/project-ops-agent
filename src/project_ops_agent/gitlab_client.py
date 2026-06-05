from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode, quote
from urllib.request import Request, urlopen

from .models import Comment, Issue, MergeRequest


class GitLabError(RuntimeError):
    pass


@dataclass(slots=True)
class GitLabClient:
    base_url: str
    project_id: str
    token: str

    def list_issues_by_label(self, label: str, limit: int = 20) -> list[Issue]:
        payload = self._request(
            "GET",
            "/issues",
            query={"labels": label, "state": "opened", "per_page": str(limit)},
        )
        return [Issue.from_gitlab(item) for item in payload]

    def get_issue(self, iid: int) -> Issue:
        return Issue.from_gitlab(self._request("GET", f"/issues/{iid}"))

    def get_issue_comments(self, iid: int) -> list[Comment]:
        payload = self._request(
            "GET",
            f"/issues/{iid}/notes",
            query={"per_page": "100", "sort": "asc", "order_by": "created_at"},
        )
        return [Comment.from_gitlab(item) for item in payload]

    def post_issue_comment(self, iid: int, body: str) -> None:
        self._request("POST", f"/issues/{iid}/notes", data={"body": body})

    def update_issue_labels(self, iid: int, labels: list[str]) -> None:
        self._request("PUT", f"/issues/{iid}", data={"labels": ",".join(labels)})

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
            "/merge_requests",
            data={
                "source_branch": source_branch,
                "target_branch": target_branch,
                "title": title,
                "description": description,
                "remove_source_branch": remove_source_branch,
            },
        )
        return MergeRequest(
            iid=int(payload["iid"]),
            web_url=str(payload.get("web_url") or ""),
            title=str(payload.get("title") or title),
        )

    def get_repo_http_url(self) -> str:
        payload = self._request("GET", "")
        return str(payload.get("http_url_to_repo") or "")

    def _request(
        self,
        method: str,
        path: str,
        data: dict[str, Any] | None = None,
        query: dict[str, str] | None = None,
    ) -> Any:
        project = quote(str(self.project_id), safe="")
        url = f"{self.base_url.rstrip('/')}/api/v4/projects/{project}{path}"
        if query:
            url = f"{url}?{urlencode(query)}"

        body = None
        headers = {"PRIVATE-TOKEN": self.token, "Content-Type": "application/json"}
        if data is not None:
            body = json.dumps(data).encode("utf-8")

        request = Request(url, data=body, headers=headers, method=method)
        try:
            with urlopen(request, timeout=60) as response:
                text = response.read().decode("utf-8")
        except Exception as exc:  # pragma: no cover - exercised against real GitLab.
            raise GitLabError(f"GitLab {method} {path} failed: {exc}") from exc

        if not text:
            return None
        return json.loads(text)

