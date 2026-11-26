#!/usr/bin/env python3
"""SRC-X.5 v1.5: submit a record through a GitHub issue (no git needed). Python standard library only.

The issue text is data, never code: it is read from a file, parsed as JSON and checked by the same srcx5.check() every
node runs. Nothing in it is passed to a shell.
  python srcx5_issue.py --body FILE --log DIR [--apply] --out RESULT.json
Without --apply the record is checked against a copy of the log; with --apply an admitted record is appended.
"""
import argparse, json, os, re, shutil, sys, tempfile
import srcx5 as core

def extract(text):
    """The record: the first ```json block, else the first {...} span, else the whole text."""
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    cand = m.group(1) if m else text[text.find("{"): text.rfind("}") + 1] if "{" in text else text
    return json.loads(cand)

def run(body, logdir, apply=False):
    if len(body.encode("utf-8")) > 256_000: return {"admitted": False, "reasons": ["issue text larger than 256 kB"]}
    try: rec = extract(body)
    except Exception: return {"admitted": False, "reasons": ["no JSON record found: paste the record as a ```json block"]}
    if not isinstance(rec, dict): return {"admitted": False, "reasons": ["a record is a JSON object"]}
    target = logdir
    if not apply:
        target = tempfile.mkdtemp(prefix="srcx5_issue_"); shutil.copy(os.path.join(logdir, "log.jsonl"), os.path.join(target, "log.jsonl"))
    log = core.Log(target)
    try: R = log.admit(rec)
    except Exception as e: R = [f"refused: {type(e).__name__}"]
    return {"admitted": not R, "quarantined": bool(R), "id": rec.get("id"), "reasons": R, "head": log.head(), "applied": apply and not R}

def main(argv=None):
    ap = argparse.ArgumentParser(prog="srcx5_issue"); ap.add_argument("--body", required=True); ap.add_argument("--log", required=True)
    ap.add_argument("--apply", action="store_true"); ap.add_argument("--out", required=True)
    A = ap.parse_args(argv)
    res = run(open(A.body, encoding="utf-8", errors="replace").read(), A.log, A.apply)
    json.dump(res, open(A.out, "w"), indent=1); print(json.dumps(res))

if __name__ == "__main__":
    main()
