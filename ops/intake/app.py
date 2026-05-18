from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from twilio.request_validator import RequestValidator

from llm_wiki.automation import save_last_answer
from llm_wiki.config import Settings
from llm_wiki.fs import ensure_dirs, now, unique_stem, write_markdown_note
from llm_wiki.jobs import create_ingest_job, create_query_job, count_jobs, newest_job
from llm_wiki.telegram import chat_allowed, download_file, send_message


settings = Settings()
app = FastAPI(title="llm-wiki intake")


def normalize_url(url: str) -> str:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"}:
        raise HTTPException(status_code=400, detail=f"Unsupported URL: {url}")
    return url.strip()


def require_shared_token(token: str | None) -> None:
    if not settings.shared_token:
        raise HTTPException(status_code=500, detail="Shared token not configured")
    if token != settings.shared_token:
        raise HTTPException(status_code=401, detail="Invalid token")


def save_upload(upload: UploadFile, stem: str) -> str:
    suffix = Path(upload.filename or "").suffix or ".bin"
    dest = settings.assets_dir / f"{stem}{suffix}"
    with dest.open("wb") as handle:
        while True:
            chunk = upload.file.read(1024 * 1024)
            if not chunk:
                break
            handle.write(chunk)
    return str(dest.relative_to(settings.app_root))


def write_inbox_note(
    title: str,
    *,
    origin: str,
    source_type: str,
    body: str,
    source_urls: list[str] | None = None,
    attachments: list[str] | None = None,
    tags: list[str] | None = None,
    extra: dict[str, object] | None = None,
) -> Path:
    stem = unique_stem(title)
    note_path = settings.inbox_dir / f"{stem}.md"
    frontmatter = {
        "title": title,
        "created": now().isoformat(),
        "origin": origin,
        "status": "inbox",
        "source_type": source_type,
        "source_urls": source_urls or [],
        "attachments": attachments or [],
        "tags": tags or [],
    }
    if extra:
        frontmatter.update(extra)
    write_markdown_note(note_path, frontmatter, body)
    return note_path


def format_status() -> str:
    latest_ingest = newest_job(settings.ingest_done_dir)
    latest_ingest_at = latest_ingest.get("done_at", "never") if latest_ingest else "never"
    latest_lint = newest_job(settings.lint_done_dir)
    latest_lint_at = latest_lint.get("done_at", "never") if latest_lint else "never"
    failed_query = newest_job(settings.query_failed_dir)
    failed_text = failed_query.get("error", "none") if failed_query else "none"
    return "\n".join(
        [
            f"Inbox: {len(list(settings.inbox_dir.glob('*.md')))} pending",
            f"Query jobs: {count_jobs(settings.query_pending_dir)} pending / {count_jobs(settings.query_running_dir)} running",
            f"Ingest jobs: {count_jobs(settings.ingest_pending_dir)} pending / {count_jobs(settings.ingest_running_dir)} running",
            f"Refinement jobs: {count_jobs(settings.lint_pending_dir)} pending / {count_jobs(settings.lint_running_dir)} running",
            f"Last ingest: {latest_ingest_at}",
            f"Last refinement: {latest_lint_at}",
            f"Last query error: {failed_text}",
        ]
    )


def latest_log_summary(limit: int = 5) -> str:
    log_path = settings.wiki_dir / "log.md"
    if not log_path.exists():
        return "No wiki log is available yet."
    entries = [line for line in log_path.read_text(encoding="utf-8").splitlines() if line.startswith("## [")]
    tail = entries[-limit:]
    if not tail:
        return "No log entries yet."
    return "Recent activity:\n" + "\n".join(f"- {line[3:]}" for line in tail)


def help_text() -> str:
    return "\n".join(
        [
            "Commands:",
            "/ask <question> - query the wiki",
            "/note <text> - save a note to inbox",
            "/link <url> - save a link to inbox",
            "/ingest - queue inbox processing",
            "/latest - show recent wiki activity",
            "/status - show queue status",
            "/save - save the last answer into wiki/answers",
            "/help - show this help",
        ]
    )


def extract_telegram_message(update: dict) -> dict | None:
    return update.get("message") or update.get("edited_message")


def capture_telegram_message(message: dict) -> tuple[Path, list[str]]:
    text = message.get("text") or message.get("caption") or ""
    urls = []
    for entity in message.get("entities") or []:
        if entity.get("type") == "url":
            offset = entity["offset"]
            length = entity["length"]
            urls.append(normalize_url(text[offset : offset + length]))
    attachments: list[str] = []
    stem = unique_stem(text[:40] or "telegram")
    document = message.get("document")
    if document:
        content, file_path = download_file(settings, document["file_id"])
        suffix = Path(file_path).suffix or ".bin"
        target = settings.assets_dir / f"{stem}{suffix}"
        target.write_bytes(content)
        attachments.append(str(target.relative_to(settings.app_root)))
    photo = message.get("photo")
    if photo:
        content, file_path = download_file(settings, photo[-1]["file_id"])
        suffix = Path(file_path).suffix or ".jpg"
        target = settings.assets_dir / f"{stem}{suffix}"
        target.write_bytes(content)
        attachments.append(str(target.relative_to(settings.app_root)))
    note_path = write_inbox_note(
        title=text[:80] or "telegram-capture",
        origin="telegram",
        source_type="message",
        source_urls=urls,
        attachments=attachments,
        body=text.strip() or "Captured from Telegram.",
        extra={
            "telegram_chat_id": str(message["chat"]["id"]),
            "telegram_message_id": message["message_id"],
        },
    )
    return note_path, attachments


@app.on_event("startup")
def startup() -> None:
    ensure_dirs(settings)


@app.get("/", response_class=HTMLResponse)
def form() -> str:
    return """
<!doctype html>
<html>
  <head>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>llm-wiki intake</title>
    <style>
      body { font-family: sans-serif; max-width: 720px; margin: 2rem auto; padding: 0 1rem; }
      label { display: block; margin-top: 1rem; font-weight: 600; }
      input, textarea { width: 100%; padding: 0.75rem; margin-top: 0.4rem; box-sizing: border-box; }
      button { margin-top: 1rem; padding: 0.8rem 1.2rem; }
      .hint { color: #555; font-size: 0.95rem; }
    </style>
  </head>
  <body>
    <h1>llm-wiki intake</h1>
    <p class="hint">Paste text or URLs, or upload a file from your phone.</p>
    <form method="post" action="/share" enctype="multipart/form-data">
      <label>Shared token<input name="token" type="password" required /></label>
      <label>Title<input name="title" placeholder="Optional short title" /></label>
      <label>Tags<input name="tags" placeholder="comma,separated,tags" /></label>
      <label>URLs<textarea name="urls" rows="5" placeholder="One URL per line"></textarea></label>
      <label>Text<textarea name="text" rows="8" placeholder="Paste notes, transcript snippets, or anything else"></textarea></label>
      <label>File<input name="file" type="file" /></label>
      <button type="submit">Save to inbox</button>
    </form>
  </body>
</html>
"""


@app.post("/share")
async def share(
    token: str = Form(...),
    title: str = Form(""),
    tags: str = Form(""),
    urls: str = Form(""),
    text: str = Form(""),
    file: UploadFile | None = File(None),
) -> JSONResponse:
    require_shared_token(token)
    entered_urls = [normalize_url(line) for line in urls.splitlines() if line.strip()]
    if not any([title.strip(), entered_urls, text.strip(), file]):
        raise HTTPException(status_code=400, detail="At least one of title, urls, text, or file is required")
    inferred_title = title.strip() or (entered_urls[0] if entered_urls else file.filename if file else "quick-capture")
    stem = unique_stem(inferred_title)
    attachments: list[str] = []
    if file is not None and file.filename:
        attachments.append(save_upload(file, stem))
    body_parts = []
    if entered_urls:
        body_parts.extend(["## URLs", ""])
        body_parts.extend(f"- {url}" for url in entered_urls)
        body_parts.append("")
    if text.strip():
        body_parts.extend(["## Notes", "", text.strip(), ""])
    note_path = write_inbox_note(
        title=inferred_title,
        origin="share-form",
        source_type="mixed",
        source_urls=entered_urls,
        attachments=attachments,
        tags=[item.strip() for item in tags.split(",") if item.strip()],
        body="\n".join(body_parts).strip() or "Captured via intake form.",
    )
    return JSONResponse({"ok": True, "path": str(note_path.relative_to(settings.app_root))})


@app.post("/telegram/{secret}")
async def telegram_webhook(secret: str, request: Request) -> JSONResponse:
    if not settings.telegram_webhook_secret or secret != settings.telegram_webhook_secret:
        raise HTTPException(status_code=403, detail="Forbidden")
    update = await request.json()
    message = extract_telegram_message(update)
    if not message:
        return JSONResponse({"ok": True, "ignored": "no-message"})
    chat_id = str(message["chat"]["id"])
    if not chat_allowed(settings, chat_id):
        raise HTTPException(status_code=403, detail="Chat not allowed")

    text = (message.get("text") or message.get("caption") or "").strip()
    if text.startswith("/help"):
        send_message(settings, chat_id, help_text())
        return JSONResponse({"ok": True})
    if text.startswith("/status"):
        send_message(settings, chat_id, format_status())
        return JSONResponse({"ok": True})
    if text.startswith("/latest"):
        send_message(settings, chat_id, latest_log_summary())
        return JSONResponse({"ok": True})
    if text.startswith("/save"):
        saved = save_last_answer(settings, chat_id)
        if not saved:
            send_message(settings, chat_id, "No cached answer is available to save yet.")
        else:
            send_message(settings, chat_id, f"Saved to {saved['path']}")
        return JSONResponse({"ok": True})
    if text.startswith("/ingest"):
        job = create_ingest_job(settings, origin="telegram", requested_by=chat_id)
        send_message(settings, chat_id, f"Ingest queued: {job.name}")
        return JSONResponse({"ok": True})
    if text.startswith("/ask "):
        question = text[5:].strip()
        if not question:
            send_message(settings, chat_id, "Usage: /ask <question>")
            return JSONResponse({"ok": True})
        job = create_query_job(settings, question, origin="telegram", chat_id=chat_id)
        send_message(settings, chat_id, f"Query queued: {job.name}")
        return JSONResponse({"ok": True})
    if text.startswith("/note "):
        note = text[6:].strip()
        if not note:
            send_message(settings, chat_id, "Usage: /note <text>")
            return JSONResponse({"ok": True})
        note_path = write_inbox_note(title=note[:80], origin="telegram", source_type="note", body=note)
        send_message(settings, chat_id, f"Saved note to {note_path.relative_to(settings.app_root).as_posix()}")
        return JSONResponse({"ok": True})
    if text.startswith("/link "):
        url = text[6:].strip()
        note_path = write_inbox_note(
            title=url[:80],
            origin="telegram",
            source_type="url",
            source_urls=[normalize_url(url)],
            body=f"## URLs\n\n- {normalize_url(url)}",
        )
        send_message(settings, chat_id, f"Saved link to {note_path.relative_to(settings.app_root).as_posix()}")
        return JSONResponse({"ok": True})

    note_path, attachments = capture_telegram_message(message)
    ack = f"Captured to {note_path.relative_to(settings.app_root).as_posix()}"
    if attachments:
        ack += f"\nAttachments: {', '.join(attachments)}"
    send_message(settings, chat_id, ack)
    return JSONResponse({"ok": True})


@app.post("/twilio/whatsapp")
async def twilio_whatsapp(
    request: Request,
    x_twilio_signature: str | None = Header(default=None),
) -> JSONResponse:
    if not settings.twilio_auth_token:
        raise HTTPException(status_code=400, detail="Twilio auth token not configured")
    validator = RequestValidator(settings.twilio_auth_token)
    form = dict(await request.form())
    if not validator.validate(str(request.url), form, x_twilio_signature or ""):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")
    body = form.get("Body", "").strip()
    from_number = form.get("From", "")
    note_path = write_inbox_note(
        title=body[:80] or "whatsapp-capture",
        origin="whatsapp",
        source_type="message",
        body=body or "Captured from WhatsApp.",
        extra={"whatsapp_from": from_number},
    )
    return JSONResponse({"ok": True, "path": str(note_path.relative_to(settings.app_root))})


@app.get("/healthz")
def healthz() -> JSONResponse:
    return JSONResponse({"ok": True})
