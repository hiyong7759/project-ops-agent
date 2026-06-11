import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


class CodexFixCommandTests(unittest.TestCase):
    def test_codex_fix_command_runs_codex_and_reports_git_changes(self):
        script = Path(__file__).resolve().parents[1] / "scripts" / "codex_fix_command.py"
        payload = {
            "issue": {
                "iid": 77,
                "title": "신규 기능",
                "description": "작은 기능을 추가합니다.",
                "labels": ["agent:queued"],
            },
            "analysis": {
                "summary": "신규 기능 추가",
            },
            "decision": "@agent A",
            "comments": ["@agent A"],
            "project": {
                "key": "demo",
                "name": "Demo",
            },
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            workspace = tmp_path / "repo"
            workspace.mkdir()
            fake_codex = tmp_path / "fake_codex.py"
            fake_codex.write_text(
                textwrap.dedent(
                    """
                    import pathlib
                    import sys

                    args = sys.argv[1:]
                    output_path = pathlib.Path(args[args.index("--output-last-message") + 1])
                    pathlib.Path("src").mkdir(exist_ok=True)
                    pathlib.Path("src/generated.py").write_text("VALUE = 1\\n", encoding="utf-8")
                    output_path.write_text("변경 요약: generated.py를 추가했습니다.\\n검증: fake codex", encoding="utf-8")
                    """
                ).strip(),
                encoding="utf-8",
            )
            subprocess.run(["git", "init"], cwd=workspace, check=True, capture_output=True)

            env = os.environ.copy()
            env["CODEX_FIX_COMMAND"] = f"{sys.executable} {fake_codex}"
            result = subprocess.run(
                [sys.executable, str(script)],
                cwd=workspace,
                input=json.dumps(payload, ensure_ascii=False),
                text=True,
                capture_output=True,
                check=False,
                env=env,
            )

            self.assertEqual(0, result.returncode, result.stderr)
            output = json.loads(result.stdout)
            self.assertTrue(output["success"])
            self.assertEqual(["src/generated.py"], output["files_changed"])
            self.assertIn("이슈 #77 수정", output["commit_message"])
            self.assertTrue((workspace / "src" / "generated.py").exists())

    def test_codex_fix_command_rejects_missing_issue_id(self):
        script = Path(__file__).resolve().parents[1] / "scripts" / "codex_fix_command.py"
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


if __name__ == "__main__":
    unittest.main()
