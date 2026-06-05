import unittest

from project_ops_agent.models import Comment, Issue


class GitHubAdapterTests(unittest.TestCase):
    def test_issue_from_github_payload(self):
        issue = Issue.from_github(
            {
                "number": 7,
                "title": "Bug",
                "body": "현재 오류. 기대 동작. 재현 조건.",
                "labels": [{"name": "agent:queued"}, {"name": "bug"}],
                "html_url": "https://github.com/me/repo/issues/7",
                "state": "open",
            }
        )
        self.assertEqual(7, issue.iid)
        self.assertEqual(["agent:queued", "bug"], issue.labels)
        self.assertEqual("https://github.com/me/repo/issues/7", issue.web_url)

    def test_comment_from_github_payload(self):
        comment = Comment.from_github(
            {
                "id": 10,
                "body": "@agent A",
                "user": {"login": "reviewer"},
                "created_at": "2026-06-05T00:00:00Z",
            }
        )
        self.assertEqual("@agent A", comment.body)
        self.assertEqual("reviewer", comment.author_username)


if __name__ == "__main__":
    unittest.main()

