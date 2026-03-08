#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 2 ]; then
  echo "usage: query_nexus.sh <search|impact|dora|pii|stats> '<json-payload>'" >&2
  exit 1
fi

ENDPOINT="$1"
PAYLOAD="$2"

API_BASE="${NEXUS_API_BASE:-http://192.168.178.100:8080}"
API_KEY="${NEXUS_API_KEY:-nexus-estably-2026}"

curl -sS \
  -X POST "${API_BASE}/${ENDPOINT}" \
  -H 'Content-Type: application/json' \
  -H "x-api-key: ${API_KEY}" \
  -d "${PAYLOAD}"
