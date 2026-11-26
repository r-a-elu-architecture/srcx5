#!/usr/bin/env python3
"""SRC-X.5 v1.5: one node that every protocol can reach, and a network that keeps signalling (Python standard library only).

The record rules (srcx5.py, v1.3) and the v1.4 network layer (srcx5_net.py, srcx5_mcp.py) are sealed and unchanged.
This file adds only ways in:
  * MCP over HTTP (Streamable HTTP, JSON responses) at POST /mcp: any cloud agent connects by URL, same six tools as stdio;
  * Agent2Agent (A2A, JSON-RPC) at POST /a2a, described by /.well-known/agent-card.json;
  * OpenAPI 3.1 for the whole node (openapi_v15.json), the format agent platforms import as actions or tools;
  * a status document: which mirrors and nodes hold the head, the Bitcoin proof state and the IPFS content id;
  * write anywhere, converge everywhere: the public log pulls admitted records from every listed node (NODES.json).

  python srcx5_node.py serve  --log DIR [--port 7860] [--peer URL]...   node: read API + submit + /mcp + /a2a + agent card
  python srcx5_node.py export --log DIR --out DIR [--base URL]          static mirror with the v1.5 documents
  python srcx5_node.py status --log DIR [--anchors DIR] [--ipfs CID]    status document (mirrors, nodes, anchors, ipfs)
  python srcx5_node.py pull   --log DIR [--nodes NODES.json]            pull admitted records from every node that answers
"""
import argparse, glob, json, os, sys, time
import srcx5 as core, srcx5_net as net, srcx5_mcp as mcp

VERSION = "1.5"
HERE = os.path.dirname(os.path.abspath(__file__))
PAGES = "https://r-a-elu-architecture.github.io/srcx5/"
A2A_VERSION = "0.3.0"

def _json(name, default):
    p = os.path.join(HERE, name)
    try: return json.load(open(p))
    except Exception: return default

def nodes():
    return [n["url"] for n in _json("NODES.json", {"nodes": []}).get("nodes", []) if n.get("url")]

def mirrors():
    return [m["url"] for m in _json("MIRRORS.json", {"mirrors": []}).get("mirrors", [])]

# ---------- descriptions every platform reads ----------
def agent_card(base):
    base = base.rstrip("/")
    skill = lambda i, n, d, ex: {"id": i, "name": n, "description": d, "tags": ["provenance", "pre-registration", "reproducibility"],
                                 "examples": ex, "inputModes": ["application/json", "text/plain"], "outputModes": ["application/json"]}
    return {"protocolVersion": A2A_VERSION, "name": "SRC-X.5", "version": VERSION,
            "description": "An open record of sealed claims, verified at the source. Lists, reads, verifies and accepts records; "
                           "every record's id is the SHA-256 of its canonical form.",
            "url": base + "/a2a", "preferredTransport": "JSONRPC",
            "additionalInterfaces": [{"url": base + "/a2a", "transport": "JSONRPC"}],
            "provider": {"organization": "SRC-X.5 (open protocol)", "url": PAGES},
            "documentationUrl": "https://github.com/r-a-elu-architecture/srcx5",
            "capabilities": {"streaming": False, "pushNotifications": False, "stateTransitionHistory": False},
            "defaultInputModes": ["application/json", "text/plain"], "defaultOutputModes": ["application/json"],
            "skills": [skill(t["name"], t["name"].replace("srcx5_", "").replace("_", " "), t["description"],
                             [json.dumps({"tool": t["name"], "arguments": {}})]) for t in mcp.TOOLS]}

def openapi(base=None):
    o = json.load(open(os.path.join(HERE, "openapi.json")))
    o["info"]["version"] = VERSION
    o["info"]["description"] = (o["info"].get("description", "") + " v1.5 adds MCP over HTTP (/mcp), A2A (/a2a, /.well-known/agent-card.json) "
                                "and a status document (/status.json on static mirrors).").strip()
    o["servers"] = [{"url": PAGES + "api", "description": "static mirror (read)"}] + \
                   [{"url": u, "description": "public node (read, submit, MCP, A2A)"} for u in nodes()] + \
                   [{"url": "{node}", "description": "any node", "variables": {"node": {"default": base or "http://localhost:7860"}}}]
    rpc = {"type": "object", "required": ["jsonrpc", "method"], "properties": {"jsonrpc": {"const": "2.0"}, "id": {}, "method": {"type": "string"},
                                                                              "params": {"type": "object"}}}
    o["paths"]["/mcp"] = {"post": {"operationId": "mcp", "summary": "Model Context Protocol over HTTP (JSON-RPC 2.0; tools srcx5_list, "
                                    "srcx5_get, srcx5_verify, srcx5_verify_log, srcx5_submit, srcx5_ld). Node only.",
                                    "requestBody": {"required": True, "content": {"application/json": {"schema": rpc}}},
                                    "responses": {"200": {"description": "JSON-RPC response", "content": {"application/json": {"schema": {"type": "object"}}}},
                                                  "202": {"description": "notification accepted"}}}}
    o["paths"]["/a2a"] = {"post": {"operationId": "a2a", "summary": "Agent2Agent JSON-RPC: message/send with a data part {tool, arguments}. Node only.",
                                    "requestBody": {"required": True, "content": {"application/json": {"schema": rpc}}},
                                    "responses": {"200": {"description": "JSON-RPC response", "content": {"application/json": {"schema": {"type": "object"}}}}}}}
    o["paths"]["/.well-known/agent-card.json"] = {"get": {"operationId": "agentCard", "summary": "A2A agent card",
        "responses": {"200": {"description": "agent card", "content": {"application/json": {"schema": {"type": "object",
                      "required": ["name", "url", "version", "skills", "capabilities", "defaultInputModes", "defaultOutputModes"]}}}}}}}
    return o

# ---------- A2A: the same six tools, as messages ----------
def a2a(log, msg):
    mid, m, p = msg.get("id"), msg.get("method"), msg.get("params") or {}
    err = lambda c, t: {"jsonrpc": "2.0", "id": mid, "error": {"code": c, "message": t}}
    if m != "message/send": return err(-32601, f"method not found: {m}")
    parts = ((p.get("message") or {}).get("parts")) or []
    req = next((x.get("data") for x in parts if x.get("kind") == "data" and isinstance(x.get("data"), dict)), None)
    if req is None:
        txt = " ".join(x.get("text", "") for x in parts if x.get("kind") == "text").strip().lower()
        req = {"tool": "srcx5_verify_log"} if "verify" in txt else {"tool": "srcx5_list"}
    try: out = mcp.call(log, req.get("tool"), req.get("arguments") or {})
    except KeyError: return err(-32602, f"unknown tool {req.get('tool')}")
    return {"jsonrpc": "2.0", "id": mid, "result": {"kind": "message", "role": "agent", "messageId": f"srcx5-{time.time_ns()}",
            "parts": [{"kind": "data", "data": {"tool": req.get("tool"), "result": out}}]}}

# ---------- the node ----------
def serve(log, port, peers=(), base=None):
    srv = net.serve(log, port, peers)
    Base = srv.RequestHandlerClass
    url = base or f"http://localhost:{port}"
    class H(Base):
        def _body(s):
            try: n = int(s.headers.get("Content-Length", ""))
            except ValueError: s._send(411, {"error": "Content-Length required"}); return None
            if n < 0 or n > net.MAX_BODY: s._send(413, {"error": f"body larger than {net.MAX_BODY} bytes"}); return None
            try: return json.loads(s.rfile.read(n).decode("utf-8"))
            except Exception: s._send(400, {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "parse error"}}); return None
        def do_GET(s):
            path = s.path.partition("?")[0]
            if path == "/.well-known/agent-card.json": return s._send(200, agent_card(url))
            if path == "/openapi_v15.json": return s._send(200, openapi(url))
            if path == "/mcp": return s._send(405, {"error": "use POST (Streamable HTTP, JSON responses)"})
            if path in ("/", "/health"):
                return s._send(200, {core.KEY: core.VERSION, "transport": net.NET_VERSION, "node": VERSION, "records": len(log.recs),
                                     "active": len(log.active()), "head": log.head(), "mission": core.MISSION,
                                     "connect": {"http": "/openapi_v15.json", "mcp": "POST /mcp", "a2a": "POST /a2a",
                                                 "agent_card": "/.well-known/agent-card.json", "submit": "POST /submit"}})
            return super().do_GET()
        def do_POST(s):
            if s.path not in ("/mcp", "/a2a"): return super().do_POST()
            msg = s._body()
            if msg is None: return
            if not isinstance(msg, dict): return s._send(400, {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "invalid request"}})
            out = mcp.handle(log, msg) if s.path == "/mcp" else a2a(log, msg)
            if out is None:
                s.send_response(202); s.send_header("Access-Control-Allow-Origin", "*"); s.send_header("Content-Length", "0"); s.end_headers(); return
            return s._send(200, out)
    srv.RequestHandlerClass = H
    return srv

# ---------- status: the network signalling ----------
def _anchors(d):
    out = []
    for f in sorted(glob.glob(os.path.join(d, "*.json"))):
        try: a = json.load(open(f)); out.append({k: a.get(k) for k in ("head", "network", "method", "status", "proof")})
        except Exception: pass
    return out

def status(log, anchors=None, ipfs=None, extra_mirrors=()):
    def probe(u):
        t = time.time()
        try:
            h = json.loads(net.fetch(u.rstrip("/") + "/head.json"))
            st = "current" if h.get("head") == log.head() else "stale"
            return {"url": u, "state": st, "count": h.get("count"), "ms": round(1000 * (time.time() - t))}
        except Exception as e: return {"url": u, "state": "down", "why": type(e).__name__}
    return {"protocol": "SRC-X.5", "node": VERSION, "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "head": log.head(), "count": len(log.entries), "chain_intact": log.verify_chain() == [],
            "mirrors": [probe(u) for u in list(mirrors()) + list(extra_mirrors)], "nodes": [probe(u) for u in nodes()],
            "anchors": _anchors(anchors) if anchors else [], "ipfs": ({"cid": ipfs, "covers": "the read API directory without status.json (ipfs add -r --cid-version 1)",
                      "gateway": f"https://{ipfs}.ipfs.dweb.link/"} if ipfs else None)}

def pull(log, urls):
    """Write anywhere, converge everywhere: take from each node what this log lacks; every record is re-checked on arrival."""
    got = []
    for u in urls:
        try: a, moved = net.sync_one(log, u); got.append({"node": u, "added": a, "bytes": moved})
        except Exception as e: got.append({"node": u, "error": type(e).__name__})
    return got

def export(log, out, base=PAGES + "api", anchors=None, ipfs=None, probe=True):
    net.export(log, out)
    os.makedirs(os.path.join(out, ".well-known"), exist_ok=True)
    node0 = (nodes() or [None])[0]
    json.dump(agent_card(node0 or base), open(os.path.join(out, ".well-known", "agent-card.json"), "w"), indent=1)
    json.dump(openapi(node0), open(os.path.join(out, "openapi_v15.json"), "w"), indent=1)
    for f in ("NODES.json",):
        if os.path.exists(os.path.join(HERE, f)): json.dump(_json(f, {}), open(os.path.join(out, f), "w"), indent=1)
    if probe: json.dump(status(log, anchors, ipfs), open(os.path.join(out, "status.json"), "w"), indent=1)

def main(argv=None):
    ap = argparse.ArgumentParser(prog="srcx5-node"); sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("serve"); s.add_argument("--log", required=True); s.add_argument("--port", type=int, default=int(os.environ.get("PORT", 7860)))
    s.add_argument("--peer", action="append", default=[]); s.add_argument("--base", default=os.environ.get("PUBLIC_URL"))
    e = sub.add_parser("export"); e.add_argument("--log", required=True); e.add_argument("--out", required=True)
    e.add_argument("--anchors"); e.add_argument("--ipfs"); e.add_argument("--no-probe", action="store_true")
    t = sub.add_parser("status"); t.add_argument("--log", required=True); t.add_argument("--anchors"); t.add_argument("--ipfs")
    p = sub.add_parser("pull"); p.add_argument("--log", required=True); p.add_argument("--node", action="append", default=[])
    A = ap.parse_args(argv); log = core.Log(A.log)
    if A.cmd == "serve":
        srv = serve(log, A.port, A.peer, A.base); print(f"SRC-X.5 node {VERSION} on :{A.port}  (/mcp, /a2a, /submit)", file=sys.stderr)
        srv.serve_forever()
    elif A.cmd == "export": export(log, A.out, anchors=A.anchors, ipfs=A.ipfs, probe=not A.no_probe)
    elif A.cmd == "status": print(json.dumps(status(log, A.anchors, A.ipfs), indent=1))
    elif A.cmd == "pull": print(json.dumps(pull(log, A.node or nodes()), indent=1))

if __name__ == "__main__":
    main()
