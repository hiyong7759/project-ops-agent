# GitHub Actions MVP 검증

개인 GitHub 저장소에서는 회사 GitLab runner 없이도 Project Ops Agent의 운영 루프를 검증할 수 있습니다.

이 저장소에는 `hiyong7759/project-ops-agent` 검증용 workflow가 포함되어 있습니다.

```text
.github/workflows/project-ops-agent.yml
```

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

조직 정책이 더 엄격하거나 cross-repository 검증이 필요하면 contents, issues, pull requests write 권한이 있는 fine-grained personal access token을 별도 secret으로 사용할 수 있습니다.
