# SRC-X.5

**An open record of sealed claims, verified at the source.** Each record says what was predicted and by which
criteria, which files were fixed and when, when it ran, what came out, and who replicated it. Its id is the SHA-256 of
its canonical form, so every copy is verified independently of the host or network it came from. No personal data. Any field.

**Paper:** [doi:10.5281/zenodo.24555259](https://doi.org/10.5281/zenodo.24555259) (preprint, CC BY 4.0). **Software archive:** [doi:10.5281/zenodo.24557469](https://doi.org/10.5281/zenodo.24557469) (v1.4.1). **See it:** [the live record](https://r-a-elu-architecture.github.io/srcx5/) re-checks every record in your browser.

## Connect from any layer
A record is canonical bytes whose identity is their own hash, so it travels unchanged over any carrier and is verified
by anyone who can compute SHA-256. Each layer connects through its own main standard ([`SPEC_SRCX5_1_4_1.md`](SPEC_SRCX5_1_4_1.md) §L):

| You are | Connect through |
|---|---|
| A person | the [browser viewer](https://r-a-elu-architecture.github.io/srcx5/): every record re-checked on your machine; add a record by [opening an issue](https://github.com/r-a-elu-architecture/srcx5/issues/new?template=submit-record.yml) (no git needed) |
| A tool or company system | HTTP and JSON: `openapi_v15.json` (OpenAPI 3.1, the format agent platforms import as actions or tools), [`schema/record.schema.json`](schema/record.schema.json) |
| A cloud AI agent | MCP over HTTP: `POST https://rsos-srcx5.hf.space/mcp` (or any node; Streamable HTTP; tools list, get, verify, verify the log, submit, linked-data view) |
| A local AI client | MCP over stdio: `python srcx5_mcp.py --log log`, or `docker run -i --rm ghcr.io/r-a-elu-architecture/srcx5 mcp` |
| Another agent | Agent2Agent (A2A): `<node>/.well-known/agent-card.json`, JSON-RPC at `POST <node>/a2a` |
| A research or linked-data tool | JSON-LD in the W3C PROV vocabulary: `api/ld/<id>.jsonld`, [`context.jsonld`](context.jsonld) |
| A node operator, anywhere | `docker run -p 7860:7860 ghcr.io/r-a-elu-architecture/srcx5`, or `pip install srcx5` then `srcx5-node serve --log log`; list it in [`NODES.json`](NODES.json) with one pull request |
| A network with long delays or broken links | records are self-contained bundles: store, forward, verify on arrival |
| A ledger, archive or content-addressed network | the head is anchored on Bitcoin (OpenTimestamps, [`anchors/`](anchors/)); the read API's IPFS content id is in `api/status.json`; Zenodo and Software Heritage keep it citable |

**Write anywhere, converge everywhere (v1.5).** A record admitted by any listed node reaches the public log at the next
heartbeat (every six hours): the log pulls from every node and re-checks each record on arrival. The heartbeat also
republishes [`status.json`](https://r-a-elu-architecture.github.io/srcx5/api/status.json): which mirrors and nodes hold
the head, the Bitcoin proof state and the IPFS content id.

Every copy answers the same paths (`ids.json`, `head.json`, `log.json`, `records/<id>.json`, `.well-known/srcx5.json`).
[`MIRRORS.json`](MIRRORS.json) lists them; sync uses the first that answers and skips any record that does not match its
own hash. A scheduled check refreshes stale mirrors; anyone running a node can be added with one pull request.

## Use it
- **Check:** `python srcx5.py verify records/CONF6.json --repo <research checkout>` checks every fingerprint byte for byte.
- **Sync:** `python srcx5_net.py sync --log mylog` pulls from the mirrors; add `--peer URL` for any other node.
- **Add:** put a record in `submissions/` and open a pull request; the admission check answers with reasons.
- **Replicate:** `python srcx5.py replicate <id> --by <handle> --outcome all|partly|none --summary "…"`.

Every record passes seven checks (DISCLOSURE, CONSENT_PRIVACY, HARM_BOUND, CONFORMANCE, NON_BLOCKING, ATTRIBUTION,
PURPOSE). Admission is non-blocking: a submission that fails a check is quarantined with its reasons, never published
and never deleted. A revision supersedes the earlier record and carries the same stable lineage identifier, and nodes
audit each other (`srcx5.py audit`). The rules live in `srcx5.py` (sealed, unchanged since v1.3); `srcx5_net.py` adds connection
(v1.4); both use the Python standard library only.

## In the log on day one
Every claim in the research release, with number, baseline and caveat: [CLAIMS.md](https://github.com/r-a-elu-architecture/rsos-one-seed/blob/main/CLAIMS.md).

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

## Cite
Elu, R. A. (2026). *SRC-X.5: an open record of sealed claims, verified at the source.* Preprint, Zenodo.
https://doi.org/10.5281/zenodo.24555259 (machine-readable: [`CITATION.cff`](CITATION.cff))
Software: Elu, R. A. (2026). *SRC-X.5* (v1.4.1) [Computer software]. Zenodo. https://doi.org/10.5281/zenodo.24557469

<!-- mcp-name: io.github.r-a-elu-architecture/srcx5 -->
