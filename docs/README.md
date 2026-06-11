# 문서 안내

이 폴더의 문서는 README를 보완하는 참조 문서입니다. 처음 읽을 때는 repository root의 `README.md`를 먼저 보고, 필요한 상황에 따라 아래 문서를 선택합니다.

문서의 기준은 사용자 관점입니다. `agent:queued` 같은 label은 내부 상태를 확인하기 위한 보조 표기이고, 항상 “무슨 상황인지”, “사용자가 무엇을 판단해야 하는지”, “에이전트가 무엇을 자동으로 하는지”와 함께 읽어야 합니다.

## 읽는 순서

### 조직원이 처음 사용할 때

1. `README.md`의 `처음 사용하는 조직원은 여기부터`
2. `README.md`의 `Issue 작성 예시`
3. `docs/OPERATING_RULES.md`의 `상태 읽는 법`

일반 사용자는 처음부터 `docs/ARCHITECTURE.md`나 `docs/MVP_VALIDATION.md`를 읽지 않아도 됩니다.

### 첫 10분 실행 순서

1. `README.md`에서 이슈를 하나 작성하고 `agent:queued`를 붙인다.
2. `docs/GITHUB_ACTIONS.md` 기준으로 Workflow를 수동 실행한다.
3. 분석 댓글이 오면 필요 답변을 남기고 재실행한다.
4. PR이 생성되면 PR 본문을 보고 승인/반려 사유를 이슈 댓글에 남긴다.
5. `agent:needs-user-test`에서 `@agent test-pass` 또는 `@agent test-fail`로 마무리한다.

처음 확인이 실패했을 때는 `README.md`의 `지금 바로 확인할 점검표 (PR 안 올라올 때)`부터 먼저 봅니다.

### 처음 이해할 때

1. `README.md`
2. `docs/OPERATING_RULES.md`
3. `docs/ARCHITECTURE.md`

### 개인 GitHub 저장소에서 검증할 때

1. `README.md`
2. `docs/GITHUB_ACTIONS.md`
3. `docs/MVP_VALIDATION.md`

### 다른 프로젝트에 붙일 때

1. `README.md`
2. `docs/PROJECT_ONBOARDING.md`
3. `docs/OPERATING_RULES.md`
4. 대상 플랫폼별 실행 문서

### 구현을 수정하거나 테스트를 추가할 때

1. `docs/ARCHITECTURE.md`
2. `docs/MVP_VALIDATION.md`
3. 관련 테스트 파일

## 문서별 역할

| 문서 | 주 독자 | 읽는 시점 | 핵심 질문 |
| --- | --- | --- | --- |
| `README.md` | 모든 조직원 | 처음 | Issue를 어떻게 만들고 어떤 댓글을 남기나 |
| `docs/OPERATING_RULES.md` | 사용자, 운영자, 리뷰어 | Issue/PR 상태를 해석할 때 | label과 댓글 규칙은 무엇인가 |
| `docs/PROJECT_ONBOARDING.md` | 도입 담당자, 운영자 | 다른 프로젝트에 붙일 때 | 대상 프로젝트에 무엇을 준비해야 하나 |
| `docs/GITHUB_ACTIONS.md` | 검증 담당자 | GitHub Actions로 실검증할 때 | workflow를 어떻게 실행하고 무엇을 확인하나 |
| `docs/ARCHITECTURE.md` | 개발자 | 구조를 바꾸거나 확장할 때 | 컴포넌트가 어떻게 나뉘고 어디에서 실행되나 |
| `docs/MVP_VALIDATION.md` | 개발자, 검증자 | 요구사항 충족 여부를 볼 때 | 현재 테스트가 무엇을 보장하나 |

## 역할별로 보면

| 역할 | 먼저 볼 문서 | 그 사람이 하는 일 |
| --- | --- | --- |
| 요청자 | `README.md` | Issue 작성, `agent:queued` label 요청 또는 부여, 에이전트 질문에 답변 |
| 검토자 | `README.md`, `docs/OPERATING_RULES.md` | PR/MR 보고서와 변경 파일 확인, 사용자 테스트 결과 기록 |
| 운영자 | `docs/OPERATING_RULES.md`, `docs/GITHUB_ACTIONS.md` | label, token, runner, workflow 실행 상태 관리 |
| 도입 담당자 | `docs/PROJECT_ONBOARDING.md` | 대상 프로젝트 설정, `fix.command`, 실행 위치 결정 |
| 개발자 | `docs/ARCHITECTURE.md`, `docs/MVP_VALIDATION.md` | 코드 구조 이해, 테스트 추가, 기능 확장 |

## 사용자와 에이전트의 경계

아래 표에서 괄호 안의 label은 GitHub/GitLab Issue에서 상태를 확인할 때 쓰는 이름입니다. 사용자는 label 이름을 외우기보다 현재 단계의 의미와 본인이 해야 할 일을 확인하면 됩니다.

| 흐름 | 사용자에게 보이는 의미 | 사용자가 할 일 | 자동화되는 일 |
| --- | --- | --- | --- |
| 작업 맡김 (`agent:queued`) | 이 Issue를 에이전트 처리 대상으로 올림 | Issue를 작성하고 처리 label을 붙임 | 에이전트가 다음 실행에서 Issue를 찾음 |
| 방향 판단 대기 (`agent:needs-info`) | 요구사항이 모호해서 코드 변경 전 멈춤 | Issue 댓글에 `@agent A/B/C`, `@agent 방향: <내용>` 또는 승인 댓글 작성 | 에이전트가 분석과 선택지를 댓글로 남김 |
| 수정과 검증 진행 (`agent:fixing`, `agent:verifying`) | 선택한 방향으로 변경과 테스트가 진행 중 | 보통 기다림 | `fix.command` 실행, 검증 명령 실행, commit 생성 |
| PR/MR 확인 대기 (`agent:needs-user-test`) | PR/MR이 생성됐고 사람이 확인해야 함 | PR/MR의 “사용자가 먼저 확인할 것”, 변경 파일, 검증 결과를 확인 | 보고서 작성, Issue 상태 전이 |
| 결과 기록 (`agent:done`, `agent:changes-requested`) | 사용자 테스트 결과가 Issue에 기록됨 | 사용자 테스트 안내 이후 `@agent test-pass` 또는 `@agent test-fail <사유>` 작성 | 안내 이후 댓글을 읽고 완료 또는 변경 요청으로 상태 변경 |
| 병합 | 조직 절차에 따라 최종 반영 여부 결정 | 사람이 merge 판단 | 에이전트는 자동 merge하지 않음 |

에이전트 댓글이나 PR/MR 보고서에는 `작성 주체: Project Ops Agent` 표식이 들어갑니다. 작성 계정이 사용자와 같아 보여도 이 표식이 있으면 에이전트 산출물로 해석합니다.

## 자동화되는 것과 아닌 것

자동화되는 것:

- Issue 탐색
- 분석 댓글 작성
- 상태 label 전이
- `fix.command` 실행
- 검증 명령 실행
- branch push
- MR/PR 생성
- MR/PR 보고서 작성

자동화되지 않는 것:

- 사용자 방향 결정
- 실제 사용자 테스트
- 최종 merge
- 프로젝트별 수정 로직 자체
- 별도 DB 상태 저장

## 현재 프로젝트에서 확인 가능한 것

이 저장소는 에이전트 MVP 자체를 검증하는 프로젝트입니다. 화면 기능이나 실제 업무 API가 없으므로 사용자가 확인할 수 있는 범위는 다음입니다.

- Issue 상태 label이 의도대로 바뀌는지
- 에이전트 댓글이 한국어로 작성되는지
- PR이 실제로 생성되는지
- PR 본문이 보고서 형태인지
- 테스트 결과가 PR 본문에 기록되는지
- 사용자 테스트 댓글 후 Issue가 `agent:done`으로 이동하는지
