# SRC-X.5 v1.5: FIX5 (deploy restored; IPFS id published beside it), sealed before it is observed

## Observed before this fix
- `rsos-one-seed` Pages deployed normally at 14:36 UTC: the fault is specific to srcx5, not to the account.
- srcx5 deployed at 11:41 and 11:44 UTC (`pages_v151`, IPFS step failed, no id reached the deploy). Every run since
  in which an id was computed and passed to the deploy (5 runs, including FIX4 with the id in its own job) failed with
  "No artifacts named github-pages". The mechanism is not understood; this fix does not depend on it.

## The fix
- `pages_v154.yml`: exactly the deploy steps of `pages_v151.yml` (last good build), with no IPFS step and no id.
- `ipfs_v154.yml`: computes the id from a fresh export of the log and commits it as `site/api/ipfs.json` (only when it
  changes), then starts `pages_v154.yml`. `heartbeat_v154.yml`, `issue_submit_v154.yml` start both.
- The v1.5.3 workflows stay unchanged in the private record.

## Criteria (fixed now, observed once)
- **F5a deploy restored:** `pages_v154` deploys, and the live mirror serves the 1.5 documents (agent card naming the
  public node https://rsos-srcx5.hf.space).
- **F5b IPFS id published:** the live `api/ipfs.json` (Pages, or the raw mirror) carries a CID for the current head.
- D3 as sealed (id inside `status.json`) is **not** claimed by this fix; if F5b holds it is reported as met in this
  alternative form, named as such.
