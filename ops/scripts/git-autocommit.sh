#!/usr/bin/env bash
set -euo pipefail

NAME="${GIT_AUTOCOMMIT_NAME:-llm-wiki-bot}"
EMAIL="${GIT_AUTOCOMMIT_EMAIL:-bot@example.com}"

git config user.name "$NAME"
git config user.email "$EMAIL"

if [[ -n "$(git status --porcelain)" ]]; then
  git add wiki raw/imports raw/inbox raw/assets docs AGENTS.md README.md
  git commit -m "chore: snapshot llm-wiki state"
fi
