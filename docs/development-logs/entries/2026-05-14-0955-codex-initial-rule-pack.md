# 2026-05-14 09:55 Initial Rule Pack

## Summary

- What changed: Added the first reusable Reference Rule pack, development log rules, agent entry instructions, and branch protection setup automation.
- Why it changed: The repository needs rules that Codex, Claude Code, and human developers can follow consistently across projects.

## Request / Source

- Requested by: LostSunset.
- Related issue, PR, or conversation: Owner request in Codex desktop session on 2026-05-14.

## Files Changed

- `README.md`: Documents how to use the rule pack.
- `Reference_sources/README.md`: Defines source classification, metadata, traceability, and key page PNG rules.
- `Reference_sources/_templates/*.json`: Provides metadata templates for books, journals, and tool user guides.
- `upstream/README.md`: Defines read-only upstream wrapper rules.
- `upstream/.gitignore`: Keeps cloned upstream repositories out of git history.
- `reference_rule_sync.py`: Adds portable validation, manifest, key-page rendering, and upstream sync automation.
- `reference_rule_manifest.json`: Initializes the traceability manifest.
- `schedule/*`: Adds Windows Task Scheduler, cron, and GitHub Actions examples.
- `AGENTS.md`: Adds Codex-facing repository instructions.
- `CLAUDE.md`: Adds Claude Code-facing repository instructions.
- `docs/development-logs/*`: Adds development log rules, template, index, and this initial log.
- `scripts/configure_branch_protection.ps1`: Adds repeatable branch protection setup.

## Decisions

- Decision: Use Markdown rules plus a Python standard-library synchronizer.
  Reason: The rule pack should work when copied into different projects without turning into a heavy tool project.
- Decision: Store upstream repositories as read-only wrappers under `upstream/repos/<owner>__<repo>/repo`.
  Reason: External code should remain traceable and separable from project-owned changes.
- Decision: Add both `AGENTS.md` and `CLAUDE.md`.
  Reason: Codex and Claude Code use different convention files, but both need the same log behavior.
- Decision: Configure branch protection so normal collaborators must use PRs while admins can still push directly.
  Reason: The owner requested direct maintenance push ability while keeping collaborator changes reviewable.

## Commands And Checks

- Command: `uv run --python 3.12 python reference_rule_sync.py validate --root .`
  Result: Passed on the local empty rule pack before publishing.
- Command: `uv run --python 3.12 python reference_rule_sync.py sync --root . --dry-run`
  Result: Passed on the local empty rule pack before publishing.
- Command: sandbox metadata dry-run with one fake journal and one fake GitHub URL.
  Result: Created an upstream wrapper in dry-run mode.
- Command: `git push -u origin main`
  Result: Published the first `main` branch to `https://github.com/LostSunset/Reference_Rule.git`.
- Command: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\configure_branch_protection.ps1 -Repository LostSunset/Reference_Rule -Branch main`
  Result: Branch protection configured for `main`; pull request review is required, stale reviews are dismissed, conversations must be resolved, force pushes and branch deletions are disabled, and admin enforcement is disabled so the owner/admin can still push directly.

## Upstream / Reference Impact

- Reference_sources impact: Adds required metadata, key page PNG, source tracing, and template rules.
- upstream impact: Adds read-only wrapper policy and sync behavior.

## Follow-up

- Remaining work: None for the initial rule pack setup.
- Risks: Branch protection lets repository admins bypass PR requirements by design, matching the owner request. Non-admin collaborators must use pull requests.
