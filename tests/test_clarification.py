import unittest

from project_ops_agent.clarification import (
    latest_agent_decision,
    latest_user_test_result,
    latest_user_test_result_after_marker,
)
from project_ops_agent.models import Comment
from project_ops_agent.templates import NEEDS_INFO_MARKER, USER_TEST_MARKER


class ClarificationTests(unittest.TestCase):
    def test_agent_marker_comments_are_not_user_decisions(self):
        comments = [
            Comment(
                id=1,
                body=f"{NEEDS_INFO_MARKER}\n## 에이전트 추가 정보 필요\n`@agent A`",
                author_username="hiyong7759",
            )
        ]
        self.assertEqual("", latest_agent_decision(comments))

    def test_custom_direction_comment_is_user_decision(self):
        comments = [Comment(id=1, body="@agent 방향: A가 아니라 기존 정책을 유지하고 메시지만 바꿔주세요.")]
        self.assertEqual(
            "@agent 방향: A가 아니라 기존 정책을 유지하고 메시지만 바꿔주세요.",
            latest_agent_decision(comments),
        )

    def test_agent_user_test_request_is_not_test_result(self):
        comments = [
            Comment(
                id=1,
                body=f"{USER_TEST_MARKER}\n## 사용자 테스트 필요\n- `@agent test-pass`",
                author_username="hiyong7759",
            )
        ]
        self.assertEqual(("", ""), latest_user_test_result(comments))

    def test_user_test_result_before_request_marker_is_ignored(self):
        comments = [
            Comment(id=1, body="@agent test-pass", author_username="user"),
            Comment(id=2, body=f"{USER_TEST_MARKER}\n## 사용자 테스트 필요"),
        ]
        self.assertEqual(("", ""), latest_user_test_result_after_marker(comments, USER_TEST_MARKER))

    def test_user_test_result_after_request_marker_is_used(self):
        comments = [
            Comment(id=1, body=f"{USER_TEST_MARKER}\n## 사용자 테스트 필요"),
            Comment(id=2, body="@agent test-fail 아직 깨집니다", author_username="user"),
        ]
        self.assertEqual(
            ("fail", "아직 깨집니다"),
            latest_user_test_result_after_marker(comments, USER_TEST_MARKER),
        )


if __name__ == "__main__":
    unittest.main()
