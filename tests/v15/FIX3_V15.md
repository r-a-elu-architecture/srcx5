# SRC-X.5 v1.5: FIX3 (IPFS content id), sealed before D3 is observed again

D3 was not met (`RESULTS_V15.md`): the IPFS step ran `ipfs init -q`, an option kubo does not have, so no content id was
computed; since FIX2 the step cannot block the deploy, so the site went out with `ipfs: null`. That result stands.

Fix: `pages_v152.yml` runs `ipfs init` without the option; nothing else changes. `heartbeat_v152.yml` and
`issue_submit_v152.yml` dispatch it. The v1.5.1 workflows stay unchanged in the private record.

Re-check: D3 as fixed in `PREDICTIONS_V15.md` (status.json carries an IPFS id and at least two mirrors current), observed
once after this push. Reported as v1.5.2 beside the v1.5 result, not in place of it.
