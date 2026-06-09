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

## 적용 절차

1. 대상 프로젝트를 선택합니다.
2. GitLab 또는 GitHub 중 사용할 이슈 플랫폼을 정합니다.
3. 대상 repo에 `agent:*`, `risk:*` label을 생성합니다.
4. project profile TOML을 작성합니다.
5. token을 환경 변수로 제공합니다.
6. 실행 위치를 정합니다.
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

[github]
owner = "hiyong7759"
repo = "project-ops-agent"
default_branch = "main"
repo_http_url = "https://github.com/hiyong7759/project-ops-agent.git"
api_url = "https://api.github.com"

[workspace]
use_current_checkout = true
```

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

처음에는 demo `fix.command`로 PR 생성 경로만 검증하고, 실제 운영에 들어갈 때 프로젝트 전용 명령으로 교체하는 방식이 안전합니다.

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
