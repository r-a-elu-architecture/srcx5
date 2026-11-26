# SRC-X.5 v1.5: FIX2 (deployment workflows), sealed before the deployment checks are observed again

## What happened (first push of v1.5.1, commit d0c7a1f in the public repository)
- **D1 container:** the image was built and pushed to ghcr.io, but the check that runs it failed before starting it:
  the check named the container `n`, and Docker requires at least two characters. A fault in the check script, not in
  the image. Run 45812257312.
- **Pages:** the IPFS tool download from dist.ipfs.tech was cut off after two minutes; because that step was required,
  the deploy was skipped and the live mirror kept serving the previous version (nothing broken, nothing new). A design
  fault: an optional step blocked the deploy. Run 45812256698.

## The fix
New workflow files; the sealed ones stay unchanged in the private record and are not active in the public repository
(as `anchor.yml` in v1.4.1):
- `pages_v151.yml`: the IPFS tool comes from the kubo release on GitHub (with retries); the step can no longer block
  the deploy (`continue-on-error`, four-minute limit). Without an id, `status.json` reports `ipfs: null`.
- `docker_v151.yml`: the check's container is named `srcx5node`.
- `heartbeat_v151.yml`, `issue_submit_v151.yml`: dispatch `pages_v151.yml` instead of `pages.yml`.

## Re-check
D1–D4 as fixed in `PREDICTIONS_V15.md`, observed once after this push. The code, the local tests and their results are
unchanged.
