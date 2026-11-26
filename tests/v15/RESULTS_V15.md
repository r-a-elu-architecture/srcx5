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
