import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class DemoFixCommandTests(unittest.TestCase):
    def test_demo_fix_command_creates_validation_artifact(self):
        script = Path(__file__).resolve().parents[1] / "scripts" / "demo_fix_command.py"
        payload = {
            "issue": {
                "iid": 123,
                "title": "로그인 오류",
            },
            "analysis": {
                "summary": "로그인 오류",
            },
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [sys.executable, str(script)],
                cwd=tmpdir,
                input=json.dumps(payload, ensure_ascii=False),
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(0, result.returncode)
            output = json.loads(result.stdout)
            self.assertTrue(output["success"])
            self.assertEqual([".agent-demo/issue-123-로그인-오류.md"], output["files_changed"])
            self.assertTrue((Path(tmpdir) / ".agent-demo" / "issue-123-로그인-오류.md").exists())

    def test_demo_fix_command_rejects_missing_issue_id(self):
        script = Path(__file__).resolve().parents[1] / "scripts" / "demo_fix_command.py"
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [sys.executable, str(script)],
                cwd=tmpdir,
                input="{}",
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(0, result.returncode)
            output = json.loads(result.stdout)
            self.assertFalse(output["success"])
            self.assertFalse((Path(tmpdir) / ".agent-demo").exists())


if __name__ == "__main__":
    unittest.main()
