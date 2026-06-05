# 아키텍처

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

## 런타임 흐름

```text
agent:queued
  -> agent:analyzing
  -> agent:needs-info
  -> @agent 답변 대기
  -> agent:fixing
  -> agent:verifying
  -> agent:needs-user-test
  -> agent:done
```

에이전트는 이슈가 `agent:needs-info` 상태일 때 코드를 수정하지 않습니다.

에이전트는 MR/PR 생성을 사용자 테스트로 간주하지 않습니다. MR/PR 생성은 리뷰와 사용자 테스트를 시작하는 게이트일 뿐입니다. 연결된 이슈에 `@agent test-pass`가 기록될 때까지 이슈는 활성 상태로 남습니다.

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
