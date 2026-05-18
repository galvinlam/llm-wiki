#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from template. Fill in secrets before deploy."
fi

mkdir -p \
  data/open-webui \
  data/intake \
  raw/inbox \
  raw/imports \
  raw/imports/processed \
  raw/imports/rejected \
  raw/sources \
  raw/assets \
  ops/state/queries/pending \
  ops/state/queries/running \
  ops/state/queries/done \
  ops/state/queries/failed \
  ops/state/ingest/pending \
  ops/state/ingest/running \
  ops/state/ingest/done \
  ops/state/ingest/failed \
  ops/state/lint/pending \
  ops/state/lint/running \
  ops/state/lint/done \
  ops/state/lint/failed \
  ops/state/telegram/last-answer \
  ops/state/scheduler \
  wiki/entities \
  wiki/concepts \
  wiki/projects \
  wiki/answers \
  wiki/syntheses \
  wiki/sources \
  openclaw/skills/telegram-query \
  openclaw/skills/wiki-maintainer \
  openclaw/skills/wiki-linter

touch \
  raw/inbox/.gitkeep \
  raw/imports/.gitkeep \
  raw/imports/processed/.gitkeep \
  raw/imports/rejected/.gitkeep \
  raw/sources/.gitkeep \
  raw/assets/.gitkeep \
  wiki/entities/.gitkeep \
  wiki/concepts/.gitkeep \
  wiki/projects/.gitkeep \
  wiki/answers/.gitkeep \
  wiki/syntheses/.gitkeep \
  wiki/sources/.gitkeep \
  ops/state/queries/pending/.gitkeep \
  ops/state/queries/running/.gitkeep \
  ops/state/queries/done/.gitkeep \
  ops/state/queries/failed/.gitkeep \
  ops/state/ingest/pending/.gitkeep \
  ops/state/ingest/running/.gitkeep \
  ops/state/ingest/done/.gitkeep \
  ops/state/ingest/failed/.gitkeep \
  ops/state/lint/pending/.gitkeep \
  ops/state/lint/running/.gitkeep \
  ops/state/lint/done/.gitkeep \
  ops/state/lint/failed/.gitkeep \
  ops/state/telegram/last-answer/.gitkeep \
  ops/state/scheduler/.gitkeep

if [[ ! -d .git ]]; then
  git init
fi

echo "Bootstrap complete."
