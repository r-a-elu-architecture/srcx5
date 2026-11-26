# SRC-X.5 v1.5 launch tests: criteria fixed before the run

v1.5 adds ways in, not rules: `srcx5.py` (rules, v1.3), `srcx5_net.py` and `srcx5_mcp.py` (v1.4) are sealed and unchanged.
New: `srcx5_node.py` (MCP over HTTP, A2A, OpenAPI v1.5, status, pull from nodes), `srcx5_issue.py` (submit by issue),
`pyproject.toml`, `deploy/` (container), `NODES.json`, `server.json`, workflows (docker, pypi, hf_space, heartbeat,
issue_submit, mcp_registry, pages).

One pass: `python tests/v15/run_v15.py` → `tests/v15/out/results_15.json`. No reruns except crashes, disclosed.

## Local tests (each passes only if every listed condition holds)

| Test | Pass condition |
|---|---|
| T1 MCP over HTTP | `initialize` returns a protocol version; a notification returns 202 with no body; `tools/list` returns the 6 tools; `srcx5_verify` is valid for 10 of 10 log records; `srcx5_verify_log` intact; a record with personal data is quarantined; `GET /mcp` 405; malformed JSON → -32700; unknown method → -32601; `tools/list` and `srcx5_verify_log` results equal those of the stdio server (v1.4) |
| T2 A2A | agent card has name, description, url ending `/a2a`, version, protocolVersion, capabilities, default input/output modes and ≥ 6 skills; `message/send` with data `{tool: srcx5_list}` returns every active record; text "verify" returns an intact chain; unknown method → -32601; unknown tool → -32602 |
| T3 Standards | `openapi_v15.json` is valid OpenAPI 3.1; it documents POST `/mcp`, POST `/a2a` and GET `/.well-known/agent-card.json`; every documented GET answer of a running node conforms to its schema (all records, all JSON-LD views, index paths, agent card) |
| T4 Install | `pip install` of the repository into a fresh virtual environment succeeds; the installed `srcx5-node export` writes a static mirror with `.well-known/agent-card.json`, `openapi_v15.json` and `head.json` equal to the log head; the installed `srcx5 check-log` reports the chain intact |
| T5 Write anywhere, converge | a record submitted to node A (`POST /submit`) is admitted there; a public log that lacks it pulls it with `srcx5_node pull`; afterwards every record is byte-identical to node A's and the chain is intact; a node serving a record that does not match its own hash adds nothing |
| T6 Submit by issue | a ```json block with a valid record → admitted (and appended with `--apply`, chain intact); text with no JSON → not admitted with a reason; a record carrying personal data → quarantined; issue text containing `$(touch …)` and backticks creates no file |
| T7 Status | for a current, a stale and a down mirror the status document reports current, stale and down; it lists the Bitcoin proof from `anchors/`, the chain state and the IPFS id when given |
| T8 Regression | v1.4 tests T1–T6 all pass again; `srcx5.py`, `srcx5_net.py`, `srcx5_mcp.py` have the hashes sealed in `tests/v14/SEAL_V14.txt` |

## Deployment checks (observed after the push, in GitHub Actions and on the live mirror)

| Check | Pass condition |
|---|---|
| D1 Container | `srcx5-docker` green: image pushed to ghcr.io; inside it `/health` reports node 1.5, `/mcp` lists the tools, the agent card answers |
| D2 Live documents | the Pages mirror serves `api/.well-known/agent-card.json`, `api/openapi_v15.json` and `api/status.json` |
| D3 Signalling | `status.json` carries an IPFS content id and at least two mirrors reported current |
| D4 Heartbeat | `srcx5-heartbeat` dispatched once runs green |

## Levels

- **All criteria met:** T1–T8 pass and D1–D4 pass.
- **Partly met:** T1–T8 pass, one or more D checks not.
- **Not met:** any of T1–T8 fails.

## Not counted here (need the owner's accounts; reported as open, not as results)

Always-on public node (Hugging Face Space), `pip install srcx5` from PyPI, MCP Registry listing, IPFS pinning.
