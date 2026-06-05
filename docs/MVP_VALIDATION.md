# MVP 검증

이 문서는 구현이 합의한 MVP 요구사항을 어떻게 만족하는지 정리합니다.

## 요구사항 체크리스트

| 요구사항 | 구현 위치 |
| --- | --- |
| 이슈 플랫폼을 source of truth로 사용 | `GitLabClient`, `GitHubClient`, label/comment/MR/PR 작업 |
| PostgreSQL 없음 | DB package 또는 DB module 없음 |
| 이슈 상태를 label로 관리 | `state.py` |
| 사용자 답변은 이슈 댓글로만 수집 | `clarification.py` |
| 모호한 이슈는 중단 | `IssueAnalyzer`, `PolicyEngine`, `Orchestrator` |
| MR/PR 보고서에 접이식 상세 섹션 사용 | `templates.py` |
| MR/PR 이후 사용자 테스트 게이트 유지 | `agent:needs-user-test`, `@agent test-pass`, `@agent test-fail` |
| 프로젝트별 설정 | `ProjectProfile`, TOML config |
| 외부 수정 도구 경계 | `ExternalFixProvider`, `fix.command` |
| 검증 명령 실행 | `CommandRunner` |
| 자동 merge 없음 | GitLab/GitHub client에 merge method 없음 |
| 사용자-facing 출력 한국어 | `templates.py`, `docs/OPERATING_RULES.md` |

## 로컬 검증

WSL에서 실행합니다.

```bash
cd ~/workspace/project-ops-agent
export PYTHONPATH=src
export PYTHONDONTWRITEBYTECODE=1
python3 -m unittest discover -s tests
```

테스트가 검증하는 항목:

- queued → clarification → MR/PR 생성 → 사용자 테스트 → done까지의 in-memory e2e 흐름
- `agent:*` label이 상호 배타적으로 유지되는지
- 모호한 이슈가 `agent:needs-info`로 이동하는지
- 사용자 방향 결정이 이슈 댓글에서 읽히는지
- 답변이 있는 이슈가 MR/PR 생성으로 진행되는지
- MR/PR 생성 후 바로 done이 아니라 `agent:needs-user-test`가 되는지
- `@agent test-pass`, `@agent test-fail` 댓글이 done 또는 changes-requested로 전이되는지
- MR/PR 보고서가 table과 `<details>` 섹션을 사용하는지
- 사용자-facing 보고서 핵심 문구가 한국어인지
- demo `fix.command`가 검증용 산출물을 생성하고 잘못된 입력을 거부하는지
- `agent:blocked` 이후 새 사용자 재개 댓글이 있으면 scan에서 다시 처리되는지
- 에이전트 marker가 있는 과거 댓글이 다음 이슈 분석 입력에서 제외되는지

## 실제 운영 검증

GitLab 또는 GitHub 실제 프로젝트에 연결하기 전에 다음을 확인합니다.

1. `docs/OPERATING_RULES.md`의 label을 생성합니다.
2. 최소 권한 token을 준비합니다.
3. GitLab이면 `GITLAB_TOKEN`, GitHub이면 `GITHUB_TOKEN`을 설정합니다.
4. `agent:queued` label이 붙은 이슈를 하나 생성합니다.
5. `scan`을 실행합니다.
6. 이슈가 `agent:analyzing`을 거쳐 분석 댓글을 받는지 확인합니다.
7. 모호한 이슈가 `agent:needs-info`로 이동하는지 확인합니다.
8. 이슈 댓글에 `@agent A`를 작성합니다.
9. 안전한 `fix.command`를 설정합니다.
10. MR/PR 보고서에 table과 `<details>` 섹션이 있는지 확인합니다.
11. 이슈가 `agent:needs-user-test`로 이동하는지 확인합니다.
12. 실제 테스트 후 이슈 댓글에 `@agent test-pass`를 작성합니다.
13. 이슈가 `agent:done`으로 이동하는지 확인합니다.

## GitHub Actions 실검증 메모

개인 GitHub 저장소에서는 `Project Ops Agent MVP` workflow를 수동 실행합니다.

기본 config는 코드 변경 전 중단되는 안전 모드입니다.

```text
configs/projects/github.sample.project.toml
```

PR 생성까지 검증하려면 demo config를 선택합니다.

```text
configs/projects/github.demo.project.toml
```
