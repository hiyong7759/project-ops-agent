# AGENTS.md

이 저장소는 Project Ops Agent MVP입니다. Codex와 Project Ops Agent 모두 이 파일을 프로젝트 정책의 기준으로 사용합니다.

## Codex 작업 규칙

- 사용자에게 보이는 문서, 이슈 댓글, PR/MR 보고서는 한국어로 작성합니다.
- 사용자의 방향 결정은 반드시 GitHub/GitLab Issue 댓글 기준으로 유지합니다.
- PR/MR 생성 자체를 사용자 테스트 완료로 간주하지 않습니다.
- 자동 merge 기능, 별도 DB, 메신저 답변 수집 기능은 추가하지 않습니다.
- `agent:needs-user-test` 게이트를 유지하고, `@agent test-pass` 또는 `@agent test-fail <사유>`는 Issue 댓글에서만 처리합니다.
- 실제 소스 작성 자동화는 Codex CLI 기준으로 설명하고 구현합니다. OpenAI API key 기반 실행은 제안하지 않습니다.
- 변경 후에는 WSL 환경에서 `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests`를 실행합니다.

## Project Ops Agent 런타임 정책

아래 `[policy]` 블록은 project profile의 기본 policy 위에 병합됩니다.

```toml
[policy]
require_info_when = [
  "requirement_ambiguous",
  "expected_behavior_missing",
  "reproduction_missing",
  "multiple_solution_paths"
]
require_approval_before_fix_when = [
  "db_migration",
  "auth_change",
  "payment_change",
  "production_config_change",
  "destructive_change"
]
forbidden_paths = [
  ".github/workflows/**",
  "infra/**",
  "secrets/**",
  ".agent-demo/**"
]
```
