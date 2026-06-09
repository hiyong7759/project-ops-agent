from __future__ import annotations

from .clarification import (
    has_marker,
    latest_agent_decision,
    latest_agent_decision_after_marker,
    latest_user_test_result,
    latest_user_test_result_after_marker,
)
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
    BLOCKED_MARKER,
    MR_COMMENT_MARKER,
    NEEDS_INFO_MARKER,
    render_blocked,
    render_issue_analysis,
    render_mr_issue_comment,
    render_mr_report,
    render_needs_info,
    render_user_test_fail_confirmation,
    render_user_test_pass_confirmation,
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
        if state == "agent:needs-info":
            decision = latest_agent_decision_after_marker(comments, NEEDS_INFO_MARKER)
            if not decision:
                return ProcessResult(
                    "needs-info",
                    "추가 정보 요청 이후 사용자 방향 결정을 기다리는 중입니다.",
                    issue.iid,
                )

        if state == "agent:blocked":
            decision = latest_agent_decision_after_marker(comments, BLOCKED_MARKER)
            if not decision:
                return ProcessResult("blocked", "중단 상태입니다. 이슈 댓글에 `@agent proceed` 또는 `@agent A`를 남기면 재시도합니다.", issue.iid)

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
            return ProcessResult("needs-info", "이슈 댓글로 사용자 방향 결정을 기다리는 중입니다.", issue.iid)

        if not self.profile.agent.can_push_branch or not self.profile.agent.can_create_mr:
            return self._block(issue, "프로젝트 설정에서 브랜치 push 또는 MR/PR 생성을 허용하지 않습니다.")

        self._set_labels(issue, "agent:fixing")
        decision_log = [
            f"이슈 #{issue.iid} 수신",
            "이슈 분석 완료",
        ]
        if decision:
            decision_log.append(f"사용자 결정 확인: {decision}")

        try:
            workspace = self.git_runner.prepare_workspace()
            branch = self.git_runner.create_branch(workspace, issue)
            decision_log.append(f"브랜치 생성: {branch}")

            install_results = self.command_runner.run_many(self.command_runner.install_commands(), workspace)
            if any(not result.ok for result in install_results):
                return self._block(issue, "설치 명령이 실패했습니다.")

            fix_result = self.fix_provider.apply(workspace, issue, analysis, comments)
            if not fix_result.success:
                return self._block(issue, fix_result.summary or "수정 명령이 실패했습니다.")

            changed_files = self.git_runner.changed_files(workspace)
            changed_files = changed_files or fix_result.files_changed
            if not changed_files:
                return self._block(issue, "수정 명령은 완료됐지만 변경된 파일이 감지되지 않았습니다.")

            forbidden = self.policy.forbidden_changed_paths(changed_files)
            if forbidden:
                return self._block(issue, f"변경 금지 경로가 수정되었습니다: {', '.join(forbidden)}")

            self._set_labels(issue, "agent:verifying")
            verification = self.command_runner.run_many(self.command_runner.verification_commands(), workspace)
            decision_log.append("검증 명령 실행 완료")

            commit_message = fix_result.commit_message or _default_commit_message(issue)
            committed = self.git_runner.commit_all(workspace, commit_message)
            if not committed:
                return self._block(issue, "커밋할 변경 사항이 없습니다.")

            self.git_runner.push_branch(workspace, branch)
            decision_log.append("브랜치 push 완료")

            report = render_mr_report(issue, analysis, fix_result, [*install_results, *verification], changed_files, decision_log)
            mr = self.gitlab.create_merge_request(
                source_branch=branch,
                target_branch=self.profile.default_branch,
                title=f"[에이전트] {issue.title}",
                description=report,
            )
            comments = self.gitlab.get_issue_comments(issue.iid)
            if not has_marker(comments, MR_COMMENT_MARKER):
                self.gitlab.post_issue_comment(issue.iid, render_mr_issue_comment(mr))
            if not has_marker(comments, USER_TEST_MARKER):
                self.gitlab.post_issue_comment(
                    issue.iid,
                    render_user_test_request(mr, analysis, changed_files, [*install_results, *verification]),
                )
            self._set_labels(issue, "agent:needs-user-test")
            return ProcessResult("needs-user-test", "MR/PR을 생성했고 사용자 테스트를 기다리는 중입니다.", issue.iid, mr_url=mr.web_url)
        except Exception as exc:
            return self._block(issue, str(exc))

    def _process_user_test(self, issue: Issue, comments) -> ProcessResult:
        if has_marker(comments, USER_TEST_MARKER):
            result, reason = latest_user_test_result_after_marker(comments, USER_TEST_MARKER)
        else:
            result, reason = latest_user_test_result(comments)
        if result == "pass":
            self.gitlab.post_issue_comment(issue.iid, render_user_test_pass_confirmation())
            self._set_labels(issue, "agent:done")
            return ProcessResult("done", "사용자 테스트가 통과했습니다.", issue.iid)
        if result == "fail":
            message = reason or "상세 사유 없이 사용자 테스트 실패가 기록되었습니다."
            self.gitlab.post_issue_comment(issue.iid, render_user_test_fail_confirmation(message))
            self._set_labels(issue, "agent:changes-requested")
            return ProcessResult("changes-requested", message, issue.iid)
        return ProcessResult("needs-user-test", "`@agent test-pass` 또는 `@agent test-fail` 댓글을 기다리는 중입니다.", issue.iid)

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
    return f"이슈 #{issue.iid} 수정: {issue.title}\n\nRefs #{issue.iid}"
