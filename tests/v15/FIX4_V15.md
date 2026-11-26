# SRC-X.5 v1.5: FIX4 (IPFS id in its own job), sealed before D3 is observed again

Observed (RESULTS_V15.md and the other session's note, 26 Nov 12:42 UTC): every Pages run whose IPFS step worked
(`pages_v152`, 11:45 and 12:43 UTC) failed at deploy with "No artifacts named github-pages", although the artifact was
uploaded and finalized; every run whose IPFS step failed (`pages_v151`, 11:41 and 11:44 UTC) deployed. A GitHub-side
artifacts fault after 11:45 would show the same pattern; one run separates the two explanations.

Fix: `pages_v153.yml` computes the IPFS id in a separate job (`ipfs`) and passes it to the deploy job as an output; the
deploy job never runs the IPFS tool. `heartbeat_v153.yml` and `issue_submit_v153.yml` dispatch it. The v1.5.2 workflows
stay unchanged in the private record.

Re-check: D3 as fixed in `PREDICTIONS_V15.md`, observed once after this push.
- Deploy succeeds and the live `status.json` carries the id: D3 met (v1.5.3).
- Deploy fails the same way: the cause is outside our files; D3 stays not met and nothing more is changed.
