# SRC-X.5

**An open record of sealed claims, verified at the source.** Each record says what was predicted and by which
criteria, which files were fixed and when, when it ran, what came out, and who replicated it. Its id is the SHA-256 of
its canonical form, so every copy, on any host or network, is checked rather than trusted. No personal data. Any field.

**See it:** [the live record](https://r-a-elu-architecture.github.io/srcx5/) re-checks every record in your browser.

## Connect from any layer
A record is canonical bytes whose identity is their own hash, so it travels unchanged over any carrier and is verified
by anyone who can compute SHA-256. Each layer connects through its own main standard ([`SPEC_SRCX5_1_4.md`](SPEC_SRCX5_1_4.md) §L):

| You are | Connect through |
|---|---|
| A person | the [browser viewer](https://r-a-elu-architecture.github.io/srcx5/): every record re-checked on your machine |
| A tool or company system | HTTP and JSON: [`openapi.json`](openapi.json) (OpenAPI 3.1), [`schema/record.schema.json`](schema/record.schema.json) |
| An AI agent or assistant | MCP: `python srcx5_mcp.py --log log` (list, get, verify, verify the log, submit, linked-data view) |
| A research or linked-data tool | JSON-LD in the W3C PROV vocabulary: `api/ld/<id>.jsonld`, [`context.jsonld`](context.jsonld) |
| A node operator, anywhere | `python srcx5_net.py serve --log log --peer <node or mirror>`: syncs what it lacks, then serves both shapes |
| A network with long delays or broken links | records are self-contained bundles: store, forward, verify on arrival |
| A ledger or archive | anchor the head hash (Bitcoin via OpenTimestamps in [`anchors/`](anchors/)); Zenodo and Software Heritage keep it citable |

Every copy answers the same paths (`ids.json`, `head.json`, `log.json`, `records/<id>.json`, `.well-known/srcx5.json`).
[`MIRRORS.json`](MIRRORS.json) lists them; sync uses the first that answers and skips any record that does not match its
own hash. A scheduled check refreshes stale mirrors; anyone running a node can be added with one pull request.

## Use it
- **Check:** `python srcx5.py verify records/CONF6.json --repo <research checkout>` checks every fingerprint byte for byte.
- **Sync:** `python srcx5_net.py sync --log mylog` pulls from the mirrors; add `--peer URL` for any other node.
- **Add:** put a record in `submissions/` and open a pull request; the admission check answers with reasons.
- **Replicate:** `python srcx5.py replicate <id> --by <handle> --outcome all|partly|none --summary "…"`.

Every record passes seven checks (DISCLOSURE, CONSENT_PRIVACY, HARM_BOUND, CONFORMANCE, NON_BLOCKING, ATTRIBUTION,
PURPOSE). Nothing is prohibited from being submitted: what fails a check is quarantined with its reasons and never
published, and nothing is deleted. A record is replaced by a modified clone that keeps its identity, and nodes audit each
other (`srcx5.py audit`). The rules live in `srcx5.py` (sealed, unchanged since v1.3); `srcx5_net.py` adds connection
(v1.4); both use the Python standard library only.

## In the log on day one
The sealed tests of the RSOS research release ([rsos-one-seed](https://github.com/r-a-elu-architecture/rsos-one-seed)),
including those whose criteria were not met, and the protocol's launch proofs. Each was fingerprinted and pushed
before it ran.

| Record | Pre-registered criteria |
|---|---|
| CONF6: whole AI–AI system bound to one RSOS structure vs plain rollout | all met: accuracy 1.000 vs 0.875, 51 % fewer tokens |
| CONF5: identified RSOS structure vs plain rollout | met in 2 of 3 rows |
| CONF1–CONF4, ABL1, STRUCT1, REAL3 | all, partly or not met, as they came |
| Launch proofs (admission, checks, supersede, peer audit, sync) | all met; see `tests/RESULTS.md` |

Version 1.4 launch tests (carriers, failover, standards, AI agents, regression, hardening, anchoring):
[`tests/v14/`](tests/v14/).

## Licence
Code Apache 2.0 ([`LICENSE`](LICENSE)); specification text CC BY 4.0.
