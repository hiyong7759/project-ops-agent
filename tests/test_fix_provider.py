import json
import unittest

from project_ops_agent.fix_provider import _parse_fix_result


class FixProviderTests(unittest.TestCase):
    def test_parse_fix_result_uses_payload_logs_when_present(self):
        result = _parse_fix_result(
            json.dumps(
                {
                    "success": True,
                    "summary": "완료",
                    "files_changed": ["src/app.py"],
                    "stdout": "도구 최종 메시지",
                    "stderr": "도구 경고",
                },
                ensure_ascii=False,
            ),
            "",
        )

        self.assertTrue(result.success)
        self.assertEqual("도구 최종 메시지", result.stdout)
        self.assertEqual("도구 경고", result.stderr)


if __name__ == "__main__":
    unittest.main()
