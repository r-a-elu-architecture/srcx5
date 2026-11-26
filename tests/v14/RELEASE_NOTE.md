# Release note (v1.4.1, owner decision 26 Nov 2026)
- The public repository runs `.github/workflows/anchor_v141.yml`, which anchors with `srcx5_anchor.py` (FIX2).
- The sealed `.github/workflows/anchor.yml` (in `SEAL_V14.txt`) is kept unchanged in the private research repository
  and left out of the public tree, so it cannot write a wrong status label. Its seal line, and the two lines for the
  T7 workflows (`.github/workflows/srcx5_anchor_test*.yml`, which live in the private repository), are the only lines
  of `SEAL_V14.txt` that cannot be checked from the public tree; every other line can.
- `anchors/` holds the first anchor of the public log: head d3d70d58…cbdda on Bitcoin (OpenTimestamps), from T7.
