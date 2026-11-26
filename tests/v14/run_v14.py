#!/usr/bin/env python3
"""SRC-X.5 v1.4 launch tests T1-T6 (criteria: tests/v14/PREDICTIONS_V14.md). T7 (anchor) runs in GitHub Actions.
Run from protocol/: python tests/v14/run_v14.py  -> tests/v14/out/results_14.json"""
import copy, http.client, json, os, random, shutil, socket, subprocess, sys, tempfile, threading, time
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
HERE = os.path.dirname(os.path.abspath(__file__)); P = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, P)
import srcx5 as core, srcx5_net as net
random.seed(14)
OUT = os.path.join(HERE, "out"); os.makedirs(OUT, exist_ok=True)
TMP = tempfile.mkdtemp(prefix="v14_")
R = {}

def port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p

def src_log(n=None):
    d = tempfile.mkdtemp(dir=TMP); lines = open(os.path.join(P, "log", "log.jsonl")).read().splitlines(True)
    open(os.path.join(d, "log.jsonl"), "w").write("".join(lines[:n] if n else lines)); return core.Log(d)

def empty():
    return core.Log(tempfile.mkdtemp(dir=TMP))

def same(E, L, need_head=True):
    """10/10 byte-identical canonical records, ids recompute, chain intact, (head equal)."""
    ok_recs = sum(1 for i, r in L.recs.items() if i in E.recs and core.canon(E.recs[i]) == core.canon(r) and core.rec_id(E.recs[i]) == i)
    d = {"records_identical": ok_recs, "of": len(L.recs), "chain_intact": E.verify_chain() == [] if E.entries else False,
         "head_equal": E.head() == L.head()}
    d["pass"] = ok_recs == len(L.recs) and d["chain_intact"] and (d["head_equal"] or not need_head)
    return d

def static_server(directory):
    p = port()
    class H(SimpleHTTPRequestHandler):
        def __init__(s, *a, **k): super().__init__(*a, directory=directory, **k)
        def log_message(s, *a): pass
    srv = ThreadingHTTPServer(("127.0.0.1", p), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{p}"

def node(L):
    p = port(); srv = net.serve(L, p); srv.server_address = ("127.0.0.1", p)
    threading.Thread(target=srv.serve_forever, daemon=True).start(); return srv, f"http://127.0.0.1:{p}"

def admit_entries(E, entries):
    for e in entries: E.admit(e["record"])
    return E

# ---------------- T1 carriers ----------------
def t1():
    L = src_log(); res = {}
    srv, url = node(L); E = empty(); net.sync_one(E, url); res["running_node"] = same(E, L); srv.shutdown()
    d = os.path.join(TMP, "mirror_t1"); net.export(L, d); s2, u2 = static_server(d); E = empty(); net.sync_one(E, u2)
    res["static_mirror_http"] = same(E, L); s2.shutdown()
    g = os.path.join(TMP, "git_src"); net.export(L, g)
    for c in (["git", "init", "-q"], ["git", "add", "-A"], ["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "log"]):
        subprocess.run(c, cwd=g, check=True)
    gc = os.path.join(TMP, "git_clone"); subprocess.run(["git", "clone", "-q", "file://" + g, gc], check=True)
    res["git_clone"] = same(admit_entries(empty(), json.load(open(os.path.join(gc, "log.json")))), L)
    fd = tempfile.mkdtemp(dir=TMP); shutil.copy(os.path.join(L.d, "log.jsonl"), os.path.join(fd, "log.jsonl"))
    res["file_copy"] = same(core.Log(fd), L)
    data = open(os.path.join(d, "log.json"), "rb").read()
    # delay-tolerant link: 1 kB bundles, 30 % loss per attempt, random delays, retransmission until all acknowledged
    bundles = [data[i:i + 1024] for i in range(0, len(data), 1024)]; got = {}; attempts = 0; clock = 0.0; arrivals = []
    while len(got) < len(bundles):
        for k, b in enumerate(bundles):
            if k in got: continue
            attempts += 1
            if random.random() < 0.30: continue
            arrivals.append((clock + random.uniform(1, 3600), k, b))
        clock += 3600
        for t, k, b in sorted(arrivals): got[k] = b
        arrivals = []
    whole = b"".join(got[k] for k in range(len(bundles)))
    r = same(admit_entries(empty(), json.loads(whole)), L); r.update({"bundles": len(bundles), "attempts": attempts, "simulated_hours": int(clock / 3600)})
    res["delay_tolerant_link"] = r
    chunks = [(k, data[i:i + 2953]) for k, i in enumerate(range(0, len(data), 2953))]; random.shuffle(chunks)
    whole = b"".join(c for _, c in sorted(chunks))
    r = same(admit_entries(empty(), json.loads(whole)), L); r["qr_chunks"] = len(chunks); res["qr_chunks"] = r
    res["pass"] = all(v["pass"] for v in res.values() if isinstance(v, dict))
    return res

# ---------------- T2 failover and refill ----------------
def t2():
    L = src_log(); res = {}
    dirs = [os.path.join(TMP, f"m{i}") for i in (1, 2, 3)]
    net.export(src_log(9), dirs[0]); net.export(L, dirs[1]); net.export(L, dirs[2])
    servers = [static_server(x) for x in dirs]; urls = [u for _, u in servers]
    st = {x["mirror"]: x["state"] for x in net.status(L, urls)}
    res["status_with_stale"] = [st[u] for u in urls]
    net.export(L, dirs[0]); st2 = {x["mirror"]: x["state"] for x in net.status(L, urls)}
    res["status_after_refill"] = [st2[u] for u in urls]
    servers[0][0].shutdown(); servers[0][0].server_close(); servers[1][0].shutdown(); servers[1][0].server_close()
    E = empty(); p, added, moved, tried = net.sync_any(E, urls)
    res["failover"] = {"answered_by": urls.index(p) + 1, "added": added, "tried": [w for _, w in tried], **same(E, L)}
    servers[2][0].shutdown(); servers[2][0].server_close()
    t0 = time.time()
    try: net.sync_any(empty(), urls); res["all_down"] = {"clean_error": False}
    except ConnectionError: res["all_down"] = {"clean_error": True, "seconds": round(time.time() - t0, 2)}
    # a poisoned mirror: one record's content changed, id kept -> skipped there, taken from the next mirror
    pd = os.path.join(TMP, "poison"); net.export(L, pd); lg = json.load(open(os.path.join(pd, "log.json")))
    victim = lg[3]["record"]["id"]; lg[3]["record"]["title"] += " (edited)"; json.dump(lg, open(os.path.join(pd, "log.json"), "w"))
    good = os.path.join(TMP, "good"); net.export(L, good)
    sp, up = static_server(pd); sg, ug = static_server(good)
    E = empty(); first = net.sync_one(E, up); poisoned_taken = victim in E.recs and core.canon(E.recs[victim]) != core.canon(L.recs[victim])
    net.sync_one(E, ug)
    res["poisoned_mirror"] = {"victim_skipped_at_poisoned_mirror": not poisoned_taken, "records_after_next_mirror": same(E, L, need_head=False)}
    sp.shutdown(); sg.shutdown()
    res["pass"] = (res["status_with_stale"] == ["stale", "current", "current"] and res["status_after_refill"] == ["current"] * 3
                   and res["failover"]["answered_by"] == 3 and res["failover"]["pass"] and res["all_down"]["clean_error"]
                   and res["all_down"].get("seconds", 99) < 60 and res["poisoned_mirror"]["victim_skipped_at_poisoned_mirror"]
                   and res["poisoned_mirror"]["records_after_next_mirror"]["records_identical"] == 10)
    return res

# ---------------- T3 standards ----------------
def t3():
    import jsonschema
    from openapi_spec_validator import validate
    from pyld import jsonld
    res = {}; oa = json.load(open(os.path.join(P, "openapi.json"))); schema = json.load(open(os.path.join(P, "schema", "record.schema.json")))
    try: validate(oa, base_uri="file://" + P + "/"); res["openapi_valid"] = True
    except Exception as e: res["openapi_valid"] = False; res["openapi_error"] = str(e)[:300]
    def inline(x):
        if isinstance(x, dict):
            if x.get("$ref") == "schema/record.schema.json": return schema
            return {k: inline(v) for k, v in x.items()}
        if isinstance(x, list): return [inline(v) for v in x]
        return x
    o = inline(oa); L = src_log(); srv, url = node(L); bad = []; n = 0
    def check(path, tmpl):
        nonlocal n
        sch = o["paths"][tmpl]["get"]["responses"]["200"]["content"]
        sch = list(sch.values())[0]["schema"]
        conn = http.client.HTTPConnection(url[7:]); conn.request("GET", path); r = conn.getresponse(); body = json.loads(r.read())
        n += 1
        if r.status != 200: bad.append((path, r.status)); return
        errs = [e.message for e in jsonschema.Draft202012Validator(sch).iter_errors(body)]
        if errs: bad.append((path, errs[:2]))
    for pth in ("/ids.json", "/active.json", "/head.json", "/log.json", "/.well-known/srcx5.json", "/health"): check(pth, pth)
    for i in L.recs: check(f"/records/{i}.json", "/records/{id}.json"); check(f"/ld/{i}.jsonld", "/ld/{id}.jsonld")
    res["node_responses"] = {"checked": n, "nonconforming": bad}
    v = jsonschema.Draft202012Validator(schema)
    res["schema_records_valid"] = sum(1 for r in L.recs.values() if not list(v.iter_errors(r)))
    ctx = json.load(open(os.path.join(P, "context.jsonld")))
    def loader(u, options=None): return {"contextUrl": None, "documentUrl": u, "document": ctx}
    okld = 0
    for i, r in L.recs.items():
        ex = jsonld.expand(net.ld(r), {"documentLoader": loader})
        if ex and ex[0].get("@id") == f"urn:srcx5:{i}" and "http://www.w3.org/ns/prov#Entity" in ex[0].get("@type", []): okld += 1
    res["jsonld_expanded_prov_entity"] = okld; srv.shutdown()
    res["pass"] = res["openapi_valid"] and not bad and res["schema_records_valid"] == 10 and okld == 10
    return res

# ---------------- T4 MCP ----------------
def t4():
    L = src_log(); res = {}
    pr = subprocess.Popen([sys.executable, os.path.join(P, "srcx5_mcp.py"), "--log", L.d], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, cwd=P)
    def rpc(obj, raw=None):
        pr.stdin.write((raw if raw is not None else json.dumps(obj)) + "\n"); pr.stdin.flush(); return json.loads(pr.stdout.readline())
    def tool(name, args, k=[100]):
        k[0] += 1; r = rpc({"jsonrpc": "2.0", "id": k[0], "method": "tools/call", "params": {"name": name, "arguments": args}})
        return r["result"]["structuredContent"]["result"]
    init = rpc({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "t", "version": "1"}}})
    pr.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n"); pr.stdin.flush()
    tl = rpc({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    rid = sorted(L.recs)[0]; tam = copy.deepcopy(L.recs[rid]); tam["title"] += " (edited)"
    v_ok = tool("srcx5_verify", {"id": rid}); v_bad = tool("srcx5_verify", {"record": tam}); vl = tool("srcx5_verify_log", {})
    sub = tool("srcx5_submit", {"record": tam}); perr = rpc(None, raw="{not json"); after = rpc({"jsonrpc": "2.0", "id": 9, "method": "ping"})
    pr.stdin.close(); pr.wait(timeout=10)
    res = {"initialize": init.get("result", {}).get("serverInfo"), "tools": [t["name"] for t in tl["result"]["tools"]],
           "verify_real": v_ok["valid"], "verify_tampered": v_bad["valid"], "tampered_reasons": v_bad["reasons"][:2],
           "verify_log": vl, "submit_tampered_quarantined": sub["quarantined"], "parse_error_code": perr.get("error", {}).get("code"),
           "still_answering": after.get("result") == {}}
    res["pass"] = (bool(res["initialize"]) and len(res["tools"]) == 6 and v_ok["valid"] and not v_bad["valid"] and vl["intact"]
                   and vl["entries"] == 10 and sub["quarantined"] and res["parse_error_code"] == -32700 and res["still_answering"])
    return res

# ---------------- T5 no regression ----------------
def valid_rec(k, parent):
    return core.finalize({"type": "claim", "title": f"v14 valid record {k}", "purpose": "Conformance of the admission path.",
            "prediction": {"criteria": "admitted"}, "seal": {"files": [{"path": f"f{k}.txt", "sha256": core.sha(str(k).encode())}], "sealed_at": "2026-11-01T00:00:00Z"},
            "run": {}, "outcome": {"criteria_met": "pending"}, "lineage": {"parents": [parent]}, "evidence": "simulated",
            "declarations": {"affects_people": False, "predicted_harm": 0, "serves_mission": True}, "consent_harm": {"personal_data": False}})

def post(url, body, raw=False):
    c = http.client.HTTPConnection(url[7:], timeout=30); b = body if raw else json.dumps(body).encode()
    c.request("POST", "/submit", b, {"Content-Type": "application/json"}); r = c.getresponse(); r.read(); return r.status

def t5():
    old = net.RATE; net.RATE = (10 ** 9, 60); L = src_log(); srv, url = node(L); held = sorted(L.recs); parent = held[0]; codes = {"bad": [], "good": []}
    for k in range(150):
        r = valid_rec(10000 + k, parent); r["id"] = core.sha(f"forged{k}".encode()); codes["bad"].append(post(url, r))
        t = copy.deepcopy(L.recs[held[k % 10]]); t["title"] = t["title"] + f" (edit {k})"; codes["bad"].append(post(url, t))
        f = valid_rec(20000 + k, parent); f.pop("id"); f["seal"]["sealed_at"] = "2030-01-01T00:00:00Z"; codes["bad"].append(post(url, core.finalize(f)))
        e = valid_rec(30000 + k, parent); e.pop("id"); e["title"] += f" contact person{k}@example.org"; codes["bad"].append(post(url, core.finalize(e)))
    for k in range(200): codes["good"].append(post(url, valid_rec(k, parent)))
    srv.shutdown(); net.RATE = old
    res = {"invalid_quarantined": codes["bad"].count(202), "invalid_total": 600, "valid_admitted": codes["good"].count(201), "valid_total": 200,
           "entries_after": len(L.entries), "chain_intact": L.verify_chain() == []}
    res["pass"] = res["invalid_quarantined"] == 600 and res["valid_admitted"] == 200 and res["entries_after"] == 210 and res["chain_intact"]
    return res

# ---------------- T6 hardening and fuzzing ----------------
def raw(url, data):
    host, p = url[7:].split(":"); s = socket.create_connection((host, int(p)), timeout=10); s.sendall(data)
    buf = b""
    try:
        while not buf.count(b"\r\n\r\n"):
            ch = s.recv(65536)
            if not ch: break
            buf += ch
    except Exception: pass
    s.close(); line = buf.split(b"\r\n", 1)[0].split()
    return int(line[1]) if len(line) > 1 and line[1].isdigit() else 0

def t6():
    old = net.RATE; net.RATE = (10 ** 9, 60); L = src_log(); before = L.head(); srv, url = node(L); codes = []
    kinds = ["bytes", "utf8", "big", "nolen", "neglen", "array", "scalar", "deep", "put", "patch", "delete", "path"]
    for k in range(400):
        kind = kinds[k % len(kinds)]
        if kind == "bytes": codes.append(post(url, os.urandom(random.randint(1, 4000)), raw=True))
        elif kind == "utf8": codes.append(post(url, b'{"type":"claim","title":"\xff\xfe"}', raw=True))
        elif kind == "big": codes.append(raw(url, b"POST /submit HTTP/1.1\r\nHost: x\r\nContent-Length: 300000\r\n\r\n" + b"{" * 1000))
        elif kind == "nolen": codes.append(raw(url, b"POST /submit HTTP/1.1\r\nHost: x\r\n\r\n{}"))
        elif kind == "neglen": codes.append(raw(url, b"POST /submit HTTP/1.1\r\nHost: x\r\nContent-Length: -5\r\n\r\n"))
        elif kind == "array": codes.append(post(url, [1, 2, 3]))
        elif kind == "scalar": codes.append(post(url, random.choice([1, "x", None, True])))
        elif kind == "deep": codes.append(post(url, b"[" * 50000 + b"]" * 50000, raw=True))
        elif kind in ("put", "patch", "delete"):
            c = http.client.HTTPConnection(url[7:], timeout=10); c.request(kind.upper(), "/record/" + sorted(L.recs)[0]); codes.append(c.getresponse().status)
        else:
            c = http.client.HTTPConnection(url[7:], timeout=10); c.request("GET", "/" + "".join(random.choice("abc/._%") for _ in range(20))); codes.append(c.getresponse().status)
    c = http.client.HTTPConnection(url[7:], timeout=10); c.request("GET", "/health"); alive = c.getresponse().status == 200
    srv.shutdown(); net.RATE = old
    L2 = src_log(); srv2, url2 = node(L2); rl = [post(url2, {"type": "claim"}) for _ in range(31)]; srv2.shutdown()
    res = {"requests": len(codes), "status_counts": {str(c): codes.count(c) for c in sorted(set(codes))}, "any_5xx": any(c >= 500 for c in codes),
           "any_zero_or_2xx_admit": any(c in (0, 200, 201) for c in codes), "alive_after": alive, "chain_intact": L.verify_chain() == [],
           "unchanged": L.head() == before and len(L.entries) == 10, "rate_limit_31st": rl[-1], "first_30": sorted(set(rl[:30]))}
    res["pass"] = (not res["any_5xx"] and not res["any_zero_or_2xx_admit"] and alive and res["chain_intact"] and res["unchanged"]
                   and rl[-1] == 429 and all(400 <= c < 500 or c == 202 for c in codes))
    return res

if __name__ == "__main__":
    t0 = time.time()
    for name, f in (("T1_carriers", t1), ("T2_failover", t2), ("T3_standards", t3), ("T4_mcp", t4), ("T5_regression", t5), ("T6_hardening", t6)):
        try: R[name] = f()
        except Exception as e:
            import traceback; R[name] = {"pass": False, "crash": traceback.format_exc()[-1500:]}
        print(name, "PASS" if R[name].get("pass") else "NOT MET", flush=True)
    R["T7_anchor"] = {"pass": None, "note": "runs in GitHub Actions (.github/workflows/srcx5_anchor.yml)"}
    R["seconds"] = round(time.time() - t0, 1); R["seed"] = 14
    json.dump(R, open(os.path.join(OUT, "results_14.json"), "w"), indent=1, default=str)
    print(json.dumps({k: (v.get("pass") if isinstance(v, dict) else v) for k, v in R.items()}))
