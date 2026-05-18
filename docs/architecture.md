# Architecture

## Goal

Run a low-maintenance shared knowledge system on a VPS where:

- you can add content from phone or laptop
- you can chat with agents in a browser or messaging app
- agents can read and update the wiki directly
- all durable knowledge lives as files in this project

## Services

### 1. Markdown-first wiki layer

Purpose:

- keep the knowledge base as plain markdown files
- allow use from Obsidian now
- preserve the option for a custom webapp later
- let agents edit the same durable files directly

Why:

- stores content as plain files
- no separate database to manage
- good fit for the "wiki as codebase" model

### 2. Open WebUI

Purpose:

- browser chat interface for Codex/OpenClaw-style sessions
- human-to-agent collaboration surface

Why:

- easy self-host
- mobile-friendly enough for routine use
- lets you connect local or API-backed models

### 3. Intake service

Purpose:

- single mobile-friendly share endpoint
- accepts pasted text, URLs, and file uploads
- receives Telegram updates
- optionally receives WhatsApp updates via Twilio webhook
- exposes the thin Telegram bot command surface

Why:

- reduces friction for adding content
- normalizes inbound items into filesystem records
- avoids building a full custom application

### 4. Maintainer worker

Purpose:

- process queued Telegram `/ask` requests
- process scheduled or requested inbox ingest jobs
- call external OpenClaw commands when configured
- fall back to local file search and placeholder ingest behavior when not configured

Why:

- keeps Telegram/webhook handling fast
- separates synchronous capture from slower agent work
- provides a stable automation seam for OpenClaw integration

## Data flow

```text
Phone/Laptop share
  -> intake service
  -> raw/inbox/ or raw/assets/
  -> agent ingest pass
  -> raw/sources/
  -> wiki/
  -> git commit
```

```text
Question in Open WebUI or Telegram
  -> query job in ops/state/queries/ or direct Open WebUI agent task
  -> agent reads wiki/index.md
  -> agent reads relevant pages
  -> answer in chat
  -> optional durable writeback to wiki/answers/ or wiki/syntheses/
```

```text
Telegram /ask or /ingest
  -> intake service writes job file under ops/state/
  -> maintainer worker picks up job
  -> OpenClaw command hook or local fallback runs
  -> Telegram reply and/or wiki writeback
```

## Trust boundaries

- Keep all services private on Tailscale when possible.
- If public exposure is needed, front them with Caddy and strong auth.
- Treat `raw/sources/` as immutable.
- Treat chat messages as transient unless promoted into the wiki.

## Why not more infrastructure

Not included by default:

- vector database
- PostgreSQL
- Redis
- workflow engine
- message queue
- full-text indexing daemon

Reason:

- the wiki is small enough initially for `index.md` plus grep-style search
- each additional stateful service increases maintenance cost

## Optional later additions

- `qmd` for larger markdown search
- a custom webapp over the repo-backed wiki
- `Caddy` for public HTTPS
- `restic` for encrypted offsite backups
- a cron/systemd job for auto-ingest and auto-commit
