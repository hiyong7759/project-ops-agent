# 다른 프로젝트에 적용하기

이 저장소는 Project Ops Agent 자체를 GitHub Actions로 검증할 수 있게 구성되어 있습니다. 하지만 실제 목적은 이 에이전트를 다른 운영 프로젝트에 붙여 이슈 기반으로 변경 요청을 처리하는 것입니다.

이 문서는 다른 프로젝트에 Project Ops Agent를 붙일 때 봅니다.

먼저 repository root의 `README.md`에서 전체 흐름을 이해하고, 운영 label과 사용자 댓글 규칙은 `docs/OPERATING_RULES.md`, 내부 구조는 `docs/ARCHITECTURE.md`를 함께 확인합니다.

핵심은 세 가지입니다.

- 대상 프로젝트의 이슈 플랫폼을 source of truth로 정합니다.
- 에이전트가 그 플랫폼과 저장소에 접근할 수 있는 위치에서 실행됩니다.
- 대상 프로젝트에 맞는 `fix.command`를 제공합니다.

지금 이 저장소에서 검증할 때는 에이전트가 자기 자신의 Issue와 PR을 관리합니다. 다른 프로젝트에 적용할 때는 에이전트 코드 자체를 바꾸는 것이 아니라, 대상 프로젝트의 repo, Issue 플랫폼, token, runner, `fix.command`를 새 project profile로 연결합니다.

## 도입 전에 결정할 것

| 결정 항목 | 사용자가 정해야 하는 것 | 자동화되는 것 |
| --- | --- | --- |
| 이슈 플랫폼 | GitLab Issue 또는 GitHub Issue 중 무엇을 source of truth로 쓸지 | 선택한 플랫폼의 Issue와 label을 읽음 |
| 실행 위치 | runner가 대상 repo와 API에 접근할 수 있는 위치 | runner 안에서 scan/process 실행 |
| 수정 방식 | 프로젝트별 `fix.command`를 무엇으로 둘지 | `fix.command` 호출, 결과 수집, commit 생성 |
| 검증 방식 | install/lint/test 명령과 사용자 테스트 기준 | 설정된 검증 명령 실행 |
| 완료 기준 | 사람이 언제 `@agent test-pass`를 남길지 | pass/fail 댓글을 읽고 label 전이 |

이 에이전트는 공통 운영 흐름을 자동화합니다. 프로젝트별 업무 지식과 실제 수정 로직은 `fix.command`와 사용자 판단으로 분리합니다.

## 조직에 안내할 최소 사용법

도입 담당자는 일반 조직원에게 아래 문장만 먼저 안내해도 됩니다.

1. 운영 수정 요청은 대상 프로젝트의 **Issues**에 작성합니다.
2. 에이전트에게 맡길 요청에는 `agent:queued` label을 붙입니다.
3. 에이전트가 질문하면 Issue 댓글에 `@agent A` 또는 `@agent 방향: <내용>`으로 답합니다.
4. PR/MR이 생성되면 본문의 **사용자가 먼저 확인할 것**을 보고 확인합니다.
5. 결과는 Issue 댓글에 `@agent test-pass` 또는 `@agent test-fail <사유>`로 남깁니다.
6. PR/MR merge는 기존 조직 절차대로 사람이 결정합니다.

일반 조직원에게 token, runner, `fix.command`, project profile을 설명할 필요는 없습니다. 이 항목은 운영자와 도입 담당자가 관리합니다.

## 도입 담당자 준비 목록

도입 담당자는 아래만 완료하면 바로 검증을 시작할 수 있습니다.

1. 라벨 준비  
   - 에이전트는 `agent:*`, `risk:*` 라벨을 실행 시 자동으로 생성하도록 설계되었습니다.
   - 수동으로 꼭 필요할 라벨은 `agent:queued` 하나입니다. 운영자 또는 요청자가 준비해 두면 됩니다.
   - 나머지 라벨은 처음 scan에서 권한이 있으면 자동 생성됩니다.

2. 실행 위치(runner) 준비  
   - GitHub 프로젝트: `Actions` 실행이면 GitHub-hosted runner 사용 가능  
   - 사내 GitLab/사내망 repo: 사내 GitLab API와 Git clone이 가능한 곳(예: GitLab Runner, 사내 self-hosted runner, VPN WSL)에서 실행

3. token 준비  
   - GitHub: 기본 `GITHUB_TOKEN` 또는 fine-grained PAT 생성 후 secret 등록  
   - GitLab: project access token 또는 personal access token 발급 (`api`, `read_repository`, `write_repository` 권한)

4. project profile 연결  
   - `configs/projects/*.project.toml` 생성/수정  
   - `[project]`, `[github]/[gitlab]`, `[commands]`, `[fix]`, `[workspace]` 값이 맞는지 점검

5. 정책 파일 연결  
   - `policy_file = "AGENTS.md"`처럼 대상 프로젝트의 루트 정책 파일을 지정

6. `fix.command` 연결  
   - 프로젝트 코드에 맞는 수정기를 `[fix]`의 `command`에 연결
   - 검증 가능한 데모부터 시작하고, 이후 실제 도구로 교체
   - `fix.command`는 issue context JSON 입력/JSON 결과 출력 계약을 지켜야 합니다.

7. 검증 명령 점검  
   - `install`, `lint`, `test`가 runner에서 실제로 실행 가능한지 먼저 확인

8. 최초 동작 확인  
   - 모호한 Issue로 `agent:needs-info`  
   - `@agent A` 또는 `@agent 방향` 반영 후 `agent:needs-user-test` 확인

## 적용 절차

1. 대상 프로젝트를 선택합니다.
2. GitLab 또는 GitHub 중 사용할 이슈 플랫폼을 정합니다.
3. 대상 repo에 `agent:queued` 라벨을 준비합니다. (위치: GitHub `Issues > Labels`, GitLab `Issues > Labels`)
4. project profile TOML을 작성합니다. (`configs/projects/<id>.project.toml`)
5. token을 환경 변수로 제공합니다.  
   - GitHub runner: 기본은 `GITHUB_TOKEN`, PAT 사용 시 workflow에서 `GH_TOKEN`을 `GITHUB_TOKEN`으로 주입  
   - GitLab runner: `GITLAB_TOKEN`
6. 실행 위치(runner)를 정합니다.
7. 안전한 `fix.command`를 연결합니다.
8. `scan`을 수동 또는 주기 실행합니다.
9. 첫 검증은 모호한 이슈로 사용자 방향 결정 대기 상태(`agent:needs-info`)까지 확인합니다.
10. 이후 PR/MR 생성과 사용자 테스트 대기 게이트(`agent:needs-user-test`)를 확인합니다.

## 도입 후 운영 흐름

사용자는 상태 label 이름을 외워서 운영하지 않습니다. 아래 흐름처럼 현재 상황과 필요한 행동을 확인합니다.

| 흐름 | 사용자에게 보이는 의미 | 사용자가 할 일 | 에이전트가 자동 처리하는 일 |
| --- | --- | --- | --- |
| 작업 요청 등록 (`agent:queued`) | 대상 프로젝트의 Issue를 에이전트에게 맡김 | 변경 요청과 기대 결과를 Issue에 작성 | 다음 실행에서 Issue 탐색 |
| 방향 결정 (`agent:needs-info`) | 요구사항이 모호하거나 승인 판단이 필요함 | Issue 댓글에 `@agent A/B/C`, `@agent 방향: <내용>` 또는 승인 댓글 작성 | 질문과 선택지 작성 후 대기 |
| 변경 생성 (`agent:fixing`) | 대상 프로젝트 코드 변경이 만들어지는 중 | 보통 기다림 | project profile의 `fix.command` 실행 |
| 검증 (`agent:verifying`) | 대상 프로젝트의 검증 명령 실행 중 | 보통 기다림 | install/lint/test 명령 실행 |
| PR/MR 확인 (`agent:needs-user-test`) | 리뷰와 사용자 테스트가 필요한 산출물이 생김 | PR/MR의 “사용자가 먼저 확인할 것”, 변경 파일, 검증 로그 확인 | branch push, PR/MR 생성, 보고서 작성 |
| 결과 판단 (`agent:done` 또는 `agent:changes-requested`) | 사용자가 통과 또는 실패를 Issue에 남김 | 사용자 테스트 안내 이후 `@agent test-pass` 또는 `@agent test-fail <사유>` 작성 | label을 완료 또는 변경 요청으로 이동 |

merge는 자동화하지 않습니다. 운영자가 기존 조직 절차에 따라 최종 반영 여부를 결정합니다.

## 실제 개발이 실행되는 위치

Project Ops Agent가 직접 소스 코드를 임의로 작성하는 것이 아니라, runner 안에서 대상 저장소를 준비한 뒤 project profile의 `fix.command`를 실행합니다.

실행 순서는 다음과 같습니다.

1. 에이전트가 Issue와 댓글을 읽고 분석합니다.
2. 모호하거나 승인 판단이 필요하면 `agent:needs-info`로 멈춥니다.
3. 진행 가능하면 `GitRunner`가 workspace를 준비합니다.
4. `workspace.use_current_checkout = true`면 현재 checkout을 그대로 사용하고, 아니면 `workspace.root` 아래로 대상 repo를 clone/fetch합니다.
5. 기본 branch 기준으로 `agent/...` 작업 branch를 만듭니다.
6. `[commands].install`이 있으면 먼저 실행합니다.
7. `[fix].command`를 workspace에서 실행합니다.
8. `fix.command`가 파일을 수정하고 JSON 결과를 stdout으로 반환합니다.
9. 에이전트가 변경 파일을 확인하고 금지 경로 정책을 검사합니다.
10. `[commands].lint`, `[commands].test`를 실행합니다.
11. 변경 사항을 commit하고 branch를 push합니다.
12. MR/PR을 만들고, Issue를 `agent:needs-user-test`로 이동합니다.

`fix.command`는 표준 입력으로 다음 context JSON을 받습니다.

```json
{
  "issue": {
    "iid": 123,
    "title": "로그인 오류",
    "description": "로그인이 안됩니다",
    "labels": ["agent:queued"],
    "web_url": "https://..."
  },
  "analysis": {},
  "decision": "@agent A",
  "comments": ["최근 이슈 댓글 최대 20개"],
  "project": {
    "key": "order-api",
    "name": "Order API"
  }
}
```

`fix.command`는 stdout으로 다음 JSON을 반환해야 합니다.

```json
{
  "success": true,
  "summary": "로그인 실패 메시지와 테스트를 수정했습니다.",
  "files_changed": ["src/login.py", "tests/test_login.py"],
  "commit_message": "이슈 #123 로그인 실패 메시지 개선\n\nRefs #123"
}
```

현재 이 저장소의 demo config는 `scripts/demo_fix_command.py`를 실행합니다. 이 명령은 실제 업무 코드를 고치지 않고 `.agent-demo/` 아래 검증용 파일만 만들어 PR 생성 경로를 확인합니다.

실제 신규 개발까지 하려면 `fix.command`를 프로젝트 전용 수정 도구로 교체해야 합니다. 이 저장소에는 Codex CLI를 호출하는 `scripts/codex_fix_command.py` wrapper가 있으며, GitHub Actions 검증용 profile은 `configs/projects/github.codex.project.toml`입니다.

`scripts/codex_fix_command.py`는 runner의 checkout 디렉터리에서 `codex exec --sandbox workspace-write`를 실행합니다. Codex가 파일을 수정하면 wrapper가 `git status --porcelain`으로 변경 파일을 수집하고, Project Ops Agent가 이후 commit/push/PR 생성을 맡습니다.

사내 GitLab Runner에서 같은 방식을 쓰려면 runner에 다음이 준비되어야 합니다.

- Python 3.12 이상
- Git
- 대상 GitLab repo clone/push 권한
- GitLab API token
- Codex CLI 또는 사내 대체 수정 도구
- Codex CLI 로그인 상태 또는 내부 수정 도구 인증 정보
- 대상 프로젝트의 install/lint/test 실행 환경

## GitHub 프로젝트

GitHub 저장소는 보통 GitHub-hosted Actions runner에서 접근 가능합니다.

대상 프로젝트 repo에 workflow를 추가하거나, 내부 운영 repo에서 대상 repo를 checkout하도록 구성할 수 있습니다.

필요한 권한:

```yaml
permissions:
  contents: write
  issues: write
  pull-requests: write
```

token은 기본 `GITHUB_TOKEN`으로 시작할 수 있습니다. cross-repository 작업이나 조직 정책이 까다로운 경우 fine-grained personal access token을 사용합니다.

GitHub Actions에서 PR 생성까지 맡기려면 repository 설정도 필요합니다. **Settings > Actions > General > Workflow permissions**에서 **Read and write permissions**와 **Allow GitHub Actions to create and approve pull requests**를 켭니다.

## 사내 GitLab 프로젝트

사내 GitLab은 외부에서 접근할 수 없는 경우가 많으므로 runner 위치가 중요합니다.

가능한 실행 위치:

- 사내 GitLab Runner
- VPN 연결된 내부 서버
- VPN 연결된 개발자 WSL/로컬 머신
- 사내망에 둔 GitHub self-hosted runner

외부 GitHub-hosted runner는 사내망 GitLab API나 clone URL에 접근할 수 없으므로 기본적으로 사용할 수 없습니다.

## project profile 작성

GitLab 예시:

```toml
[project]
key = "order-api"
name = "Order API"
platform = "gitlab"
policy_file = "AGENTS.md"

[gitlab]
url = "https://gitlab.company.local"
project_id = "123"
default_branch = "main"
repo_http_url = "https://gitlab.company.local/group/order-api.git"

[agent]
branch_prefix = "agent"
can_push_branch = true
can_create_mr = true
can_merge = false

[commands]
install = "npm ci"
lint = "npm run lint"
test = "npm test"

[fix]
command = "codex-fix-issue"
timeout_seconds = 1800

[workspace]
root = "workspaces"
```

GitHub 예시:

```toml
[project]
key = "project-ops-agent"
name = "Project Ops Agent"
platform = "github"
policy_file = "AGENTS.md"

[github]
owner = "hiyong7759"
repo = "project-ops-agent"
default_branch = "main"
repo_http_url = "https://github.com/hiyong7759/project-ops-agent.git"
api_url = "https://api.github.com"

[workspace]
use_current_checkout = true
```

`project` 섹션의 `policy_file`은 Markdown/TOML/JSON 형식의 정책 파일을 가리킵니다.  
예시의 경우 저장소 루트 `AGENTS.md`의 `[policy]` 블록이 기본 policy 위에 병합됩니다.

## fix.command 선택

`fix.command`는 실제 프로젝트별 수정 책임을 갖는 외부 명령입니다.

에이전트가 담당하는 일:

- 이슈 분석
- 정책 게이트
- label 전이
- workspace 준비
- 검증 명령 실행
- commit과 push
- MR/PR 생성
- 보고서 작성

`fix.command`가 담당하는 일:

- 프로젝트 코드를 실제로 수정
- 필요한 테스트 파일 추가
- 변경 요약과 commit message 반환

처음에는 demo `fix.command`로 PR 생성 경로만 검증하고, 그 다음 `scripts/codex_fix_command.py`로 실제 수정 흐름을 검증합니다. 실제 운영에 들어갈 때는 프로젝트 전용 Codex prompt, 사내 LLM 도구, 또는 규칙 기반 수정기로 교체할 수 있습니다.

## 한국어 운영 원칙

대상 프로젝트에서도 사용자-facing 산출물은 한국어로 유지합니다.

- 이슈 제목과 본문은 가능하면 한국어로 작성합니다.
- 에이전트 댓글은 한국어로 작성됩니다.
- MR/PR 보고서는 한국어로 작성됩니다.
- 사용자는 이슈 댓글로만 방향을 결정합니다.
- `@agent A`, `@agent test-pass` 같은 명령 token은 원문을 유지합니다.
- 에이전트가 제시한 선택지가 맞지 않으면 `@agent 방향: <내용>`으로 직접 방향을 남깁니다.
- 에이전트 산출물에는 `작성 주체: Project Ops Agent` 표식을 남겨 계정명 혼동을 줄입니다.

## 첫 검증용 이슈

모호한 이슈로 시작하면 안전하게 clarification 루프를 검증할 수 있습니다.

GitHub 또는 GitLab에서 대상 프로젝트의 **Issues** 화면을 열고 새 Issue를 만듭니다. 제목과 본문을 아래처럼 입력한 뒤 `agent:queued` label을 붙입니다.

```markdown
Title: 로그인 오류

Body:
로그인이 안됩니다
```

예상 결과:

- 에이전트가 분석 댓글을 남깁니다.
- 이슈가 사용자 방향 결정 대기 상태(`agent:needs-info`)로 이동합니다.
- 에이전트가 `@agent A` 답변 형식을 안내합니다.

그 다음 사용자가 이슈 댓글에 답합니다.

```text
@agent A
```

또는 선택지 밖의 방향을 직접 적습니다.

```text
@agent 방향: 로그인 정책은 바꾸지 말고, 실패 메시지와 재현 테스트만 보강해주세요.
```

`fix.command`가 설정되어 있으면 다음 run에서 branch와 MR/PR 생성으로 진행합니다.
