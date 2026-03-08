#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "usage: query_memory.sh '<cypher>'" >&2
  exit 1
fi

HOST="${NEXUS_HOST:-192.168.178.100}"
GRAPH="${NEXUS_GRAPH:-estably_graphrag}"

if ! ssh -o ConnectTimeout=3 -o BatchMode=yes "chsturn@${HOST}" true 2>/dev/null; then
  echo "ERROR: cannot reach nexus host ${HOST} via SSH" >&2
  exit 2
fi

CY="$1"
ssh "chsturn@${HOST}" \
  "docker exec falkordb redis-cli --raw GRAPH.QUERY ${GRAPH} \"$CY\""
