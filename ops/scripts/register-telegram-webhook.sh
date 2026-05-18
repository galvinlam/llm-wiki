#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f .env ]]; then
  echo ".env not found"
  exit 1
fi

set -a
source .env
set +a

if [[ -z "${TELEGRAM_BOT_TOKEN:-}" || -z "${TELEGRAM_WEBHOOK_SECRET:-}" || -z "${INTAKE_BASE_URL:-}" ]]; then
  echo "TELEGRAM_BOT_TOKEN, TELEGRAM_WEBHOOK_SECRET, and INTAKE_BASE_URL must be set"
  exit 1
fi

curl -fsSL "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook" \
  --data-urlencode "url=${INTAKE_BASE_URL}/telegram/${TELEGRAM_WEBHOOK_SECRET}"

echo
echo "Webhook registered."
