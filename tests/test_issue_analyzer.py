import unittest

from project_ops_agent.issue_analyzer import IssueAnalyzer
from project_ops_agent.models import Comment, Issue


class IssueAnalyzerTests(unittest.TestCase):
    def test_ambiguous_issue_requires_info(self):
        issue = Issue(iid=1, title="login broken", description="로그인이 안됩니다")
        analysis = IssueAnalyzer().analyze(issue)
        self.assertIn("expected_behavior_missing", analysis.ambiguity_reasons)
        self.assertIn("reproduction_missing", analysis.ambiguity_reasons)
        self.assertTrue(analysis.needs_info)

    def test_agent_decision_clears_ambiguity(self):
        issue = Issue(iid=2, title="login timeout", description="현재 login timeout 오류. 기대 동작은 정상 로그인.")
        comments = [Comment(id=1, body="@agent A")]
        analysis = IssueAnalyzer().analyze(issue, comments, decision="@agent A")
        self.assertEqual([], analysis.ambiguity_reasons)
        self.assertEqual("@agent A", analysis.decision)

    def test_sensitive_keywords_set_policy_flag_and_high_risk(self):
        issue = Issue(iid=3, title="결제 권한 오류", description="결제 permission 변경 필요. 재현 조건 있음. 기대 동작 설명.")
        analysis = IssueAnalyzer().analyze(issue)
        self.assertIn("auth_change", analysis.policy_flags)
        self.assertIn("payment_change", analysis.policy_flags)
        self.assertEqual("high", analysis.risk)

    def test_agent_marker_comments_are_ignored_for_analysis_input(self):
        issue = Issue(iid=4, title="로그인 오류", description="로그인이 안됩니다")
        comments = [
            Comment(
                id=1,
                body="<!-- project-ops-agent:analysis -->\n- Expected behavior: not found\n- Reproduction: not found",
                author_username="github-actions",
            ),
            Comment(id=2, body="@agent A", author_username="user"),
        ]
        analysis = IssueAnalyzer().analyze(issue, comments)
        self.assertEqual("", analysis.expected_behavior)
        self.assertEqual("", analysis.reproduction)
        self.assertIn("로그인", analysis.related_keywords)


if __name__ == "__main__":
    unittest.main()
