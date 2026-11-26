#!/usr/bin/env python3
"""SRC-X.5 anchors (v1.4.1): stamp the log head on Bitcoin through OpenTimestamps, upgrade pending proofs, report status.
Replaces `srcx5_net.py anchor`, whose status label read "confirmed" for pending proofs (disclosed in tests/v14/FIX2_ANCHOR.md).
Status comes from the proof itself: confirmed only when it holds a Bitcoin block-header attestation.

  python srcx5_anchor.py stamp  --log log --dir anchors     stamp the current head (if not yet stamped), then upgrade
  python srcx5_anchor.py status --dir anchors               upgrade every proof and report pending / confirmed
"""
import argparse, glob, json, os, subprocess
import srcx5 as core

def state(ots_file):
    subprocess.run(["ots", "upgrade", ots_file], capture_output=True, text=True)
    info = subprocess.run(["ots", "info", ots_file], capture_output=True, text=True).stdout
    return "confirmed" if "BitcoinBlockHeaderAttestation" in info else "pending"

def record(d, head, count):
    base = os.path.join(d, head); st = state(base + ".ots")
    rec = {"head": head, "count": count, "network": "bitcoin", "method": "opentimestamps", "proof": head + ".ots", "status": st}
    json.dump(rec, open(base + ".json", "w"), indent=1); return rec

def stamp(log, d):
    os.makedirs(d, exist_ok=True); head = log.head(); base = os.path.join(d, head)
    if not os.path.exists(base): open(base, "w").write(head + "\n")
    if not os.path.exists(base + ".ots"): subprocess.run(["ots", "stamp", base], check=True)
    return record(d, head, len(log.entries))

def status(d):
    out = []
    for f in sorted(glob.glob(os.path.join(d, "*.json"))):
        r = json.load(open(f))
        if os.path.exists(os.path.join(d, r.get("proof", ""))): out.append(record(d, r["head"], r.get("count")))
    return out

def main(argv=None):
    ap = argparse.ArgumentParser(prog="srcx5_anchor"); sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("stamp"); s.add_argument("--log", required=True); s.add_argument("--dir", default="anchors")
    t = sub.add_parser("status"); t.add_argument("--dir", default="anchors")
    A = ap.parse_args(argv)
    print(json.dumps(stamp(core.Log(A.log), A.dir) if A.cmd == "stamp" else status(A.dir), indent=1))

if __name__ == "__main__":
    main()
