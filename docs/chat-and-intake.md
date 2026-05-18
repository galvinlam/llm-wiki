# Chat And Intake

## Recommended interaction surfaces

Use three entry points:

1. Open WebUI for normal desktop/mobile chat with agents
2. Telegram bot for quick capture and lightweight conversation
3. Intake web form for links, pasted text, PDFs, screenshots, and files

This gives you:

- reliable browser chat
- fast phone sharing
- no need to build or maintain a native mobile app

## Telegram

Telegram is the best first messaging integration for this project.

Why:

- easy bot setup
- direct file and text delivery
- webhook-friendly
- works well from phone

Recommended behavior:

- every inbound message gets written to `raw/inbox/`
- file attachments are downloaded into `raw/assets/`
- a small markdown envelope is created with metadata
- `/ask` creates a query job handled by the maintainer worker
- agents can later ingest or respond

Suggested commands:

- `/note ...` for plain notes
- `/link <url>` for direct links
- `/ask ...` for agent questions
- `/ingest` to request processing of the latest inbox items
- `/save` to persist the last answer
- `/status` to inspect queues
- `/latest` to summarize recent wiki activity

## WhatsApp

WhatsApp is possible, but not as clean for a minimal self-hosted stack.

Recommendation:

- support WhatsApp only through Twilio webhook integration
- use it for lightweight capture, not as the primary agent interface

Why not first:

- Meta/WhatsApp business onboarding is more operationally heavy
- media handling is more awkward than Telegram
- long-term maintenance is worse than Telegram for a personal VPS

## Intake web form

The intake service exposes a simple mobile page where you can:

- paste one or more URLs
- paste free text
- upload files such as PDFs or images
- add tags and a short title

This is the easiest universal entry point for:

- web links
- X posts
- GitHub links
- YouTube links
- Instagram links
- PDFs
- clipboard snippets

The system should not try to fully parse every source class at intake time. It should capture first, normalize second.

## Source-specific handling

### PDFs

- accept direct upload
- store original file under `raw/assets/`
- create a matching intake note under `raw/inbox/`

### Web links

- store URL immediately
- let the ingest agent fetch and summarize later

### X / GitHub / YouTube / Instagram

- store the original URL and metadata first
- do not overfit the intake path to each platform
- platform-specific extraction can be added later if needed

This keeps intake durable even when site-specific scrapers break.

## Durable format for intake notes

Every intake item should produce a markdown file with frontmatter like:

```yaml
---
title: Example Intake
created: 2026-04-04T12:00:00-07:00
source_type: url
source_url: https://example.com
origin: telegram
status: inbox
tags:
  - research
attachments:
  - raw/assets/example.pdf
---
```

## Chat writeback policy

Not every chat should become a wiki page.

Promote to the wiki when the output is:

- a synthesis
- a reusable answer
- a comparison
- a decision
- a durable summary

Write these to:

- `wiki/answers/`
- `wiki/syntheses/`

and append to `wiki/log.md`.
