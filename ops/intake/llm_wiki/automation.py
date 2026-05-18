from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Any

from .config import Settings
from .fs import (
    append_log,
    insert_index_entry,
    load_json,
    now,
    parse_markdown_note,
    save_json,
    slugify,
    unique_stem,
    write_markdown_note,
)
from .retrieval import fallback_query


def run_openclaw_command(settings: Settings, command: str, job_path: Path, output_path: Path) -> dict[str, Any] | None:
    env = os.environ.copy()
    env.update(
        {
            "LLM_WIKI_ROOT": str(settings.app_root),
            "LLM_WIKI_JOB_FILE": str(job_path),
            "LLM_WIKI_OUTPUT_FILE": str(output_path),
        }
    )
    result = subprocess.run(command, shell=True, cwd=settings.app_root, env=env, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {result.stderr.strip() or result.stdout.strip()}")
    if not output_path.exists():
        return None
    return load_json(output_path)


def process_query(settings: Settings, job_path: Path) -> dict[str, Any]:
    output_path = settings.query_running_dir / f"{job_path.stem}-output.json"
    payload = load_json(job_path)
    if settings.openclaw_query_command:
        try:
            output = run_openclaw_command(settings, settings.openclaw_query_command, job_path, output_path)
            if output:
                return output
        except Exception as exc:
            fallback = fallback_query(settings, payload["question"])
            fallback["reply_markdown"] = (
                "The external query agent failed, so I used local fallback retrieval instead.\n\n"
                f"Error: {exc}\n\n{fallback['reply_markdown']}"
            )
            return fallback
    return fallback_query(settings, payload["question"])


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if value is None:
        return []
    text = str(value).strip()
    return [text] if text else []


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return cleaned[:80] or "item"


def _infer_domains(title: str, body: str, tags: list[str], source_urls: list[str]) -> list[str]:
    haystack = "\n".join([title, body, " ".join(tags), " ".join(source_urls)]).lower()
    rules = {
        "ai": [" ai ", "llm", "model", "agent", "openai", "anthropic", "prompt", "inference", "rag", "codex"],
        "finance": ["finance", "invest", "portfolio", "market", "valuation", "earnings", "fed", "macro"],
        "crypto": ["crypto", "bitcoin", "btc", "ethereum", "eth", "solana", "sol", "stablecoin", "defi", "token"],
        "retirement": ["retirement", "401k", "ira", "roth", "pension", "withdrawal rate"],
        "tax": ["tax", "irs", "deduction", "capital gains", "1099", "w-2", "write-off"],
        "cooking": ["recipe", "ingredients", "cook", "cooking", "bake", "fry", "kitchen"],
        "software": ["github", "repository", "repo", "architecture", "readme", "deployment", "runbook"],
    }
    domains = []
    padded = f" {haystack} "
    for domain, needles in rules.items():
        if any(needle in padded or needle in haystack for needle in needles):
            domains.append(domain)
    return domains


def _infer_tickers(title: str, body: str, tags: list[str]) -> list[str]:
    haystack = "\n".join([title, body, " ".join(tags)])
    tickers = set(re.findall(r"\$([A-Z]{1,6})\b", haystack))
    aliases = {
        "btc": "BTC",
        "bitcoin": "BTC",
        "eth": "ETH",
        "ethereum": "ETH",
        "sol": "SOL",
        "solana": "SOL",
        "spy": "SPY",
        "qqq": "QQQ",
        "tsla": "TSLA",
        "nvda": "NVDA",
        "msft": "MSFT",
        "goog": "GOOG",
        "googl": "GOOGL",
        "amzn": "AMZN",
        "meta": "META",
        "aapl": "AAPL",
    }
    lower = haystack.lower()
    for needle, ticker in aliases.items():
        if re.search(rf"\b{re.escape(needle)}\b", lower):
            tickers.add(ticker)
    return sorted(tickers)


def _detect_content_type(title: str, body: str, tags: list[str], source_type: str, source_urls: list[str]) -> str:
    lower_tags = {tag.lower() for tag in tags}
    lower_title = title.lower()
    lower_body = body.lower()
    joined_urls = " ".join(source_urls).lower()
    if "youtube.com" in joined_urls or "youtu.be" in joined_urls:
        if {"recipe", "cooking", "ingredients", "kitchen"} & lower_tags or any(term in lower_title or term in lower_body for term in ["recipe", "ingredients", "cook", "cooking"]):
            return "recipe_video"
        return "youtube_video"
    if "x.com" in joined_urls or "twitter.com" in joined_urls:
        return "x_post"
    if "github.com" in joined_urls:
        return "github_repo"
    if "reddit.com" in joined_urls:
        return "reddit_post"
    if "linkedin.com" in joined_urls:
        return "linkedin_post"
    if {"repo", "repository", "architecture", "readme"} & lower_tags:
        return "project_repo"
    if {"recipe", "cooking", "ingredients", "kitchen"} & lower_tags:
        return "recipe"
    if source_type == "url":
        return "web_page"
    return source_type or "unknown"


def _looks_like_recipe(title: str, body: str, tags: list[str], content_type: str) -> bool:
    lower_tags = {tag.lower() for tag in tags}
    haystack = f"{title}\n{body}".lower()
    if content_type in {"recipe", "recipe_video", "cooking_video"}:
        return True
    if {"recipe", "cooking", "ingredients", "kitchen"} & lower_tags:
        return True
    return any(term in haystack for term in ["ingredients", "recipe", "cook", "cooking", "marinate", "simmer", "bake", "fry"])


def _looks_like_repository(title: str, body: str, tags: list[str], content_type: str, source_urls: list[str]) -> bool:
    lower_tags = {tag.lower() for tag in tags}
    haystack = f"{title}\n{body}".lower()
    joined_urls = " ".join(source_urls).lower()
    if content_type in {"github_repo", "project_repo", "repo_doc"}:
        return True
    if "github.com" in joined_urls:
        return True
    if {"repo", "repository", "architecture", "readme", "runbook", "ops"} & lower_tags:
        return True
    return any(term in haystack for term in ["repository", "repo", "architecture", "readme", "deployment", "operator", "runbook"])


def _ensure_repository_page(settings: Settings, title: str, source_note_rel: str, wiki_source_rel: str, tags: list[str], source_language: str | None, translation_languages: list[str], domains: list[str], content_type: str) -> str:
    rel_path = f"wiki/repositories/{_slug(title)}.md"
    page_path = settings.app_root / rel_path
    if page_path.exists():
        return rel_path
    page_content_type = content_type if content_type in {"github_repo", "project_repo", "repo_doc"} else "project_repo"
    frontmatter = {
        "title": title,
        "kind": "repository",
        "status": "draft",
        "updated": now().date().isoformat(),
        "sources": [wiki_source_rel, source_note_rel],
        "relationships": {
            "extracted": [wiki_source_rel],
            "inferred": [],
            "ambiguous": [],
        },
        "tags": sorted(set(tags + ["repository"])),
        "content_type": page_content_type,
        "source_language": source_language,
        "translation_languages": translation_languages or ([source_language] if source_language else []),
        "domains": domains,
        "tickers": [],
        "confidence": "low",
        "last_verified": now().date().isoformat(),
        "supersedes": [],
        "translation_of": None,
    }
    body = "\n".join([
        f"# {title}",
        "",
        "## Purpose",
        "",
        "Fallback-created repository page. Needs agent review of repo purpose and why it matters.",
        "",
        "## Current State",
        "",
        "## Architecture",
        "",
        "## Interfaces And Entry Points",
        "",
        "## Operations",
        "",
        "## Key Files And Directories",
        "",
        "- Add important paths here after repo inspection.",
        "",
        "## Decisions",
        "",
        "## Related Sources",
        "",
        f"- `{wiki_source_rel}`",
        "",
        "## Change Tracking",
        "",
        f"- [{now().date().isoformat()}] Repository page created from `{wiki_source_rel}`.",
        "",
        "## Open Questions",
        "",
        "## Timeline",
        "",
        f"- [{now().date().isoformat()}] Initial repository page created.",
    ])
    write_markdown_note(page_path, frontmatter, body)
    insert_index_entry(settings, "Repositories", f"- [{page_path.name}](/home/linuxuser/projects/llm-wiki/{rel_path}) - Repository knowledge awaiting enrichment.")
    return rel_path


def _ensure_recipe_page(settings: Settings, title: str, source_note_rel: str, wiki_source_rel: str, tags: list[str], source_language: str | None, translation_languages: list[str]) -> str:
    rel_path = f"wiki/recipes/{_slug(title)}.md"
    page_path = settings.app_root / rel_path
    if page_path.exists():
        return rel_path
    frontmatter = {
        "title": title,
        "kind": "recipe",
        "status": "draft",
        "updated": now().date().isoformat(),
        "sources": [wiki_source_rel, source_note_rel],
        "relationships": {
            "extracted": [wiki_source_rel],
            "inferred": [],
            "ambiguous": [],
        },
        "tags": sorted(set(tags + ["recipe"])),
        "content_type": "recipe_video",
        "source_language": source_language,
        "translation_languages": translation_languages or ([source_language] if source_language else []),
        "confidence": "low",
        "last_verified": now().date().isoformat(),
        "supersedes": [],
        "translation_of": None,
    }
    body = "\n".join([
        f"# {title}",
        "",
        "## Language And Coverage",
        "",
        f"- Source language: {source_language or 'unknown'}",
        f"- Translation languages: {', '.join(translation_languages) if translation_languages else 'none recorded'}",
        "",
        "## Summary",
        "",
        "Fallback-created recipe page. Needs agent extraction of ingredients, methods, timing, and notes.",
        "",
        "## Ingredients",
        "",
        "- None extracted yet.",
        "",
        "## Methods",
        "",
        "1. Review the source and extract the cooking steps.",
        "",
        "## Equipment",
        "",
        "## Timing",
        "",
        "## Notes And Variations",
        "",
        "## Source Language Terms",
        "",
        "## Related Concepts",
        "",
        "## Timeline",
        "",
        f"- [{now().date().isoformat()}] Recipe page created from `{wiki_source_rel}`.",
    ])
    write_markdown_note(page_path, frontmatter, body)
    insert_index_entry(settings, "Recipes", f"- [{page_path.name}](/home/linuxuser/projects/llm-wiki/{rel_path}) - Structured cooking knowledge awaiting enrichment.")
    return rel_path


def _ensure_concept_page(settings: Settings, tag: str) -> str:
    rel_path = f"wiki/concepts/{_slug(tag)}.md"
    page_path = settings.app_root / rel_path
    if page_path.exists():
        return rel_path
    frontmatter = {
        "title": tag,
        "kind": "concept",
        "status": "draft",
        "updated": now().date().isoformat(),
        "sources": [],
        "relationships": {
            "extracted": [],
            "inferred": [],
            "ambiguous": [],
        },
        "tags": [tag],
    }
    body = "\n".join(
        [
            f"# {tag}",
            "",
            "## Summary",
            "",
            "Fallback-created concept page based on intake tags. Needs agent review and expansion.",
            "",
            "## Key Claims",
            "",
            "## Evidence",
            "",
            "## Related Entities",
            "",
            "## Related Projects",
            "",
            "## Contradictions Or Tensions",
        ]
    )
    write_markdown_note(page_path, frontmatter, body)
    insert_index_entry(
        settings,
        "Concepts",
        f"- [{page_path.name}](/home/linuxuser/projects/llm-wiki/{rel_path}) - Tag-derived concept page awaiting enrichment.",
    )
    return rel_path


def _related_existing_pages(settings: Settings, title: str, body: str, tags: list[str]) -> list[str]:
    candidate_dirs = [
        settings.wiki_dir / "entities",
        settings.wiki_dir / "concepts",
        settings.wiki_dir / "projects",
        settings.wiki_dir / "repositories",
        settings.wiki_dir / "recipes",
    ]
    terms = {_slug(title)}
    terms.update(_slug(tag) for tag in tags if tag.strip())
    terms.update(token for token in re.findall(r"[a-zA-Z0-9_]{4,}", body.lower())[:50])
    related: list[str] = []
    for directory in candidate_dirs:
        if not directory.exists():
            continue
        for path in sorted(directory.glob("*.md")):
            if path.name == ".gitkeep":
                continue
            path_terms = {_slug(path.stem)}
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
            if any(term and (term in path_terms or term in text) for term in terms):
                rel_path = path.relative_to(settings.app_root).as_posix()
                if rel_path not in related:
                    related.append(rel_path)
    return related


def ingest_one_note(settings: Settings, note_path: Path) -> dict[str, Any]:
    frontmatter, body = parse_markdown_note(note_path)
    title = str(frontmatter.get("title") or note_path.stem)
    source_stem = unique_stem(title)
    source_note = settings.sources_dir / f"{source_stem}.md"
    wiki_note = settings.wiki_sources_dir / f"{source_stem}.md"
    attachments = _string_list(frontmatter.get("attachments"))
    source_urls = _string_list(frontmatter.get("source_urls"))
    tags = _string_list(frontmatter.get("tags"))
    source_type = str(frontmatter.get("source_type") or "unknown")
    source_language = frontmatter.get("source_language")
    translation_languages = _string_list(frontmatter.get("translation_languages"))
    domains = _string_list(frontmatter.get("domains")) or _infer_domains(title, body, tags, source_urls)
    tickers = _string_list(frontmatter.get("tickers")) or _infer_tickers(title, body, tags)
    content_type = str(frontmatter.get("content_type") or _detect_content_type(title, body, tags, source_type, source_urls))
    confidence = str(frontmatter.get("confidence") or "low")
    last_verified = str(frontmatter.get("last_verified") or now().date().isoformat())
    source_frontmatter = {
        "title": title,
        "created": now().isoformat(),
        "status": "accepted",
        "ingested_from": str(note_path.relative_to(settings.app_root)),
        "origin": frontmatter.get("origin", "unknown"),
        "source_type": source_type,
        "content_type": content_type,
        "source_language": source_language,
        "translation_languages": translation_languages,
        "domains": domains,
        "tickers": tickers,
        "confidence": confidence,
        "last_verified": last_verified,
        "source_urls": source_urls,
        "attachments": attachments,
        "tags": tags,
        "content_type": content_type,
        "source_language": source_language,
        "translation_languages": translation_languages,
        "domains": domains,
        "tickers": tickers,
        "confidence": confidence,
        "last_verified": last_verified,
        "supersedes": [],
        "translation_of": None,
    }
    source_body_lines = [
        "## Source Record",
        "",
        f"- Title: {title}",
        f"- Origin: {frontmatter.get('origin', 'unknown')}",
        f"- Source type: {source_type}",
        f"- Content type: {content_type}",
        f"- Source language: {source_language or 'unknown'}",
        f"- Confidence: {confidence}",
        f"- Last verified: {last_verified}",
        f"- Domains: {", ".join(domains) if domains else "none recorded"}",
        f"- Tickers: {", ".join(tickers) if tickers else "none recorded"}",
        f"- Content type: {content_type}",
        "",
    ]
    if source_language:
        source_body_lines.append(f"- Source language: {source_language}")
    if translation_languages:
        source_body_lines.append(f"- Translation languages: {", ".join(translation_languages)}")
    if domains:
        source_body_lines.append(f"- Domains: {", ".join(domains)}")
    if tickers:
        source_body_lines.append(f"- Tickers: {", ".join(tickers)}")
    source_body_lines.append("")
    if source_urls:
        source_body_lines.extend(["## URLs", ""])
        source_body_lines.extend(f"- {url}" for url in source_urls)
        source_body_lines.append("")
    if attachments:
        source_body_lines.extend(["## Attachments", ""])
        source_body_lines.extend(f"- `{attachment}`" for attachment in attachments)
        source_body_lines.append("")
    source_body_lines.extend(
        [
            "## Captured Content",
            "",
            body or "No additional body content was captured.",
        ]
    )
    source_body = "\n".join(source_body_lines)
    write_markdown_note(source_note, source_frontmatter, source_body)

    tag_concepts = [_ensure_concept_page(settings, tag) for tag in tags]
    related_pages = _related_existing_pages(settings, title, body, tags)
    for concept_rel in tag_concepts:
        if concept_rel not in related_pages:
            related_pages.append(concept_rel)

    if _looks_like_recipe(title, body, tags, content_type):
        recipe_rel = _ensure_recipe_page(
            settings,
            title,
            str(source_note.relative_to(settings.app_root)),
            str(wiki_note.relative_to(settings.app_root)),
            tags,
            source_language if isinstance(source_language, str) and source_language else None,
            translation_languages,
        )
        if recipe_rel not in related_pages:
            related_pages.append(recipe_rel)

    if _looks_like_repository(title, body, tags, content_type, source_urls):
        repository_rel = _ensure_repository_page(
            settings,
            title,
            str(source_note.relative_to(settings.app_root)),
            str(wiki_note.relative_to(settings.app_root)),
            tags,
            source_language if isinstance(source_language, str) and source_language else None,
            translation_languages,
            domains,
            content_type,
        )
        if repository_rel not in related_pages:
            related_pages.append(repository_rel)

    wiki_frontmatter = {
        "title": title,
        "kind": "source",
        "status": "draft",
        "updated": now().date().isoformat(),
        "sources": [str(source_note.relative_to(settings.app_root))],
        "relationships": {
            "extracted": [],
            "inferred": related_pages,
            "ambiguous": [],
        },
        "tags": tags,
    }
    summary_line = "Fallback ingest created this normalized source page. It still needs agent enrichment."
    key_points = [
        f"- Origin: {frontmatter.get('origin', 'unknown')}",
        f"- Source type: {source_type}",
        f"- Content type: {content_type}",
    ]
    if source_urls:
        key_points.append(f"- Captured URLs: {len(source_urls)}")
    if attachments:
        key_points.append(f"- Attachments: {len(attachments)}")
    if tags:
        key_points.append(f"- Tags: {', '.join(tags)}")

    wiki_body_lines = [
        f"# {title}",
        "",
        "## Source Record",
        "",
        f"- Source note: [{source_note.name}](/home/linuxuser/projects/llm-wiki/{source_note.relative_to(settings.app_root).as_posix()})",
        f"- Origin: {frontmatter.get('origin', 'unknown')}",
        f"- Source type: {source_type}",
        f"- Content type: {content_type}",
        "",
        "## Summary",
        "",
        summary_line,
        "",
        "## Key Points",
        "",
        *key_points,
        "",
        "## Structured Extraction",
        "",
        "- Add ingredients, methods, entities, procedures, repo structure, or claim breakdowns here when the agent extracts them.",
        "",
        "## Market Or Domain Signals",
        "",
        f"- Domains: {", ".join(domains) if domains else "none recorded"}",
        f"- Tickers: {", ".join(tickers) if tickers else "none recorded"}",
        "- Why this matters:",
        "",
        "## Relationships",
        "",
        "### Extracted",
        "",
        "- None yet.",
        "",
        "### Inferred",
        "",
    ]
    if related_pages:
        wiki_body_lines.extend(
            f"- `{rel_path}`" for rel_path in related_pages
        )
    else:
        wiki_body_lines.append("- None yet.")
    wiki_body_lines.extend(
        [
            "",
            "### Ambiguous",
            "",
            "- None yet.",
            "",
            "## Open Questions",
            "",
            "- What is the most important durable takeaway from this source?",
            "- Which existing entities, concepts, or projects should be updated?",
            "- Does this source confirm, contradict, or extend existing pages?",
        ]
    )
    write_markdown_note(wiki_note, wiki_frontmatter, "\n".join(wiki_body_lines))

    processed_note = settings.processed_dir / note_path.name
    note_path.rename(processed_note)

    rel_wiki = wiki_note.relative_to(settings.app_root).as_posix()
    insert_index_entry(settings, "Sources", f"- [{wiki_note.name}](/home/linuxuser/projects/llm-wiki/{rel_wiki}) - Captured source awaiting or containing synthesis.")
    append_log(
        settings,
        "ingest",
        title,
        [
            f"- accepted from `{processed_note.relative_to(settings.app_root).as_posix()}`",
            f"- source note: `{source_note.relative_to(settings.app_root).as_posix()}`",
            f"- wiki page: `{rel_wiki}`",
            f"- inferred links: {', '.join(f'`{item}`' for item in related_pages) if related_pages else 'none'}",
        ],
    )
    return {
        "title": title,
        "source_note": str(source_note.relative_to(settings.app_root)),
        "wiki_note": rel_wiki,
        "processed_note": str(processed_note.relative_to(settings.app_root)),
        "linked_pages": related_pages,
    }



def process_ingest(settings: Settings, job_path: Path) -> dict[str, Any]:
    output_path = settings.ingest_running_dir / f"{job_path.stem}-output.json"
    if settings.openclaw_ingest_command:
        try:
            output = run_openclaw_command(settings, settings.openclaw_ingest_command, job_path, output_path)
            if output:
                return output
        except Exception as exc:
            append_log(
                settings,
                "maintenance",
                "ingest fallback triggered",
                [f"- external ingest command failed: {exc}", "- using local fallback ingest"],
            )
    processed: list[dict[str, Any]] = []
    pending_notes = sorted(settings.inbox_dir.glob("*.md"))
    for note_path in pending_notes[:5]:
        processed.append(ingest_one_note(settings, note_path))
    if not processed:
        return {"summary": "No inbox items were pending.", "processed": []}
    summary = f"Processed {len(processed)} inbox item(s) into source and wiki records."
    return {"summary": summary, "processed": processed}


def process_lint(settings: Settings, job_path: Path) -> dict[str, Any]:
    output_path = settings.lint_running_dir / f"{job_path.stem}-output.json"
    if settings.openclaw_lint_command:
        try:
            output = run_openclaw_command(settings, settings.openclaw_lint_command, job_path, output_path)
            if output:
                return output
        except Exception as exc:
            append_log(
                settings,
                "maintenance",
                "lint fallback triggered",
                [f"- external lint command failed: {exc}", "- using local fallback lint summary"],
            )

    payload = load_json(job_path)
    focus_paths = payload.get("focus_paths") or []
    if focus_paths:
        summary = f"No external lint command result; kept targeted lint job over {len(focus_paths)} focus path(s) for later re-run."
    else:
        summary = "No external lint command result; no durable lint changes were made."
    return {"summary": summary, "touched": []}


def save_last_answer(settings: Settings, chat_id: str) -> dict[str, Any] | None:
    cache_path = settings.telegram_last_answer_dir / f"{chat_id}.json"
    if not cache_path.exists():
        return None
    cached = load_json(cache_path)
    title = cached.get("title") or "telegram-answer"
    stem = unique_stem(f"answer-{title}")
    answer_path = settings.wiki_dir / "answers" / f"{stem}.md"
    frontmatter = {
        "title": title,
        "kind": "answer",
        "status": "published",
        "updated": now().date().isoformat(),
        "sources": cached.get("citations", []),
        "origin": "telegram-save",
    }
    body_lines = [
        cached["reply_markdown"],
        "",
        "## Citations",
        "",
    ]
    for citation in cached.get("citations", []):
        body_lines.append(f"- `{citation}`")
    write_markdown_note(answer_path, frontmatter, "\n".join(body_lines))
    rel = answer_path.relative_to(settings.app_root).as_posix()
    insert_index_entry(settings, "Answers", f"- [{answer_path.name}](/home/linuxuser/projects/llm-wiki/{rel}) - Saved Telegram answer.")
    append_log(settings, "query", title, [f"- saved answer: `{rel}`"])
    return {"path": rel}


def cache_answer(settings: Settings, chat_id: str, question: str, result: dict[str, Any]) -> None:
    save_json(
        settings.telegram_last_answer_dir / f"{chat_id}.json",
        {
            "title": question[:80],
            "question": question,
            "reply_markdown": result["reply_markdown"],
            "citations": result.get("citations", []),
            "cached_at": now().isoformat(),
        },
    )
