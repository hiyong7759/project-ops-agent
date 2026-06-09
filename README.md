# Project Ops Agent

Project Ops Agent는 GitLab 또는 GitHub 이슈를 기준으로 운영 코드 변경을 진행하는 에이전트 MVP입니다.

사용자는 이슈에 요청과 결정을 남깁니다. 에이전트는 이슈를 읽고, 모호하면 질문하고, 수정 branch와 MR/PR을 만들고, 검증 결과를 보고서로 남깁니다. 작업 완료 여부는 PR이 만들어졌다는 사실이 아니라, 사용자가 이슈 댓글에 테스트 결과를 남겼는지로 판단합니다.

## 목표

운영 코드 변경에 필요한 반복 작업을 줄이되, 사용자가 판단해야 할 지점을 흐리지 않는 것입니다.

리뷰어와 사용자는 MR/PR에서 다음을 바로 확인할 수 있어야 합니다.

- 어떤 이슈에서 시작된 작업인지
- 에이전트가 무엇을 이해했고 어디를 모호하다고 봤는지
- 사용자가 어떤 방향을 선택했는지
- 어떤 파일이 바뀌었는지
- 어떤 검증이 통과했는지
- 병합 전 사용자 테스트가 남아 있는지

## 한눈에 보는 흐름

아래 표는 사용자가 실제로 보게 되는 흐름입니다. 괄호 안의 `agent:*` 값은 이슈 label에 기록되는 내부 상태명입니다.

| 단계 | 사용자가 보는 의미 | 사용자가 할 일 | 에이전트가 하는 일 |
| --- | --- | --- | --- |
| 작업 요청 등록 | 이 이슈를 에이전트에게 맡긴다 (`agent:queued`) | 이슈에 요청을 쓰고 처리 label을 붙입니다. | 다음 실행 때 이슈를 읽습니다. |
| 이슈 분석 | 에이전트가 요청을 이해하려고 읽는 중 (`agent:analyzing`) | 기다립니다. | 이슈 본문과 사용자 댓글을 분석합니다. |
| 추가 정보 필요 | 요구사항이 모호하거나 승인 판단이 필요함 (`agent:needs-info`) | 이슈 댓글에 `@agent A` 같은 선택을 남깁니다. | 선택지를 제시하고 코드 변경 전 멈춥니다. |
| 수정 진행 | 선택된 방향으로 코드 변경 중 (`agent:fixing`) | 기다립니다. | `fix.command`를 실행하고 변경 파일을 만듭니다. |
| 검증 진행 | 테스트/검증 명령 실행 중 (`agent:verifying`) | 기다립니다. | 설정된 검증 명령을 실행합니다. |
| PR 생성 | 리뷰와 테스트를 위한 PR이 만들어짐 (`agent:needs-user-test`) | PR을 보고 실제로 확인합니다. | branch를 push하고 MR/PR 보고서를 작성합니다. |
| 사용자 테스트 결과 기록 | PR 확인 결과를 이슈에 남김 | 이슈 댓글에 `@agent test-pass` 또는 `@agent test-fail <사유>`를 남깁니다. | 댓글을 읽고 완료 또는 변경 요청으로 상태를 바꿉니다. |
| 완료 | 사용자가 통과를 확인함 (`agent:done`) | 필요하면 사람이 merge합니다. | 더 이상 자동 진행하지 않습니다. |

중단 상태(`agent:blocked`)는 에이전트가 혼자 해결할 수 없는 설정, 권한, 정책 문제가 있다는 뜻입니다. 운영자가 원인을 해결한 뒤 같은 이슈에 `@agent proceed` 또는 기존 선택지인 `@agent A`를 남기면 다음 실행에서 다시 시도합니다.

## 사용자가 판단하는 것

사용자가 반드시 판단해야 하는 부분은 네 가지입니다.

- 이 이슈를 에이전트에게 맡길지 결정합니다.
- 모호한 요구사항에 대해 A/B/C 같은 방향을 선택합니다.
- PR이 만들어진 뒤 실제 사용자 테스트 또는 검토 결과를 판단합니다.
- 최종 merge 여부를 사람이 결정합니다.

에이전트는 merge하지 않습니다. PR이 만들어져도 자동으로 완료 처리하지 않습니다.

## 자동화되는 것

에이전트가 자동으로 처리하는 부분은 다음입니다.

- 처리 대상 이슈 찾기
- 이슈 상태 label 전이
- 이슈 분석 댓글 작성
- 추가 정보 요청 댓글 작성
- `fix.command` 실행
- 검증 명령 실행
- branch push
- MR/PR 생성
- MR/PR 보고서 작성
- 사용자 테스트 댓글을 읽고 완료/변경 요청 상태로 전이

## 자동화되지 않는 것

다음은 MVP에서 자동화하지 않습니다.

- MR/PR merge
- 별도 DB 저장
- 네이버웍스나 메신저 답변 수집
- `fix.command` 없이 프로젝트 코드를 임의 수정
- PR 생성만 보고 사용자 테스트 통과 처리

## 현재 프로젝트에서 확인할 수 있는 것

이 저장소는 화면 기능이 있는 서비스가 아니라 agent 자체의 MVP입니다. 그래서 사용자가 확인할 수 있는 것은 “화면이 잘 동작하는가”가 아니라 다음입니다.

- 이슈에서 시작한 작업이 PR로 올라왔는가
- PR 본문이 사용자가 검토할 수 있는 보고서 형태인가
- 변경 파일이 이슈 내용과 맞는가
- 로컬/Actions 검증 결과가 보고서에 남아 있는가
- PR 생성 후 이슈가 사용자 테스트 대기 상태가 되는가
- 이슈 댓글의 `@agent test-pass`가 완료 상태로 반영되는가

## 문서 지도

처음에는 README만 읽어도 전체 흐름을 이해할 수 있어야 합니다. 세부 상황에서는 아래 문서를 봅니다.

| 문서 | 언제 보는가 | 답하는 질문 |
| --- | --- | --- |
| `README.md` | 처음 볼 때 | 이 도구가 무엇이고 사용자는 무엇을 해야 하나 |
| `docs/README.md` | 문서 관계가 헷갈릴 때 | 어떤 문서를 어떤 순서로 읽어야 하나 |
| `docs/OPERATING_RULES.md` | 실제 이슈를 운영할 때 | 상태 label은 어떤 의미이고 사용자는 언제 무엇을 답하나 |
| `docs/GITHUB_ACTIONS.md` | 개인 GitHub repo에서 검증할 때 | Actions로 어떻게 돌리고 PR 생성을 어떻게 확인하나 |
| `docs/PROJECT_ONBOARDING.md` | 다른 프로젝트에 붙일 때 | 대상 프로젝트에 무엇을 준비해야 하나 |
| `docs/ARCHITECTURE.md` | 구조를 이해하거나 확장할 때 | 내부 구성 요소와 실행 위치는 어떻게 되나 |
| `docs/MVP_VALIDATION.md` | 구현이 MVP 요구사항을 만족하는지 볼 때 | 테스트와 검증 항목은 무엇인가 |

## 빠른 시작

로컬 테스트:

```bash
cd ~/workspace/project-ops-agent
export PYTHONPATH=src
export PYTHONDONTWRITEBYTECODE=1
python3 -m unittest discover -s tests
```

GitHub에서 이 저장소를 검증하려면 GitHub Actions의 **Project Ops Agent MVP** workflow를 수동 실행합니다.

안전한 첫 검증은 코드 변경 없이 이슈 분석과 질문 흐름만 확인합니다.

```text
configs/projects/github.sample.project.toml
```

PR 생성까지 확인하려면 demo fix config를 사용합니다.

```text
configs/projects/github.demo.project.toml
```

자세한 절차는 [docs/GITHUB_ACTIONS.md](docs/GITHUB_ACTIONS.md)를 참고하세요.

## demo fix.command란?

`fix.command`는 에이전트가 실제 코드 수정을 맡기는 외부 명령입니다. 에이전트는 이슈와 분석 결과를 JSON으로 전달하고, `fix.command`는 파일을 수정한 뒤 결과 JSON을 반환합니다.

`scripts/demo_fix_command.py`는 실무 버그를 고치는 도구가 아닙니다. GitHub Actions에서 branch push, commit, PR 생성, 사용자 테스트 대기 흐름을 검증하기 위해 `.agent-demo/` 아래에 작은 검증용 파일을 만드는 데모 명령입니다.

실제 프로젝트에서는 이 자리에 프로젝트 전용 수정 도구를 연결합니다.

## 다른 프로젝트에 붙이는 방법

다른 프로젝트에 적용할 때는 이 저장소가 아니라 대상 프로젝트의 이슈와 repo를 기준으로 설정합니다.

1. 대상 프로젝트의 이슈 플랫폼을 정합니다.
2. 에이전트가 그 플랫폼에 접근할 수 있는 실행 위치를 준비합니다.
3. 대상 프로젝트용 TOML config를 작성합니다.
4. 필요한 label을 만듭니다.
5. token을 환경 변수로 제공합니다.
6. 대상 프로젝트에 맞는 `fix.command`를 연결합니다.
7. 첫 실행은 모호한 이슈로 질문 흐름을 확인합니다.
8. 이후 PR 생성과 사용자 테스트 대기 흐름을 확인합니다.

GitHub repo는 GitHub Actions로 검증하기 쉽습니다. 사내 GitLab은 사내망 안의 GitLab Runner, VPN 연결 서버, 또는 self-hosted runner에서 실행해야 합니다.

자세한 적용 절차는 [docs/PROJECT_ONBOARDING.md](docs/PROJECT_ONBOARDING.md)를 참고하세요.
