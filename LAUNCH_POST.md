# Launch post (draft for the owner's approval)

**Title:** Sealed before it ran: an open method that beat plain rollout on three unrelated hosts, and an open record anyone can check

Every test below was fingerprinted and pushed before its first cell ran, with its pass criteria fixed in advance.
Every test whose criteria were not met is published next to the ones that were.

- Two real AI models on a split-information question, 200 fresh questions: **200 of 200 correct** (plain rollout 175)
  with **51 % fewer tokens**.
- AI agents: **43 % fewer tokens** at higher accuracy (0.95 vs 0.83), 44 of 48 cells.
- Satellite downlink: better in **all 20** fresh cells.

Check it yourself in under a minute:

    git clone <research repository> && cd <it> && pip install numpy scipy && bash reproduce_conf6.sh

Every claim is also a record in SRC-X.5, an open, append-only log. The viewer re-checks each record in your
browser; `python srcx5.py serve` makes you a node; one command adds a replication. Before launch its admission check
caught 600 of 600 forged, tampered and personal-data records without blocking a single valid one.

Paper (with the limits and every disclosed error), code under Apache 2.0, the specification under CC BY 4.0. Criticism
is welcome where it lands: as an issue, or as a replication record.
