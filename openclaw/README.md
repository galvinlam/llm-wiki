# OpenClaw Roles

This folder defines the expected OpenClaw roles for this repository.

- `telegram-query` handles user-facing retrieval and answer writeback decisions
- `wiki-maintainer` handles scheduled inbox processing and wiki updates
- `wiki-linter` handles cleanup, backlog discovery, and synthesis passes

Each role has a `SKILLS.md` file describing:

- what it reads
- what it writes
- what it must avoid
- the expected output contract when used through worker command hooks

The source of truth for the worker-to-agent interface is `openclaw/contracts/`.
