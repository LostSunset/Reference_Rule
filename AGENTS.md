# Agent Instructions

This repository is a reusable rule pack. It is not an application project.

Before changing files, Codex agents must read:

- `README.md`
- `Reference_sources/README.md`
- `upstream/README.md`
- `docs/development-logs/README.md`

## Required Development Log Behavior

For every non-trivial change, create or update one development log entry under:

```text
docs/development-logs/entries/
```

Use this filename format:

```text
YYYY-MM-DD-HHMM-<github-or-agent-name>-<short-topic>.md
```

Use `docs/development-logs/TEMPLATE.md` as the entry structure.

At minimum, record:

- request summary
- files changed
- decisions made
- commands or checks run
- remaining risks or follow-up work

Do not include secrets, tokens, private credentials, or personal data unrelated to the work.

## Upstream Policy

Never modify files under:

```text
upstream/repos/*/repo/
```

Those directories are read-only upstream clones. Write adapters, notes, or patches outside the upstream clone.

