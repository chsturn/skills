#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "usage: query_memory.sh '<cypher>'" >&2
  exit 1
fi

CY="$1"
ssh chsturn@192.168.178.100 \
  "docker exec falkordb redis-cli --raw GRAPH.QUERY carlo_memory \"$CY\""
