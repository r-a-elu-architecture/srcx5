#!/usr/bin/env python3
"""RSOS Sealed Claims (RSC) v1.2: reference node, command-line tool and sync, in one file (Python standard library only).

A sealed claim record says, checkably: what was intended, what was predicted and by which criteria, which files were
fixed (fingerprinted) and when, when it ran, what came out, who replicated it, where it came from, and that it carries
no personal data. Specification: SPEC.md. Licence: Apache 2.0.

  python rsc.py verify  <record.json>... [--repo DIR]   check records (and, with --repo, every fingerprinted file)
  python rsc.py admit   <record.json> --log DIR         run admission and append to a log
  python rsc.py create  --title T --purpose P --criteria C --seal-file F --sealed-at ISO [--run-at ISO] [--parent ID] > rec.json
  python rsc.py replicate <record-id> --by NAME --outcome all|partly|none --summary S [--log DIR] > rep.json
  python rsc.py serve   --log DIR [--port 8787] [--peer URL]...   run a node (HTTP API below)
  python rsc.py sync    --log DIR --peer URL                    pull only the records this log lacks
  python rsc.py check-log --log DIR                             verify the whole hash chain

HTTP API of a node: GET /ids, GET /record/<id>, GET /log, GET /head, POST /submit (JSON record) -> 201 or 422 with reasons.
"""
import argparse, hashlib, json, os, re, sys, threading, urllib.request
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

VERSION = "1.2"
VERSIONS = ("1.2",)
TYPES = ("claim", "replication", "forecast", "health")
EVIDENCE = ("real", "simulated", "both")   # where the claim was shown
OUTCOMES = ("all", "partly", "none", "pending")
REQUIRED = {"claim": ("title", "purpose", "prediction", "seal", "outcome", "lineage", "consent_harm"),
            "replication": ("title", "replicates", "outcome", "by", "consent_harm"),
            "forecast": ("title", "purpose", "prediction", "seal", "outcome", "consent_harm"),
            "health": ("title", "by", "audits", "outcome", "consent_harm")}

MISSION = ("Healing, transforming and evolving, and signalling this to others, for the growth, development, "
           "transformation and healing of all living beings.")
CHECKS = [("DISCLOSURE", "disclosed and logged before it runs: content matches its id, criteria stated, sealed before the run"),
          ("CONSENT_PRIVACY", "no personal data; everyone affected has consented"),
          ("HARM_BOUND", "declared predicted harm at or below 0.3"),
          ("CONFORMANCE", "version, evidence domain, lineage and references are valid"),
          ("NON_BLOCKING", "a valid record is never blocked (measured in every proof)"),
          ("ATTRIBUTION", "a measured outcome carries fingerprinted results; a replication names who made it"),
          ("PURPOSE", "declares that it serves the stated mission")]
HARM_MAX = 0.3
def _luhn(d):
    d = [int(c) for c in d if c.isdigit()]; t = 0
    for i, x in enumerate(reversed(d)): t += x if i % 2 == 0 else (x * 2 - 9 if x > 4 else x * 2)
    return t % 10 == 0

PERSONAL = [("email address", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), None),
            ("phone number", re.compile(r"\+\d{1,3}[ \-]?\(?\d{1,4}\)?(?:[ \-]?\d{2,4}){2,4}"), None),
            ("payment card number", re.compile(r"\b(?:\d[ -]?){13,19}\b"), _luhn),
            ("IBAN", re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b"), None)]
ALLOW_KEYS = {"sha256", "id", "parents", "prev", "entry_hash", "replicates", "seal_hash", "commit", "run_id"}

# ---------- canonical form and identity ----------
def canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()

def sha(b): return hashlib.sha256(b).hexdigest()

def body(rec): return {k: v for k, v in rec.items() if k != "id"}

def rec_id(rec): return sha(canon(body(rec)))

def finalize(rec):
    rec = dict(rec); rec.setdefault("rsc", VERSION); rec["id"] = rec_id(rec); return rec

def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")) if isinstance(s, str) else None

# ---------- admission: the same rules in the node, the CLI and the public workflow ----------
def _strings(x, path=""):
    if isinstance(x, dict):
        for k, v in x.items():
            if k in ALLOW_KEYS: continue
            yield from _strings(v, f"{path}.{k}")
    elif isinstance(x, list):
        for i, v in enumerate(x): yield from _strings(v, f"{path}[{i}]")
    elif isinstance(x, str): yield path, x

def _identity(rec): return (rec.get("lineage") or {}).get("identity") or rec.get("id")

def check(rec, known=None, repo=None, known_recs=None):
    """Return a list of reasons; empty means admitted. known: ids already in the log."""
    R = []
    if not isinstance(rec, dict): return ["not a JSON object"]
    if rec.get("rsc") not in VERSIONS: R.append(f"[CONFORMANCE] rsc version must be one of {VERSIONS}")
    t = rec.get("type")
    if t not in TYPES: R.append(f"type must be one of {TYPES}"); return R
    for k in REQUIRED[t]:
        if k not in rec: R.append(f"[DISCLOSURE] missing field: {k}")
    if R: return R
    if rec.get("id") != rec_id(rec): R.append("[DISCLOSURE] id does not match the record's content (tampered or forged)")
    out = rec["outcome"]
    if not isinstance(out, dict) or out.get("criteria_met") not in OUTCOMES: R.append(f"outcome.criteria_met must be one of {OUTCOMES}")
    if t in ("claim", "forecast"):
        p, s = rec["prediction"], rec["seal"]
        if not isinstance(p, dict) or not p.get("criteria"): R.append("[DISCLOSURE] prediction.criteria must state the pass criteria")
        if not isinstance(s, dict) or not s.get("sealed_at") or not isinstance(s.get("files"), list) or not s["files"]:
            R.append("[DISCLOSURE] seal must list fingerprinted files and sealed_at")
        else:
            for f in s["files"]:
                if not (isinstance(f, dict) and re.fullmatch(r"[0-9a-f]{64}", str(f.get("sha256", ""))) and f.get("path")):
                    R.append(f"seal file entry invalid: {f}"); break
            sa, ra = ts(s.get("sealed_at")), ts((rec.get("run") or {}).get("started_at"))
            if sa is None: R.append("seal.sealed_at is not an ISO time")
            elif sa > datetime.now(sa.tzinfo): R.append("[DISCLOSURE] sealed in the future: a seal cannot be dated after its own arrival")
            if ra is not None and sa is not None and not sa < ra: R.append("[DISCLOSURE] sealed after the run started (seal must precede the run)")
            if t == "claim" and out.get("criteria_met") != "pending" and ra is None: R.append("[ATTRIBUTION] a claim with an outcome must give run.started_at")
            if repo:
                for f in s["files"]:
                    fp = os.path.join(repo, f["path"])
                    if not os.path.exists(fp): R.append(f"fingerprinted file missing in repo: {f['path']}")
                    elif sha(open(fp, "rb").read()) != f["sha256"]: R.append(f"fingerprint mismatch: {f['path']}")
    if t == "replication" and known is not None and rec["replicates"] not in known: R.append("[CONFORMANCE] replicates an unknown record")
    for par in (rec.get("lineage") or {}).get("parents", []) if isinstance(rec.get("lineage"), dict) else []:
        if known is not None and par not in known: R.append(f"[CONFORMANCE] lineage parent not in the log: {par[:12]}")
    if True:
        if rec.get("evidence") not in EVIDENCE: R.append(f"[CONFORMANCE] evidence must be one of {EVIDENCE}")
        sp = rec.get("declarations")
        if not isinstance(sp, dict): R.append("[DISCLOSURE] declarations missing")
        else:
            if t != "health" and not rec.get("purpose") and t != "replication": R.append("[DISCLOSURE] purpose not disclosed")
            if sp.get("affects_people") and sp.get("consent") is not True: R.append("[CONSENT_PRIVACY] people are affected and consent is not declared")
            try:
                if float(sp.get("predicted_harm", 0)) > HARM_MAX: R.append(f"[HARM_BOUND] predicted harm above {HARM_MAX}")
            except (TypeError, ValueError): R.append("[HARM_BOUND] predicted harm is not a number")
            if sp.get("serves_mission") is not True: R.append("[PURPOSE] does not declare that it serves the mission")
        if out.get("criteria_met") not in ("pending", None) and t in ("claim", "forecast"):
            if not out.get("result_files"): R.append("[ATTRIBUTION] an outcome must be measured: result files with fingerprints")
        if t == "replication" and not rec.get("by"): R.append("[ATTRIBUTION] a replication must be attributed")
        sup = rec.get("supersedes")
        if sup is not None:
            if known is not None and sup not in known: R.append("[CONFORMANCE] supersedes an unknown record")
            held = (known_recs or {}).get(sup)
            if held is not None and (rec.get("lineage") or {}).get("identity") != _identity(held):
                R.append("[CONFORMANCE] identity must hold: a superseding record keeps the identity of what it supersedes")
    def _floats(x):
        if isinstance(x, float): return True
        if isinstance(x, dict): return any(_floats(v) for v in x.values())
        if isinstance(x, list): return any(_floats(v) for v in x)
        return False
    if _floats(rec): R.append("numbers must be integers or strings (one canonical form in every language)")
    ch = rec["consent_harm"]
    if not isinstance(ch, dict) or ch.get("personal_data") is not False: R.append("[CONSENT_PRIVACY] consent_harm.personal_data must be false (no personal data in the open log)")
    for path, sv in _strings(rec):
        for name, rx, extra in PERSONAL:
            m = rx.search(sv)
            if m and (extra is None or extra(m.group(0))): R.append(f"[CONSENT_PRIVACY] possible {name} in {path}"); break
    return R

# ---------- the log: append-only, hash-chained, one JSON line per entry ----------
class Log:
    def __init__(s, d):
        s.d = d; os.makedirs(d, exist_ok=True); s.f = os.path.join(d, "log.jsonl"); s.lock = threading.Lock()
        s.entries = [json.loads(l) for l in open(s.f)] if os.path.exists(s.f) else []
        s.recs = {}
        for e in s.entries: s.recs[e["record"]["id"]] = e["record"]

    def head(s): return s.entries[-1]["entry_hash"] if s.entries else "0" * 64

    def admit(s, rec):
        with s.lock:
            held = s.recs.get(rec.get("id")) if isinstance(rec, dict) else None
            if held is not None:                            # same id: identical content is a no-op, anything else is tampering
                return [] if canon(held) == canon(rec) else ["id already held with different content (tampered copy)"]
            R = check(rec, known=set(s.recs), known_recs=s.recs)
            if R:                                           # quarantined, not published: kept with its reasons, never deleted
                os.makedirs(os.path.join(s.d, "quarantine"), exist_ok=True)
                with open(os.path.join(s.d, "quarantine", "quarantine.jsonl"), "a") as fh:
                    fh.write(json.dumps({"reasons": R, "id": rec.get("id") if isinstance(rec, dict) else None}, ensure_ascii=False) + "\n")
                return R
            e = {"seq": len(s.entries), "prev": s.head(), "record": rec}
            e["entry_hash"] = sha(canon(e)); s.entries.append(e); s.recs[rec["id"]] = rec
            with open(s.f, "a") as fh: fh.write(json.dumps(e, sort_keys=True, ensure_ascii=False) + "\n")
            return []

    def active(s):
        """The active set: every record not superseded by a later one (a modified clone with the same identity replaces it)."""
        gone = {r.get("supersedes") for r in s.recs.values() if r.get("supersedes")}
        return [i for i in s.recs if i not in gone]

    def verify_chain(s):
        prev = "0" * 64; bad = []
        for i, e in enumerate(s.entries):
            x = {k: v for k, v in e.items() if k != "entry_hash"}
            if e["seq"] != i or e["prev"] != prev or sha(canon(x)) != e["entry_hash"]: bad.append(i)
            if rec_id(e["record"]) != e["record"]["id"]: bad.append(i)
            prev = e["entry_hash"]
        return sorted(set(bad))

    def export(s, out):
        """Static read API for GitHub Pages: ids.json, head.json, log.json, records/<id>.json."""
        os.makedirs(os.path.join(out, "records"), exist_ok=True)
        json.dump(sorted(s.recs), open(os.path.join(out, "ids.json"), "w"))
        json.dump(sorted(s.active()), open(os.path.join(out, "active.json"), "w"))
        json.dump({"head": s.head(), "count": len(s.entries), "rsc": VERSION}, open(os.path.join(out, "head.json"), "w"))
        json.dump(s.entries, open(os.path.join(out, "log.json"), "w"), ensure_ascii=False, indent=1)
        for i, r in s.recs.items(): json.dump(r, open(os.path.join(out, "records", f"{i}.json"), "w"), ensure_ascii=False, indent=1)

# ---------- sync: send only what the receiver lacks ----------
def get(url):
    with urllib.request.urlopen(url, timeout=30) as r: return r.read()

def sync(log, peer):
    """Pull from peer only the records this log lacks, in the peer's log order. Returns (added, bytes moved)."""
    moved = 0; raw = get(peer.rstrip("/") + "/ids"); moved += len(raw)
    missing = [i for i in json.loads(raw) if i not in log.recs]
    if not missing: return 0, moved
    raw = get(peer.rstrip("/") + "/log?ids=" + ",".join(missing)); moved += len(raw)
    added = 0
    for e in json.loads(raw):
        if not log.admit(e["record"]): added += 1
    return added, moved

# ---------- peer audit ----------
def audit(log, peer):
    """Two independent signals about a peer: (1) its own chain does not verify; (2) a record it serves differs from ours.
    Drift is raised only when both agree (never act on a single signal)."""
    entries = json.loads(get(peer.rstrip("/") + "/log"))
    tmp = Log.__new__(Log); tmp.entries = entries; tmp.recs = {e["record"].get("id"): e["record"] for e in entries}
    s1 = tmp.verify_chain() != []
    s2 = any(i in log.recs and canon(log.recs[i]) != canon(r) for i, r in tmp.recs.items()) or \
         any(rec_id(e["record"]) != e["record"].get("id") for e in entries)
    return {"peer": peer, "chain_broken": s1, "content_differs": s2, "drift": bool(s1 and s2), "entries": len(entries)}

# ---------- node ----------
def serve(log, port, peers=(), quiet=False):
    class H(BaseHTTPRequestHandler):
        def log_message(s, *a):
            if not quiet: super().log_message(*a)
        def _send(s, code, obj):
            b = obj if isinstance(obj, bytes) else json.dumps(obj, ensure_ascii=False).encode()
            s.send_response(code); s.send_header("Content-Type", "application/json"); s.send_header("Access-Control-Allow-Origin", "*")
            s.send_header("Content-Length", str(len(b))); s.end_headers(); s.wfile.write(b)
        def do_GET(s):
            path, _, q = s.path.partition("?")
            if path == "/ids": return s._send(200, sorted(log.recs))
            if path == "/head": return s._send(200, {"head": log.head(), "count": len(log.entries), "rsc": VERSION})
            if path == "/log":
                want = set(q.split("=", 1)[1].split(",")) if q.startswith("ids=") else None
                return s._send(200, [e for e in log.entries if want is None or e["record"]["id"] in want])
            if path.startswith("/record/"):
                r = log.recs.get(path[len("/record/"):]); return s._send(200, r) if r else s._send(404, {"error": "unknown id"})
            if path == "/active": return s._send(200, sorted(log.active()))
            if path in ("/", "/health"): return s._send(200, {"rsc": VERSION, "records": len(log.recs), "active": len(log.active()), "head": log.head(),
                                                         "mission": MISSION, "checks": [c[0] for c in CHECKS],
                                                         "api": ["/ids", "/active", "/head", "/log", "/record/<id>", "POST /submit"]})
            return s._send(404, {"error": "not found"})
        def do_POST(s):
            if s.path != "/submit": return s._send(404, {"error": "not found"})
            n = int(s.headers.get("Content-Length", 0))
            if n > 1_000_000: return s._send(413, {"error": "record too large"})
            try: rec = json.loads(s.rfile.read(n))
            except Exception: return s._send(422, {"admitted": False, "reasons": ["not valid JSON"]})
            R = log.admit(rec)
            return s._send(201 if not R else 202, {"admitted": not R, "quarantined": bool(R), "id": rec.get("id") if isinstance(rec, dict) else None, "reasons": R, "head": log.head()})
    for p in peers:
        try: print("sync from", p, sync(log, p), file=sys.stderr)
        except Exception as e: print("peer unreachable:", p, e, file=sys.stderr)
    srv = ThreadingHTTPServer(("0.0.0.0", port), H)
    return srv

# ---------- command line ----------
def main(argv=None):
    ap = argparse.ArgumentParser(prog="rsc", description="RSOS Sealed Claims v1.0"); sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("verify"); v.add_argument("files", nargs="+"); v.add_argument("--repo")
    a = sub.add_parser("admit"); a.add_argument("file"); a.add_argument("--log", required=True)
    c = sub.add_parser("create")
    for k in ("title", "purpose", "criteria", "seal-file", "sealed-at"): c.add_argument("--" + k, required=True)
    c.add_argument("--run-at"); c.add_argument("--parent", action="append", default=[]); c.add_argument("--repo", default=".")
    r = sub.add_parser("replicate"); r.add_argument("id"); r.add_argument("--by", required=True); r.add_argument("--outcome", required=True, choices=OUTCOMES)
    r.add_argument("--summary", required=True); r.add_argument("--log")
    s = sub.add_parser("serve"); s.add_argument("--log", required=True); s.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8787))); s.add_argument("--peer", action="append", default=[])
    y = sub.add_parser("sync"); y.add_argument("--log", required=True); y.add_argument("--peer", required=True)
    k = sub.add_parser("check-log"); k.add_argument("--log", required=True)
    au = sub.add_parser("audit"); au.add_argument("--log", required=True); au.add_argument("--peer", required=True)
    x = sub.add_parser("export"); x.add_argument("--log", required=True); x.add_argument("--out", required=True)
    A = ap.parse_args(argv)
    if A.cmd == "verify":
        bad = 0
        for f in A.files:
            R = check(json.load(open(f)), repo=A.repo); bad += bool(R)
            print(("OK    " if not R else "FAIL  ") + f + ("" if not R else "\n      " + "\n      ".join(R)))
        return 1 if bad else 0
    if A.cmd == "admit":
        R = Log(A.log).admit(json.load(open(A.file))); print("admitted" if not R else "rejected:\n  " + "\n  ".join(R)); return 1 if R else 0
    if A.cmd == "create":
        files = []
        for line in open(A.seal_file):
            if line.strip() and not line.startswith("#"):
                h, p = line.split(None, 1); files.append({"path": p.strip(), "sha256": h})
        rec = {"type": "claim", "title": A.title, "purpose": A.purpose, "prediction": {"criteria": A.criteria},
               "seal": {"files": files, "seal_file": A.seal_file, "sealed_at": A.sealed_at},
               "run": {"started_at": A.run_at} if A.run_at else {}, "outcome": {"criteria_met": "pending"},
               "lineage": {"parents": A.parent}, "consent_harm": {"personal_data": False}}
        print(json.dumps(finalize(rec), indent=1, ensure_ascii=False)); return 0
    if A.cmd == "replicate":
        rec = {"type": "replication", "title": f"Replication of {A.id[:12]}", "replicates": A.id, "by": A.by,
               "outcome": {"criteria_met": A.outcome, "summary": A.summary}, "consent_harm": {"personal_data": False}}
        rec = finalize(rec); R = check(rec, known=set(Log(A.log).recs) if A.log else None)
        if R: print("\n".join(R), file=sys.stderr); return 1
        print(json.dumps(rec, indent=1, ensure_ascii=False)); return 0
    if A.cmd == "serve":
        L = Log(A.log); srv = serve(L, A.port, A.peer); print(f"RSC node on :{A.port}, {len(L.recs)} records, head {L.head()[:12]}", file=sys.stderr)
        srv.serve_forever()
    if A.cmd == "sync":
        print("added %d records, %d bytes moved" % sync(Log(A.log), A.peer)); return 0
    if A.cmd == "check-log":
        L = Log(A.log); bad = L.verify_chain(); print(f"{len(L.entries)} entries; chain {'intact' if not bad else 'BROKEN at ' + str(bad)}"); return 1 if bad else 0
    if A.cmd == "audit":
        r = audit(Log(A.log), A.peer); print(json.dumps(r)); return 1 if r["drift"] else 0
    if A.cmd == "export":
        Log(A.log).export(A.out); print("exported to", A.out); return 0

if __name__ == "__main__":
    sys.exit(main())
