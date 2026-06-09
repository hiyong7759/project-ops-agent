# GitHub Actions MVP 검증

개인 GitHub 저장소에서는 회사 GitLab runner 없이도 Project Ops Agent의 운영 루프를 검증할 수 있습니다.

이 저장소에는 `hiyong7759/project-ops-agent` 검증용 workflow가 포함되어 있습니다.

```text
.github/workflows/project-ops-agent.yml
```

이 문서는 실제 GitHub Actions에서 에이전트가 Issue를 읽고, branch를 push하고, Pull Request를 만들 수 있는지 확인할 때 봅니다.

전체 개념은 repository root의 `README.md`, 문서 읽는 순서는 `docs/README.md`, 운영 label 규칙은 `docs/OPERATING_RULES.md`를 함께 참고합니다.

## 검증 범위

이 저장소는 Project Ops Agent 자체를 검증하는 MVP입니다. 화면 기능이나 실제 서비스 API가 없으므로 사용자가 확인할 수 있는 범위는 다음입니다.

| 확인 대상 | 사용자가 보는 곳 | 의미 |
| --- | --- | --- |
| Issue 상태 | GitHub Issue label | 에이전트가 현재 어느 단계에 있는지 |
| 에이전트 질문 | GitHub Issue comment | 사용자가 `@agent A/B/C`로 판단해야 할 내용 |
| PR 생성 | GitHub Pull Requests | 에이전트가 branch push와 PR 생성을 완료했는지 |
| PR 보고서 | PR 본문 | 분석, 사용자 결정, 검증 결과가 읽을 수 있게 정리됐는지 |
| 변경 파일 | PR Files changed | demo `fix.command`가 검증용 파일을 만들었는지 |
| 사용자 테스트 게이트 | 연결 Issue label | PR 생성 뒤에도 `agent:needs-user-test`에서 멈추는지 |
| 완료 처리 | Issue comment/label | `@agent test-pass` 후 `agent:done`으로 이동하는지 |

이 MVP에서 PR이 올라왔다는 사실만으로 실제 기능 테스트가 끝난 것은 아닙니다. 현재 프로젝트에서는 화면 확인 대신 PR 보고서, 변경 파일, 검증 로그, Issue 상태 전이를 확인하는 것이 사용자 테스트입니다.

## 흐름

```text
GitHub Issue에 agent:queued label 추가
  -> GitHub Actions workflow 수동 실행
  -> project_ops_agent scan 실행
  -> 이슈 분석 댓글 작성
  -> 모호하면 agent:needs-info
  -> 사용자가 이슈 댓글에 @agent A 작성
  -> 다음 workflow run에서 재개
  -> branch push
  -> Agent Report가 포함된 Pull Request 생성
  -> 이슈가 agent:needs-user-test로 이동
  -> 사용자가 이슈 댓글에 @agent test-pass 또는 @agent test-fail 작성
```

## Workflow

GitHub Actions 화면에 표시되는 workflow 이름:

```text
Project Ops Agent MVP
```

workflow는 `workflow_dispatch`를 지원합니다. 10분 주기 실행용 schedule은 workflow 파일에 주석으로 남겨두었습니다.

수동 실행 시 `config_path` 입력값으로 사용할 project config를 선택할 수 있습니다.

| config_path | 용도 |
| --- | --- |
| `configs/projects/github.sample.project.toml` | 안전한 기본 검증. `fix.command`가 비어 있어 코드 변경 전 중단 |
| `configs/projects/github.demo.project.toml` | demo `fix.command`로 PR 생성과 사용자 테스트 게이트까지 검증 |

workflow가 실행하는 명령:

```bash
python -m project_ops_agent.cli scan --config "$CONFIG_PATH"
```

필요한 권한:

```yaml
permissions:
  contents: write
  issues: write
  pull-requests: write
```

Pull Request를 GitHub Actions의 `GITHUB_TOKEN`으로 생성하려면 repository 설정도 맞아야 합니다.

GitHub에서 **Settings > Actions > General > Workflow permissions**를 열고 다음을 선택합니다.

- **Read and write permissions**
- **Allow GitHub Actions to create and approve pull requests**

이 설정이 꺼져 있으면 workflow 로그에 `PullRequests: write`가 보여도 PR 생성 API에서 다음 오류가 날 수 있습니다.

```text
GitHub POST /pulls failed: HTTP Error 403: Forbidden
```

## 기본 profile

기본 GitHub profile은 현재 checkout을 그대로 사용합니다.

```toml
[github]
owner = "hiyong7759"
repo = "project-ops-agent"
repo_http_url = "https://github.com/hiyong7759/project-ops-agent.git"

[workspace]
use_current_checkout = true
```

이 설정은 `actions/checkout`이 받아온 저장소에서 바로 branch 생성, commit, push를 수행하게 합니다. 별도 clone을 피할 수 있고 private repo credential 문제도 줄어듭니다.

## demo fix.command

`scripts/demo_fix_command.py`는 실무 수정 도구가 아닙니다. PR 생성 경로를 검증하기 위한 데모 명령입니다.

에이전트가 전달한 JSON에서 이슈 번호와 제목을 읽고, `.agent-demo/` 아래에 검증용 Markdown 파일을 만듭니다. 그런 다음 다음과 같은 결과 JSON을 반환합니다.

```json
{
  "success": true,
  "summary": "demo fix.command가 검증용 산출물을 생성했습니다.",
  "files_changed": [".agent-demo/issue-123-example.md"],
  "commit_message": "이슈 #123 데모 수정 생성\n\nRefs #123"
}
```

이 명령을 쓰면 실제 업무 코드를 고치지 않고도 다음을 검증할 수 있습니다.

- `fix.command` 실행
- 변경 파일 감지
- 검증 명령 실행
- commit 생성
- branch push
- PR 생성
- 이슈를 `agent:needs-user-test`로 이동

## 수동 검증 절차

1. GitHub에서 **Actions**를 엽니다.
2. **Project Ops Agent MVP**를 선택합니다.
3. **Run workflow**를 누릅니다.
4. branch는 `main`을 유지합니다.
5. `config_path`를 선택합니다.
6. **Run workflow**를 다시 눌러 실행합니다.

안전한 첫 검증은 기본 config로 시작합니다.

```text
configs/projects/github.sample.project.toml
```

PR 생성까지 검증하려면 demo config를 사용합니다.

```text
configs/projects/github.demo.project.toml
```

실행 전 WSL에서 로컬 테스트도 확인합니다.

```bash
cd ~/workspace/project-ops-agent
export PYTHONPATH=src
export PYTHONDONTWRITEBYTECODE=1
python3 -m unittest discover -s tests
```

## 사용자가 판단하는 시점

| 시점 | 사용자가 할 일 | 에이전트가 다음 run에서 할 일 |
| --- | --- | --- |
| `agent:needs-info` | 연결 Issue에 `@agent A`, `@agent B`, `@agent C` 중 하나를 댓글로 작성 | 댓글을 읽고 수정 단계로 진행 |
| PR 생성 후 `agent:needs-user-test` | PR 본문, 변경 파일, workflow 검증 결과를 확인 | 대기 |
| 확인 통과 | 연결 Issue에 `@agent test-pass` 댓글 작성 | Issue를 `agent:done`으로 이동 |
| 확인 실패 | 연결 Issue에 `@agent test-fail <사유>` 댓글 작성 | Issue를 `agent:changes-requested`로 이동 |

에이전트는 PR을 만들 수 있지만 merge하지 않습니다. merge 여부는 사람이 PR을 검토한 뒤 결정합니다.

## 필요한 label

workflow를 실행하기 전에 저장소에 다음 label이 있어야 합니다.

```text
agent:queued
agent:analyzing
agent:needs-info
agent:fixing
agent:verifying
agent:mr-created
agent:needs-user-test
agent:changes-requested
agent:blocked
agent:done
risk:low
risk:medium
risk:high
```

`agent:mr-created`는 GitLab 흐름과의 호환을 위해 이름을 유지합니다. GitHub에서는 Pull Request가 생성됐다는 뜻입니다.

## 테스트용 이슈 예시

모호한 이슈를 만들어 `agent:needs-info` 흐름을 검증합니다.

```markdown
Title: MVP 검증: 로그인 오류

Body:
로그인이 안됩니다
```

이슈에 `agent:queued` label을 붙이고 workflow를 실행합니다. 에이전트가 분석 댓글과 추가 정보 요청 댓글을 남기면 사용자는 이슈 댓글에 답합니다.

```text
@agent A
```

PR이 생성되고 이슈가 `agent:needs-user-test`가 되면 PR을 직접 확인하고 테스트합니다. 결과는 연결된 이슈에 남깁니다.

```text
@agent test-pass
```

또는:

```text
@agent test-fail workflow 실행 중 unittest discovery가 실패합니다
```

## Token

기본 `GITHUB_TOKEN`은 workflow 권한에 `contents: write`, `issues: write`, `pull-requests: write`가 있으면 MVP 검증에 충분합니다.

단, PR 생성까지 검증하려면 repository의 Workflow permissions가 `Read and write permissions`로 설정되어 있고, GitHub Actions의 PR 생성이 허용되어 있어야 합니다.

조직 정책이 더 엄격하거나 cross-repository 검증이 필요하면 contents, issues, pull requests write 권한이 있는 fine-grained personal access token을 별도 secret으로 사용할 수 있습니다.
