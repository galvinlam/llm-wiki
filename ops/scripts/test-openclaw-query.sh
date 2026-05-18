#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

AGENT_ID="${OPENCLAW_QUERY_AGENT_ID:-morpheus}"
TIMEOUT_SECONDS="${OPENCLAW_AGENT_TIMEOUT_SECONDS:-60}"

cat > "$TMP_DIR/query.json" <<'EOF'
{
  "kind": "query",
  "status": "pending",
  "created": "2026-04-06T12:30:00-07:00",
  "origin": "diagnostic",
  "chat_id": "diagnostic",
  "question": "What does wiki/index.md currently contain? Return only JSON with reply_markdown, citations, save_candidate."
}
EOF

set +e
LLM_WIKI_ROOT="$ROOT_DIR" \
LLM_WIKI_JOB_FILE="$TMP_DIR/query.json" \
LLM_WIKI_OUTPUT_FILE="$TMP_DIR/output.json" \
OPENCLAW_QUERY_AGENT_ID="$AGENT_ID" \
OPENCLAW_AGENT_TIMEOUT_SECONDS="$TIMEOUT_SECONDS" \
python3 "$ROOT_DIR/ops/openclaw/run_query_job.py"
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
