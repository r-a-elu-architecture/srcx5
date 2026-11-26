"""RSC v1.2 proofs (pass criteria in tests/PREDICTIONS_V12.md, sealed before the confirming run). Seed 1 = screen.
  python tests/proofs_v11.py <seed>
CHECKS: one violation per check is quarantined and names that check; NON_BLOCKING: no valid record is blocked.
SUPERSEDE: identity holds, the old record leaves the active whole but stays in the log; an identity change is contained.
PEER AUDIT: a peer with a corrupted stored entry is flagged (two signals agree); a clean peer and a peer that is only behind are not."""
import os, sys, json, copy, random, tempfile, threading
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, ROOT)
import rsc
IDX = json.load(open(os.path.join(ROOT, "records", "INDEX.json")))
BASE = [json.load(open(os.path.join(ROOT, "records", f"{k}.json"))) for k in IDX]

def valid(rng, i):
    r = copy.deepcopy(rng.choice(BASE)); r.pop("id"); r.pop("supersedes", None)
    r["title"] += f" (variant {i}-{rng.randrange(10**9)})"; r["lineage"] = {"parents": []}; return rsc.finalize(r)

def violate(v, check_name):
    a = copy.deepcopy(v); a.pop("id")
    if check_name == "DISCLOSURE": a["seal"]["sealed_at"] = "2027-01-01T00:00:00Z"
    elif check_name == "CONSENT_PRIVACY": a["declarations"]["affects_people"] = True; a["declarations"].pop("consent", None)
    elif check_name == "HARM_BOUND": a["declarations"]["predicted_harm"] = 0.5
    elif check_name == "CONFORMANCE": a["evidence"] = "elsewhere"
    elif check_name == "ATTRIBUTION": a["outcome"]["result_files"] = []
    elif check_name == "PURPOSE": a["declarations"]["serves_mission"] = False
    return rsc.finalize(a)

def fresh_log(d):
    L = rsc.Log(d)
    src = rsc.Log(os.path.join(ROOT, "log"))
    for e in src.entries: assert not L.admit(e["record"]), "base log must re-admit"
    return L

def checks(rng):
    L = fresh_log(tempfile.mkdtemp()); V = [valid(rng, i) for i in range(200)]
    blocked = sum(bool(L.admit(v)) for v in V)                     # NON_BLOCKING
    res = {}
    for check_name in ("DISCLOSURE", "CONSENT_PRIVACY", "HARM_BOUND", "CONFORMANCE", "ATTRIBUTION", "PURPOSE"):
        hit = named = 0
        pool = [v for v in V if check_name != "ATTRIBUTION" or v["outcome"].get("criteria_met") != "pending"]   # attribution applies to measured outcomes
        for v in rng.sample(pool, 30):
            R = L.admit(violate(v, check_name)); hit += bool(R); named += any(x.startswith(f"[{check_name}]") for x in R)
        res[check_name] = {"contained": hit, "named": named, "of": 30}
    pub = rsc.Log(L.d); leaked = sum(1 for r in pub.recs.values() if "variant" in r.get("title", "") and rsc.check(r))
    return {"valid": 200, "valid_blocked": blocked, "violations": res, "contained_published": leaked}

def supersede(rng):
    L = fresh_log(tempfile.mkdtemp()); v = valid(rng, 0); assert not L.admit(v)
    c = copy.deepcopy(v); c.pop("id"); c["supersedes"] = v["id"]; c["lineage"]["identity"] = v["id"]
    c["outcome"]["summary"] += " (corrected in a modified clone)"; c = rsc.finalize(c); ok = not L.admit(c)
    bad = copy.deepcopy(v); bad.pop("id"); bad["supersedes"] = v["id"]; bad["lineage"]["identity"] = "%064x" % rng.getrandbits(256)
    bad = rsc.finalize(bad); R = L.admit(bad)
    return {"clone_admitted": ok, "old_still_in_log": v["id"] in L.recs, "old_active": v["id"] in L.active(),
            "clone_active": c["id"] in L.active(), "identity_change_contained": bool(R) and any("identity" in x for x in R)}

def peer_audit(rng):
    d = [tempfile.mkdtemp() for _ in range(4)]; logs = [fresh_log(x) for x in d[:3]]
    extra = [valid(rng, i) for i in range(20)]
    for L in logs:
        for r in extra: assert not L.admit(r)
    behind = rsc.Log(d[3]); src = rsc.Log(os.path.join(ROOT, "log"))
    for e in src.entries[: len(src.entries) // 2]: assert not behind.admit(e["record"])
    lines = open(logs[2].f).read().splitlines(); k = len(lines) - 5; e = json.loads(lines[k])
    e["record"]["outcome"]["summary"] += " (edited in storage)"; lines[k] = json.dumps(e, sort_keys=True)
    open(logs[2].f, "w").write("\n".join(lines) + "\n"); logs[2] = rsc.Log(d[2])
    srv = [rsc.serve(L, 0, quiet=True) for L in logs + [behind]]
    for s in srv: threading.Thread(target=s.serve_forever, daemon=True).start()
    u = lambda i: f"http://127.0.0.1:{srv[i].server_address[1]}"
    clean, corrupt, lag = rsc.audit(logs[0], u(1)), rsc.audit(logs[0], u(2)), rsc.audit(logs[0], u(3))
    for s in srv: s.shutdown()
    return {"clean_peer": clean, "corrupted_peer": corrupt, "behind_peer": lag}

if __name__ == "__main__":
    seed = int(sys.argv[1]); rng = random.Random(seed)
    r = {"seed": seed, "checks": checks(rng), "supersede": supersede(rng), "peer_audit": peer_audit(rng)}
    print(json.dumps(r, indent=1, ensure_ascii=False))
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True); json.dump(r, open(os.path.join(HERE, "out", f"v12_{seed}.json"), "w"), indent=1)
