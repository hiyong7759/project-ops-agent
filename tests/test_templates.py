import unittest

from project_ops_agent.models import CommandResult, FixResult, Issue, IssueAnalysis
from project_ops_agent.templates import render_mr_report


class TemplateTests(unittest.TestCase):
    def test_mr_report_is_compact_and_expandable(self):
        issue = Issue(iid=10, title="주문 상태 오류", web_url="https://gitlab.local/issues/10")
        analysis = IssueAnalysis(
            issue_iid=10,
            summary="주문 상태 오류",
            observed_behavior="현재 실패",
            expected_behavior="정상 성공",
            reproduction="재현 단계",
            ambiguity_reasons=[],
            policy_flags=[],
            risk="low",
            related_keywords=["주문", "상태"],
        )
        report = render_mr_report(
            issue,
            analysis,
            FixResult(success=True, summary="가드를 추가했습니다."),
            [CommandResult(command="npm test", exit_code=0, stdout="ok")],
            ["src/order.ts"],
            ["이슈 분석 완료"],
        )
        self.assertIn("<table>", report)
        self.assertIn("<details>", report)
        self.assertIn("작성 주체:", report)
        self.assertIn("사용자가 먼저 확인할 것", report)
        self.assertIn("코드 리뷰 참고", report)
        self.assertIn("검토 요약", report)
        self.assertIn("사용자 테스트 게이트", report)
        self.assertIn("@agent test-pass", report)
        self.assertIn("관련 이슈: #10", report)


if __name__ == "__main__":
    unittest.main()
