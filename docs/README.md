# 문서 안내

이 폴더의 문서는 README를 보완하는 참조 문서입니다. 처음 읽을 때는 repository root의 `README.md`를 먼저 보고, 필요한 상황에 따라 아래 문서를 선택합니다.

## 읽는 순서

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
| `README.md` | 모든 사용자 | 처음 | 이 에이전트가 무엇을 하고, 사용자는 무엇을 해야 하나 |
| `docs/OPERATING_RULES.md` | 운영자, 리뷰어, 개발자 | Issue/PR 상태를 해석할 때 | label과 댓글 규칙은 무엇인가 |
| `docs/PROJECT_ONBOARDING.md` | 도입 담당자 | 다른 프로젝트에 붙일 때 | 대상 프로젝트에 무엇을 준비해야 하나 |
| `docs/GITHUB_ACTIONS.md` | 개인 검증 사용자 | GitHub Actions로 실검증할 때 | workflow를 어떻게 실행하고 무엇을 확인하나 |
| `docs/ARCHITECTURE.md` | 개발자 | 구조를 바꾸거나 확장할 때 | 컴포넌트가 어떻게 나뉘고 어디에서 실행되나 |
| `docs/MVP_VALIDATION.md` | 개발자, 검증자 | 요구사항 충족 여부를 볼 때 | 현재 테스트가 무엇을 보장하나 |

## 사용자와 에이전트의 경계

| 단계 | 사용자 책임 | 에이전트 책임 |
| --- | --- | --- |
| 작업 요청 | Issue 작성, `agent:queued` label 부여 | queued Issue 탐색 |
| 요구사항 판단 | 모호한 부분에 대해 `@agent A/B/C` 답변 | 분석 댓글과 선택지 작성 |
| 코드 수정 | 필요 시 정책 방향 결정 | `fix.command` 실행 |
| 검증 | PR/MR 확인, 실제 사용자 테스트 | 검증 명령 실행, 보고서 작성 |
| 완료 판단 | `@agent test-pass` 또는 `@agent test-fail` 댓글 작성 | label을 `agent:done` 또는 `agent:changes-requested`로 전이 |
| 병합 | 조직 절차에 따라 merge 판단 | 자동 merge하지 않음 |

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
