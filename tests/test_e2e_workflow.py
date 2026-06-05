import unittest
from pathlib import Path

from project_ops_agent.models import (
    AgentSettings,
    CommandResult,
    CommandsSettings,
    Comment,
    FixResult,
    GitHubSettings,
    Issue,
    MergeRequest,
    PolicySettings,
    ProjectProfile,
    WorkspaceSettings,
)
from project_ops_agent.orchestrator import Orchestrator


class InMemoryIssuePlatform:
    def __init__(self, issue):
        self.issue = issue
        self.comments = []
        self.next_comment_id = 1
        self.created_mrs = []

    def list_issues_by_label(self, label, limit=20):
        if label in self.issue.labels and self.issue.state in {"opened", "open"}:
            return [self.issue]
        return []

    def get_issue_comments(self, iid):
        return list(self.comments)

    def post_issue_comment(self, iid, body):
        self.comments.append(Comment(id=self.next_comment_id, body=body, author_username="agent"))
        self.next_comment_id += 1

    def update_issue_labels(self, iid, labels):
        self.issue.labels = list(labels)

    def create_merge_request(self, source_branch, target_branch, title, description, remove_source_branch=True):
        mr = MergeRequest(iid=1, web_url="https://github.com/hiyong7759/project-ops-agent/pull/1", title=title)
        self.created_mrs.append(
            {
                "source_branch": source_branch,
                "target_branch": target_branch,
                "title": title,
                "description": description,
            }
        )
        return mr


class E2EGitRunner:
    def prepare_workspace(self):
        return Path.cwd()

    def create_branch(self, workspace, issue):
        return f"agent/demo-{issue.iid}"

    def changed_files(self, workspace):
        return ["src/demo.py", "tests/test_demo.py"]

    def commit_all(self, workspace, message):
        return True

    def push_branch(self, workspace, branch):
        return None


class E2ECommandRunner:
    def install_commands(self):
        return []

    def verification_commands(self):
        return ["unit-test", "lint"]

    def run_many(self, commands, cwd):
        return [CommandResult(command=command, exit_code=0, stdout="ok") for command in commands]


class E2EFixProvider:
    def apply(self, workspace, issue, analysis, comments):
        return FixResult(
            success=True,
            summary="Applied a minimal fix and added regression coverage.",
            files_changed=["src/demo.py", "tests/test_demo.py"],
            commit_message=f"Fix issue #{issue.iid}: {issue.title}\n\nRefs #{issue.iid}",
        )


def github_profile():
    return ProjectProfile(
        key="project-ops-agent",
        name="Project Ops Agent",
        platform="github",
        github=GitHubSettings(
            owner="hiyong7759",
            repo="project-ops-agent",
            default_branch="main",
            repo_http_url="https://github.com/hiyong7759/project-ops-agent.git",
        ),
        agent=AgentSettings(can_push_branch=True, can_create_mr=True, can_merge=False),
        commands=CommandsSettings(),
        policy=PolicySettings(
            require_info_when=[
                "requirement_ambiguous",
                "expected_behavior_missing",
                "reproduction_missing",
                "multiple_solution_paths",
            ],
            require_approval_before_fix_when=[],
            forbidden_paths=[".github/workflows/**"],
        ),
        workspace=WorkspaceSettings(root=Path("workspaces"), use_current_checkout=True),
    )


class E2EWorkflowTests(unittest.TestCase):
    def test_ambiguous_issue_to_pr_to_user_test_done(self):
        issue = Issue(
            iid=42,
            title="운영 화면 오류",
            description="운영 화면에서 오류가 납니다",
            labels=["agent:queued"],
            web_url="https://github.com/hiyong7759/project-ops-agent/issues/42",
            state="open",
        )
        platform = InMemoryIssuePlatform(issue)
        orchestrator = Orchestrator(
            platform,
            github_profile(),
            git_runner=E2EGitRunner(),
            command_runner=E2ECommandRunner(),
            fix_provider=E2EFixProvider(),
        )

        first = orchestrator.process_queued(limit=10)
        self.assertEqual("needs-info", first[0].status)
        self.assertIn("agent:needs-info", issue.labels)
        self.assertTrue(any("Agent Needs Info" in comment.body for comment in platform.comments))

        platform.comments.append(Comment(id=99, body="@agent A", author_username="user"))
        second = orchestrator.process_queued(limit=10)
        self.assertEqual("needs-user-test", second[0].status)
        self.assertIn("agent:needs-user-test", issue.labels)
        self.assertEqual(1, len(platform.created_mrs))
        self.assertIn("User Test Gate", platform.created_mrs[0]["description"])

        platform.comments.append(Comment(id=100, body="@agent test-pass", author_username="user"))
        third = orchestrator.process_queued(limit=10)
        self.assertEqual("done", third[0].status)
        self.assertIn("agent:done", issue.labels)


if __name__ == "__main__":
    unittest.main()

