#!/usr/bin/env python3
"""SRC-X.5 v1.4 network layer: how anyone, at any layer, connects to the open record (Python standard library only).

The record rules live in srcx5.py (v1.3, sealed, unchanged). This file adds only connection:
  * one shape everywhere: a running node and a static mirror answer the same paths (ids.json, head.json, log.json,
    records/<id>.json), so a client never needs to know which one it reached;
  * sync from any list of peers or mirrors, in order, with failover: the first that answers is used;
  * a hardened node (size limit, rate limit, strict JSON, never crashes on bad input) that also serves the interfaces
    (OpenAPI, JSON Schema, JSON-LD context, mirror list, llms.txt);
  * a JSON-LD / W3C PROV view of every record, for linked-data and science tools;
  * mirror status (which mirrors hold the current head) and anchoring of the head on public networks.

  python srcx5_net.py sync    --log DIR [--peer URL]... [--mirrors MIRRORS.json]   pull what is missing, first peer that answers
  python srcx5_net.py serve   --log DIR [--port 8787] [--peer URL]...              run a node (both shapes + interfaces)
  python srcx5_net.py export  --log DIR --out DIR                                  static mirror: core API + JSON-LD + interfaces
  python srcx5_net.py status  --log DIR [--mirrors MIRRORS.json]                   which mirrors hold this log's head
  python srcx5_net.py anchor  --log DIR [--dir anchors]                            stamp the head on Bitcoin (OpenTimestamps)
"""
import argparse, json, os, shutil, subprocess, sys, threading, time, urllib.request
import srcx5 as core

NET_VERSION = "1.4"
HERE = os.path.dirname(os.path.abspath(__file__))
INTERFACES = ["openapi.json", "schema/record.schema.json", "context.jsonld", "MIRRORS.json", "llms.txt"]
MAX_BODY = 256_000          # bytes per submission
RATE = (30, 60)             # at most 30 submissions per client per 60 s

# ---------- fetching: live node or static mirror, same answer ----------
def fetch(url, timeout=10):
    req = urllib.request.Request(url, headers={"User-Agent": "srcx5/" + NET_VERSION, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r: return r.read()

def _ids(peer):
    """(ids, bytes) from a peer of either shape."""
    base = peer.rstrip("/")
    for path in ("/ids.json", "/ids"):
        try: raw = fetch(base + path); return json.loads(raw), len(raw)
        except Exception: continue
    raise ConnectionError(f"no answer from {peer}")

def _entries(peer, missing):
    """Log entries (in the peer's chain order) for the missing ids: a live node sends only those; a static mirror sends
    its whole log.json, from which only the missing entries are taken."""
    base = peer.rstrip("/")
    try:
        raw = fetch(base + "/log?ids=" + ",".join(missing))
        ent = json.loads(raw)
        if isinstance(ent, list): return ent, len(raw)
    except Exception: pass
    raw = fetch(base + "/log.json"); want = set(missing)
    return [e for e in json.loads(raw) if e["record"]["id"] in want], len(raw)

def sync_one(log, peer):
    ids, moved = _ids(peer)
    missing = [i for i in ids if i not in log.recs]
    if not missing: return 0, moved
    ent, n = _entries(peer, missing); moved += n
    added = 0
    for e in ent:
        r = e.get("record", {})
        if core.rec_id(r) != r.get("id"): continue           # a record that does not match its own hash is never taken
        if not log.admit(r): added += 1
    return added, moved

def load_mirrors(path=None):
    p = path or os.path.join(HERE, "MIRRORS.json")
    try: return [m["url"] for m in json.load(open(p))["mirrors"]]
    except Exception: return []

def sync_any(log, peers):
    """Try each peer in order; the first that answers is used. Returns (peer, added, bytes, tried)."""
    tried = []
    for p in peers:
        try:
            a, m = sync_one(log, p); return p, a, m, tried + [(p, "ok")]
        except Exception as e:
            tried.append((p, type(e).__name__))
    raise ConnectionError("no peer answered: " + ", ".join(f"{p} ({w})" for p, w in tried))

# ---------- linked data: a record as W3C PROV in JSON-LD ----------
def ld(rec):
    i = rec["id"]; t = rec.get("type")
    d = {"@context": "https://r-a-elu-architecture.github.io/srcx5/context.jsonld", "@id": f"urn:srcx5:{i}",
         "@type": ["prov:Entity", "srcx5:" + str(t).capitalize()], "srcx5:id": i, "dct:title": rec.get("title"),
         "srcx5:evidence": rec.get("evidence"), "srcx5:criteriaMet": (rec.get("outcome") or {}).get("criteria_met")}
    if rec.get("purpose"): d["dct:description"] = rec["purpose"]
    seal = rec.get("seal") or {}
    if seal.get("sealed_at"): d["srcx5:sealedAt"] = {"@value": seal["sealed_at"], "@type": "xsd:dateTime"}
    if seal.get("files"): d["srcx5:fingerprint"] = [{"prov:atLocation": f["path"], "srcx5:sha256": f["sha256"]} for f in seal["files"]]
    run = rec.get("run") or {}
    if run.get("started_at"):
        d["prov:wasGeneratedBy"] = {"@type": "prov:Activity", "prov:startedAtTime": {"@value": run["started_at"], "@type": "xsd:dateTime"}}
    par = (rec.get("lineage") or {}).get("parents") or []
    if par: d["prov:wasDerivedFrom"] = [{"@id": f"urn:srcx5:{p}"} for p in par]
    if rec.get("replicates"): d["srcx5:replicates"] = {"@id": f"urn:srcx5:{rec['replicates']}"}
    if rec.get("supersedes"): d["prov:wasRevisionOf"] = {"@id": f"urn:srcx5:{rec['supersedes']}"}
    if rec.get("by"): d["prov:wasAttributedTo"] = {"@type": "prov:Agent", "foaf:name": rec["by"]}
    return {k: v for k, v in d.items() if v is not None}

# ---------- static mirror: the core API + linked data + interfaces ----------
def export(log, out):
    log.export(out)                                          # ids.json, active.json, head.json, log.json, records/<id>.json
    os.makedirs(os.path.join(out, "ld"), exist_ok=True)
    for i, r in log.recs.items(): json.dump(ld(r), open(os.path.join(out, "ld", f"{i}.jsonld"), "w"), ensure_ascii=False, indent=1)
    h = json.load(open(os.path.join(out, "head.json"))); h["transport"] = NET_VERSION
    json.dump(h, open(os.path.join(out, "head.json"), "w"))
    for f in INTERFACES:
        src = os.path.join(HERE, f)
        if os.path.exists(src):
            os.makedirs(os.path.dirname(os.path.join(out, f)) or out, exist_ok=True); shutil.copy(src, os.path.join(out, f))
    os.makedirs(os.path.join(out, ".well-known"), exist_ok=True)
    json.dump({"protocol": "SRC-X.5", "record": core.VERSION, "transport": NET_VERSION, "head": log.head(), "count": len(log.entries),
               "api": "openapi.json", "schema": "schema/record.schema.json", "context": "context.jsonld", "mirrors": "MIRRORS.json"},
              open(os.path.join(out, ".well-known", "srcx5.json"), "w"), indent=1)

# ---------- node: both shapes, the interfaces, hardened ----------
def serve(log, port, peers=(), quiet=True):
    srv = core.serve(log, port, (), quiet)
    Base = srv.RequestHandlerClass
    hits, lock = {}, threading.Lock()
    def files(name):
        p = os.path.join(HERE, name)
        return open(p, "rb").read() if os.path.exists(p) else None
    class H(Base):
        def handle_one_request(s):
            try: super().handle_one_request()
            except Exception:
                try: s._send(400, {"error": "bad request"})
                except Exception: pass
        def do_GET(s):
            path = s.path.partition("?")[0]
            if path == "/ids.json": return s._send(200, sorted(log.recs))
            if path == "/active.json": return s._send(200, sorted(log.active()))
            if path in ("/head.json", "/head"): return s._send(200, {"head": log.head(), "count": len(log.entries), core.KEY: core.VERSION, "transport": NET_VERSION})
            if path == "/log.json": return s._send(200, log.entries)
            if path.startswith("/records/") and path.endswith(".json"):
                r = log.recs.get(path[len("/records/"):-5]); return s._send(200, r) if r else s._send(404, {"error": "unknown id"})
            if path.startswith("/ld/") and path.endswith(".jsonld"):
                r = log.recs.get(path[len("/ld/"):-7]); return s._send(200, ld(r)) if r else s._send(404, {"error": "unknown id"})
            if path == "/.well-known/srcx5.json":
                return s._send(200, {"protocol": "SRC-X.5", "record": core.VERSION, "transport": NET_VERSION, "head": log.head(),
                                     "count": len(log.entries), "api": "openapi.json", "schema": "schema/record.schema.json",
                                     "context": "context.jsonld", "mirrors": "MIRRORS.json"})
            if path.lstrip("/") in INTERFACES:
                b = files(path.lstrip("/"))
                if b is not None: return s._send(200, b)
            if path in ("/", "/health"):
                return s._send(200, {core.KEY: core.VERSION, "transport": NET_VERSION, "records": len(log.recs), "active": len(log.active()),
                                     "head": log.head(), "mission": core.MISSION, "checks": [c[0] for c in core.CHECKS],
                                     "api": ["/ids", "/ids.json", "/active", "/head", "/log", "/log.json", "/record/<id>", "/records/<id>.json",
                                             "/ld/<id>.jsonld", "/openapi.json", "/.well-known/srcx5.json", "POST /submit"]})
            return super().do_GET()
        def do_POST(s):
            if s.path != "/submit": return s._send(404, {"error": "not found"})
            ip = s.client_address[0]; now = time.time()
            with lock:
                q = [t for t in hits.get(ip, []) if now - t < RATE[1]]
                if len(q) >= RATE[0]: return s._send(429, {"error": "too many submissions; retry later"})
                hits[ip] = q + [now]
            try: n = int(s.headers.get("Content-Length", ""))
            except ValueError: return s._send(411, {"error": "Content-Length required"})
            if n < 0 or n > MAX_BODY: return s._send(413, {"error": f"record larger than {MAX_BODY} bytes"})
            try: rec = json.loads(s.rfile.read(n).decode("utf-8"))
            except Exception: return s._send(422, {"admitted": False, "reasons": ["not valid UTF-8 JSON"]})
            if not isinstance(rec, dict): return s._send(422, {"admitted": False, "reasons": ["a record is a JSON object"]})
            try: R = log.admit(rec)
            except Exception as e: R = [f"refused: {type(e).__name__}"]
            return s._send(201 if not R else 202, {"admitted": not R, "quarantined": bool(R), "id": rec.get("id"), "reasons": R, "head": log.head()})
        def do_PUT(s): return s._send(405, {"error": "the record is append-only"})
        do_DELETE = do_PATCH = do_PUT
        def do_OPTIONS(s):
            s.send_response(204); s.send_header("Access-Control-Allow-Origin", "*"); s.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            s.send_header("Access-Control-Allow-Headers", "Content-Type"); s.end_headers()
    srv.RequestHandlerClass = H
    if peers:
        try: print("synced", sync_any(log, peers)[:3], file=sys.stderr)
        except Exception as e: print("no peer answered:", e, file=sys.stderr)
    return srv

# ---------- mirrors and anchors ----------
def status(log, mirrors):
    out = []
    for m in mirrors:
        try:
            h = json.loads(fetch(m.rstrip("/") + "/head.json"))
            out.append({"mirror": m, "state": "current" if h.get("head") == log.head() else "stale", "count": h.get("count")})
        except Exception as e: out.append({"mirror": m, "state": "down", "why": type(e).__name__})
    return out

def anchor(log, d):
    """Stamp the log head on Bitcoin through OpenTimestamps (free; proof final after a few hours, `ots upgrade`)."""
    os.makedirs(d, exist_ok=True); head = log.head(); base = os.path.join(d, head)
    open(base, "w").write(head + "\n")
    if not os.path.exists(base + ".ots"):
        subprocess.run(["ots", "stamp", base], check=True)
    st = subprocess.run(["ots", "upgrade", base + ".ots"], capture_output=True, text=True)
    final = "Success" in (st.stdout + st.stderr) or "complete" in (st.stdout + st.stderr).lower()
    rec = {"head": head, "count": len(log.entries), "network": "bitcoin", "method": "opentimestamps", "proof": os.path.basename(base) + ".ots",
           "status": "confirmed" if final else "pending"}
    json.dump(rec, open(base + ".json", "w"), indent=1)
    return rec

# ---------- command line ----------
def main(argv=None):
    ap = argparse.ArgumentParser(prog="srcx5_net", description="SRC-X.5 v1.4 network layer"); sub = ap.add_subparsers(dest="cmd", required=True)
    y = sub.add_parser("sync"); y.add_argument("--log", required=True); y.add_argument("--peer", action="append", default=[]); y.add_argument("--mirrors")
    s = sub.add_parser("serve"); s.add_argument("--log", required=True); s.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8787)))
    s.add_argument("--peer", action="append", default=[])
    x = sub.add_parser("export"); x.add_argument("--log", required=True); x.add_argument("--out", required=True)
    t = sub.add_parser("status"); t.add_argument("--log", required=True); t.add_argument("--mirrors")
    a = sub.add_parser("anchor"); a.add_argument("--log", required=True); a.add_argument("--dir", default="anchors")
    A = ap.parse_args(argv); L = core.Log(A.log)
    if A.cmd == "sync":
        p, n, m, tried = sync_any(L, A.peer + load_mirrors(A.mirrors)); print(f"from {p}: added {n} records, {m} bytes moved; tried {tried}"); return 0
    if A.cmd == "serve":
        srv = serve(L, A.port, A.peer, quiet=False); print(f"SRC-X.5 node (transport {NET_VERSION}) on :{A.port}, {len(L.recs)} records", file=sys.stderr)
        srv.serve_forever()
    if A.cmd == "export": export(L, A.out); print("exported to", A.out); return 0
    if A.cmd == "status": r = status(L, load_mirrors(A.mirrors)); print(json.dumps(r, indent=1)); return 0 if all(x["state"] == "current" for x in r) else 1
    if A.cmd == "anchor": print(json.dumps(anchor(L, A.dir))); return 0

if __name__ == "__main__":
    sys.exit(main())
