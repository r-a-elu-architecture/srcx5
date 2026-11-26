# SRC-X.5 v1.5: FIX1 (installed copy), sealed before its re-check

## What happened
The sealed one-pass run of v1.5 (`out/results_15.json`, commit e0a811a5) met T1–T3 and T5–T8. **T4 (install) was not
met**: `pip install` succeeded and the installed `srcx5 check-log` worked, but the installed `srcx5-node export` exited
with an error after writing the agent card. Cause: an installed copy carries only the Python modules; the interface
files (`openapi.json`, `schema/`, `context.jsonld`, `MIRRORS.json`, `NODES.json`, `llms.txt`) were not in the package,
and the modules look for them beside themselves. That result stands as reported: v1.5 as sealed, **not met (T4)**.

## The fix (v1.5.1)
- The sealed modules are unchanged (`srcx5.py`, `srcx5_net.py`, `srcx5_mcp.py`, `srcx5_node.py`, `srcx5_issue.py`).
- New `srcx5_install.py`: the installed commands (`srcx5-node`, `srcx5-net`, `srcx5-mcp`) point those modules at
  `<prefix>/share/srcx5` when the interface files are not beside them, then run them.
- `pyproject.toml` (build configuration): version 1.5.1; ships the interface files under `share/srcx5`; the three
  commands use the launcher. Its sealed v1.5 form stays in commit a9abb2fe.

## Re-check, criteria unchanged
The unchanged sealed harness `run_v15.py` is run once more, all of T1–T8, with the criteria of `PREDICTIONS_V15.md`.
Results go to `out/results_15_fix1.json`; the first results file is kept as it is. Levels as sealed.
