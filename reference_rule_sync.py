#!/usr/bin/env python3
"""Portable Reference_sources/upstream synchronizer.

This script intentionally uses only Python's standard library. It expects git to
be available for upstream synchronization, and optionally uses pdftoppm or mutool
when rendering PDF pages to PNG.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


CATEGORIES = {
    "Books": "book",
    "Journals": "journal",
    "Tools_User_Guides": "tool_user_guide",
}

MANIFEST_NAME = "reference_rule_manifest.json"
REPO_URL_RE = re.compile(
    r"(?:https://|git@)(?:github\.com|gitlab\.com)[/:][A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\.git)?"
)


@dataclass
class Issue:
    level: str
    message: str
    path: str | None = None

    def as_dict(self) -> dict[str, str]:
        data = {"level": self.level, "message": self.message}
        if self.path:
            data["path"] = self.path
        return data


@dataclass
class SourceRecord:
    category: str
    source_dir: Path
    metadata_path: Path
    metadata: dict[str, Any]
    issues: list[Issue] = field(default_factory=list)


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def today_local() -> str:
    return dt.date.today().isoformat()


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return "sha256:" + digest.hexdigest()


def run(cmd: list[str], cwd: Path | None = None, dry_run: bool = False) -> tuple[int, str, str]:
    printable = " ".join(cmd)
    if dry_run:
        return 0, f"DRY-RUN {printable}", ""
    completed = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return completed.returncode, completed.stdout.strip(), completed.stderr.strip()


def ensure_structure(root: Path) -> None:
    (root / "Reference_sources").mkdir(exist_ok=True)
    for category in CATEGORIES:
        (root / "Reference_sources" / category).mkdir(parents=True, exist_ok=True)
    (root / "upstream" / "repos").mkdir(parents=True, exist_ok=True)
    manifest = root / MANIFEST_NAME
    if not manifest.exists():
        write_json(
            manifest,
            {
                "schema_version": "1.0",
                "generated_at": None,
                "reference_sources": [],
                "upstream_repositories": [],
                "issues": [],
            },
        )


def load_sources(root: Path) -> list[SourceRecord]:
    records: list[SourceRecord] = []
    base = root / "Reference_sources"
    for category, expected_type in CATEGORIES.items():
        category_dir = base / category
        if not category_dir.exists():
            continue
        for source_dir in sorted(p for p in category_dir.iterdir() if p.is_dir()):
            if source_dir.name.startswith("_"):
                continue
            metadata_path = source_dir / "metadata.json"
            record = SourceRecord(category, source_dir, metadata_path, {})
            if not metadata_path.exists():
                record.issues.append(Issue("error", "Missing metadata.json", str(metadata_path)))
                records.append(record)
                continue
            try:
                record.metadata = read_json(metadata_path)
            except json.JSONDecodeError as exc:
                record.issues.append(Issue("error", f"Invalid JSON: {exc}", str(metadata_path)))
                records.append(record)
                continue
            validate_metadata(record, expected_type)
            records.append(record)
    return records


def validate_metadata(record: SourceRecord, expected_type: str) -> None:
    meta = record.metadata
    required = ["id", "type", "title", "source_url", "downloaded_at", "local_files"]
    for field_name in required:
        if not meta.get(field_name):
            record.issues.append(Issue("error", f"Missing required field: {field_name}", str(record.metadata_path)))

    if meta.get("id") and meta["id"] != record.source_dir.name:
        record.issues.append(
            Issue("error", "metadata.id must equal the source folder name", str(record.metadata_path))
        )

    if meta.get("type") and meta["type"] != expected_type:
        record.issues.append(
            Issue("error", f"metadata.type must be {expected_type}", str(record.metadata_path))
        )

    local_files = meta.get("local_files", [])
    if not isinstance(local_files, list):
        record.issues.append(Issue("error", "local_files must be a list", str(record.metadata_path)))
        local_files = []

    for rel in local_files:
        file_path = record.source_dir / str(rel)
        if not file_path.exists():
            record.issues.append(Issue("error", f"Listed local file does not exist: {rel}", str(file_path)))

    for page in meta.get("key_pages", []) or []:
        if not isinstance(page, dict):
            record.issues.append(Issue("error", "Each key_pages item must be an object", str(record.metadata_path)))
            continue
        if not isinstance(page.get("page"), int):
            record.issues.append(Issue("error", "Each key page needs an integer page", str(record.metadata_path)))
        png = page.get("png")
        if png and not (record.source_dir / png).exists():
            record.issues.append(Issue("warning", f"Key page PNG not found yet: {png}", str(record.source_dir / png)))


def update_hashes(record: SourceRecord) -> None:
    meta = record.metadata
    if not meta:
        return
    hashes = dict(meta.get("hashes") or {})
    for rel in meta.get("local_files", []) or []:
        path = record.source_dir / str(rel)
        if path.is_file():
            hashes[str(rel)] = sha256_file(path)
    meta["hashes"] = hashes
    write_json(record.metadata_path, meta)


def source_summary(record: SourceRecord) -> dict[str, Any]:
    meta = record.metadata
    return {
        "id": meta.get("id", record.source_dir.name),
        "category": record.category,
        "type": meta.get("type"),
        "title": meta.get("title"),
        "source_url": meta.get("source_url"),
        "downloaded_at": meta.get("downloaded_at"),
        "metadata_path": str(record.metadata_path),
        "local_files": meta.get("local_files", []),
        "hashes": meta.get("hashes", {}),
        "summary_html": meta.get("summary_html", "summary.html"),
        "image_reading": meta.get("image_reading", {}),
        "key_pages": meta.get("key_pages", []),
    }


def walk_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        strings: list[str] = []
        for item in value:
            strings.extend(walk_strings(item))
        return strings
    if isinstance(value, dict):
        strings = []
        for item in value.values():
            strings.extend(walk_strings(item))
        return strings
    return []


def normalize_repo_url(url: str) -> str:
    cleaned = url.strip().rstrip(").,;]")
    if cleaned.startswith("git@"):
        cleaned = cleaned.replace(":", "/", 1)
        cleaned = "https://" + cleaned[4:]
    if cleaned.endswith(".git"):
        cleaned = cleaned[:-4]
    return cleaned.rstrip("/")


def repo_id_from_url(url: str) -> str:
    normalized = normalize_repo_url(url)
    parsed = urlparse(normalized)
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) < 2:
        raise ValueError(f"Cannot derive repo id from URL: {url}")
    return f"{parts[-2]}__{parts[-1]}".replace(".", "_")


def extract_repo_entries(record: SourceRecord) -> list[dict[str, str]]:
    meta = record.metadata
    entries: dict[str, dict[str, str]] = {}

    explicit = meta.get("upstream_repositories", []) or []
    if isinstance(explicit, list):
        for item in explicit:
            if isinstance(item, str):
                url = item
                reason = "Listed in upstream_repositories."
            elif isinstance(item, dict):
                url = str(item.get("url", ""))
                reason = str(item.get("reason", "Listed in upstream_repositories."))
            else:
                continue
            if url:
                normalized = normalize_repo_url(url)
                entries[normalized] = {
                    "url": normalized,
                    "reason": reason,
                    "source_id": str(meta.get("id", record.source_dir.name)),
                    "source_metadata": str(record.metadata_path),
                }

    for text in walk_strings(meta):
        for match in REPO_URL_RE.findall(text):
            normalized = normalize_repo_url(match)
            entries.setdefault(
                normalized,
                {
                    "url": normalized,
                    "reason": "Detected in source metadata.",
                    "source_id": str(meta.get("id", record.source_dir.name)),
                    "source_metadata": str(record.metadata_path),
                },
            )

    return list(entries.values())


def git_head(repo_dir: Path) -> str | None:
    code, out, _ = run(["git", "rev-parse", "HEAD"], cwd=repo_dir)
    return out if code == 0 else None


def sync_one_repo(root: Path, entry: dict[str, str], dry_run: bool = False) -> dict[str, Any]:
    repo_id = repo_id_from_url(entry["url"])
    wrapper_dir = root / "upstream" / "repos" / repo_id
    repo_dir = wrapper_dir / "repo"
    wrapper_dir.mkdir(parents=True, exist_ok=True)
    status = "ok"
    message = ""

    if not repo_dir.exists():
        code, out, err = run(["git", "clone", entry["url"], str(repo_dir)], dry_run=dry_run)
        if code != 0:
            status = "error"
            message = err or out
    else:
        code, out, err = run(["git", "status", "--porcelain"], cwd=repo_dir)
        if code != 0:
            status = "error"
            message = err or out
        elif out:
            status = "dirty"
            message = "Upstream repo has local modifications; skipped update."
        else:
            for cmd in (
                ["git", "fetch", "--all", "--tags", "--prune"],
                ["git", "pull", "--ff-only"],
            ):
                code, out, err = run(cmd, cwd=repo_dir, dry_run=dry_run)
                if code != 0:
                    status = "error"
                    message = err or out
                    break

    head = git_head(repo_dir) if repo_dir.exists() and not dry_run else None
    wrapper = {
        "schema_version": "1.0",
        "policy": "read_only_upstream_wrapper",
        "repository": {
            "id": repo_id,
            "url": entry["url"],
            "local_repo_path": str(repo_dir),
        },
        "sources": [
            {
                "source_id": entry["source_id"],
                "source_metadata": entry["source_metadata"],
                "reason": entry["reason"],
            }
        ],
        "sync": {
            "last_attempt_at": now_utc(),
            "last_status": status,
            "last_message": message,
            "last_head": head,
        },
    }
    write_json(wrapper_dir / "wrapper.json", wrapper)
    readme = wrapper_dir / "README.md"
    if not readme.exists():
        readme.write_text(
            "# Read-only upstream wrapper\n\n"
            f"- Repository: {entry['url']}\n"
            "- Local clone: `repo/`\n"
            "- Policy: never modify files under `repo/`; write adapters or patches outside this clone.\n",
            encoding="utf-8",
            newline="\n",
        )

    return {
        "id": repo_id,
        "url": entry["url"],
        "wrapper_path": str(wrapper_dir),
        "repo_path": str(repo_dir),
        "source_ids": [entry["source_id"]],
        "last_synced_at": now_utc(),
        "last_status": status,
        "last_head": head,
        "message": message,
    }


def collect_repo_entries(records: list[SourceRecord]) -> list[dict[str, str]]:
    merged: dict[str, dict[str, str]] = {}
    for record in records:
        if record.metadata:
            for entry in extract_repo_entries(record):
                existing = merged.get(entry["url"])
                if existing:
                    ids = set(existing["source_id"].split(", "))
                    ids.add(entry["source_id"])
                    existing["source_id"] = ", ".join(sorted(ids))
                    existing["reason"] = existing["reason"] + " | " + entry["reason"]
                else:
                    merged[entry["url"]] = entry
    return list(merged.values())


def default_png_name(page: int, label: str | None) -> str:
    suffix = ""
    if label:
        safe = re.sub(r"[^a-zA-Z0-9_-]+", "-", label.strip()).strip("-").lower()
        if safe:
            suffix = "_" + safe[:60]
    return f"key_pages/page_{page:03d}{suffix}.png"


def find_pdf_for_record(record: SourceRecord) -> Path | None:
    meta = record.metadata
    preferred = meta.get("pdf")
    if preferred and (record.source_dir / preferred).exists():
        return record.source_dir / preferred
    for rel in meta.get("local_files", []) or []:
        path = record.source_dir / str(rel)
        if path.suffix.lower() == ".pdf" and path.exists():
            return path
    return None


def default_summary_html(record: SourceRecord) -> str:
    meta = record.metadata
    title = html.escape(str(meta.get("title") or record.source_dir.name))
    source_id = html.escape(str(meta.get("id") or record.source_dir.name))
    source_type = html.escape(str(meta.get("type") or record.category))
    source_url = html.escape(str(meta.get("source_url") or "unknown"))
    authors = meta.get("authors") or []
    if isinstance(authors, list):
        author_text = ", ".join(str(author) for author in authors)
    else:
        author_text = str(authors)
    author_text = html.escape(author_text or "unknown")
    year = html.escape(str(meta.get("year") or "unknown"))
    key_pages = meta.get("key_pages", []) or []
    key_page_items = []
    for item in key_pages:
        if not isinstance(item, dict):
            continue
        page = html.escape(str(item.get("page", "unknown")))
        label = html.escape(str(item.get("label") or item.get("reason") or "key page"))
        png = html.escape(str(item.get("png") or ""))
        suffix = f" - {png}" if png else ""
        key_page_items.append(f"<li>page {page}: {label}{suffix}</li>")
    key_page_html = "\n        ".join(key_page_items) if key_page_items else "<li>No key pages recorded yet.</li>"

    return f"""<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <title>{title} - Summary</title>
  <style>
    body {{ font-family: system-ui, sans-serif; line-height: 1.6; max-width: 960px; margin: 2rem auto; padding: 0 1rem; }}
    h1, h2 {{ line-height: 1.25; }}
    code {{ background: #f3f4f6; padding: 0.1rem 0.25rem; border-radius: 4px; }}
    .meta {{ color: #4b5563; }}
  </style>
</head>
<body>
  <h1>{title}</h1>
  <p class="meta">ID: <code>{source_id}</code> | Type: {source_type} | Year: {year}</p>
  <p class="meta">Authors / Organization: {author_text}</p>
  <p class="meta">Source: <a href="{source_url}">{source_url}</a></p>

  <h2>重點摘要</h2>
  <ul>
    <li>這份來源要解決的問題：尚待 AI 閱讀後補充。</li>
    <li>專案應採用的重點結論：尚待 AI 閱讀後補充。</li>
    <li>重要限制、授權或可信度注意事項：尚待 AI 閱讀後補充。</li>
  </ul>

  <h2>關鍵頁面</h2>
  <ul>
        {key_page_html}
  </ul>

  <h2>公式、表格、圖與 API</h2>
  <ul>
    <li>尚待 AI 補充公式、表格、圖、API 行為與對應頁碼。</li>
  </ul>

  <h2>Upstream / Code / Dataset 關聯</h2>
  <ul>
    <li>尚待 AI 補充此來源提到的 repo、工具、SDK、資料集或範例程式。</li>
  </ul>
</body>
</html>
"""


def ensure_summary_html(record: SourceRecord, dry_run: bool = False) -> list[Issue]:
    if not record.metadata:
        return []
    meta = record.metadata
    summary_rel = str(meta.get("summary_html") or "summary.html")
    summary_path = record.source_dir / summary_rel
    changed = False
    if meta.get("summary_html") != summary_rel:
        meta["summary_html"] = summary_rel
        changed = True
    if not summary_path.exists() and not dry_run:
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(default_summary_html(record), encoding="utf-8", newline="\n")
    if changed and not dry_run:
        write_json(record.metadata_path, meta)
    return []


def image_reading_config(record: SourceRecord) -> dict[str, Any]:
    raw = record.metadata.get("image_reading")
    if not isinstance(raw, dict):
        raw = {}
    return {
        "enabled": bool(raw.get("enabled", True)),
        "directory": str(raw.get("directory") or "reading_pages"),
        "dpi": int(raw.get("dpi") or 180),
        "status": str(raw.get("status") or "recommended"),
    }


def render_reading_pages(record: SourceRecord, dry_run: bool = False) -> list[Issue]:
    issues: list[Issue] = []
    if not record.metadata:
        return issues
    config = image_reading_config(record)
    if not config["enabled"]:
        return issues

    pdf_path = find_pdf_for_record(record)
    if not pdf_path:
        issues.append(Issue("warning", "image_reading enabled but no PDF found in local_files", str(record.metadata_path)))
        return issues

    output_dir = record.source_dir / config["directory"]
    existing_pngs = list(output_dir.glob("*.png")) if output_dir.exists() else []
    if existing_pngs:
        return issues

    pdftoppm = shutil.which("pdftoppm")
    mutool = shutil.which("mutool")
    if not pdftoppm and not mutool:
        issues.append(
            Issue(
                "warning",
                "Cannot render reading_pages because pdftoppm or mutool is not available.",
                str(record.metadata_path),
            )
        )
        return issues

    if not dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)

    if pdftoppm:
        prefix = output_dir / "page"
        cmd = ["pdftoppm", "-png", "-r", str(config["dpi"]), str(pdf_path), str(prefix)]
    else:
        cmd = ["mutool", "draw", "-o", str(output_dir / "page_%03d.png"), "-r", str(config["dpi"]), str(pdf_path)]

    code, out, err = run(cmd, dry_run=dry_run)
    if code != 0:
        issues.append(Issue("error", f"Failed to render reading pages: {err or out}", str(pdf_path)))
        return issues

    meta = record.metadata
    previous = meta.get("image_reading")
    updated = {
        "enabled": config["enabled"],
        "directory": config["directory"],
        "dpi": config["dpi"],
        "status": "rendered" if not dry_run else config["status"],
    }
    if not dry_run:
        updated["last_rendered_at"] = now_utc()
    if previous != updated and not dry_run:
        meta["image_reading"] = updated
        write_json(record.metadata_path, meta)
    return issues


def render_key_pages(record: SourceRecord, dry_run: bool = False) -> list[Issue]:
    issues: list[Issue] = []
    meta = record.metadata
    key_pages = meta.get("key_pages", []) or []
    if not key_pages:
        return issues
    pdf_path = find_pdf_for_record(record)
    if not pdf_path:
        issues.append(Issue("error", "key_pages defined but no PDF found in local_files", str(record.metadata_path)))
        return issues

    pdftoppm = shutil.which("pdftoppm")
    mutool = shutil.which("mutool")
    if not pdftoppm and not mutool:
        issues.append(
            Issue(
                "warning",
                "Cannot render key pages because pdftoppm or mutool is not available.",
                str(record.metadata_path),
            )
        )
        return issues

    changed = False
    for item in key_pages:
        if not isinstance(item, dict) or not isinstance(item.get("page"), int):
            continue
        page = int(item["page"])
        rel_png = item.get("png") or default_png_name(page, item.get("label"))
        item["png"] = rel_png
        changed = True
        output_path = record.source_dir / rel_png
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if output_path.exists():
            continue
        if pdftoppm:
            prefix = output_path.with_suffix("")
            cmd = ["pdftoppm", "-f", str(page), "-l", str(page), "-png", "-singlefile", str(pdf_path), str(prefix)]
        else:
            cmd = ["mutool", "draw", "-o", str(output_path), "-r", "180", str(pdf_path), str(page)]
        code, out, err = run(cmd, dry_run=dry_run)
        if code != 0:
            issues.append(Issue("error", f"Failed to render page {page}: {err or out}", str(pdf_path)))

    if changed and not dry_run:
        write_json(record.metadata_path, meta)
    return issues


def write_manifest(root: Path, records: list[SourceRecord], upstream_results: list[dict[str, Any]]) -> None:
    issues = []
    for record in records:
        issues.extend(issue.as_dict() for issue in record.issues)
    for result in upstream_results:
        if result.get("last_status") not in {"ok", None}:
            issues.append(
                {
                    "level": "error" if result.get("last_status") == "error" else "warning",
                    "message": result.get("message") or f"Upstream status: {result.get('last_status')}",
                    "path": result.get("wrapper_path"),
                }
            )

    manifest = {
        "schema_version": "1.0",
        "generated_at": None,
        "reference_sources": [source_summary(record) for record in records if record.metadata],
        "upstream_repositories": upstream_results,
        "issues": issues,
    }

    manifest_path = root / MANIFEST_NAME
    if manifest_path.exists():
        try:
            current = read_json(manifest_path)
            comparable = dict(current)
            comparable["generated_at"] = None
            if comparable == manifest:
                return
        except (OSError, json.JSONDecodeError):
            pass

    manifest["generated_at"] = now_utc()
    write_json(root / MANIFEST_NAME, manifest)


def command_init(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    ensure_structure(root)
    print(f"Initialized reference rule structure at {root}")
    return 0


def command_validate(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    ensure_structure(root)
    records = load_sources(root)
    for record in records:
        if record.metadata and not args.no_hash:
            update_hashes(record)
        if record.metadata:
            ensure_summary_html(record, dry_run=args.dry_run)
    records = load_sources(root)
    write_manifest(root, records, [])
    issues = [issue for record in records for issue in record.issues if issue.level == "error"]
    warnings = [issue for record in records for issue in record.issues if issue.level == "warning"]
    print(f"Validated {len(records)} source(s): {len(issues)} error(s), {len(warnings)} warning(s).")
    for issue in issues + warnings:
        location = f" [{issue.path}]" if issue.path else ""
        print(f"{issue.level.upper()}: {issue.message}{location}")
    return 1 if issues else 0


def command_render_pages(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    ensure_structure(root)
    records = load_sources(root)
    extra_issues: list[Issue] = []
    for record in records:
        if record.metadata:
            extra_issues.extend(ensure_summary_html(record, dry_run=args.dry_run))
            extra_issues.extend(render_reading_pages(record, dry_run=args.dry_run))
            extra_issues.extend(render_key_pages(record, dry_run=args.dry_run))
    records = load_sources(root)
    if extra_issues:
        records.append(
            SourceRecord(
                "render-pages",
                root,
                root / MANIFEST_NAME,
                {},
                extra_issues,
            )
        )
    write_manifest(root, records, [])
    errors = [issue for issue in extra_issues if issue.level == "error"]
    print(f"Rendered reading/key pages with {len(errors)} error(s) and {len(extra_issues) - len(errors)} warning(s).")
    for issue in extra_issues:
        location = f" [{issue.path}]" if issue.path else ""
        print(f"{issue.level.upper()}: {issue.message}{location}")
    return 1 if errors else 0


def command_sync_upstream(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    ensure_structure(root)
    records = load_sources(root)
    entries = collect_repo_entries(records)
    results = []
    for entry in entries:
        results.append(sync_one_repo(root, entry, dry_run=args.dry_run))
    write_manifest(root, records, results)
    errors = [result for result in results if result.get("last_status") == "error"]
    dirty = [result for result in results if result.get("last_status") == "dirty"]
    print(f"Synced {len(results)} upstream repo(s): {len(errors)} error(s), {len(dirty)} dirty skipped.")
    for result in errors + dirty:
        print(f"{result['last_status'].upper()}: {result['url']} - {result.get('message', '')}")
    return 1 if errors else 0


def command_sync(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    ensure_structure(root)
    records = load_sources(root)
    for record in records:
        if record.metadata and not args.no_hash:
            update_hashes(record)
        if record.metadata:
            ensure_summary_html(record, dry_run=args.dry_run)
    records = load_sources(root)
    render_issues: list[Issue] = []
    for record in records:
        if record.metadata:
            render_issues.extend(render_reading_pages(record, dry_run=args.dry_run))
            render_issues.extend(render_key_pages(record, dry_run=args.dry_run))
    records = load_sources(root)
    for issue in render_issues:
        records.append(SourceRecord("render-pages", root, root / MANIFEST_NAME, {}, [issue]))
    entries = collect_repo_entries([record for record in records if record.metadata])
    results = [sync_one_repo(root, entry, dry_run=args.dry_run) for entry in entries]
    write_manifest(root, records, results)
    errors = [issue for issue in render_issues if issue.level == "error"]
    errors.extend(Issue("error", result.get("message", ""), result.get("wrapper_path")) for result in results if result.get("last_status") == "error")
    print(
        f"Sync complete: {len(records)} source record(s), {len(results)} upstream repo(s), "
        f"{len(errors)} error(s)."
    )
    for issue in errors:
        location = f" [{issue.path}]" if issue.path else ""
        print(f"ERROR: {issue.message}{location}")
    return 1 if errors else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sync Reference_sources, reading images, summaries, and upstream wrappers.")
    parser.add_argument(
        "command",
        choices=["init", "validate", "render-pages", "sync-upstream", "sync"],
        help="Operation to run.",
    )
    parser.add_argument("--root", default=".", help="Project root containing Reference_sources and upstream.")
    parser.add_argument("--dry-run", action="store_true", help="Print external operations without running them.")
    parser.add_argument("--no-hash", action="store_true", help="Skip local file sha256 updates.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    handlers = {
        "init": command_init,
        "validate": command_validate,
        "render-pages": command_render_pages,
        "sync-upstream": command_sync_upstream,
        "sync": command_sync,
    }
    return handlers[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
