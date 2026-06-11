# Project Ops Agent

Project Ops Agent는 GitLab 또는 GitHub 이슈를 기준으로 운영 코드 변경을 진행하는 에이전트 MVP입니다.

사용자는 이슈에 요청과 결정을 남깁니다. 에이전트는 이슈를 읽고, 모호하면 질문하고, 수정 branch와 MR/PR을 만들고, 검증 결과를 보고서로 남깁니다. 작업 완료 여부는 PR이 만들어졌다는 사실이 아니라, PR 생성 후 사용자가 이슈 댓글에 테스트 결과를 남겼는지로 판단합니다.

## 목표

운영 코드 변경에 필요한 반복 작업을 줄이되, 사용자가 판단해야 할 지점을 흐리지 않는 것입니다.

리뷰어와 사용자는 MR/PR에서 다음을 바로 확인할 수 있어야 합니다.

- 어떤 이슈에서 시작된 작업인지
- 에이전트가 무엇을 이해했고 어디를 모호하다고 봤는지
- 사용자가 어떤 방향을 선택했는지
- 어떤 파일이 바뀌었는지
- 어떤 검증이 통과했는지
- 병합 전 사용자 테스트가 남아 있는지

## 기본 용어

- Issue: GitHub/GitLab의 **Issues** 화면에 만드는 작업 요청 글입니다. 버그, 운영 수정 요청, 확인할 일을 한 건씩 적습니다.
- Label: Issue에 붙이는 꼬리표입니다. 에이전트는 `agent:queued` 같은 label을 보고 어떤 Issue를 처리할지, 현재 어디까지 진행됐는지 판단합니다.
- `agent:queued`: “이 Issue를 에이전트가 처리해도 된다”는 시작 label입니다.

## 처음 사용하는 조직원은 여기부터

일반 사용자가 처음 한 건을 맡길 때 필요한 일은 많지 않습니다.

1. GitHub 또는 GitLab에서 대상 프로젝트의 **Issues** 화면을 엽니다.
2. **New issue**를 눌러 요청 내용을 씁니다.
3. Issue에 `agent:queued` label을 붙입니다.
4. 에이전트가 실행될 때까지 기다립니다.
5. 에이전트가 질문하면 같은 Issue 댓글에 `@agent A` 또는 `@agent 방향: <내용>`으로 답합니다.
6. PR/MR이 생기면 본문에서 **사용자가 먼저 확인할 것**을 보고 확인합니다.
7. 결과를 같은 Issue 댓글에 `@agent test-pass` 또는 `@agent test-fail <사유>`로 남깁니다.

조직의 운영자 또는 도입 담당자가 미리 준비해야 하는 것은 다음입니다.

아래는 "어디서/어떻게"까지 적은 준비 체크리스트입니다.

1. 라벨 준비(필수)
   - 에이전트는 scan 시작 시점에 `agent:*`, `risk:*` 라벨을 API로 자동 생성할 수 있는 상태여야 합니다.
   - `agent:queued`는 사용자가 직접 붙일 수 있어야 하므로 시작 전 한 번 준비해 둡니다.
   - 필요 라벨: `agent:queued`, `agent:analyzing`, `agent:needs-info`, `agent:fixing`, `agent:verifying`, `agent:needs-user-test`, `agent:changes-requested`, `agent:done`, `agent:blocked`, `agent:mr-created`, `risk:low`, `risk:medium`, `risk:high`

2. 실행 위치(runner) 준비
   - 이 저장소의 개인 GitHub 검증은 GitHub-hosted runner에서 동작합니다(추가 runner 설정 불필요).
   - 사내 GitLab 등을 붙일 때는 API/클론이 되는 위치에 runner가 있어야 합니다(예: self-hosted runner, VPN 연결 내부 서버, WSL).

3. token 준비
   - 이 저장소 GitHub workflow 기본은 `GITHUB_TOKEN`을 사용합니다. 별도 secret 없이도 실행 가능합니다.
   - 조직 정책상 cross-repo 작업이 필요하면 토큰을 발급해 secret에 넣고, workflow의 `env.GITHUB_TOKEN`을 해당 secret으로 바꿉니다.
     - GitHub: repo 또는 org Settings → **Secrets and variables** → **Actions** → `GH_TOKEN`
     - GitLab: 대상 project Settings → **Access Tokens** → `GITLAB_TOKEN`
   - 로컬에서 실행할 때는 `export GITHUB_TOKEN=...` 또는 `export GITLAB_TOKEN=...`로 넘겨줍니다.

4. 대상 프로젝트별 `fix.command`/검증 명령 설정
   - `configs/projects/*.project.toml`의 `[fix]`와 `[commands]`를 수정해 연결합니다.
   - `fix.command`는 issue context JSON을 입력받아 결과 JSON(`success`, `summary`, `files_changed`, `commit_message`)을 반환해야 합니다.
   - 예시:

   ```toml
   [commands]
   install = "npm ci"
   lint = "npm run lint"
   test = "npm test"

   [fix]
   command = "python scripts/my_fix.py"
   ```

일반 사용자는 token, runner, `fix.command`를 직접 알 필요가 없습니다. Issue 작성, 방향 결정, PR/MR 확인, 테스트 결과 댓글만 책임집니다.

## Issue 작성 예시

Issue에는 에이전트와 리뷰어가 판단할 수 있는 정보를 적습니다. 처음부터 완벽하지 않아도 됩니다. 부족하면 에이전트가 `agent:needs-info` 상태에서 질문합니다.

권장 형식:

```markdown
Title: 로그인 실패 메시지 개선

Body:
## 요청
로그인 실패 시 사용자가 원인을 이해할 수 있게 메시지를 개선해주세요.

## 현재 증상
비밀번호가 틀려도 "로그인이 안됩니다"처럼 원인을 알기 어려운 메시지가 보입니다.

## 기대 결과
비밀번호 오류, 계정 잠김, 권한 없음처럼 사용자가 다음 행동을 알 수 있는 메시지가 보여야 합니다.

## 확인 방법
테스트 계정으로 잘못된 비밀번호를 입력해 로그인 실패 화면을 확인합니다.

## 주의할 점
로그인 정책 자체는 바꾸지 말고 메시지와 테스트만 보강해주세요.
```

최소 예시:

```markdown
Title: 로그인 오류

Body:
로그인이 안됩니다.
```

최소 예시처럼 정보가 부족하면 에이전트는 바로 수정하지 않고 질문을 남깁니다.

## 한눈에 보는 흐름

아래 표는 사용자가 실제로 보게 되는 흐름입니다. 괄호 안의 `agent:*` 값은 Issue label에 기록되는 내부 상태명입니다.

| 단계 | 사용자가 보는 의미 | 사용자가 할 일 | 에이전트가 하는 일 |
| --- | --- | --- | --- |
| 작업 요청 등록 | 이 이슈를 에이전트에게 맡긴다 (`agent:queued`) | 이슈에 요청을 쓰고 처리 label을 붙입니다. | 다음 실행 때 이슈를 읽습니다. |
| 이슈 분석 | 에이전트가 요청을 이해하려고 읽는 중 (`agent:analyzing`) | 기다립니다. | 이슈 본문과 사용자 댓글을 분석합니다. |
| 추가 정보 필요 | 요구사항이 모호하거나 승인 판단이 필요함 (`agent:needs-info`) | 이슈 댓글에 `@agent A` 또는 `@agent 방향: <내용>`을 남깁니다. | 선택지와 답변 형식을 제시하고 코드 변경 전 멈춥니다. |
| 수정 진행 | 선택된 방향으로 코드 변경 중 (`agent:fixing`) | 기다립니다. | `fix.command`를 실행하고 변경 파일을 만듭니다. |
| 검증 진행 | 테스트/검증 명령 실행 중 (`agent:verifying`) | 기다립니다. | 설정된 검증 명령을 실행합니다. |
| PR 생성 | 리뷰와 테스트를 위한 PR이 만들어짐 (`agent:needs-user-test`) | PR을 보고 실제로 확인합니다. | branch를 push하고 MR/PR 보고서를 작성합니다. |
| 사용자 테스트 결과 기록 | PR 확인 결과를 이슈에 남김 | 사용자 테스트 안내 댓글 이후에 `@agent test-pass` 또는 `@agent test-fail <사유>`를 남깁니다. | 안내 이후의 댓글만 읽고 완료 또는 변경 요청으로 상태를 바꿉니다. |
| 완료 | 사용자가 통과를 확인함 (`agent:done`) | 필요하면 사람이 merge합니다. | 더 이상 자동 진행하지 않습니다. |

중단 상태(`agent:blocked`)는 에이전트가 혼자 해결할 수 없는 설정, 권한, 정책 문제가 있다는 뜻입니다. 운영자가 원인을 해결한 뒤 같은 이슈에 `@agent proceed` 또는 기존 선택지인 `@agent A`를 남기면 다음 실행에서 다시 시도합니다.

### 예시로 보는 흐름

아래 예시는 GitHub 화면 기준입니다. GitLab도 **Issues**, **New issue**, **Labels** 위치만 다를 뿐 흐름은 같습니다.

사용자가 Issue에 “로그인이 안됩니다”라고만 쓰면 에이전트는 바로 코드를 고치지 않습니다. 이슈가 너무 짧고 기대 동작이나 재현 조건이 부족하기 때문입니다.

1. GitHub 저장소에서 **Issues** 탭을 엽니다.
2. **New issue**를 누릅니다.
3. 제목과 본문을 입력합니다.

```markdown
Title: 로그인 오류

Body:
로그인이 안됩니다.
```

4. Issue 오른쪽의 **Labels**에서 `agent:queued`를 선택합니다.

이 label은 “에이전트가 이 Issue를 처리 대상으로 가져가도 된다”는 표시입니다. 저장소에 `agent:queued` label이 없다면 운영자에게 요청해 준비해 주세요. 나머지 `agent:*`, `risk:*` 라벨은 에이전트가 첫 실행에서 자동 생성합니다.

5. Issue를 저장합니다.
6. GitHub Actions의 **Project Ops Agent MVP** workflow를 실행합니다.
7. 에이전트가 Issue 댓글에 분석 결과와 질문을 남깁니다.
8. 사용자는 제시된 선택지를 고를 수 있습니다.

```text
@agent A
```

9. 제시된 선택지가 맞지 않으면 사용자가 직접 방향을 적을 수 있습니다.

```text
@agent 방향: 기존 로그인 정책은 유지하고, 실패 메시지만 사용자가 이해하기 쉽게 바꿔주세요.
```

10. workflow를 다시 실행하면 에이전트가 branch와 PR을 만듭니다.
11. 사용자는 PR의 “사용자가 먼저 확인할 것”을 기준으로 확인합니다.
12. 통과하면 연결된 Issue에 결과를 남깁니다.

```text
@agent test-pass
```

실패하면 사유를 함께 남깁니다.

```text
@agent test-fail 로그인 실패 메시지는 바뀌었지만 모바일 화면에서 줄바꿈이 깨집니다.
```

## 에이전트 댓글 구분

GitHub Actions나 개인 token 설정에 따라 에이전트가 남긴 댓글이 사용자 계정으로 보일 수 있습니다. 그래서 에이전트가 작성하는 Issue 댓글과 PR 보고서에는 보이는 표식을 넣습니다.

```text
작성 주체: Project Ops Agent
```

이 표식이 있는 댓글은 계정명이 사용자와 같아도 에이전트 산출물로 봅니다. 사용자의 결정은 이 표식이 없는 Issue 댓글의 `@agent ...` 명령으로 남깁니다.

## 사용자가 판단하는 것

사용자가 반드시 판단해야 하는 부분은 네 가지입니다.

- 이 이슈를 에이전트에게 맡길지 결정합니다.
- 모호한 요구사항에 대해 A/B/C를 선택하거나 직접 방향을 제시합니다.
- PR이 만들어진 뒤 실제 사용자 테스트 또는 검토 결과를 판단합니다.
- 최종 merge 여부를 사람이 결정합니다.

에이전트는 merge하지 않습니다. PR이 만들어져도 자동으로 완료 처리하지 않습니다.
PR 생성 전에 미리 남긴 `@agent test-pass`는 완료 신호로 사용하지 않습니다.

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

## 지금 바로 확인할 점검표 (PR 안 올라올 때)

PR이 안 보이면 아래 순서로 먼저 확인합니다.

1. Issues에서 처리 이슈가 `agent:queued`로 시작했는지 확인합니다.
2. Actions 실행이 완료되었는지 확인하고, 이슈 댓글에 다음 중 하나라도 남았는지 봅니다.
   - `에이전트가 분석 중`
   - `추가 정보가 필요함`
   - `사용자 테스트 안내`
   - `에이전트 중단`
3. 이슈에 `agent:needs-info`가 붙어 있으면 `@agent A` 또는 `@agent 방향: <내용>`으로 먼저 답변합니다.
4. 그 외에 오류가 보이면 Actions 로그를 먼저 확인해 `403`, `permission`, `push`/`PR` 오류를 찾습니다.
5. 여전히 PR이 없다면 `Settings > Actions > General`에서 `Read and write permissions`와 `Allow GitHub Actions to create and approve pull requests`가 켜져 있는지 확인합니다.

위 4~5단계에서 해결이 되면 workflow를 다시 실행합니다. 이슈 상태가 `agent:needs-user-test`로 바뀌고 PR이 생성되어야 다음 단계입니다.

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

Codex CLI로 실제 소스 수정을 시도하려면 codex fix config를 사용합니다.

```text
configs/projects/github.codex.project.toml
```

자세한 절차는 [docs/GITHUB_ACTIONS.md](docs/GITHUB_ACTIONS.md)를 참고하세요.

## demo fix.command란?

`fix.command`는 에이전트가 실제 코드 수정을 맡기는 외부 명령입니다. 에이전트는 이슈와 분석 결과를 JSON으로 전달하고, `fix.command`는 파일을 수정한 뒤 결과 JSON을 반환합니다.

`scripts/demo_fix_command.py`는 실무 버그를 고치는 도구가 아닙니다. GitHub Actions에서 branch push, commit, PR 생성, 사용자 테스트 대기 흐름을 검증하기 위해 `.agent-demo/` 아래에 작은 검증용 파일을 만드는 데모 명령입니다.

`scripts/codex_fix_command.py`는 runner에 설치된 `codex exec`를 호출해 실제 소스 수정을 시도하는 wrapper입니다. GitHub-hosted runner와 사내 GitLab Runner 모두 같은 방식으로 쓸 수 있지만, runner에 Codex CLI와 인증 정보가 준비되어 있어야 합니다.

실제 프로젝트에서는 이 자리에 프로젝트 전용 수정 도구, Codex CLI wrapper, 사내 LLM 도구를 연결합니다.

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
