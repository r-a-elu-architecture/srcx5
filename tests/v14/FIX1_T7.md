# FIX1 for T7 (disclosed before T7 ran)
The sealed workflow `.github/workflows/srcx5_anchor_test.yml` checks the seal from `protocol/`, where the seal's one
repository-root path (the workflow itself) cannot be found, so the job would stop before stamping. Found by running that
step locally before any T7 run. `.github/workflows/srcx5_anchor_test_fix1.yml` changes only the seal-check line (run
from the repository root, and also check this fix's seal) and its trigger file. The sealed file is unchanged; T1-T6 are
unaffected (they ran locally from the sealed files). Criteria unchanged.
