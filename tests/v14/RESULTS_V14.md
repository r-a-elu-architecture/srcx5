# SRC-X.5 v1.4 launch tests: results

Criteria: `PREDICTIONS_V14.md`, sealed in `SEAL_V14.txt` (pushed in commit 40cee1c9, 2026-11-26T08:41:03Z) before any
run. One run, seed 14, 6.7 s (T1-T6, local); T7 in GitHub Actions. The rules file `srcx5.py` is byte-identical to its
v1.3 seal. Raw results: `out/results_14.json`.

| Test | Result | Criteria |
|---|---|---|
| T1 Carriers | 10/10 records byte-identical, ids recomputed, chain intact, head equal, through all six carriers: running node, static mirror, git clone, file copy, delay-tolerant link (86 bundles, 130 attempts at 30 % loss, 5 simulated hours), QR-sized chunks (30, shuffled) | met |
| T2 Failover and refill | stale mirror reported stale, others current; after refill all current; with mirrors 1-2 down, mirror 3 answered with 10/10; all down: clean error in 0.0 s; poisoned record skipped and taken from the next mirror (10/10) | met |
| T3 Standards | OpenAPI 3.1 valid; 26 live responses all conform; 10/10 records valid against the JSON Schema; 10/10 JSON-LD views expand to `prov:Entity` with `urn:srcx5:<id>` | met |
| T4 AI layer (MCP) | 6 tools; real record valid; tampered copy invalid ("id does not match the record's content"); log intact, 10 entries; tampered submission quarantined; malformed line answered -32700 and the server kept answering | met |
| T5 No regression | 600/600 invalid quarantined; 200/200 valid admitted; 210 entries, chain intact | met |
| T6 Hardening and fuzzing | 400 hostile requests: 404 ×33, 405 ×99, 411 ×34, 413 ×67, 422 ×167; no 5xx; nothing admitted; node alive; chain unchanged; 31st submission in a minute answered 429 | met |
| T7 Anchor | Run 45785355641: OpenTimestamps proof (875 bytes) for head d3d70d58… created and submitted to four public calendars; status **pending** (Bitcoin confirmation follows within hours) | met; see FIX1 and FIX2 |

**Disclosures.** FIX1 (`FIX1_T7.md`): the sealed T7 workflow checked its seal from the wrong folder; a copy with only
that line corrected was sealed and pushed before T7 ran. FIX2 (`FIX2_ANCHOR.md`): the status label written by
`srcx5_net.py anchor` said "confirmed" for a pending proof; corrected in a new file, `srcx5_anchor.py`.

**Level: all seven met, ready to launch.**
