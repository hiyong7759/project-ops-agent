# GitHub Actions MVP 검증

개인 GitHub 저장소에서는 회사 GitLab runner 없이도 Project Ops Agent의 운영 루프를 검증할 수 있습니다.

이 저장소에는 `hiyong7759/project-ops-agent` 검증용 workflow가 포함되어 있습니다.

```text
.github/workflows/project-ops-agent.yml
```

이 문서는 실제 GitHub Actions에서 에이전트가 Issue를 읽고, branch를 push하고, Pull Request를 만들 수 있는지 확인할 때 봅니다.

전체 개념은 repository root의 `README.md`, 문서 읽는 순서는 `docs/README.md`, 운영 label 규칙은 `docs/OPERATING_RULES.md`를 함께 참고합니다.

## 실행 전 반드시 준비할 것

이 단계는 PR이 안 올라왔을 때 먼저 확인하는 항목입니다.

### 1) 라벨 준비

에이전트는 scan 시작 시점에 누락된 `agent:*`, `risk:*` 라벨을 자동 생성합니다.

- `agent:queued`만 수동으로 준비하면 되고, 나머지는 자동 생성됩니다.
- `agent:queued`는 수동으로 붙일 수 있어야 합니다.

필요 시 GitHub에서 `agent:queued`만 먼저 만들고 시작하세요.

1. 저장소에서 **Issues**
2. 오른쪽 상단 **Labels**
3. **New label**

이름: `agent:queued`

GitLab이 대상이면 동일하게 **Issues** 화면에서 라벨을 생성하면 됩니다.

### 2) 토큰/권한 준비

이 저장소 MVP는 기본적으로 `GITHUB_TOKEN`을 사용합니다.

1. workflow 파일에서 `permissions`를 `contents: write`, `issues: write`, `pull-requests: write`로 유지합니다.  
2. repository 설정에서 **Settings > Actions > General > Workflow permissions**를 열고  
   - **Read and write permissions**
   - **Allow GitHub Actions to create and approve pull requests**
   를 ON 합니다.

cross-repo(다른 저장소), 조직 정책이 엄격한 환경에서는 PAT을 써야 합니다.

1. GitHub token 생성: **Settings > Developer settings > Personal access tokens > Fine-grained tokens > Generate new token**
2. scope: `contents`, `issues`, `pull-requests` 쓰기 권한 최소값으로 제한
3. repo secret 등록: `Settings > Secrets and variables > Actions > New repository secret`에서 예: `GH_TOKEN` 생성
4. workflow가 PAT을 쓰도록 `env.GITHUB_TOKEN` 값을 `${{ secrets.GH_TOKEN }}`로 변경

### 3) `fix.command`와 검증 명령 연결

`project` 설정은 `configs/projects/*.project.toml`에서 관리합니다.

- `[commands]`는 install/lint/test를 정의합니다.
- `[fix]`의 `command`는 실제 코드를 수정할 외부 명령입니다.
- `fix.command`는 issue context JSON을 입력으로 받아 JSON 결과(`success`, `summary`, `files_changed`, `commit_message`)를 stdout으로 반환해야 합니다.

예시:

```toml
[commands]
install = "npm ci"
lint = "npm run lint"
test = "npm test"

[fix]
command = "python scripts/fix_for_project.py"
timeout_seconds = 1800
```

`fix.command`가 없거나 비어 있으면 실제 코드 변경은 수행되지 않고 흐름이 중단됩니다.

## 검증 범위

이 저장소는 Project Ops Agent 자체를 검증하는 MVP입니다. 화면 기능이나 실제 서비스 API가 없으므로 사용자가 확인할 수 있는 범위는 다음입니다.

| 확인 대상 | 사용자가 보는 곳 | 의미 |
| --- | --- | --- |
| Issue 상태 | GitHub Issue label | 에이전트가 현재 어느 단계에 있는지 |
| 에이전트 질문 | GitHub Issue comment | 사용자가 `@agent A/B/C` 또는 `@agent 방향: <내용>`으로 판단해야 할 내용 |
| PR 생성 | GitHub Pull Requests | 에이전트가 branch push와 PR 생성을 완료했는지 |
| PR 보고서 | PR 본문 | 먼저 확인할 테스트 항목, 분석, 사용자 결정, 검증 결과가 읽을 수 있게 정리됐는지 |
| 변경 파일 | PR Files changed | demo `fix.command`가 검증용 파일을 만들었는지 |
| 사용자 테스트 게이트 | 연결 Issue label | PR 생성 뒤에도 `agent:needs-user-test`에서 멈추는지 |
| 완료 처리 | Issue comment/label | `@agent test-pass` 후 `agent:done`으로 이동하는지 |

이 MVP에서 PR이 올라왔다는 사실만으로 실제 기능 테스트가 끝난 것은 아닙니다. 현재 프로젝트에서는 화면 확인 대신 PR 보고서, 변경 파일, 검증 로그, Issue 상태 전이를 확인하는 것이 사용자 테스트입니다.

## 사용자가 보는 전체 흐름

괄호 안의 label은 GitHub Issue에서 현재 위치를 확인하기 위한 보조 표기입니다.

| 흐름 | 사용자가 확인할 곳 | 현재 의미 | 사용자가 할 일 |
| --- | --- | --- | --- |
| 작업 맡김 (`agent:queued`) | GitHub Issue | 이 이슈를 에이전트가 처리하도록 표시함 | 이슈 내용이 충분한지 확인하고 workflow 실행 |
| 분석 결과 확인 (`agent:analyzing`) | Issue comment, Actions log | 에이전트가 이슈를 읽고 판단 중 | 보통 기다림 |
| 질문에 답하기 (`agent:needs-info`) | Issue comment | 코드 변경 전에 사용자의 방향 결정이 필요함 | Issue 댓글에 `@agent A` 또는 `@agent 방향: <내용>` 같은 답변 작성 후 workflow 재실행 |
| 수정/검증 진행 (`agent:fixing`, `agent:verifying`) | Actions log | demo `fix.command`와 테스트가 실행 중 | workflow가 끝날 때까지 기다림 |
| PR 확인 (`agent:needs-user-test`) | Pull Requests, PR 본문, Files changed | PR이 생성됐고 사람이 검토해야 함 | PR 본문의 “사용자가 먼저 확인할 것”을 테스트하고, 필요하면 Files changed에서 코드 리뷰 |
| 완료 또는 보완 (`agent:done`, `agent:changes-requested`) | Issue label/comment | 사용자 테스트 결과가 반영됨 | 필요하면 사람이 merge하거나 보완 이슈를 이어감 |

PR이 아직 없다면 PR 본문을 확인하는 단계가 아닙니다. 먼저 Issue 댓글에 질문이 남았는지, Actions 로그에 권한 또는 검증 오류가 있는지 확인합니다.

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
| `configs/projects/github.codex.project.toml` | Codex CLI wrapper로 실제 소스 수정을 시도 |

workflow가 실행하는 명령:

```bash
python -m project_ops_agent.cli scan --config "$CONFIG_PATH"
```

`github.codex.project.toml`을 선택하면 workflow가 Codex CLI를 설치하고 `scripts/codex_fix_command.py`를 `fix.command`로 실행합니다. 이 모드는 runner에서 Codex CLI 인증이 이미 준비되어 있어야 동작합니다.

보안상 이 모드는 신뢰하는 private repo와 runner에서 먼저 검증하세요. 최종 사내 운영에서는 GitLab Runner나 self-hosted runner에 Codex CLI 로그인 상태와 필요한 설정을 runner 내부에 준비하는 방식을 기준으로 합니다.

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
[project]
policy_file = "AGENTS.md"

[github]
owner = "hiyong7759"
repo = "project-ops-agent"
repo_http_url = "https://github.com/hiyong7759/project-ops-agent.git"

[workspace]
use_current_checkout = true
```

`policy_file`은 Markdown/TOML/JSON 정책 파일 경로입니다. `AGENTS.md`처럼 config 파일 옆에 없는 파일명은 상위 디렉터리에서 찾아 저장소 루트의 `AGENTS.md`를 사용할 수 있습니다.

이 설정은 `actions/checkout`이 받아온 저장소에서 바로 branch 생성, commit, push를 수행하게 합니다. 별도 clone을 피할 수 있고 private repo credential 문제도 줄어듭니다.

workflow는 checkout 시 전체 이력을 가져오고, 에이전트는 `origin/main` 같은 원격 기준 branch에서 작업 branch를 다시 만듭니다. PR 생성 권한 오류처럼 branch push 이후 PR 생성 전에 실패한 경우에도, 권한을 고친 뒤 재실행하면 에이전트가 자신의 `agent/...` branch를 갱신해 다시 시도할 수 있습니다.

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
- 이슈를 사용자 테스트 대기 상태(`agent:needs-user-test`)로 이동

## 수동 검증 절차

1. GitHub 저장소에서 **Issues**를 엽니다.
2. **New issue**를 눌러 테스트 Issue를 만듭니다.
3. 제목과 본문을 입력합니다.
4. Issue 오른쪽 **Labels**에서 `agent:queued`를 붙입니다.
5. **Create**를 눌러 Issue를 저장합니다.
6. GitHub에서 **Actions**를 엽니다.
7. **Project Ops Agent MVP**를 선택합니다.
8. **Run workflow**를 누릅니다.
9. branch는 `main`을 유지합니다.
10. `config_path`를 선택합니다.
11. **Run workflow**를 다시 눌러 실행합니다.

`agent:queued` label이 보이지 않으면 먼저 `agent:queued`부터 준비한 뒤 workflow를 실행하세요. 나머지 라벨은 에이전트가 자동 생성합니다.

처음 검증하는 조직원은 아래 config를 사용합니다.

```text
configs/projects/github.sample.project.toml
```

이 config는 실제 코드를 수정하지 않고 Issue 분석과 질문 흐름만 확인합니다.

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

| 상황 | 사용자가 해석할 의미 | 사용자가 할 일 | 에이전트가 다음 run에서 할 일 |
| --- | --- | --- | --- |
| Issue에 추가 정보 요청 댓글이 있음 | 에이전트가 코드 변경 전 방향을 묻고 있음 | 연결 Issue에 `@agent A`, `@agent B`, `@agent C` 중 하나를 댓글로 작성 | 댓글을 읽고 수정 단계로 진행 |
| 선택지 밖의 방향이 필요함 | A/B/C보다 더 맞는 처리 방향이 있음 | 연결 Issue에 `@agent 방향: <내용>` 형식으로 직접 지시 | 해당 방향을 사용자 결정으로 기록하고 수정 단계로 진행 |
| PR이 생성되고 Issue가 사용자 테스트 대기 상태임 | 자동 수정과 기본 검증은 끝났고 사람이 확인할 차례 | PR 본문의 “사용자가 먼저 확인할 것”, 변경 파일, workflow 검증 결과를 확인 | 테스트 결과 댓글을 기다림 |
| 확인 결과가 통과임 | 이 PR은 사용자가 보기에 반영 가능함 | 사용자 테스트 안내 댓글 이후 연결 Issue에 `@agent test-pass` 댓글 작성 | Issue를 완료 상태로 이동 |
| 확인 결과가 실패임 | 이 PR은 보완이 필요함 | 사용자 테스트 안내 댓글 이후 연결 Issue에 `@agent test-fail <사유>` 댓글 작성 | Issue를 변경 요청 상태로 이동 |

에이전트는 PR을 만들 수 있지만 merge하지 않습니다. merge 여부는 사람이 PR을 검토한 뒤 결정합니다.
PR이 생성되기 전에 미리 남긴 `@agent test-pass`는 완료 신호로 인정되지 않습니다.

## 필요한 label

workflow를 실행하기 전에 저장소에 반드시 있어야 하는 것은 `agent:queued`입니다.

GitHub에서 `agent:queued` label은 **Issues > Labels > New label**에서 만듭니다. 나머지 `agent:*`, `risk:*`는 권한이 있으면 에이전트가 자동 생성합니다.

| label | 사용자 관점의 의미 |
| --- | --- |
| `agent:queued` | 처리할 이슈로 등록됨 |
| `agent:analyzing` | 에이전트가 이슈를 읽는 중 |
| `agent:needs-info` | 사용자의 방향 결정 또는 추가 정보가 필요함 |
| `agent:fixing` | 에이전트가 파일 변경을 만드는 중 |
| `agent:verifying` | 에이전트가 검증 명령을 실행하는 중 |
| `agent:mr-created` | MR/PR 생성 호출이 완료됨 |
| `agent:needs-user-test` | PR/MR을 사람이 확인하고 결과를 Issue에 남겨야 함 |
| `agent:changes-requested` | 사용자 확인 결과 보완이 필요함 |
| `agent:blocked` | 권한, 설정, 정책 문제로 자동 진행이 막힘 |
| `agent:done` | 사용자가 통과를 확인해 작업이 완료됨 |
| `risk:low` | 작고 국소적인 변경 |
| `risk:medium` | 동작 또는 검증 리스크가 있는 변경 |
| `risk:high` | 운영 민감 영역 또는 승인 필요 영역 |

`agent:mr-created`는 GitLab 흐름과의 호환을 위해 이름을 유지합니다. GitHub에서는 Pull Request가 생성됐다는 뜻입니다.

## PR이 없을 때 확인 순서

PR은 `fix.command`가 성공하고 branch push와 PR 생성 API가 모두 통과해야 만들어집니다. PR이 보이지 않으면 아래 순서로 확인합니다.

| 확인할 곳 | 무엇을 보면 되는가 | 다음 행동 |
| --- | --- | --- |
| Issue label/comment | 추가 정보 요청 상태인지 확인 | 질문이 있으면 Issue에 `@agent A`처럼 답변 |
| Actions run log | 테스트 실패, 권한 오류, push 오류가 있는지 확인 | 오류 메시지에 맞게 설정 또는 코드를 수정 |
| Repository Actions 설정 | PR 생성 권한이 켜져 있는지 확인 | Workflow permissions를 read/write와 PR 생성 허용으로 변경 |
| Issue comment의 에이전트 중단 메시지 | 자동 진행이 막힌 원인을 확인 | 원인을 해결한 뒤 Issue에 `@agent proceed` 작성 |
| 기존 agent branch | 이전 실패에서 남은 `agent/...` branch가 있는지 확인 | 보통 삭제하지 않아도 됩니다. 에이전트가 재시도 때 자신의 branch를 갱신합니다. |

## PR이 있을 때 확인 순서

PR이 생성되면 먼저 PR 본문을 위에서 아래로 읽습니다.

| 확인할 곳 | 무엇을 보면 되는가 | 판단 기준 |
| --- | --- | --- |
| 작성 주체 표식 | `작성 주체: Project Ops Agent`가 있는지 | 이 본문이 에이전트 보고서인지 구분 |
| 사용자가 먼저 확인할 것 | 재현 조건, 기대 동작, 변경 범위, 검증 결과 | 실제 사용자 테스트의 우선순위 |
| 코드 리뷰 참고 | 우선 볼 파일과 리뷰 관점 | 필요할 때 Files changed로 이동 |
| 검토 요약 | 원인/현상, 변경 요약, 주의 사항 | 요청과 변경 방향이 맞는지 |
| 접이식 상세 | 이슈 분석, 구현 상세, 검증 로그, 결정 로그 | 더 깊은 코드 리뷰나 실패 원인 확인 |

## 테스트용 이슈 예시

모호한 이슈를 만들어 에이전트가 코드 변경 전 사용자 방향 결정을 요청하는지 검증합니다.

GitHub 화면에서 하는 일:

1. 저장소의 **Issues** 탭을 엽니다.
2. **New issue**를 누릅니다.
3. 아래 제목과 본문을 입력합니다.
4. 오른쪽 **Labels**에서 `agent:queued`를 선택합니다.
5. **Create**를 눌러 Issue를 만듭니다.

```markdown
Title: MVP 검증: 로그인 오류

Body:
로그인이 안됩니다
```

이후 workflow를 실행합니다. 에이전트가 분석 댓글과 추가 정보 요청 댓글을 남기면 사용자는 같은 Issue 댓글에 답합니다.

```text
@agent A
```

선택지가 맞지 않으면 사용자가 직접 방향을 남길 수 있습니다.

```text
@agent 방향: 로그인 정책은 바꾸지 말고, 실패 메시지와 테스트만 보강해주세요.
```

PR이 생성되고 이슈가 사용자 테스트 대기 상태(`agent:needs-user-test`)가 되면 PR을 직접 확인하고 테스트합니다. 결과는 연결된 이슈에 남깁니다.

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
