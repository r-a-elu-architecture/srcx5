#!/bin/sh
# Joins by syncing from the mirrors and any PEERS (comma-separated), then serves. "mcp" runs the stdio MCP server instead.
PEERS_ARGS=""
for m in $(python -c 'import json;print(" ".join(m["url"] for m in json.load(open("MIRRORS.json"))["mirrors"]))') $(echo "${PEERS:-}" | tr ',' ' '); do
  PEERS_ARGS="$PEERS_ARGS --peer $m"
done
if [ "$1" = "mcp" ]; then exec python srcx5_mcp.py --log log $PEERS_ARGS; fi
exec python srcx5_node.py serve --log log --port "${PORT:-7860}" $PEERS_ARGS
