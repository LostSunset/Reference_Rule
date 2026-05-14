# Development Log Rules

Development logs make this rule pack traceable for humans, Codex, Claude Code, and other AI coding agents.

Every non-trivial change must have a log entry.

## Location

```text
docs/development-logs/
  README.md
  TEMPLATE.md
  INDEX.md
  entries/
    YYYY-MM-DD-HHMM-<github-or-agent-name>-<short-topic>.md
```

## When To Create A Log

Create or update a log entry when the work includes any of these:

- changing repository rules
- changing `Reference_sources` rules
- changing `upstream` rules
- adding scripts or automation
- changing branch protection or repository settings
- adding, removing, or reorganizing source/reference material
- making a direct owner/admin push to `main`

Tiny typo fixes may skip a new entry if the commit message is clear.

## Filename Rule

Use local date and 24-hour time:

```text
YYYY-MM-DD-HHMM-<github-or-agent-name>-<short-topic>.md
```

Examples:

```text
2026-05-14-0955-LostSunset-initial-rule-pack.md
2026-05-14-1012-codex-branch-protection.md
```

Use lowercase kebab-case for `<short-topic>`.

## Required Sections

Each entry must use `TEMPLATE.md` and include:

- summary
- request/source
- files changed
- decisions
- commands and checks
- follow-up

## Rules For AI Agents

AI agents must:

1. Read the existing latest log before starting a non-trivial change.
2. Create one log entry for the current work session.
3. Update the same entry during the session instead of creating many fragmented logs.
4. Add the entry to `INDEX.md`.
5. Mention verification commands and their results.

AI agents must not:

- log secrets, tokens, or private credentials
- edit another developer's historical log except for obvious formatting fixes
- claim checks passed unless they actually ran the command
- hide direct pushes or repository setting changes

## Branch Protection Expectation

The default branch should require pull requests for normal collaborators.

Repository owner/admin maintenance pushes may bypass this rule when urgent or when bootstrapping the rule pack. Such direct pushes still require a development log entry.

