# SRC-X.5

*An open record of sealed claims, verified at the source.* Written `srcx5` in code. v1.3 renames v1.2 ("RSOS Sealed Claims"); every rule is unchanged and every earlier record keeps its id.

**An open record of claims that anyone can check.** Each record says what was predicted and by which criteria, which
files were fixed and when, when it ran, what came out, and who replicated it. No personal data. Any field.

- **See it:** the [live record](https://r-a-elu-architecture.github.io/rsos-sealed-claims/) re-checks every record in your browser.
- **Check it:** `python srcx5.py verify records/CONF6.json --repo <research checkout>` checks every fingerprint byte for byte.
- **Run a node:** `python srcx5.py serve --log log --peer <node>`. It syncs only what it lacks, and re-checks every record.
- **Add to it:** put a record in `submissions/` and open a pull request; the admission check answers with reasons.
- **Replicate:** `python srcx5.py replicate <id> --by <handle> --outcome all|partly|none --summary "…"`.

Every record passes seven checks (DISCLOSURE, CONSENT_PRIVACY, HARM_BOUND, CONFORMANCE, NON_BLOCKING, ATTRIBUTION,
PURPOSE). Nothing is prohibited from being submitted: what fails a check is quarantined with its reasons and never
published, and nothing is deleted. A record is replaced by a modified clone that keeps its identity, and nodes audit each
other (`srcx5.py audit`).

One file (`srcx5.py`, Python standard library only) is the node, the command-line tool and the sync. The same admission
function runs in every node, on every laptop and in the public workflow. Specification: [`SPEC_SRCX5.md`](SPEC_SRCX5.md) (v1.3; the v1.2 text stays in `SPEC.md`).

## What is in the log on day one
The sealed tests of the RSOS research release, including the ones whose criteria were not met, and the protocol's own
launch proofs. Each was fingerprinted and pushed before it ran.

| Record | Pre-registered criteria |
|---|---|
| CONF6: whole AI–AI system bound to one RSOS structure vs plain rollout | all met: accuracy 1.000 vs 0.875, 51 % fewer tokens |
| CONF5: identified RSOS structure vs plain rollout | met in 2 of 3 rows |
| CONF1–CONF4, ABL1, STRUCT1, REAL3 | all, partly or not met, as they came |
| Launch proof: immune (admission against 15 attack classes) | see `tests/RESULTS.md` |
| Launch proof: sync (three live nodes) | see `tests/RESULTS.md` |
| Proof: checks, supersede, peer audit | see `tests/RESULTS.md` |

## Licence
Code Apache 2.0 ([`LICENSE`](LICENSE)); specification text CC BY 4.0.
