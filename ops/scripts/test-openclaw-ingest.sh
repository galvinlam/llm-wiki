#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

INGEST_AGENT_ID="${OPENCLAW_INGEST_AGENT_ID:-apoc}"
TIMEOUT_SECONDS="${OPENCLAW_AGENT_TIMEOUT_SECONDS:-180}"

mkdir -p \
  "$TMP_DIR/raw/inbox" \
  "$TMP_DIR/raw/imports/processed" \
  "$TMP_DIR/raw/imports/rejected" \
  "$TMP_DIR/raw/sources" \
  "$TMP_DIR/raw/assets" \
  "$TMP_DIR/wiki/sources" \
  "$TMP_DIR/wiki/entities" \
  "$TMP_DIR/wiki/concepts" \
  "$TMP_DIR/wiki/projects" \
  "$TMP_DIR/wiki/answers" \
  "$TMP_DIR/wiki/syntheses" \
  "$TMP_DIR/wiki/templates" \
  "$TMP_DIR/ops/state/queries/pending" \
  "$TMP_DIR/ops/state/queries/running" \
  "$TMP_DIR/ops/state/queries/done" \
  "$TMP_DIR/ops/state/queries/failed" \
  "$TMP_DIR/ops/state/ingest/pending" \
  "$TMP_DIR/ops/state/ingest/running" \
  "$TMP_DIR/ops/state/ingest/done" \
  "$TMP_DIR/ops/state/ingest/failed" \
  "$TMP_DIR/ops/state/telegram/last-answer" \
  "$TMP_DIR/ops/state/scheduler"

cat > "$TMP_DIR/wiki/index.md" <<'EOF'
# Wiki Index

## Core

- [home.md](/tmp/home.md) - Temporary test index.
EOF

cat > "$TMP_DIR/wiki/overview.md" <<'EOF'
# Wiki Overview

Test overview.
EOF

cat > "$TMP_DIR/wiki/log.md" <<'EOF'
# Wiki Log
EOF

cat > "$TMP_DIR/raw/inbox/sample.md" <<'EOF'
---
title: "Graphify notes"
created: "2026-04-10T12:00:00-07:00"
origin: "diagnostic"
status: "inbox"
source_type: "url"
source_urls:
  - "https://github.com/safishamsi/graphify"
attachments: []
tags:
  - "graph"
  - "agents"
---

Useful repo ideas around graph-shaped knowledge access for agents.
EOF

cat > "$TMP_DIR/ingest.json" <<'EOF'
{
  "kind": "ingest",
  "status": "pending",
  "created": "2026-04-10T12:30:00-07:00",
  "origin": "diagnostic",
  "requested_by": null
}
EOF

set +e
LLM_WIKI_ROOT="$TMP_DIR" \
LLM_WIKI_JOB_FILE="$TMP_DIR/ingest.json" \
LLM_WIKI_OUTPUT_FILE="$TMP_DIR/output.json" \
OPENCLAW_INGEST_AGENT_ID="$INGEST_AGENT_ID" \
OPENCLAW_AGENT_TIMEOUT_SECONDS="$TIMEOUT_SECONDS" \
python3 "$ROOT_DIR/ops/openclaw/run_ingest_job.py"
status=$?
set -e

echo "Adapter exit code: $status"
if [[ -f "$TMP_DIR/output.json" ]]; then
  echo "Output file:"
  cat "$TMP_DIR/output.json"
else
  echo "No output file was produced."
fi

exit 0
