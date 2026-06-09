# Project Ops Agent

Project Ops Agent는 GitLab 또는 GitHub Issue를 단일 source of truth로 사용하는 운영 소스 관리 에이전트 MVP입니다.

Issue는 작업 요청과 사용자 결정을 담고, label은 에이전트 상태를 담으며, MR/PR 본문은 검토자가 읽는 접이식 보고서가 됩니다. 별도 DB, Jira, 메신저 답변 수집 없이 이슈 플랫폼 안에서 운영 흐름을 닫는 것이 목표입니다.

## 목표

운영 코드 변경에 필요한 반복 작업을 줄이되, 리뷰어와 사용자가 의사결정 흐름을 놓치지 않게 합니다.

리뷰어는 MR/PR 본문에서 다음을 바로 확인할 수 있어야 합니다.

- 어떤 Issue에서 시작된 작업인지
- 에이전트가 무엇을 분석했는지
- 사용자가 어떤 방향을 선택했는지
- 어떤 파일이 바뀌었는지
- 어떤 검증이 수행됐는지
- 병합 전 사용자 테스트가 남아 있는지

## 한 줄 흐름

```text
Issue 생성
  -> agent:queued
  -> 에이전트 분석
  -> 필요하면 사용자 방향 결정
  -> fix.command 실행
  -> 검증
  -> MR/PR 생성
  -> 사용자 테스트 대기
  -> @agent test-pass 또는 @agent test-fail
```

## 역할 구분

| 주체 | 하는 일 | 하지 않는 일 |
| --- | --- | --- |
| 사용자 | Issue 작성, 방향 선택, PR/MR 확인, 사용자 테스트 결과 댓글 작성 | 메신저로 결정을 대신 전달하지 않음 |
| 에이전트 | Issue 분석, label 전이, `fix.command` 실행, 검증, branch push, MR/PR 보고서 생성 | 자동 merge하지 않음, 사용자 테스트를 대신 판단하지 않음 |
| `fix.command` | 프로젝트별 실제 파일 수정 | Issue 상태 관리나 PR 생성은 하지 않음 |
| runner | 에이전트를 실행하고 GitLab/GitHub와 repo에 접근 | source of truth를 따로 저장하지 않음 |

## 사용자가 판단하는 것

사용자가 반드시 판단해야 하는 지점은 세 가지입니다.

1. 요구사항이 모호할 때 방향 선택

```text
@agent A
@agent B
@agent C
```

2. PR/MR 생성 후 실제 확인 결과

```text
@agent test-pass
@agent test-fail <사유>
```

3. 최종 merge 여부

에이전트는 MR/PR을 만들 수 있지만 merge하지 않습니다. merge는 사람 또는 기존 조직 절차가 결정합니다.

## 자동화되는 것

- `agent:queued` Issue 탐색
- Issue 본문과 댓글 분석
- 모호한 요구사항 감지
- `agent:*`, `risk:*` label 전이
- 사용자 답변 댓글 감지
- `fix.command` 실행
- 설치/테스트/검증 명령 실행
- commit과 branch push
- MR/PR 생성
- MR/PR 보고서 작성
- 사용자 테스트 결과 댓글 감지

## 자동화하지 않는 것

- 자동 merge
- 별도 DB 상태 저장
- 메신저 답변 수집
- `fix.command` 없는 임의 코드 수정
- PR/MR 생성만으로 사용자 테스트 통과 처리

## 전체 워크플로우

| 단계 | 사용자 | 에이전트 | 산출물/상태 |
| --- | --- | --- | --- |
| 1. 요청 | Issue를 작성하고 `agent:queued` label을 붙임 | queued Issue를 찾음 | `agent:queued` |
| 2. 분석 | 기다림 | Issue와 사용자 댓글을 분석 | 분석 댓글, `risk:*` |
| 3. 방향 결정 | 필요한 경우 `@agent A/B/C` 댓글 작성 | 모호하면 멈춤 | `agent:needs-info` |
| 4. 수정 | 기다림 | `fix.command` 실행, 파일 변경 | agent branch |
| 5. 검증 | 기다림 | 테스트/검증 명령 실행 | 검증 로그 |
| 6. 리뷰 | PR/MR을 확인 | 보고서 포함 PR/MR 생성 | `agent:needs-user-test` |
| 7. 사용자 테스트 | 직접 확인 후 `@agent test-pass/fail` 작성 | 결과 댓글 감지 | `agent:done` 또는 `agent:changes-requested` |

현재 이 저장소에는 화면 기능이 없으므로 사용자 테스트는 “Issue에 대응하는 PR이 생성됐는지, PR 본문과 변경 파일이 검토 가능한지, 검증 결과가 기록됐는지”를 확인하는 것으로 충분합니다.

## 문서 지도

처음 읽을 때는 이 README만 보면 됩니다. 더 깊게 확인할 때 아래 문서를 봅니다.

| 문서 | 언제 보는가 | 답하는 질문 |
| --- | --- | --- |
| [docs/README.md](docs/README.md) | 문서 전체 구조를 알고 싶을 때 | 어떤 문서를 어떤 순서로 읽어야 하나 |
| [docs/OPERATING_RULES.md](docs/OPERATING_RULES.md) | 운영 규칙을 확인할 때 | label, 사용자 댓글, 테스트 게이트 규칙은 무엇인가 |
| [docs/PROJECT_ONBOARDING.md](docs/PROJECT_ONBOARDING.md) | 다른 프로젝트에 붙일 때 | 새 프로젝트에서 무엇을 준비해야 하나 |
| [docs/GITHUB_ACTIONS.md](docs/GITHUB_ACTIONS.md) | 개인 GitHub repo에서 검증할 때 | Actions로 어떻게 돌리고 무엇을 확인하나 |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 내부 구조를 이해할 때 | 컴포넌트와 실행 위치는 어떻게 나뉘나 |
| [docs/MVP_VALIDATION.md](docs/MVP_VALIDATION.md) | MVP 요구사항을 검증할 때 | 현재 테스트가 무엇을 보장하나 |

## 빠른 시작

로컬 테스트:

```bash
cd ~/workspace/project-ops-agent
export PYTHONPATH=src
export PYTHONDONTWRITEBYTECODE=1
python3 -m unittest discover -s tests
```

GitLab 대상 실행:

```bash
export GITLAB_TOKEN="..."
python3 -m project_ops_agent.cli scan --config configs/projects/sample.project.toml
```

GitHub 대상 실행:

```bash
export GITHUB_TOKEN="..."
python3 -m project_ops_agent.cli scan --config configs/projects/github.sample.project.toml
```

단일 Issue 처리:

```bash
export GITLAB_TOKEN="..."
python3 -m project_ops_agent.cli process --config configs/projects/sample.project.toml --issue 123
```

## GitHub Actions 검증

이 저장소에는 자기 자신을 검증하기 위한 GitHub Actions workflow가 포함되어 있습니다.

- workflow 이름: `Project Ops Agent MVP`
- 안전한 기본 config: `configs/projects/github.sample.project.toml`
- PR 생성 검증 config: `configs/projects/github.demo.project.toml`

기본 config는 `fix.command = ""`이므로 Issue 탐색, 분석 댓글, label 전이, `agent:needs-info` 루프를 안전하게 검증합니다.

PR 생성까지 검증하려면 workflow 수동 실행 시 `config_path`에 아래 값을 넣습니다.

```text
configs/projects/github.demo.project.toml
```

자세한 절차는 [docs/GITHUB_ACTIONS.md](docs/GITHUB_ACTIONS.md)를 참고하세요.

## fix.command란?

`fix.command`는 에이전트가 실제 코드 수정을 맡기는 외부 명령입니다. 에이전트는 Issue와 분석 결과를 JSON으로 stdin에 전달하고, `fix.command`는 파일을 수정한 뒤 결과 JSON을 stdout으로 반환합니다.

`scripts/demo_fix_command.py`는 실무 버그를 고치는 도구가 아닙니다. GitHub Actions에서 branch push, commit, PR 생성, `agent:needs-user-test` 전이를 검증하기 위해 `.agent-demo/` 아래에 작은 검증용 파일을 만드는 데모 명령입니다.

실제 프로젝트에서는 이 자리에 다음 중 하나를 연결합니다.

- Codex CLI wrapper
- 사내 LLM 기반 수정 도구
- 규칙 기반 patch generator
- 사람이 만든 patch를 적용하는 내부 스크립트

## 다른 프로젝트에 붙이는 방법

1. 대상 프로젝트의 이슈 플랫폼을 정합니다.
2. 에이전트가 그 플랫폼과 repo에 접근할 수 있는 실행 위치를 정합니다.
3. 대상 프로젝트용 TOML config를 만듭니다.
4. 필요한 token과 label을 준비합니다.
5. 프로젝트 전용 `fix.command`를 연결합니다.
6. `scan`을 수동 또는 주기 실행합니다.
7. 처음에는 모호한 Issue로 `agent:needs-info`까지 검증합니다.
8. 이후 PR/MR 생성과 `agent:needs-user-test` 게이트를 확인합니다.

GitHub처럼 외부에서 접근 가능한 repo는 GitHub Actions로 검증할 수 있습니다. 사내 GitLab은 사내망 안의 GitLab Runner, VPN이 연결된 서버, 또는 self-hosted runner에서 실행해야 합니다.

자세한 적용 절차는 [docs/PROJECT_ONBOARDING.md](docs/PROJECT_ONBOARDING.md)를 참고하세요.

## 언어 원칙

사용자가 보는 운영 문서는 한국어를 기본으로 합니다.

- Issue에 남기는 에이전트 댓글은 한국어로 작성합니다.
- MR/PR 보고서 본문은 한국어로 작성합니다.
- 사용자에게 요청하는 답변 형식은 Issue 댓글 기준으로 안내합니다.
- 명령어, label, JSON field, API name처럼 시스템 식별자는 원문을 유지합니다.
