import unittest
from pathlib import Path

from project_ops_agent.models import (
    AgentSettings,
    CommandResult,
    CommandsSettings,
    FixResult,
    GitLabSettings,
    Issue,
    MergeRequest,
    PolicySettings,
    ProjectProfile,
    WorkspaceSettings,
)
from project_ops_agent.orchestrator import Orchestrator


class FakeGitLab:
    def __init__(self, comments=None):
        self.comments = comments or []
        self.label_updates = []
        self.posted_comments = []
        self.created_mrs = []

    def list_issues_by_label(self, label, limit=20):
        return []

    def get_issue_comments(self, iid):
        return self.comments

    def post_issue_comment(self, iid, body):
        self.posted_comments.append(body)

    def update_issue_labels(self, iid, labels):
        self.label_updates.append(list(labels))

    def create_merge_request(self, source_branch, target_branch, title, description, remove_source_branch=True):
        self.created_mrs.append(description)
        return MergeRequest(iid=1, web_url="https://gitlab.local/mr/1", title=title)


class FakeGitRunner:
    def prepare_workspace(self):
        return Path.cwd()

    def create_branch(self, workspace, issue):
        return f"agent/test-{issue.iid}"

    def changed_files(self, workspace):
        return ["src/order.py"]

    def commit_all(self, workspace, message):
        return True

    def push_branch(self, workspace, branch):
        return None


class FakeCommandRunner:
    def install_commands(self):
        return []

    def verification_commands(self):
        return ["unit-test"]

    def run_many(self, commands, cwd):
        return [CommandResult(command=command, exit_code=0, stdout="ok") for command in commands]


class FakeFixProvider:
    def apply(self, workspace, issue, analysis, comments):
        return FixResult(success=True, summary="이슈를 수정했습니다.", files_changed=["src/order.py"])


def profile():
    return ProjectProfile(
        key="order-api",
        name="Order API",
        gitlab=GitLabSettings(url="https://gitlab.local", project_id="1", default_branch="main"),
        agent=AgentSettings(can_push_branch=True, can_create_mr=True, can_merge=False),
        commands=CommandsSettings(),
        policy=PolicySettings(
            require_info_when=[
                "requirement_ambiguous",
                "expected_behavior_missing",
                "reproduction_missing",
                "multiple_solution_paths",
            ],
            require_approval_before_fix_when=["auth_change", "payment_change"],
            forbidden_paths=["infra/**"],
        ),
        workspace=WorkspaceSettings(root=Path("workspaces")),
    )


class OrchestratorTests(unittest.TestCase):
    def test_ambiguous_issue_stops_for_gitlab_comment_direction(self):
        client = FakeGitLab()
        issue = Issue(iid=1, title="로그인 안됨", description="로그인이 안됩니다", labels=["agent:queued"])
        result = Orchestrator(client, profile()).process_issue(issue)
        self.assertEqual("needs-info", result.status)
        self.assertTrue(any("에이전트 추가 정보 필요" in body for body in client.posted_comments))
        self.assertIn("agent:needs-info", client.label_updates[-1])

    def test_answered_issue_can_create_mr(self):
        from project_ops_agent.models import Comment

        client = FakeGitLab(comments=[Comment(id=1, body="@agent A")])
        issue = Issue(
            iid=2,
            title="Order status timeout",
            description="현재 timeout 오류. 기대 동작은 정상 응답. 재현 조건은 주문 상태 조회.",
            labels=["agent:queued"],
        )
        result = Orchestrator(
            client,
            profile(),
            git_runner=FakeGitRunner(),
            command_runner=FakeCommandRunner(),
            fix_provider=FakeFixProvider(),
        ).process_issue(issue)
        self.assertEqual("needs-user-test", result.status)
        self.assertEqual("https://gitlab.local/mr/1", result.mr_url)
        self.assertIn("agent:needs-user-test", client.label_updates[-1])
        self.assertIn("<details>", client.created_mrs[0])
        self.assertIn("사용자 테스트 게이트", client.created_mrs[0])

    def test_custom_direction_comment_can_create_mr(self):
        from project_ops_agent.models import Comment

        client = FakeGitLab(comments=[Comment(id=1, body="@agent 방향: 기존 정책은 유지하고 오류 문구만 명확하게 바꿔주세요.")])
        issue = Issue(
            iid=7,
            title="로그인 오류",
            description="로그인이 안됩니다",
            labels=["agent:needs-info"],
        )
        result = Orchestrator(
            client,
            profile(),
            git_runner=FakeGitRunner(),
            command_runner=FakeCommandRunner(),
            fix_provider=FakeFixProvider(),
        ).process_issue(issue)
        self.assertEqual("needs-user-test", result.status)
        self.assertIn("@agent 방향: 기존 정책은 유지하고 오류 문구만 명확하게 바꿔주세요.", client.created_mrs[0])

    def test_needs_info_issue_waits_without_new_user_direction(self):
        from project_ops_agent.models import Comment
        from project_ops_agent.templates import NEEDS_INFO_MARKER

        client = FakeGitLab(
            comments=[
                Comment(
                    id=1,
                    body=f"{NEEDS_INFO_MARKER}\n## 에이전트 추가 정보 필요\n```text\n@agent A\n```",
                    author_username="hiyong7759",
                )
            ]
        )
        issue = Issue(
            iid=9,
            title="로그인 오류",
            description="로그인이 안됩니다",
            labels=["agent:needs-info"],
        )
        result = Orchestrator(
            client,
            profile(),
            git_runner=FakeGitRunner(),
            command_runner=FakeCommandRunner(),
            fix_provider=FakeFixProvider(),
        ).process_issue(issue)
        self.assertEqual("needs-info", result.status)
        self.assertEqual([], client.label_updates)
        self.assertEqual([], client.created_mrs)

    def test_needs_info_issue_resumes_with_new_user_direction_after_marker(self):
        from project_ops_agent.models import Comment
        from project_ops_agent.templates import NEEDS_INFO_MARKER

        client = FakeGitLab(
            comments=[
                Comment(id=1, body=f"{NEEDS_INFO_MARKER}\n## 에이전트 추가 정보 필요\n`@agent A`"),
                Comment(id=2, body="@agent A", author_username="user"),
            ]
        )
        issue = Issue(
            iid=10,
            title="로그인 오류",
            description="로그인이 안됩니다",
            labels=["agent:needs-info"],
        )
        result = Orchestrator(
            client,
            profile(),
            git_runner=FakeGitRunner(),
            command_runner=FakeCommandRunner(),
            fix_provider=FakeFixProvider(),
        ).process_issue(issue)
        self.assertEqual("needs-user-test", result.status)
        self.assertIn("agent:needs-user-test", client.label_updates[-1])

    def test_user_test_pass_marks_done(self):
        from project_ops_agent.models import Comment
        from project_ops_agent.templates import USER_TEST_MARKER

        client = FakeGitLab(
            comments=[
                Comment(id=1, body=f"{USER_TEST_MARKER}\n## 사용자 테스트 필요"),
                Comment(id=2, body="@agent test-pass"),
            ]
        )
        issue = Issue(iid=3, title="Ready", description="Done", labels=["agent:needs-user-test"])
        result = Orchestrator(client, profile()).process_issue(issue)
        self.assertEqual("done", result.status)
        self.assertIn("agent:done", client.label_updates[-1])

    def test_user_test_fail_marks_changes_requested(self):
        from project_ops_agent.models import Comment
        from project_ops_agent.templates import USER_TEST_MARKER

        client = FakeGitLab(
            comments=[
                Comment(id=1, body=f"{USER_TEST_MARKER}\n## 사용자 테스트 필요"),
                Comment(id=2, body="@agent test-fail still broken"),
            ]
        )
        issue = Issue(iid=4, title="Ready", description="Done", labels=["agent:needs-user-test"])
        result = Orchestrator(client, profile()).process_issue(issue)
        self.assertEqual("changes-requested", result.status)
        self.assertIn("agent:changes-requested", client.label_updates[-1])

    def test_user_test_result_without_request_marker_is_ignored(self):
        from project_ops_agent.models import Comment

        client = FakeGitLab(comments=[Comment(id=1, body="@agent test-pass", author_username="user")])
        issue = Issue(iid=13, title="Ready", description="Done", labels=["agent:needs-user-test"])
        result = Orchestrator(client, profile()).process_issue(issue)
        self.assertEqual("needs-user-test", result.status)
        self.assertEqual([], client.label_updates)

    def test_agent_user_test_request_does_not_mark_done(self):
        from project_ops_agent.models import Comment
        from project_ops_agent.templates import USER_TEST_MARKER

        client = FakeGitLab(
            comments=[
                Comment(
                    id=1,
                    body=f"{USER_TEST_MARKER}\n## 사용자 테스트 필요\n- `@agent test-pass`",
                    author_username="hiyong7759",
                )
            ]
        )
        issue = Issue(iid=8, title="Ready", description="Done", labels=["agent:needs-user-test"])
        result = Orchestrator(client, profile()).process_issue(issue)
        self.assertEqual("needs-user-test", result.status)
        self.assertEqual([], client.label_updates)

    def test_user_test_result_before_request_does_not_mark_done(self):
        from project_ops_agent.models import Comment
        from project_ops_agent.templates import USER_TEST_MARKER

        client = FakeGitLab(
            comments=[
                Comment(id=1, body="@agent test-pass", author_username="user"),
                Comment(id=2, body=f"{USER_TEST_MARKER}\n## 사용자 테스트 필요"),
            ]
        )
        issue = Issue(iid=11, title="Ready", description="Done", labels=["agent:needs-user-test"])
        result = Orchestrator(client, profile()).process_issue(issue)
        self.assertEqual("needs-user-test", result.status)
        self.assertEqual([], client.label_updates)

    def test_user_test_result_after_request_marks_done(self):
        from project_ops_agent.models import Comment
        from project_ops_agent.templates import USER_TEST_MARKER

        client = FakeGitLab(
            comments=[
                Comment(id=1, body=f"{USER_TEST_MARKER}\n## 사용자 테스트 필요"),
                Comment(id=2, body="@agent test-pass", author_username="user"),
            ]
        )
        issue = Issue(iid=12, title="Ready", description="Done", labels=["agent:needs-user-test"])
        result = Orchestrator(client, profile()).process_issue(issue)
        self.assertEqual("done", result.status)
        self.assertIn("agent:done", client.label_updates[-1])

    def test_blocked_issue_waits_until_new_user_resume_comment(self):
        from project_ops_agent.models import Comment

        client = FakeGitLab(
            comments=[
                Comment(id=1, body="@agent A"),
                Comment(id=2, body="<!-- project-ops-agent:blocked -->\n## 에이전트 중단"),
            ]
        )
        issue = Issue(iid=5, title="Ready", description="Done", labels=["agent:blocked"])
        result = Orchestrator(
            client,
            profile(),
            git_runner=FakeGitRunner(),
            command_runner=FakeCommandRunner(),
            fix_provider=FakeFixProvider(),
        ).process_issue(issue)
        self.assertEqual("blocked", result.status)
        self.assertEqual([], client.label_updates)
        self.assertEqual([], client.created_mrs)

    def test_blocked_issue_resumes_when_user_comment_is_after_blocked_marker(self):
        from project_ops_agent.models import Comment

        client = FakeGitLab(
            comments=[
                Comment(id=1, body="<!-- project-ops-agent:blocked -->\n## 에이전트 중단"),
                Comment(id=2, body="@agent proceed"),
            ]
        )
        issue = Issue(
            iid=6,
            title="Ready",
            description="현재 오류. 기대 동작은 정상 처리. 재현 조건 있음.",
            labels=["agent:blocked"],
        )
        result = Orchestrator(
            client,
            profile(),
            git_runner=FakeGitRunner(),
            command_runner=FakeCommandRunner(),
            fix_provider=FakeFixProvider(),
        ).process_issue(issue)
        self.assertEqual("needs-user-test", result.status)
        self.assertIn("agent:needs-user-test", client.label_updates[-1])


if __name__ == "__main__":
    unittest.main()
