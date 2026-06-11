import unittest
from pathlib import Path

from project_ops_agent.git_runner import GitRunner
from project_ops_agent.models import AgentSettings, GitHubSettings, Issue, ProjectProfile, WorkspaceSettings


class RecordingGitRunner(GitRunner):
    def __init__(self, profile):
        super().__init__(profile)
        self.commands = []

    def _run(self, args, cwd, check=True):
        self.commands.append(list(args))

        class Result:
            stdout = ""
            stderr = ""
            returncode = 0

        return Result()


def profile():
    return ProjectProfile(
        key="project-ops-agent",
        platform="github",
        name="Project Ops Agent",
        github=GitHubSettings(
            owner="hiyong7759",
            repo="project-ops-agent",
            default_branch="main",
            repo_http_url="https://github.com/hiyong7759/project-ops-agent.git",
        ),
        agent=AgentSettings(branch_prefix="agent"),
        workspace=WorkspaceSettings(use_current_checkout=True),
    )


class GitRunnerTests(unittest.TestCase):
    def test_create_branch_uses_origin_base_for_actions_checkout(self):
        runner = RecordingGitRunner(profile())
        issue = Issue(iid=4, title="문서 흐름 개선")

        branch = runner.create_branch(Path.cwd(), issue)

        self.assertEqual("agent/project-ops-agent-4-issue", branch)
        self.assertEqual(
            [
                ["git", "fetch", "origin", "main"],
                ["git", "checkout", "-B", "main", "origin/main"],
                ["git", "checkout", "-B", branch],
            ],
            runner.commands,
        )

    def test_push_branch_updates_agent_branch_on_retry(self):
        runner = RecordingGitRunner(profile())

        runner.push_branch(Path.cwd(), "agent/project-ops-agent-4-issue")

        self.assertEqual(
            [["git", "push", "--force-with-lease", "-u", "origin", "agent/project-ops-agent-4-issue"]],
            runner.commands,
        )


if __name__ == "__main__":
    unittest.main()
