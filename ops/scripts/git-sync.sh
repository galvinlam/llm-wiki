#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="/home/linuxuser/projects/llm-wiki"
BRANCH="main"

cd "$REPO_DIR"

git add -A

if ! git diff --cached --quiet; then
  git commit -m "llm-wiki daily sync $(date +%F)"
fi

git pull --rebase --autostash origin "$BRANCH"
git push origin "$BRANCH"
