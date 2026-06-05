import unittest
from pathlib import Path

from project_ops_agent.config import load_project_profile


class ConfigTests(unittest.TestCase):
    def test_load_gitlab_profile(self):
        profile = load_project_profile(Path("configs/projects/sample.project.toml"))
        self.assertEqual("gitlab", profile.platform)
        self.assertEqual("main", profile.default_branch)
        self.assertTrue(profile.repo_http_url.endswith("/group/order-api.git"))

    def test_load_github_profile(self):
        profile = load_project_profile(Path("configs/projects/github.sample.project.toml"))
        self.assertEqual("github", profile.platform)
        self.assertEqual("main", profile.default_branch)
        self.assertEqual("https://api.github.com", profile.github.api_url)
        self.assertEqual("hiyong7759", profile.github.owner)
        self.assertEqual("project-ops-agent", profile.github.repo)
        self.assertEqual("https://github.com/hiyong7759/project-ops-agent.git", profile.repo_http_url)
        self.assertTrue(profile.workspace.use_current_checkout)

    def test_load_github_demo_profile(self):
        profile = load_project_profile(Path("configs/projects/github.demo.project.toml"))
        self.assertEqual("github", profile.platform)
        self.assertEqual("python scripts/demo_fix_command.py", profile.fix.command)
        self.assertTrue(profile.workspace.use_current_checkout)


if __name__ == "__main__":
    unittest.main()
