#!/usr/bin/env python3
"""SRC-X.5 node on a Hugging Face Space (Gradio SDK, CPU basic). Python standard library only.

Joins by syncing from the mirrors, then serves the v1.5 node (srcx5_node.py, unchanged). A browser that opens "/" gets a
landing page; every machine path (/health, /mcp, /a2a, /submit, /records/..., agent card) answers exactly as on any node.
"""
import html, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import srcx5 as core, srcx5_net as net, srcx5_node as node

PAGES = "https://r-a-elu-architecture.github.io/srcx5/"
REPO = "https://github.com/r-a-elu-architecture/srcx5"

PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SRC-X.5 node</title><style>
:root{{--a:#2a8a82;--t:#1d2327;--m:#5b6670;--l:#e6eaec}}
body{{margin:0;font:16px/1.55 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;color:var(--t);background:#fff}}
main{{max-width:780px;margin:0 auto;padding:40px 22px 56px}} h1{{font-size:28px;margin:0 0 6px}} h2{{font-size:17px;margin:30px 0 8px}}
p{{margin:8px 0}} .m{{color:var(--m)}} a{{color:var(--a)}} code{{font:14px ui-monospace,SFMono-Regular,Menlo,monospace;background:#f4f6f7;padding:1px 5px;border-radius:4px}}
.s{{display:flex;gap:14px;flex-wrap:wrap;margin:18px 0}} .s div{{border:1px solid var(--l);border-radius:8px;padding:10px 14px;min-width:120px}}
.s b{{display:block;font-size:20px}} .s span{{font-size:13px;color:var(--m)}}
table{{border-collapse:collapse;width:100%}} td{{border-top:1px solid var(--l);padding:8px 6px;vertical-align:top}} td:first-child{{width:34%;color:var(--m)}}
.bar{{height:3px;background:var(--a);opacity:.55;margin-bottom:26px}}
</style></head><body><main><div class="bar"></div>
<h1>SRC-X.5 node</h1>
<p class="m">An open record of sealed claims, verified at the source. Each record states what was predicted and by which
criteria, which files were fixed and when, what came out, and who replicated it. Its id is the SHA-256 of its canonical
form, so any copy is verified independently of where it came from.</p>
<div class="s"><div><b>{count}</b><span>records</span></div><div><b>{active}</b><span>active</span></div>
<div><b>{chain}</b><span>hash chain</span></div><div><b><code>{head}</code></b><span>log head</span></div></div>
<p><a href="{pages}">Verify every record in your browser</a> &middot; <a href="{repo}">Repository</a> &middot;
<a href="https://doi.org/10.5281/zenodo.24555259">Paper</a></p>
<h2>Connect</h2><table>
<tr><td>AI agents (MCP over HTTP)</td><td><code>POST {base}/mcp</code></td></tr>
<tr><td>Agent2Agent (A2A)</td><td><code>{base}/.well-known/agent-card.json</code> &middot; <code>POST {base}/a2a</code></td></tr>
<tr><td>HTTP and JSON</td><td><a href="{base}/openapi_v15.json"><code>/openapi_v15.json</code></a> (OpenAPI 3.1) &middot; <a href="{base}/health"><code>/health</code></a> &middot; <a href="{base}/ids.json"><code>/ids.json</code></a></td></tr>
<tr><td>Submit a record</td><td><code>POST {base}/submit</code>, or the <a href="{repo}/issues/new?template=submit-record.yml">issue form</a> (no git needed)</td></tr>
<tr><td>Python</td><td><code>pip install srcx5</code></td></tr>
<tr><td>Run your own node</td><td><code>docker run -p 7860:7860 ghcr.io/r-a-elu-architecture/srcx5</code></td></tr>
<tr><td>MCP Registry</td><td><code>io.github.r-a-elu-architecture/srcx5</code></td></tr>
</table>
<p class="m" style="margin-top:22px">Records admitted here reach the public log at the next heartbeat (every six hours) and every mirror after it.
Rules: <a href="{repo}/blob/main/SPEC_SRCX5_1_4_1.md">specification</a>. Code Apache 2.0, specification CC BY 4.0.</p>
</main></body></html>"""

def main():
    log = core.Log("log")
    peers = [m["url"] for m in json.load(open("MIRRORS.json"))["mirrors"]]
    for u in peers:                      # join: take from the mirrors what this copy lacks, re-checked on arrival
        try: net.sync_one(log, u); break
        except Exception: pass
    base = os.environ.get("PUBLIC_URL") or ("https://" + os.environ["SPACE_HOST"] if os.environ.get("SPACE_HOST") else "")
    srv = node.serve(log, int(os.environ.get("PORT", 7860)), peers, base or None)
    Base = srv.RequestHandlerClass
    class H(Base):
        def do_GET(s):
            path = s.path.partition("?")[0]
            if path in ("/", "/index.html") and "text/html" in (s.headers.get("Accept") or ""):
                body = PAGE.format(count=len(log.entries), active=len(log.active()), chain="intact" if log.verify_chain() == [] else "broken",
                                   head=html.escape(log.head()[:12]) + "…", pages=PAGES, repo=REPO, base=html.escape(base)).encode("utf-8")
                s.send_response(200); s.send_header("Content-Type", "text/html; charset=utf-8")
                s.send_header("Content-Length", str(len(body))); s.end_headers(); s.wfile.write(body); return
            return super().do_GET()
    srv.RequestHandlerClass = H
    print(f"SRC-X.5 node on :{srv.server_address[1]}", flush=True)
    srv.serve_forever()

if __name__ == "__main__":
    main()
