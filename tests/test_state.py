import unittest

from project_ops_agent.state import PROCESSABLE_STATES, current_agent_state, with_agent_state, with_risk_label


class StateTests(unittest.TestCase):
    def test_agent_state_is_mutually_exclusive(self):
        labels = ["bug", "agent:queued", "agent:fixing"]
        result = with_agent_state(labels, "agent:needs-info")
        self.assertEqual(current_agent_state(result), "agent:needs-info")
        self.assertNotIn("agent:queued", result)
        self.assertNotIn("agent:fixing", result)
        self.assertIn("bug", result)

    def test_risk_label_is_mutually_exclusive(self):
        labels = ["risk:low", "agent:queued"]
        result = with_risk_label(labels, "high")
        self.assertIn("risk:high", result)
        self.assertNotIn("risk:low", result)

    def test_scan_processes_waiting_states(self):
        self.assertIn("agent:queued", PROCESSABLE_STATES)
        self.assertIn("agent:needs-info", PROCESSABLE_STATES)
        self.assertIn("agent:needs-user-test", PROCESSABLE_STATES)


if __name__ == "__main__":
    unittest.main()
