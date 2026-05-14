# 2026-05-14 12:00 Large Document Image Strategy

## Summary

- What changed: Added a page-count-based strategy for deciding how many PDF pages to convert into reading PNGs.
- Why it changed: LostSunset requested a rule for handling documents with too many pages.

## Request / Source

- Requested by: LostSunset.
- Related issue, PR, or conversation: Codex desktop session on 2026-05-14.

## Files Changed

- `Reference_sources/README.md`: Documents the large-document image conversion strategy and thresholds.
- `Reference_sources/_templates/metadata.book.json`: Adds strategy thresholds to `image_reading`.
- `Reference_sources/_templates/metadata.journal.json`: Adds strategy thresholds to `image_reading`.
- `Reference_sources/_templates/metadata.tool_user_guide.json`: Adds strategy thresholds to `image_reading`.
- `README.md`: Mentions page-count-aware image rendering.
- `reference_rule_sync.py`: Adds page-count detection, conversion planning, chunked rendering, and selective rendering logic.
- `tests/test_reference_rule_sync.py`: Adds tests for full, chunked, selective, and deferred image rendering plans.
- `docs/development-logs/INDEX.md`: Adds this log entry.
- `docs/development-logs/entries/2026-05-14-1200-codex-large-document-image-strategy.md`: Records this change.

## Decisions

- Decision: Use `auto` as the default strategy.
  Reason: Different projects can reuse the rule pack without manually classifying every PDF.
- Decision: Render `1-120` pages fully, `121-500` pages in chunks, and `501+` pages selectively by default.
  Reason: This keeps short papers convenient while preventing long books and manuals from producing excessive image files.
- Decision: If page count cannot be detected, defer full conversion.
  Reason: Blindly rendering an unknown-size PDF can create unexpectedly large output.

## Commands And Checks

- Command: `uv run --python 3.12 python -m unittest tests.test_reference_rule_sync -v`
  Result: Passed 4 tests for full, chunked, selective, and deferred image rendering plans.
- Command: `uv run --python 3.12 python reference_rule_sync.py validate --root .`
  Result: Passed with 0 errors and 0 warnings.
- Command: `uv run --python 3.12 python reference_rule_sync.py sync --root . --dry-run`
  Result: Passed with 0 errors.

## Upstream / Reference Impact

- Reference_sources impact: Sources can now tune image conversion with `max_full_pages`, `max_chunked_pages`, `chunk_size`, and `front_matter_pages`.
- upstream impact: No direct change.

## Follow-up

- Remaining work: None planned.
- Risks: Page counting depends on `pdfinfo` or `mutool`; if neither is available, the strategy intentionally defers full conversion.
