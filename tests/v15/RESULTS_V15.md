# SRC-X.5 v1.5 results

Criteria: `PREDICTIONS_V15.md` (sealed `SEAL_V15.txt`, 2026-11-26T11:35:26Z). One pass each; every fix sealed before its re-check.

## Local tests
| Test | v1.5 as sealed (`out/results_15.json`) | after FIX1 (`out/results_15_fix1.json`) |
|---|---|---|
| T1 MCP over HTTP | met | met |
| T2 A2A | met | met |
| T3 Standards (OpenAPI 3.1, 27 node answers conform) | met | met |
| T4 Install | **not met**: the installed copy lacked its interface files | met (FIX1: `srcx5_install.py`, packaged interface files) |
| T5 Write anywhere, converge | met | met |
| T6 Submit by issue | met | met |
| T7 Status | met | met |
| T8 Regression (v1.4 T1–T6, sealed hashes) | met | met |

## Deployment checks (public repository; FIX2 sealed before they were observed again)
| Check | Result | Evidence |
|---|---|---|
| D1 Container | met | `srcx5-docker-v151` run 45812815541 (first run 45812257312 failed in the check script: container name; FIX2) |
| D2 Live documents | met | `api/.well-known/agent-card.json`, `api/openapi_v15.json`, `api/status.json` served by Pages |
| D3 Signalling | **not met**: three mirrors current, no IPFS id (`ipfs init -q`: unknown option; the step no longer blocks the deploy, so the site went out without it) | `srcx5-pages-v151` run 45812815322 |
| D4 Heartbeat | met | `srcx5-heartbeat-v151` run 45813203804 |

Disclosed: the Pages deploy started by the heartbeat (run 45813220974) failed on a GitHub artifact-service error ("re-run the deployment at a later time") and was re-run once as a crash; it then passed.

## Level: partly met
T1–T8 met (T4 after FIX1); D1, D2, D4 met; D3 not met. FIX3 (the IPFS command) is recorded separately in `FIX3_V15.md`.

## Open (owner accounts; not results)
Always-on public node (Hugging Face Space), PyPI, MCP Registry listing, IPFS pinning.

## FIX3 re-check of D3 (observed once, as sealed in `SEAL_V15_FIX3.txt`)
- The IPFS content id is now computed: `bafybeievk7qjhfhxmujaeyeqkc7tcht4n2fkl4ewtyucraq3jiclwqegxa` (run 45813478497 log).
- The deploy did not go out: GitHub's Pages deploy step reported "No artifacts named github-pages" 0.3 s after the
  artifact was uploaded and finalized (artifact 15115105048); re-run once as a crash, same error. The live
  `status.json` therefore still shows `ipfs: null`.
- **D3 remains not met.** No further change is made; `heartbeat_v152.yml` redeploys every six hours, and D3 will be
  reported met only when the live `status.json` is seen carrying the id.

## FIX4 re-check of D3 (observed once, as sealed in `SEAL_V15_FIX4.txt`)
- Run 45829107677 (`pages_v153`, 13:26 UTC): job `ipfs` succeeded (id `bafybeievk7qjhfhxmujaeyeqkc7tcht4n2fkl4ewtyucraq3jiclwqegxa`);
  job `deploy`, which never runs the IPFS tool, failed with GitHub's "Fetching artifact metadata failed … re-run the
  deployment at a later time" / "No artifacts named github-pages".
- By the rule fixed in `FIX4_V15.md`, the cause is outside these files (GitHub's Pages artifact service for this
  repository, failing since about 11:45 UTC). **D3 stays not met; nothing more is changed.**
- Effect: the Pages mirror keeps serving its 11:44 UTC build (10 records, head `d3d70d58…`, intact). The raw.githubusercontent
  and jsDelivr mirrors read the repository directly and do not depend on Pages deploys.

## FIX5 (observed once, as sealed in `SEAL_V15_FIX5.txt`)
- **F5a deploy restored: met.** `pages_v154` deployed at 14:40 UTC (first deploy since 11:44); the live agent card names the public node (`https://rsos-srcx5.hf.space/a2a`, version 1.5).
- **F5b IPFS id published: met.** Live `api/ipfs.json`: `bafybeidmljksaoqv7koakohwtneiqt2qmjy3v3wtx5ybaujxv776sytxhi` for head `d3d70d58…` (commit 12934e4 by `ipfs_v154`). It differs from the FIX3/FIX4 id because it covers a fresh export without `status.json` and `ipfs.json`, as stated in the file.
- Disclosed: a manual start of `ipfs_v154` ran at the same moment as the automatic one; its push was rejected ("fetch first") because the other had already committed the same id. No effect.
- **D3 as sealed (id inside `status.json`) remains not met**; the id is published in the alternative form fixed in `FIX5_V15.md`.

## Level, unchanged: partly met
T1–T8 met (T4 after FIX1); D1, D2, D4 met; D3 not met as sealed, met in the alternative form of FIX5 (F5a, F5b).
