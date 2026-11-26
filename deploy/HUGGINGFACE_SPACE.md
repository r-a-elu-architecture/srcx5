---
title: SRC-X.5 node
sdk: docker
app_port: 7860
---
# Run a free SRC-X.5 node on Hugging Face Spaces
1. Create a new Space, SDK "Docker" (free CPU tier).
2. Copy the whole `srcx5` repository into it (or at least `srcx5*.py`, `SPEC_SRCX5_1_4.md`, `openapi.json`, `schema/`, `context.jsonld`, `MIRRORS.json`, `llms.txt`, `log/`), with `deploy/Dockerfile` as `Dockerfile`; put this file's header in its `README.md`.
3. Optional: set the variable `PEERS` to other nodes' URLs, comma-separated; the node syncs only what it lacks on start.
Free Spaces sleep when idle and wake on the next request. Every record a node holds is re-checked on arrival; a node is a
copy, never an authority.
