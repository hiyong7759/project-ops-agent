from __future__ import annotations

from .clarification import has_marker, latest_agent_decision, latest_user_test_result
from .command_runner import CommandRunner
from .fix_provider import ExternalFixProvider
from .git_runner import GitRunner
from .issue_analyzer import IssueAnalyzer
from .models import Issue, ProcessResult, ProjectProfile
from .policy import PolicyEngine
from .state import with_agent_state, with_risk_label
from .state import PROCESSABLE_STATES, current_agent_state
from .templates import (
    ANALYSIS_MARKER,
    MR_COMMENT_MARKER,
    NEEDS_INFO_MARKER,
    render_blocked,
    render_issue_analysis,
    render_mr_issue_comment,
    render_mr_report,
    render_needs_info,
    render_user_test_request,
    USER_TEST_MARKER,
)


class Orchestrator:
    def __init__(
        self,
        issue_client,
        profile: ProjectProfile,
        analyzer: IssueAnalyzer | None = None,
        policy: PolicyEngine | None = None,
        git_runner: GitRunner | None = None,
        command_runner: CommandRunner | None = None,
        fix_provider: ExternalFixProvider | None = None,
    ) -> None:
        self.gitlab = issue_client
        self.profile = profile
        self.analyzer = analyzer or IssueAnalyzer()
        self.policy = policy or PolicyEngine(profile.policy)
        self.git_runner = git_runner or GitRunner(profile)
        self.command_runner = command_runner or CommandRunner(profile.commands)
        self.fix_provider = fix_provider or ExternalFixProvider(profile)

    def process_queued(self, limit: int = 20) -> list[ProcessResult]:
        seen: set[int] = set()
        issues: list[Issue] = []
        for label in PROCESSABLE_STATES:
            for issue in self.gitlab.list_issues_by_label(label, limit=limit):
                if issue.iid not in seen:
                    seen.add(issue.iid)
                    issues.append(issue)
        return [self.process_issue(issue) for issue in issues[:limit]]

    def process_issue(self, issue: Issue) -> ProcessResult:
        comments = self.gitlab.get_issue_comments(issue.iid)
        state = current_agent_state(issue.labels)
        if state == "agent:needs-user-test":
            return self._process_user_test(issue, comments)

        decision = latest_agent_decision(comments)

        self._set_labels(issue, "agent:analyzing")
        analysis = self.analyzer.analyze(issue, comments, decision=decision)

        if not has_marker(comments, ANALYSIS_MARKER):
            self.gitlab.post_issue_comment(issue.iid, render_issue_analysis(analysis))

        labels_with_risk = with_risk_label(issue.labels, analysis.risk)
        if labels_with_risk != issue.labels:
            issue.labels = labels_with_risk
            self.gitlab.update_issue_labels(issue.iid, labels_with_risk)

        if self.policy.requires_human_direction(analysis):
            comments = self.gitlab.get_issue_comments(issue.iid)
            if not has_marker(comments, NEEDS_INFO_MARKER):
                self.gitlab.post_issue_comment(issue.iid, render_needs_info(analysis))
            self._set_labels(issue, "agent:needs-info")
            return ProcessResult("needs-info", "Waiting for GitLab issue comment direction.", issue.iid)

        if not self.profile.agent.can_push_branch or not self.profile.agent.can_create_mr:
            return self._block(issue, "Project profile does not allow branch push or MR creation.")

        self._set_labels(issue, "agent:fixing")
        decision_log = [
            f"Issue #{issue.iid} received",
            "Analysis completed",
        ]
        if decision:
            decision_log.append(f"Human decision detected: {decision}")

        try:
            workspace = self.git_runner.prepare_workspace()
            branch = self.git_runner.create_branch(workspace, issue)
            decision_log.append(f"Branch created: {branch}")

            install_results = self.command_runner.run_many(self.command_runner.install_commands(), workspace)
            if any(not result.ok for result in install_results):
                return self._block(issue, "Install command failed.")

            fix_result = self.fix_provider.apply(workspace, issue, analysis, comments)
            if not fix_result.success:
                return self._block(issue, fix_result.summary or "Fix command failed.")

            changed_files = self.git_runner.changed_files(workspace)
            changed_files = changed_files or fix_result.files_changed
            if not changed_files:
                return self._block(issue, "Fix command completed but no file changes were detected.")

            forbidden = self.policy.forbidden_changed_paths(changed_files)
            if forbidden:
                return self._block(issue, f"Forbidden files changed: {', '.join(forbidden)}")

            self._set_labels(issue, "agent:verifying")
            verification = self.command_runner.run_many(self.command_runner.verification_commands(), workspace)
            decision_log.append("Verification commands completed")

            commit_message = fix_result.commit_message or _default_commit_message(issue)
            committed = self.git_runner.commit_all(workspace, commit_message)
            if not committed:
                return self._block(issue, "No changes were available to commit.")

            self.git_runner.push_branch(workspace, branch)
            decision_log.append("Branch pushed")

            report = render_mr_report(issue, analysis, fix_result, [*install_results, *verification], changed_files, decision_log)
            mr = self.gitlab.create_merge_request(
                source_branch=branch,
                target_branch=self.profile.default_branch,
                title=f"[Agent] {issue.title}",
                description=report,
            )
            comments = self.gitlab.get_issue_comments(issue.iid)
            if not has_marker(comments, MR_COMMENT_MARKER):
                self.gitlab.post_issue_comment(issue.iid, render_mr_issue_comment(mr))
            if not has_marker(comments, USER_TEST_MARKER):
                self.gitlab.post_issue_comment(issue.iid, render_user_test_request(mr))
            self._set_labels(issue, "agent:needs-user-test")
            return ProcessResult("needs-user-test", "Merge request created and waiting for user testing.", issue.iid, mr_url=mr.web_url)
        except Exception as exc:
            return self._block(issue, str(exc))

    def _process_user_test(self, issue: Issue, comments) -> ProcessResult:
        result, reason = latest_user_test_result(comments)
        if result == "pass":
            self.gitlab.post_issue_comment(
                issue.iid,
                "## Agent User Test Accepted\n\nUser testing was recorded with `@agent test-pass`.",
            )
            self._set_labels(issue, "agent:done")
            return ProcessResult("done", "User testing passed.", issue.iid)
        if result == "fail":
            message = reason or "User testing failed without a detailed reason."
            self.gitlab.post_issue_comment(
                issue.iid,
                f"## Agent Changes Requested\n\nUser testing failed: {message}",
            )
            self._set_labels(issue, "agent:changes-requested")
            return ProcessResult("changes-requested", message, issue.iid)
        return ProcessResult("needs-user-test", "Waiting for @agent test-pass or @agent test-fail.", issue.iid)

    def _block(self, issue: Issue, reason: str) -> ProcessResult:
        self.gitlab.post_issue_comment(issue.iid, render_blocked(reason))
        self._set_labels(issue, "agent:blocked")
        return ProcessResult("blocked", reason, issue.iid)

    def _set_labels(self, issue: Issue, state: str) -> None:
        labels = with_agent_state(issue.labels, state)
        if labels != issue.labels:
            issue.labels = labels
            self.gitlab.update_issue_labels(issue.iid, labels)


def _default_commit_message(issue: Issue) -> str:
    return f"Fix issue #{issue.iid}: {issue.title}\n\nRefs #{issue.iid}"
