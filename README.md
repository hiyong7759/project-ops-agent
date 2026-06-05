# Project Ops Agent

Project Ops Agent는 GitLab 또는 GitHub 이슈를 단일 source of truth로 사용하는 운영 소스 관리 에이전트 MVP입니다.

이슈는 작업 요청과 사용자 결정을 담고, label은 에이전트 상태를 담으며, MR/PR 본문은 검토자가 빠르게 읽을 수 있는 접이식 보고서가 됩니다. 이 MVP는 별도 DB, Jira, 메신저 답변 수집 없이 이슈 플랫폼 안에서 운영 흐름을 닫는 것을 목표로 합니다.

현재 이 저장소에서는 GitHub Actions로 자기 자신을 검증할 수 있습니다. 다른 프로젝트에서 사용할 때는 이 저장소를 그대로 자기 관리 대상으로 삼는 것이 아니라, 대상 프로젝트에 맞는 project config와 실행 위치를 준비해서 붙입니다.

## 목표

운영 코드 변경에 필요한 사람의 반복 작업을 줄이되, 리뷰어와 사용자가 의사결정 흐름을 놓치지 않게 합니다.

리뷰어는 MR/PR 본문에서 다음을 바로 확인할 수 있어야 합니다.

- 어떤 이슈에서 시작된 작업인지
- 에이전트가 무엇을 분석했는지
- 사용자가 어떤 방향을 선택했는지
- 어떤 파일이 바뀌었는지
- 어떤 검증이 수행됐는지
- 병합 전 사용자 테스트가 남아 있는지

## MVP가 하는 일

- `agent:queued` label이 붙은 이슈를 찾습니다.
- 이슈의 `agent:*` 상태 label을 전이합니다.
- 이슈 본문과 댓글을 분석해 모호한 요구사항을 감지합니다.
- 모호하면 `agent:needs-info`로 멈추고 이슈 댓글에 선택지를 남깁니다.
- 사용자는 이슈 댓글에 `@agent A`, `@agent B`, `@agent C`처럼 답합니다.
- 실행 가능한 이슈는 프로젝트별 `fix.command`를 호출합니다.
- 설정된 검증 명령을 실행합니다.
- MR/PR을 만들고 table + `<details>` 기반 보고서를 작성합니다.
- MR/PR 생성 후 바로 완료하지 않고 `agent:needs-user-test`로 사용자 테스트를 기다립니다.
- 사용자는 이슈 댓글에 `@agent test-pass` 또는 `@agent test-fail <사유>`를 남깁니다.

## MVP가 하지 않는 일

- MR/PR을 자동 merge하지 않습니다.
- 별도 DB에 상태를 저장하지 않습니다.
- 네이버웍스나 메신저 답변을 의사결정으로 받지 않습니다.
- `fix.command`가 없으면 프로젝트별 코드를 임의로 고치지 않습니다.
- PR/MR이 만들어졌다는 사실만으로 사용자 테스트를 통과 처리하지 않습니다.

## 언어 원칙

사용자가 보는 운영 문서는 한국어를 기본으로 합니다.

- 이슈에 남기는 에이전트 댓글은 한국어로 작성합니다.
- MR/PR 보고서 본문은 한국어로 작성합니다.
- 사용자에게 요청하는 답변 형식은 이슈 댓글 기준으로 안내합니다.
- 명령어, label, JSON field, API name처럼 시스템 식별자는 원문을 유지합니다.

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

단일 이슈 처리:

```bash
export GITLAB_TOKEN="..."
python3 -m project_ops_agent.cli process --config configs/projects/sample.project.toml --issue 123
```

## GitHub Actions 검증

이 저장소에는 GitHub Actions workflow가 포함되어 있습니다.

- workflow 이름: `Project Ops Agent MVP`
- 기본 config: `configs/projects/github.sample.project.toml`
- demo fix config: `configs/projects/github.demo.project.toml`

기본 config는 `fix.command = ""`이므로 이슈 탐색, 분석 댓글, label 전이, `agent:needs-info` 루프를 안전하게 검증하는 용도입니다.

PR 생성까지 검증하려면 workflow 수동 실행 시 `config_path` 입력값에 아래 경로를 넣습니다.

```text
configs/projects/github.demo.project.toml
```

자세한 절차는 [docs/GITHUB_ACTIONS.md](docs/GITHUB_ACTIONS.md)를 참고하세요.

## demo fix.command란?

`fix.command`는 에이전트가 실제 코드 수정을 맡기는 외부 명령입니다. 에이전트는 이슈와 분석 결과를 JSON으로 stdin에 전달하고, `fix.command`는 파일을 수정한 뒤 결과 JSON을 stdout으로 반환합니다.

`scripts/demo_fix_command.py`는 실무 버그를 고치는 도구가 아닙니다. GitHub Actions에서 branch push, commit, PR 생성, `agent:needs-user-test` 전이를 검증하기 위해 `.agent-demo/` 아래에 작은 검증용 파일을 만드는 데모 명령입니다.

실제 프로젝트에서는 이 자리에 다음 중 하나를 연결합니다.

- Codex CLI wrapper
- 사내 LLM 기반 수정 도구
- 규칙 기반 patch generator
- 사람이 만든 patch를 적용하는 내부 스크립트

## 다른 프로젝트에 붙이는 방법

1. 대상 프로젝트에 agent 실행 환경을 준비합니다.
2. 이 저장소의 package를 설치하거나 소스 checkout 후 `PYTHONPATH=src`로 실행합니다.
3. 대상 프로젝트용 TOML config를 만듭니다.
4. GitLab 또는 GitHub token을 환경 변수로 제공합니다.
5. 대상 repo에 필요한 `agent:*`, `risk:*` label을 만듭니다.
6. 대상 프로젝트에 맞는 `fix.command`를 설정합니다.
7. runner가 대상 repo를 clone하거나 현재 checkout을 사용할 수 있게 합니다.
8. `scan`을 주기 실행하거나 수동 실행합니다.

GitHub처럼 외부에서 접근 가능한 repo는 GitHub Actions로 쉽게 검증할 수 있습니다. 사내 GitLab은 외부 Actions runner가 접근할 수 없으므로 사내망 안의 GitLab Runner, VPN이 연결된 서버, 또는 self-hosted runner에서 실행해야 합니다.

자세한 적용 절차는 [docs/PROJECT_ONBOARDING.md](docs/PROJECT_ONBOARDING.md)를 참고하세요.

## fix.command 계약

에이전트는 `fix.command`에 JSON을 stdin으로 전달합니다. 명령은 checkout된 프로젝트 workspace 안에서 실행됩니다.

입력 예시:

```json
{
  "issue": {
    "iid": 123,
    "title": "...",
    "description": "...",
    "labels": []
  },
  "analysis": {
    "summary": "...",
    "risk": "low",
    "ambiguity_reasons": []
  },
  "decision": "@agent A",
  "project": {
    "key": "order-api",
    "name": "Order API"
  }
}
```

출력 예시:

```json
{
  "success": true,
  "summary": "널 처리 가드와 회귀 테스트를 추가했습니다.",
  "files_changed": ["src/order/status.ts", "test/order/status.test.ts"],
  "commit_message": "이슈 #123 주문 상태 null 처리 수정\n\nRefs #123"
}
```

`fix.command`가 설정되지 않으면 에이전트는 이슈 분석과 추가 정보 요청까지는 수행하지만, 코드 변경 직전에 중단합니다.

## 사용자 테스트 게이트

MR/PR은 사용자 테스트 자체가 아닙니다. MR/PR은 리뷰와 테스트를 시작하기 위한 산출물입니다.

MR/PR 생성 후 이슈는 다음 상태로 이동합니다.

```text
agent:needs-user-test
```

사용자 또는 승인자는 변경 사항을 테스트한 뒤 연결된 이슈에 댓글을 남깁니다.

```text
@agent test-pass
```

또는:

```text
@agent test-fail 주문 상태 변경 시 여전히 실패합니다
```

통과하면 `agent:done`, 실패하면 `agent:changes-requested`로 이동합니다.
