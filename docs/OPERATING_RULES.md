# Operating Rules

## Core Rules

1. The selected issue platform is the only source of truth.
2. Human answers must be written in issue comments.
3. Messenger tools may notify, but they must not collect decisions in the MVP.
4. The agent may create branches and MRs.
5. The agent must not merge.
6. The agent must stop before code changes when requirements are unclear.
7. The MR description is a report, not a casual summary.

## Labels

Only one `agent:*` state label should exist on an issue at a time.

| Label | Meaning |
| --- | --- |
| `agent:queued` | Issue is ready for agent processing |
| `agent:analyzing` | Agent is analyzing the issue |
| `agent:needs-info` | Agent is waiting for human direction |
| `agent:fixing` | Agent is changing code |
| `agent:verifying` | Agent is running verification |
| `agent:mr-created` | Agent created an MR |
| `agent:needs-user-test` | MR/PR exists and human user testing is required |
| `agent:changes-requested` | User testing failed or requested a revision |
| `agent:blocked` | Agent cannot continue |
| `agent:done` | Work is complete |

Risk labels:

| Label | Meaning |
| --- | --- |
| `risk:low` | Small localized change |
| `risk:medium` | Meaningful behavior or verification risk |
| `risk:high` | Production-sensitive or approval-required area |

## Clarification Format

When the agent needs direction, it writes:

```markdown
## Agent Needs Info

### What I understood
- ...

### Ambiguous points
- ...

### Options
- A: ...
- B: ...
- C: ...

### Reply format
`@agent A`
```

The agent resumes only after it sees a later issue comment containing one of:

```text
@agent A
@agent B
@agent C
@agent proceed
@agent approve
```

## MR Report Shape

The MR description must include:

- compact reviewer summary
- issue link
- risk level
- selected decision
- verification result
- user test gate
- expandable issue analysis
- expandable implementation details
- expandable verification logs
- expandable agent decision log

GitLab and GitHub render Markdown with tags such as `<table>` and `<details>`, so the MVP uses those instead of a separate HTML artifact.

## User Testing

The MR/PR is not the user test itself. It is the artifact that lets a reviewer or user test the change.

After the MR/PR is created, the agent moves the issue to `agent:needs-user-test`.

The test result must be written on the linked issue:

```text
@agent test-pass
```

or:

```text
@agent test-fail <reason>
```

On pass, the agent moves the issue to `agent:done`.

On fail, the agent moves the issue to `agent:changes-requested`.
