#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "usage: query_memory.sh '<cypher>'" >&2
  exit 1
fi

HOST="192.168.178.100"

if ! ssh -o ConnectTimeout=3 -o BatchMode=yes "chsturn@${HOST}" true 2>/dev/null; then
  echo "ERROR: cannot reach carlo_memory host ${HOST} via SSH" >&2
  exit 2
fi

CY="$1"
ssh "chsturn@${HOST}" \
  "docker exec falkordb redis-cli --raw GRAPH.QUERY carlo_memory \"$CY\""
