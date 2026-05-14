# 2026-05-14 11:55 Reading Images And HTML Summary

## Summary

- What changed: Added rules and automation for full-document reading PNGs and per-source `summary.html` files.
- Why it changed: LostSunset requested that journals, books, and documents should preferably be read as images, and that each source should automatically include an HTML file summarizing its key points.

## Request / Source

- Requested by: LostSunset.
- Related issue, PR, or conversation: Codex desktop session on 2026-05-14.

## Files Changed

- `README.md`: Adds the new AI behavior requirements for `reading_pages/` and `summary.html`.
- `Reference_sources/README.md`: Defines full-document image reading and HTML summary rules.
- `Reference_sources/_templates/metadata.book.json`: Adds `summary_html` and `image_reading`.
- `Reference_sources/_templates/metadata.journal.json`: Adds `summary_html` and `image_reading`.
- `Reference_sources/_templates/metadata.tool_user_guide.json`: Adds `summary_html` and `image_reading`.
- `reference_rule_sync.py`: Creates missing `summary.html` files and renders full-document reading PNGs when enabled.
- `docs/development-logs/INDEX.md`: Adds this log entry.
- `docs/development-logs/entries/2026-05-14-1155-codex-reading-images-and-html-summary.md`: Records this change.

## Decisions

- Decision: Use `summary.html` as the default per-source summary file.
  Reason: HTML is portable, offline-readable, and can include structured links to images and key pages.
- Decision: Use `reading_pages/` for full-document PNGs and keep `key_pages/` for selected critical pages.
  Reason: AI can scan the whole source visually while still having a curated set of high-value pages.
- Decision: Treat full-document rendering as recommended automation, not a hard blocker.
  Reason: Large books may be expensive to render, and some environments may not have `pdftoppm` or `mutool`.

## Commands And Checks

- Command: `uv run --python 3.12 python reference_rule_sync.py validate --root .`
  Result: Passed on the local empty rule pack with 0 errors and 0 warnings.
- Command: `uv run --python 3.12 python reference_rule_sync.py sync --root . --dry-run`
  Result: Passed on the local empty rule pack with 0 errors.
- Command: sandbox validation with one fake book source and no `summary_html` field.
  Result: Passed and automatically created `summary.html` while adding `summary_html` to metadata.
- Command: `Get-Command pdftoppm` and `Get-Command mutool`
  Result: Neither renderer is installed in this local environment; full-document PNG rendering will run in environments that provide one of those tools.

## Upstream / Reference Impact

- Reference_sources impact: New sources should include `summary_html`, `image_reading`, `reading_pages/`, and `summary.html`.
- upstream impact: No direct change to upstream wrapper policy.

## Follow-up

- Remaining work: None planned.
- Risks: Full-document PNG conversion can create many large files for books; projects may set `image_reading.status` to `deferred` with a note when needed.
