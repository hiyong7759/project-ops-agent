# 아키텍처

이 문서는 Project Ops Agent의 내부 구성과 실행 위치를 이해하거나 확장할 때 봅니다.

운영자가 Issue/label 규칙만 확인하려면 `docs/OPERATING_RULES.md`가 더 적합합니다. 다른 프로젝트에 적용하는 절차는 `docs/PROJECT_ONBOARDING.md`를 참고합니다.

## 목적

Project Ops Agent는 운영 코드 유지보수의 반복 부담을 줄이되, 의사결정을 숨기지 않기 위해 존재합니다.

핵심 산출물은 리뷰어가 보는 MR/PR입니다. 보고서는 기본적으로 짧아야 하고, 필요할 때 `<details>` 섹션을 열어 상세 내용을 볼 수 있어야 합니다.

## Source of Truth

MVP에서는 선택한 이슈 플랫폼이 단일 source of truth입니다. GitLab은 운영 환경의 기본 대상이고, GitHub는 개인 저장소 검증을 지원합니다.

| 관심사 | 플랫폼 객체 |
| --- | --- |
| 작업 요청 | Issue |
| 에이전트 상태 | Issue label |
| 사용자 결정 | Issue comment |
| 에이전트 분석 로그 | Issue comment |
| 코드 리뷰 | Merge Request 또는 Pull Request |
| 리뷰어 보고서 | MR/PR description |
| 코드 변경 이력 | Commit message |

에이전트가 남긴 Issue 댓글에는 숨은 marker와 보이는 작성 주체 표식이 함께 들어갑니다. 숨은 marker는 파서가 에이전트 안내문 안의 예시 명령을 사용자 답변으로 오인하지 않게 하고, 보이는 표식은 작성 계정이 사용자 계정처럼 보일 때도 운영자가 에이전트 산출물을 구분하게 합니다.

## 구성 요소

```text
Issue Platform
  -> GitLabClient 또는 GitHubClient
  -> Orchestrator
  -> IssueAnalyzer
  -> PolicyEngine
  -> ClarificationGate
  -> Workspace GitRunner
  -> ExternalFixProvider
  -> CommandRunner
  -> MRReportBuilder
  -> MR 또는 PR
```

| 구성 요소 | 책임 |
| --- | --- |
| GitLabClient/GitHubClient | Issue, comment, label, MR/PR API 호출 |
| Orchestrator | 전체 상태 전이와 작업 순서 제어 |
| IssueAnalyzer | Issue 본문과 사용자 댓글 분석 |
| PolicyEngine | 위험도와 중단 조건 판단 |
| ClarificationGate | 사용자 답변 댓글 감지 |
| GitRunner | checkout, branch, commit, push |
| ExternalFixProvider | `fix.command` 호출 |
| CommandRunner | install/lint/test 같은 검증 명령 실행 |
| MRReportBuilder | 리뷰어용 MR/PR 보고서 생성 |

## 런타임 흐름

| 사용자-visible 흐름 | 내부 상태 label | 내부 처리 |
| --- | --- | --- |
| 처리할 Issue가 등록됨 | `agent:queued` | Orchestrator가 scan 대상 Issue로 선택 |
| 에이전트가 요청을 읽음 | `agent:analyzing` | IssueAnalyzer와 PolicyEngine 실행 |
| 사용자 방향 결정이 필요함 | `agent:needs-info` | ClarificationGate가 새 사용자 댓글을 기다림 |
| 선택된 방향으로 수정함 | `agent:fixing` | ExternalFixProvider가 project profile의 `fix.command` 실행 |
| 검증 명령을 실행함 | `agent:verifying` | CommandRunner가 install/lint/test를 실행 |
| PR/MR이 만들어지고 사람 확인을 기다림 | `agent:needs-user-test` | MRReportBuilder가 보고서를 만들고 플랫폼 client가 PR/MR 생성 |
| 사용자가 통과를 확인함 | `agent:done` | 이후 자동 진행 없음 |

에이전트는 이슈가 `agent:needs-info` 상태일 때 코드를 수정하지 않습니다.

에이전트는 MR/PR 생성을 사용자 테스트로 간주하지 않습니다. MR/PR 생성은 리뷰와 사용자 테스트를 시작하는 게이트일 뿐입니다. 연결된 이슈에 사용자 테스트 안내 댓글이 남은 뒤 `@agent test-pass`가 기록될 때까지 이슈는 활성 상태로 남습니다.

## 실행 위치

에이전트는 이슈 플랫폼에 접근할 수 있는 위치에서 실행되어야 합니다.

GitHub 저장소는 인터넷에서 접근 가능하므로 GitHub-hosted Actions runner에서 바로 검증할 수 있습니다.

사내 GitLab은 외부에서 접근할 수 없는 경우가 많습니다. 이때는 에이전트를 사내망 안에서 실행합니다.

- 사내 GitLab Runner
- VPN이 연결된 내부 서버
- VPN이 연결된 개발자 WSL/로컬 머신
- 사내망에 배치한 GitHub self-hosted runner

중요한 점은 외부 서비스가 사내 GitLab로 inbound 접속하는 구조가 아니라는 점입니다. 사내망 안의 runner가 GitLab API와 repo에 접근하고, 필요한 경우 승인된 외부 API나 내부 LLM 도구로 outbound 호출을 수행합니다.

코드나 이슈 내용을 외부 모델로 보낼 수 없는 회사라면 `fix.command`를 내부 도구, 로컬 모델, 또는 승인된 엔터프라이즈 경로로 연결해야 합니다.

## DB를 두지 않는 이유

MVP는 GitLab/GitHub label과 comment를 지속 상태로 사용합니다.

이 방식은 운영을 단순하게 유지합니다.

- 상태 동기화 문제가 없습니다.
- 별도 감사 DB가 필요 없습니다.
- 메신저 답변을 이슈 답변으로 매핑하지 않아도 됩니다.
- 모든 결정이 이슈와 MR/PR 옆에 남습니다.

나중에 dashboard, metrics, multi-project scheduling이 필요하면 DB를 추가할 수 있습니다. 첫 운영 루프에는 필요하지 않습니다.

## 수정 실행 경계

에이전트는 프로젝트별 소스 수정을 하드코딩하지 않습니다.

대신 project profile에 `fix.command`를 설정할 수 있습니다. 이 명령은 표준화된 JSON context를 입력으로 받고, checkout된 workspace 안에서 파일을 수정합니다.

각 프로젝트는 자신에게 맞는 수정 방식을 선택할 수 있습니다.

- Codex CLI wrapper
- 사내 LLM 도구
- 규칙 기반 수정 스크립트
- 사람이 만든 patch 적용기

Orchestrator는 여전히 label 전이, 정책 게이트, 검증 명령, commit, push, MR/PR 보고서를 통제합니다.
