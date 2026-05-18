from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import Settings


def now() -> datetime:
    return datetime.now().astimezone()


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return cleaned[:80] or "item"


def unique_stem(prefix: str) -> str:
    ts = now().strftime("%Y-%m-%dT%H-%M-%S-%f")
    digest = hashlib.sha1(f"{ts}-{prefix}".encode("utf-8")).hexdigest()[:8]
    return f"{ts}-{slugify(prefix)}-{digest}"


def ensure_dirs(settings: Settings) -> None:
    dirs = [
        settings.inbox_dir,
        settings.imports_dir,
        settings.processed_dir,
        settings.rejected_dir,
        settings.sources_dir,
        settings.assets_dir,
        settings.wiki_dir,
        settings.wiki_sources_dir,
        settings.wiki_entities_dir,
        settings.wiki_concepts_dir,
        settings.wiki_projects_dir,
        settings.wiki_repositories_dir,
        settings.wiki_answers_dir,
        settings.wiki_recipes_dir,
        settings.wiki_syntheses_dir,
        settings.wiki_templates_dir,
        settings.query_pending_dir,
        settings.query_running_dir,
        settings.query_done_dir,
        settings.query_failed_dir,
        settings.ingest_pending_dir,
        settings.ingest_running_dir,
        settings.ingest_done_dir,
        settings.ingest_failed_dir,
        settings.lint_pending_dir,
        settings.lint_running_dir,
        settings.lint_done_dir,
        settings.lint_failed_dir,
        settings.telegram_last_answer_dir,
        settings.scheduler_dir,
    ]
    for path in dirs:
        path.mkdir(parents=True, exist_ok=True)


def yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value).replace('"', '\\"')
    return f'"{text}"'


def render_yaml_line(key: str, value: Any, indent: int) -> list[str]:
    prefix = "  " * indent
    if isinstance(value, list):
        lines = [f"{prefix}{key}:"]
        if not value:
            lines[-1] += " []"
            return lines
        for item in value:
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}  - {json.dumps(item, ensure_ascii=True)}")
            else:
                lines.append(f"{prefix}  - {yaml_scalar(item)}")
        return lines
    if isinstance(value, dict):
        lines = [f"{prefix}{key}:"]
        for nested_key, nested_value in value.items():
            lines.extend(render_yaml_line(nested_key, nested_value, indent + 1))
        return lines
    return [f"{prefix}{key}: {yaml_scalar(value)}"]


def write_markdown_note(path: Path, frontmatter: dict[str, Any], body: str) -> None:
    lines = ["---"]
    for key, value in frontmatter.items():
        lines.extend(render_yaml_line(key, value, 0))
    lines.append("---")
    lines.append("")
    lines.append(body.rstrip())
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_markdown_note(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}, text
    parts = text.split("\n---\n", 1)
    if len(parts) != 2:
        return {}, text
    head, body = parts
    frontmatter_lines = head.splitlines()[1:]
    frontmatter: dict[str, Any] = {}
    current_key: str | None = None
    current_list: list[str] | None = None
    for line in frontmatter_lines:
        if not line.strip():
            continue
        if line.startswith("  - ") and current_key:
            if current_list is None:
                current_list = []
                frontmatter[current_key] = current_list
            current_list.append(line[4:].strip().strip('"'))
            continue
        if ":" in line:
            key, raw_value = line.split(":", 1)
            key = key.strip()
            raw_value = raw_value.strip()
            current_key = key
            current_list = None
            if raw_value == "[]":
                frontmatter[key] = []
            elif raw_value in {"true", "false"}:
                frontmatter[key] = raw_value == "true"
            elif raw_value == "null":
                frontmatter[key] = None
            elif raw_value.startswith('"') and raw_value.endswith('"'):
                frontmatter[key] = raw_value[1:-1].replace('\\"', '"')
            elif raw_value:
                frontmatter[key] = raw_value
            else:
                frontmatter[key] = []
    return frontmatter, body.strip()


def append_log(settings: Settings, entry_type: str, title: str, lines: list[str]) -> None:
    log_path = settings.wiki_dir / "log.md"
    existing = log_path.read_text(encoding="utf-8") if log_path.exists() else "# Wiki Log\n"
    block = [f"## [{now().date().isoformat()}] {entry_type} | {title}", ""]
    block.extend(lines)
    block.append("")
    log_path.write_text(existing.rstrip() + "\n\n" + "\n".join(block), encoding="utf-8")


def insert_index_entry(settings: Settings, section: str, entry: str) -> None:
    index_path = settings.wiki_dir / "index.md"
    if not index_path.exists():
        index_path.write_text("# Wiki Index\n\n", encoding="utf-8")
    lines = index_path.read_text(encoding="utf-8").splitlines()
    section_header = f"## {section}"
    if section_header not in lines:
        lines.extend(["", section_header, "", entry])
        index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return
    updated: list[str] = []
    inserted = False
    for idx, line in enumerate(lines):
        updated.append(line)
        if line == section_header:
            next_line = lines[idx + 1] if idx + 1 < len(lines) else ""
            if next_line != "":
                updated.append("")
            updated.append(entry)
            inserted = True
    if not inserted:
        updated.extend(["", section_header, "", entry])
    index_path.write_text("\n".join(updated) + "\n", encoding="utf-8")


def save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
