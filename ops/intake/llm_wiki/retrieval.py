from __future__ import annotations

import re
from pathlib import Path

from .config import Settings


def query_terms(question: str) -> list[str]:
    terms = re.findall(r"[a-zA-Z0-9_]{3,}", question.lower())
    return [term for term in terms if term not in {"what", "about", "with", "from", "this", "that", "have"}]


def score_document(path: Path, terms: list[str]) -> tuple[int, list[str]]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    lower = text.lower()
    score = 0
    excerpts: list[str] = []
    for term in terms:
        hits = lower.count(term)
        score += hits
        if hits and len(excerpts) < 2:
            idx = lower.find(term)
            start = max(0, idx - 120)
            end = min(len(text), idx + 220)
            excerpt = text[start:end].replace("\n", " ").strip()
            excerpts.append(excerpt)
    return score, excerpts


def fallback_query(settings: Settings, question: str) -> dict[str, object]:
    terms = query_terms(question)
    candidates = sorted(settings.wiki_dir.rglob("*.md"))
    scored: list[tuple[int, Path, list[str]]] = []
    for path in candidates:
        score, excerpts = score_document(path, terms)
        if score > 0:
            scored.append((score, path, excerpts))
    scored.sort(key=lambda item: item[0], reverse=True)
    top = scored[:3]
    if not top:
        return {
            "reply_markdown": (
                "I could not find a strong match in the current wiki yet. "
                "If this came in recently, it may still be waiting in raw/inbox/ for ingest."
            ),
            "citations": ["wiki/index.md", "wiki/log.md"],
            "save_candidate": False,
        }
    lines = []
    citations = []
    for _, path, excerpts in top:
        rel = path.relative_to(settings.app_root).as_posix()
        citations.append(rel)
        if excerpts:
            lines.append(f"- {rel}: {excerpts[0]}")
    summary = "Here are the closest matches I found in the current wiki:\n\n" + "\n".join(lines)
    return {"reply_markdown": summary, "citations": citations, "save_candidate": False}
