#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

QUERY_AGENT_ID="${OPENCLAW_QUERY_AGENT_ID:-telegram-query}"
INGEST_AGENT_ID="${OPENCLAW_INGEST_AGENT_ID:-wiki-maintainer}"
LINT_AGENT_ID="${OPENCLAW_LINT_AGENT_ID:-wiki-linter}"

mkdir -p \
  "$ROOT_DIR/openclaw/workspaces/$QUERY_AGENT_ID" \
  "$ROOT_DIR/openclaw/workspaces/$INGEST_AGENT_ID" \
  "$ROOT_DIR/openclaw/workspaces/$LINT_AGENT_ID"

add_agent() {
  local agent_id="$1"
  local workspace="$2"
  if timeout 15s openclaw agents list --json 2>/dev/null | grep -q "\"id\"[[:space:]]*:[[:space:]]*\"$agent_id\""; then
    echo "Agent already exists: $agent_id"
    return 0
  fi
  timeout 30s openclaw agents add "$agent_id" --workspace "$workspace" --non-interactive --json
}

add_agent "$QUERY_AGENT_ID" "$ROOT_DIR/openclaw/workspaces/$QUERY_AGENT_ID"
add_agent "$INGEST_AGENT_ID" "$ROOT_DIR/openclaw/workspaces/$INGEST_AGENT_ID"
add_agent "$LINT_AGENT_ID" "$ROOT_DIR/openclaw/workspaces/$LINT_AGENT_ID"

echo "OpenClaw agents are set up."
