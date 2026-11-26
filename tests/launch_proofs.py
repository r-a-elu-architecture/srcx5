"""RSC launch proofs (sealed before the confirming run; PREDICTIONS.md fixes the pass criteria).
  python tests/launch_proofs.py immune <seed>   inject harmful/forged records against admission; measure catch and false-block rates
  python tests/launch_proofs.py sync <seed>    three live nodes on local ports; measure convergence and bytes moved
Seed 1 = development screen; seed 2 = the sealed confirming run (fresh cases)."""
import os, sys, json, copy, random, tempfile, threading, time, glob
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, ROOT)
import rsc

BASE = [json.load(open(os.path.join(ROOT, "records", f"{k}.json"))) for k in json.load(open(os.path.join(ROOT, "records", "INDEX.json")))]   # lineage order

def fresh_valid(rng, i):
    r = copy.deepcopy(rng.choice(BASE)); r.pop("id")
    r["title"] = f"{r['title']} (variant {i}-{rng.randrange(10**9)})"; r["lineage"] = {"parents": []}
    return rsc.finalize(r)

def attacks(rng, v, known):
    """Each attack takes a valid record and returns a harmful or forged one, with its class."""
    out = []
    a = copy.deepcopy(v); a["outcome"]["criteria_met"] = "all"; a["outcome"]["summary"] += " (edited after sealing)"
    if a["outcome"] != v["outcome"]: out.append(("tampered after the id was set", a))
    a = copy.deepcopy(v); a["id"] = "%064x" % rng.getrandbits(256); out.append(("forged id", a))
    a = copy.deepcopy(v); a.pop("id"); a["seal"]["sealed_at"] = "2026-12-31T23:59:59Z"; out.append(("back-dated seal (sealed after the run)", rsc.finalize(a)))
    a = copy.deepcopy(v); a.pop("id"); a["seal"]["files"] = []; out.append(("no fingerprinted files", rsc.finalize(a)))
    a = copy.deepcopy(v); a.pop("id"); a["seal"]["files"][0]["sha256"] = "not-a-hash"; out.append(("invalid fingerprint", rsc.finalize(a)))
    a = copy.deepcopy(v); a.pop("id"); a["lineage"]["parents"] = ["%064x" % rng.getrandbits(256)]; out.append(("unknown lineage parent", rsc.finalize(a)))
    a = copy.deepcopy(v); a.pop("id"); a["prediction"]["criteria"] = ""; out.append(("no pass criteria", rsc.finalize(a)))
    a = copy.deepcopy(v); a.pop("id"); a["run"] = {}; out.append(("outcome without a run time", rsc.finalize(a)))
    a = copy.deepcopy(v); a.pop("id"); a["rsc"] = "0.9"; out.append(("wrong protocol version", rsc.finalize(a)))
    for name, pii in (("personal data: email", f"contact jane.doe{rng.randrange(999)}@example.org"),
                      ("personal data: phone", f"call +44 20 7946 {rng.randrange(1000, 9999)}"),
                      ("personal data: card", "card 4111 1111 1111 1111"), ("personal data: IBAN", "IBAN DE89370400440532013000")):
        a = copy.deepcopy(v); a.pop("id"); a["outcome"]["summary"] += " " + pii; out.append((name, rsc.finalize(a)))
    a = copy.deepcopy(v); a.pop("id"); a["consent_harm"]["personal_data"] = True; out.append(("declares personal data", rsc.finalize(a)))
    rep = rsc.finalize({"type": "replication", "title": "fake replication", "replicates": "%064x" % rng.getrandbits(256), "by": "x",
                        "outcome": {"criteria_met": "all"}, "consent_harm": {"personal_data": False}})
    out.append(("replication of an unknown record", rep))
    return out

def immune(seed, n_valid=200):
    rng = random.Random(seed); d = tempfile.mkdtemp(); L = rsc.Log(d)
    for r in BASE: assert not L.admit(r)
    valid = [fresh_valid(rng, i) for i in range(n_valid)]
    fb = sum(1 for v in valid if L.admit(v))                      # false blocks: valid records rejected
    caught, total, by = 0, 0, {}
    for v in rng.sample(valid, 40):
        for cls, a in attacks(rng, v, set(L.recs)):
            ok = bool(L.admit(a)); total += 1; caught += ok; c = by.setdefault(cls, [0, 0]); c[0] += ok; c[1] += 1
    # log tampering: edit one stored entry; the chain check must find it
    before = L.verify_chain(); lines = open(L.f).read().splitlines(); k = rng.randrange(len(lines))
    e = json.loads(lines[k]); e["record"]["title"] += " (edited in storage)"; lines[k] = json.dumps(e, sort_keys=True)
    open(L.f, "w").write("\n".join(lines) + "\n"); after = rsc.Log(d).verify_chain()
    res = {"seed": seed, "valid": n_valid, "false_blocks": fb, "attacks": total, "caught": caught,
           "catch_rate": caught / total, "false_block_rate": fb / n_valid, "by_class": by,
           "chain_intact_before_tamper": before == [], "tamper_detected_at": after}
    return res

def sync_test(seed=1):
    dirs = [tempfile.mkdtemp() for _ in range(3)]; logs = [rsc.Log(x) for x in dirs]
    rng = random.Random(seed); recs = BASE + [fresh_valid(rng, i) for i in range(300)]
    for r in recs: assert not logs[0].admit(r)
    for r in recs[: len(recs) // 2]: assert not logs[1].admit(r)
    srv = [rsc.serve(L, 0, quiet=True) for L in logs]; ports = [s.server_address[1] for s in srv]
    for s in srv: threading.Thread(target=s.serve_forever, daemon=True).start()
    url = lambda i: f"http://127.0.0.1:{ports[i]}"
    full = len(rsc.get(url(0) + "/log"))                          # bytes of a naive full copy
    addB, movB = rsc.sync(logs[1], url(0))                         # B lacks half
    addC, movC = rsc.sync(logs[2], url(1))                         # C pulls everything from B
    addC2, movC2 = rsc.sync(logs[2], url(0))                       # then checks A: nothing missing
    ids = [set(L.recs) for L in logs]
    for s in srv: s.shutdown()
    return {"records": len(recs), "full_copy_bytes": full, "B_added": addB, "B_bytes": movB, "B_share_of_full": movB / full,
            "C_added": addC, "C_bytes": movC, "C_recheck_added": addC2, "C_recheck_bytes": movC2,
            "converged": ids[0] == ids[1] == ids[2], "chains_intact": all(L.verify_chain() == [] for L in logs)}

if __name__ == "__main__":
    what = sys.argv[1]
    r = immune(int(sys.argv[2])) if what == "immune" else sync_test(int(sys.argv[2]) if len(sys.argv) > 2 else 1)
    print(json.dumps(r, indent=1))
    out = os.path.join(HERE, "out"); os.makedirs(out, exist_ok=True)
    json.dump(r, open(os.path.join(out, f"{what}_{sys.argv[2] if len(sys.argv) > 2 else 'run'}.json"), "w"), indent=1)
