# OpenClaw Contracts

This folder defines the file contracts between the lightweight platform and OpenClaw agents.

The platform owns:

- capture
- durable file storage
- queueing
- status tracking
- Telegram/web interfaces

OpenClaw owns:

- fetch and extract work
- research and enrichment
- categorization
- synthesis
- linking
- wiki improvement

## Contract model

For each queued job, the worker provides:

- `LLM_WIKI_ROOT`
- `LLM_WIKI_JOB_FILE`
- `LLM_WIKI_OUTPUT_FILE`

The OpenClaw adapter should:

1. read the job JSON
2. read and update the repo
3. write result JSON to the output path

## Files

- `query-job.example.json`
- `ingest-job.example.json`
- `lint-job.example.json`
- `query-output.example.json`
- `ingest-output.example.json`
- `lint-output.example.json`

These are examples and reference contracts, not strict schemas enforced by a validator yet.
