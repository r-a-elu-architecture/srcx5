#!/usr/bin/env python3
"""SRC-X.5 for AI agents: a Model Context Protocol server over stdio (JSON-RPC 2.0, Python standard library only).

Any MCP client (assistants, agent frameworks, IDEs) can list, read, verify and submit records.
  python srcx5_mcp.py --log log                    work on a local copy of the log
  python srcx5_mcp.py --log log --peer URL ...     sync it first from a node or mirror (first that answers)
Tools: srcx5_list, srcx5_get, srcx5_verify, srcx5_verify_log, srcx5_submit, srcx5_ld.
"""
import argparse, json, sys
import srcx5 as core, srcx5_net as net

PROTOCOL = "2025-06-18"
TOOLS = [
    {"name": "srcx5_list", "description": "List the active records of the open log: id, type, title, outcome.",
     "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False}},
    {"name": "srcx5_get", "description": "Return one record by its id (the SHA-256 of its canonical form).",
     "inputSchema": {"type": "object", "properties": {"id": {"type": "string", "pattern": "^[0-9a-f]{64}$"}}, "required": ["id"]}},
    {"name": "srcx5_verify", "description": "Check a record against every rule (identity hash, disclosure, consent and privacy, harm bound, "
     "conformance, attribution, purpose). Give a record object, or the id of a record in the log. Returns the reasons; empty means valid.",
     "inputSchema": {"type": "object", "properties": {"record": {"type": "object"}, "id": {"type": "string"}}}},
    {"name": "srcx5_verify_log", "description": "Verify the whole hash chain of the log. Returns the entry count and any broken entries.",
     "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False}},
    {"name": "srcx5_submit", "description": "Submit a record. Valid records are appended to the log; others are quarantined with reasons, never deleted.",
     "inputSchema": {"type": "object", "properties": {"record": {"type": "object"}}, "required": ["record"]}},
    {"name": "srcx5_ld", "description": "Return a record as JSON-LD in the W3C PROV vocabulary, for linked-data and provenance tools.",
     "inputSchema": {"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]}},
]

def call(log, name, a):
    if name == "srcx5_list":
        return [{"id": i, "type": log.recs[i].get("type"), "title": log.recs[i].get("title"),
                 "criteria_met": (log.recs[i].get("outcome") or {}).get("criteria_met")} for i in log.active()]
    if name == "srcx5_get":
        r = log.recs.get(a.get("id", ""));  return r if r else {"error": "unknown id"}
    if name == "srcx5_verify":
        rec = a.get("record") if isinstance(a.get("record"), dict) else log.recs.get(a.get("id", ""))
        if rec is None: return {"error": "give a record or a known id"}
        R = core.check(rec, known=set(log.recs), known_recs=log.recs)
        if rec.get("id") in log.recs and core.canon(log.recs[rec["id"]]) == core.canon(rec): R = [x for x in R if "already" not in x]
        return {"valid": not R, "reasons": R}
    if name == "srcx5_verify_log":
        bad = log.verify_chain(); return {"entries": len(log.entries), "intact": not bad, "broken": bad, "head": log.head()}
    if name == "srcx5_submit":
        R = log.admit(a.get("record")) if isinstance(a.get("record"), dict) else ["a record is a JSON object"]
        return {"admitted": not R, "quarantined": bool(R), "reasons": R, "head": log.head()}
    if name == "srcx5_ld":
        r = log.recs.get(a.get("id", "")); return net.ld(r) if r else {"error": "unknown id"}
    raise KeyError(name)

def handle(log, msg):
    mid, m, p = msg.get("id"), msg.get("method"), msg.get("params") or {}
    if m == "initialize":
        res = {"protocolVersion": PROTOCOL, "capabilities": {"tools": {"listChanged": False}},
               "serverInfo": {"name": "srcx5", "version": net.NET_VERSION},
               "instructions": "SRC-X.5: an open record of sealed claims. Every record's id is the SHA-256 of its canonical form; verify before you trust."}
    elif m == "tools/list": res = {"tools": TOOLS}
    elif m == "tools/call":
        try:
            out = call(log, p.get("name"), p.get("arguments") or {})
            res = {"content": [{"type": "text", "text": json.dumps(out, ensure_ascii=False)}], "structuredContent": {"result": out}, "isError": False}
        except KeyError: return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32602, "message": f"unknown tool {p.get('name')}"}}
        except Exception as e: res = {"content": [{"type": "text", "text": f"{type(e).__name__}: {e}"}], "isError": True}
    elif m == "ping": res = {}
    elif m and m.startswith("notifications/"): return None
    else: return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"method not found: {m}"}}
    return {"jsonrpc": "2.0", "id": mid, "result": res}

def main(argv=None):
    ap = argparse.ArgumentParser(prog="srcx5_mcp"); ap.add_argument("--log", required=True); ap.add_argument("--peer", action="append", default=[])
    A = ap.parse_args(argv); log = core.Log(A.log)
    if A.peer:
        try: net.sync_any(log, A.peer)
        except Exception as e: print("no peer answered:", e, file=sys.stderr)
    for line in sys.stdin:
        line = line.strip()
        if not line: continue
        try: msg = json.loads(line)
        except Exception: out = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "parse error"}}
        else: out = handle(log, msg) if isinstance(msg, dict) else {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "invalid request"}}
        if out is not None: sys.stdout.write(json.dumps(out, ensure_ascii=False) + "\n"); sys.stdout.flush()

if __name__ == "__main__":
    main()
