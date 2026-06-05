import unittest

from project_ops_agent.models import CommandResult, FixResult, Issue, IssueAnalysis
from project_ops_agent.templates import render_mr_report


class TemplateTests(unittest.TestCase):
    def test_mr_report_is_compact_and_expandable(self):
        issue = Issue(iid=10, title="Order status bug", web_url="https://gitlab.local/issues/10")
        analysis = IssueAnalysis(
            issue_iid=10,
            summary="Order status bug",
            observed_behavior="actual failure",
            expected_behavior="expected success",
            reproduction="repro steps",
            ambiguity_reasons=[],
            policy_flags=[],
            risk="low",
            related_keywords=["order", "status"],
        )
        report = render_mr_report(
            issue,
            analysis,
            FixResult(success=True, summary="Added guard"),
            [CommandResult(command="npm test", exit_code=0, stdout="ok")],
            ["src/order.ts"],
            ["Analysis completed"],
        )
        self.assertIn("<table>", report)
        self.assertIn("<details>", report)
        self.assertIn("Reviewer Summary", report)
        self.assertIn("User Test Gate", report)
        self.assertIn("@agent test-pass", report)
        self.assertIn("Closes #10", report)


if __name__ == "__main__":
    unittest.main()
