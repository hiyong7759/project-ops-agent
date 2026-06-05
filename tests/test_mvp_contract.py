import inspect
import unittest

from project_ops_agent import state
from project_ops_agent import templates
from project_ops_agent.github_client import GitHubClient
from project_ops_agent.gitlab_client import GitLabClient


class MvpContractTests(unittest.TestCase):
    def test_documented_agent_states_exist(self):
        self.assertEqual(
            (
                "agent:queued",
                "agent:analyzing",
                "agent:needs-info",
                "agent:fixing",
                "agent:verifying",
                "agent:mr-created",
                "agent:needs-user-test",
                "agent:changes-requested",
                "agent:blocked",
                "agent:done",
            ),
            state.AGENT_STATES,
        )

    def test_platform_clients_have_no_merge_operation(self):
        for client_type in (GitLabClient, GitHubClient):
            public_methods = [
                name
                for name, _value in inspect.getmembers(client_type, predicate=inspect.isfunction)
                if not name.startswith("_")
            ]
            self.assertNotIn("merge", public_methods)
            self.assertNotIn("merge_merge_request", public_methods)

    def test_report_template_uses_expandable_sections(self):
        source = inspect.getsource(templates.render_mr_report)
        self.assertIn("<table>", source)
        self.assertIn("<details>", source)
        self.assertIn("검토 요약", source)


if __name__ == "__main__":
    unittest.main()
