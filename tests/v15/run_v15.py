#!/usr/bin/env python3
"""SRC-X.5 v1.5 launch tests T1-T8 (criteria: tests/v15/PREDICTIONS_V15.md). D1-D4 are observed in GitHub Actions.
Run from protocol/: python tests/v15/run_v15.py  -> tests/v15/out/results_15.json"""
import copy, hashlib, http.client, importlib.util, json, os, shutil, subprocess, sys, tempfile, threading, time, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); P = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, P)
import srcx5 as core, srcx5_net as net, srcx5_mcp as mcp, srcx5_node as node15, srcx5_issue as issue
spec = importlib.util.spec_from_file_location("run_v14", os.path.join(P, "tests", "v14", "run_v14.py"))
v14 = importlib.util.module_from_spec(spec); spec.loader.exec_module(v14)
OUT = os.path.join(HERE, "out"); os.makedirs(OUT, exist_ok=True)
TMP = tempfile.mkdtemp(prefix="v15_"); R = {}

def src_log(n=None):
    d = tempfile.mkdtemp(dir=TMP); lines = open(os.path.join(P, "log", "log.jsonl")).read().splitlines(True)
    open(os.path.join(d, "log.jsonl"), "w").write("".join(lines[:n] if n else lines)); return core.Log(d)

def start(L):
    srv = node15.serve(L, 0); p = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start(); return srv, f"http://127.0.0.1:{p}"

def req(url, method="GET", body=None, raw=None):
    c = http.client.HTTPConnection(url.split("//")[1].split("/")[0]); path = "/" + url.split("//")[1].partition("/")[2]
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    c.request(method, path, data, {"Content-Type": "application/json"} if data is not None else {})
    r = c.getresponse(); b = r.read(); return r.status, (json.loads(b) if b else None)

def personal(L):
    r = copy.deepcopy(L.recs[L.active()[0]]); r.pop("id"); r["title"] += " contact jane.doe@example.org"; return core.finalize(r)

# ---------------- T1 MCP over HTTP ----------------
def t1():
    L = src_log(); srv, u = start(L); res = {}; k = [0]
    def rpc(m, params=None):
        k[0] += 1; return req(u + "/mcp", "POST", {"jsonrpc": "2.0", "id": k[0], "method": m, "params": params or {}})[1]
    def tool(n, a): return json.loads(rpc("tools/call", {"name": n, "arguments": a})["result"]["content"][0]["text"])
    res["init_version"] = rpc("initialize").get("result", {}).get("protocolVersion")
    st, b = req(u + "/mcp", "POST", {"jsonrpc": "2.0", "method": "notifications/initialized"}); res["notification"] = [st, b]
    tl = rpc("tools/list")["result"]["tools"]; res["tools"] = len(tl)
    res["verify_valid"] = sum(1 for i in L.recs if tool("srcx5_verify", {"id": i}).get("valid"))
    vl = tool("srcx5_verify_log", {}); res["log_intact"] = vl.get("intact")
    sub = tool("srcx5_submit", {"record": personal(L)}); res["personal_quarantined"] = sub.get("quarantined") is True
    res["get_405"] = req(u + "/mcp")[0]
    res["parse_error"] = req(u + "/mcp", "POST", raw=b"{not json")[1]["error"]["code"]
    res["unknown_method"] = rpc("nope/x").get("error", {}).get("code")
    L2 = src_log(); stdio = {m: mcp.handle(L2, {"jsonrpc": "2.0", "id": 1, "method": m, "params": p})["result"]
                             for m, p in (("tools/list", {}), ("tools/call", {"name": "srcx5_verify_log", "arguments": {}}))}
    res["equals_stdio"] = (stdio["tools/list"]["tools"] == tl and
                           json.loads(stdio["tools/call"]["content"][0]["text"]) == json.loads(json.dumps(vl)))
    srv.shutdown()
    res["pass"] = (bool(res["init_version"]) and res["notification"] == [202, None] and res["tools"] == 6 and res["verify_valid"] == len(L.recs) == 10
                   and res["log_intact"] and res["personal_quarantined"] and res["get_405"] == 405 and res["parse_error"] == -32700
                   and res["unknown_method"] == -32601 and res["equals_stdio"])
    return res

# ---------------- T2 A2A ----------------
def t2():
    L = src_log(); srv, u = start(L); res = {}
    st, card = req(u + "/.well-known/agent-card.json")
    need = ["name", "description", "url", "version", "protocolVersion", "capabilities", "defaultInputModes", "defaultOutputModes", "skills"]
    res["card_fields"] = all(k in card for k in need) and card["url"].endswith("/a2a") and len(card["skills"]) >= 6
    def send(parts, m="message/send"):
        return req(u + "/a2a", "POST", {"jsonrpc": "2.0", "id": 7, "method": m, "params": {"message": {"role": "user", "messageId": "t", "parts": parts}}})[1]
    lst = send([{"kind": "data", "data": {"tool": "srcx5_list"}}])["result"]["parts"][0]["data"]["result"]
    res["list_all_active"] = sorted(x["id"] for x in lst) == sorted(L.active())
    res["text_verify_intact"] = send([{"kind": "text", "text": "verify the log"}])["result"]["parts"][0]["data"]["result"].get("intact")
    res["unknown_method"] = send([], "tasks/zzz").get("error", {}).get("code")
    res["unknown_tool"] = send([{"kind": "data", "data": {"tool": "nope"}}]).get("error", {}).get("code")
    srv.shutdown()
    res["pass"] = res["card_fields"] and res["list_all_active"] and res["text_verify_intact"] is True and res["unknown_method"] == -32601 and res["unknown_tool"] == -32602
    return res

# ---------------- T3 standards ----------------
def t3():
    import jsonschema
    from openapi_spec_validator import validate
    L = src_log(); srv, u = start(L); res = {}
    oa = node15.openapi(u); schema = json.load(open(os.path.join(P, "schema", "record.schema.json")))
    try: validate(oa, base_uri="file://" + P + "/"); res["openapi_valid"] = True
    except Exception as e: res["openapi_valid"] = False; res["openapi_error"] = str(e)[:300]
    res["documents_new"] = "post" in oa["paths"].get("/mcp", {}) and "post" in oa["paths"].get("/a2a", {}) and "get" in oa["paths"].get("/.well-known/agent-card.json", {})
    def inline(x):
        if isinstance(x, dict):
            if x.get("$ref") == "schema/record.schema.json": return schema
            return {k: inline(v) for k, v in x.items()}
        if isinstance(x, list): return [inline(v) for v in x]
        return x
    o = inline(oa); bad = []; n = 0
    def check(path, tmpl):
        nonlocal n
        sch = list(o["paths"][tmpl]["get"]["responses"]["200"]["content"].values())[0]["schema"]
        st, body = req(u + path); n += 1
        if st != 200: bad.append((path, st)); return
        errs = [e.message for e in jsonschema.Draft202012Validator(sch).iter_errors(body)]
        if errs: bad.append((path, errs[:2]))
    for pth in ("/ids.json", "/active.json", "/head.json", "/log.json", "/.well-known/srcx5.json", "/health", "/.well-known/agent-card.json"): check(pth, pth)
    for i in L.recs: check(f"/records/{i}.json", "/records/{id}.json"); check(f"/ld/{i}.jsonld", "/ld/{id}.jsonld")
    res["node_responses"] = {"checked": n, "nonconforming": bad}; srv.shutdown()
    res["pass"] = res["openapi_valid"] and res["documents_new"] and not bad and n == 27
    return res

# ---------------- T4 install ----------------
def t4():
    res = {}; venv = os.path.join(TMP, "venv"); src = os.path.join(TMP, "pkg")
    shutil.copytree(P, src, ignore=shutil.ignore_patterns("tests", "__pycache__", "*.pyc", "anchors", "site"))
    subprocess.run([sys.executable, "-m", "venv", venv], check=True)
    pip = subprocess.run([os.path.join(venv, "bin", "pip"), "install", "-q", src], capture_output=True, text=True)
    res["pip_ok"] = pip.returncode == 0; res["pip_tail"] = (pip.stdout + pip.stderr)[-300:]
    L = src_log(); out = os.path.join(TMP, "mirror_t4")
    ex = subprocess.run([os.path.join(venv, "bin", "srcx5-node"), "export", "--log", L.d, "--out", out, "--no-probe"], capture_output=True, text=True, cwd=TMP)
    res["export_rc"] = ex.returncode
    h = json.load(open(os.path.join(out, "head.json"))) if os.path.exists(os.path.join(out, "head.json")) else {}
    res["files"] = {f: os.path.exists(os.path.join(out, f)) for f in (".well-known/agent-card.json", "openapi_v15.json", "head.json")}
    res["head_equal"] = h.get("head") == L.head()
    ck = subprocess.run([os.path.join(venv, "bin", "srcx5"), "check-log", "--log", L.d], capture_output=True, text=True, cwd=TMP)
    res["check_log"] = (ck.stdout + ck.stderr).strip()[-120:]
    res["pass"] = res["pip_ok"] and res["export_rc"] == 0 and all(res["files"].values()) and res["head_equal"] and ck.returncode == 0 and "intact" in res["check_log"]
    return res

# ---------------- T5 write anywhere, converge ----------------
def t5():
    res = {}; full = src_log(); A = src_log(9); srv, u = start(A)
    tenth = json.loads(open(os.path.join(P, "log", "log.jsonl")).read().splitlines()[9])["record"]
    st, b = req(u + "/submit", "POST", tenth); res["submit"] = [st, b.get("admitted")]
    C = src_log(8); pulled = node15.pull(C, [u]); res["pulled"] = pulled
    res["same_as_A"] = v14.same(C, A)
    # a node serving a record that does not match its own hash
    bad = src_log(8); d = tempfile.mkdtemp(dir=TMP); net.export(full, d)
    victim = tenth["id"]; rp = os.path.join(d, "records", f"{victim}.json"); r = json.load(open(rp)); r["title"] += " (tampered)"; json.dump(r, open(rp, "w"))
    lj = json.load(open(os.path.join(d, "log.json")))
    for e in lj:
        if e["record"]["id"] == victim: e["record"]["title"] += " (tampered)"
    json.dump(lj, open(os.path.join(d, "log.json"), "w"))
    s2, u2 = v14.static_server(d); before = set(bad.recs); node15.pull(bad, [u2])
    res["tampered_taken"] = victim in bad.recs and victim not in set(src_log(8).recs)
    res["tampered_record_bytes_ok"] = all(core.rec_id(r) == i for i, r in bad.recs.items())
    s2.shutdown(); srv.shutdown()
    res["pass"] = res["submit"] == [201, True] and res["same_as_A"]["pass"] and not res["tampered_taken"] and res["tampered_record_bytes_ok"]
    return res

# ---------------- T6 submit by issue ----------------
def t6():
    res = {}; L9 = src_log(9)
    tenth = json.loads(open(os.path.join(P, "log", "log.jsonl")).read().splitlines()[9])["record"]
    ok = issue.run("Here is my record:\n```json\n" + json.dumps(tenth) + "\n```\n", L9.d, apply=False); res["valid"] = ok["admitted"]
    ap = issue.run("```json\n" + json.dumps(tenth) + "\n```", L9.d, apply=True); L9b = core.Log(L9.d)
    res["applied"] = ap["applied"] and len(L9b.entries) == 10 and L9b.verify_chain() == []
    nj = issue.run("hello, I would like to add a record", L9.d); res["no_json"] = (not nj["admitted"]) and bool(nj["reasons"])
    pr = issue.run("```json\n" + json.dumps(personal(src_log())) + "\n```", src_log().d); res["personal_quarantined"] = pr.get("quarantined") is True
    marker = os.path.join(TMP, "pwn_v15"); evil = copy.deepcopy(tenth); evil.pop("id"); evil["title"] += f" $(touch {marker}) `touch {marker}`"
    body = os.path.join(TMP, "body.txt"); open(body, "w").write("```json\n" + json.dumps(core.finalize(evil)) + "\n```")
    subprocess.run([sys.executable, os.path.join(P, "srcx5_issue.py"), "--body", body, "--log", src_log(9).d, "--out", os.path.join(TMP, "r.json")], capture_output=True)
    res["no_shell_effect"] = not os.path.exists(marker)
    res["pass"] = res["valid"] and res["applied"] and res["no_json"] and res["personal_quarantined"] and res["no_shell_effect"]
    return res

# ---------------- T7 status ----------------
def t7():
    res = {}; L = src_log(); cur = tempfile.mkdtemp(dir=TMP); net.export(L, cur); old = tempfile.mkdtemp(dir=TMP); net.export(src_log(8), old)
    s1, u1 = v14.static_server(cur); s2, u2 = v14.static_server(old); down = f"http://127.0.0.1:{v14.port()}"
    saved = node15.mirrors; node15.mirrors = lambda: []
    try: st = node15.status(L, os.path.join(P, "anchors"), "bafyTESTcid", extra_mirrors=(u1, u2, down))
    finally: node15.mirrors = saved
    states = [m["state"] for m in st["mirrors"]]; res["states"] = states
    res["anchor"] = st["anchors"][:1]; res["chain_intact"] = st["chain_intact"]; res["ipfs"] = st["ipfs"]
    s1.shutdown(); s2.shutdown()
    res["pass"] = (states == ["current", "stale", "down"] and len(st["anchors"]) >= 1 and st["anchors"][0].get("network") == "bitcoin"
                   and st["chain_intact"] is True and (st["ipfs"] or {}).get("cid") == "bafyTESTcid")
    return res

# ---------------- T8 regression ----------------
def t8():
    res = {}
    for name, f in (("T1", v14.t1), ("T2", v14.t2), ("T3", v14.t3), ("T4", v14.t4), ("T5", v14.t5), ("T6", v14.t6)):
        try: res[name] = bool(f().get("pass"))
        except Exception as e: res[name] = f"crash {type(e).__name__}: {e}"
    sealed = {l.split()[1]: l.split()[0] for l in open(os.path.join(P, "tests", "v14", "SEAL_V14.txt")) if l[:1] in "0123456789abcdef" and len(l.split()) == 2}
    res["hashes"] = {f: hashlib.sha256(open(os.path.join(P, f.replace("protocol/", "")), "rb").read()).hexdigest() == sealed[f]
                     for f in ("protocol/srcx5.py", "protocol/srcx5_net.py", "protocol/srcx5_mcp.py")}
    res["pass"] = all(res[k] is True for k in ("T1", "T2", "T3", "T4", "T5", "T6")) and all(res["hashes"].values())
    return res

if __name__ == "__main__":
    t0 = time.time()
    for name, f in (("T1_mcp_http", t1), ("T2_a2a", t2), ("T3_standards", t3), ("T4_install", t4), ("T5_converge", t5),
                    ("T6_issue", t6), ("T7_status", t7), ("T8_regression", t8)):
        try: R[name] = f()
        except Exception:
            import traceback; R[name] = {"pass": False, "crash": traceback.format_exc()[-1500:]}
        print(name, "PASS" if R[name].get("pass") else "NOT MET", flush=True)
    R["D1_D4"] = {"pass": None, "note": "observed in GitHub Actions and on the live mirror after the push"}
    R["seconds"] = round(time.time() - t0, 1)
    json.dump(R, open(os.path.join(OUT, "results_15.json"), "w"), indent=1, default=str)
    print(json.dumps({k: (v.get("pass") if isinstance(v, dict) else v) for k, v in R.items()}))
