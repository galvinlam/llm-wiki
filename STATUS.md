# Status

## Current state

The repo now has a runnable first version of the `llm-wiki` platform with a clearer markdown-first knowledge interface.

Current working pieces:

- browser chat via Open WebUI
- phone/laptop capture via `/share`
- Telegram bot capture and async query flow
- file-based query and ingest queues
- background worker for scheduled or requested processing
- OpenClaw adapter and job contracts
- fallback local retrieval
- fallback ingest that now writes schema-aligned source pages
- agent-friendly wiki structure with overview, templates, and provenance fields

The preferred knowledge surface is now markdown-first:

- usable from Obsidian immediately
- compatible with a future custom webapp
- directly editable by agents

## What is done

- Created the project structure and operating contract in [AGENTS.md](AGENTS.md)
- Added repo-local operating context in [AGENTS.md](AGENTS.md)
- Implemented the intake service in [ops/intake/app.py](ops/intake/app.py)
- Implemented the maintainer worker in [ops/intake/worker.py](ops/intake/worker.py)
- Implemented shared queue, filesystem, retrieval, Telegram, and automation helpers in [ops/intake/llm_wiki](ops/intake/llm_wiki)
- Added Docker deployment in [docker-compose.yml](docker-compose.yml)
- Added operator scripts in [ops/scripts](ops/scripts)
- Added OpenClaw role skills in [openclaw/skills](openclaw/skills)
- Added OpenClaw job contracts in [openclaw/contracts](openclaw/contracts)
- Added wiki schema guidance in [docs/wiki-schema.md](docs/wiki-schema.md)
- Added [wiki/overview.md](wiki/overview.md) and page templates under [wiki/templates](wiki/templates)
- Updated fallback ingest so it now:
  - writes schema-aligned source pages
  - populates `relationships.extracted/inferred/ambiguous`
  - creates tag-derived concept stubs when needed
  - links new source pages into the wiki more coherently

## What still needs to be built

### 1. Real OpenClaw execution path

The adapters and contracts exist. The repo now defaults to a shared OpenClaw exec wrapper that can tolerate splash/noise output, but the real runtime still needs validation against your existing precreated agents.

Need:

- verify the real production `openclaw agent --agent <id> --message ...` invocation for each role
- verify the chosen precreated agents are responsive
- confirm the wrapper can consistently extract the final JSON object
- validate the ingest path specifically against the chosen ingest agent

### 2. Real agent-driven enrichment

The fallback ingest path is now structurally better, but it is still intentionally lightweight.

OpenClaw still needs to do the real enrichment work for:

- PDFs
- generic web pages
- X links
- GitHub links
- YouTube links
- Instagram links

Next work:

- wire the maintainer role to a real OpenClaw execution path
- let the agent fetch, extract, research, categorize, synthesize, and link
- keep Python-side enrichment narrow and deterministic

### 3. Better retrieval quality

Current fallback retrieval is still plain markdown matching.

Next work:

- improve page selection/ranking
- surface recent un-ingested inbox items relevant to a query
- optionally add a lightweight markdown search/index layer later

### 4. Deployment hardening

The repo is not yet hardened for public deployment.

Next work:

- choose Tailscale-only or public HTTPS exposure
- add reverse proxy guidance if public
- add auth/routing guidance for the web surfaces
- add backup guidance

### 5. Scheduled maintenance and enhancement loops

The maintainer can process ingest jobs, but deeper continuous enhancement still needs recurring automation.

Next work:

- schedule wiki lint runs
- schedule weekly summaries
- promote repeated answers into syntheses
- improve entity/concept/project cross-linking

## What I need from you to continue

### Required for deployment

- VPS hostname or public base URL
- whether access should be Tailscale-only or public HTTPS
- desired filesystem location if not `/srv/llm-wiki`

### Required for Telegram

- Telegram bot token
- Telegram allowed chat ID or IDs
- desired webhook base URL

### Required for intake and app secrets

- `INTAKE_SHARED_TOKEN`
- `OPENWEBUI_SECRET_KEY`

### Required for OpenClaw integration

- confirm the production OpenClaw invocation pattern
- confirm whether OpenClaw runs on this VPS directly or through another service
- confirm any required profile/container/model flags

### Optional

- whether to enable WhatsApp at all
- if yes, Twilio auth token and WhatsApp sender number
- whether to enable auto-commit
- whether to add backups next

## Recommended next implementation order

1. Validate the real OpenClaw execution path.
2. Deploy and validate Telegram end to end.
3. Make the maintainer role perform real fetch/extract/linking work.
4. Add scheduled lint and synthesis passes.
5. Harden deployment and backups.

## Validation already performed

- `python3 -m py_compile ops/intake/app.py ops/intake/worker.py ops/intake/llm_wiki/*.py`
- `bash ops/scripts/bootstrap.sh`
- `docker-compose config`
- direct CLI smoke test showed `openclaw agent` requires a session selector such as `--agent`
- direct adapter smoke test against `telegram-query` timed out without producing JSON output
- fallback ingest smoke test confirmed schema-aligned source pages and tag-derived concept links are being written
- local `.env` currently points ingest to the working `link` agent id

## Notes

- `origin/main` currently contains only the initial scaffold commit.
- The working tree contains additional uncommitted schema/interface work after that initial push.
- The project is usable now with fallback behavior, but the intended design is still a thin platform with agent-driven knowledge work.
