#!/usr/bin/env python3
"""SRC-X.5 v1.5.1 (FIX1, tests/v15/FIX1_V15.md): entry points for an installed copy (pip install).

An installed copy keeps its interface files (openapi.json, schema/, context.jsonld, MIRRORS.json, NODES.json, llms.txt)
in <prefix>/share/srcx5, not beside the modules. This launcher points the sealed modules (srcx5_net, srcx5_node; both
unchanged) at that directory when the files are not beside them, then runs them. Python standard library only.
"""
import os, sys
import srcx5_net as net, srcx5_node as node

def _locate():
    here = os.path.dirname(os.path.abspath(node.__file__))
    if os.path.exists(os.path.join(here, "openapi.json")): return here
    for d in (os.path.join(sys.prefix, "share", "srcx5"), os.path.join(sys.base_prefix, "share", "srcx5"),
              os.path.join(os.path.expanduser("~"), ".local", "share", "srcx5")):
        if os.path.exists(os.path.join(d, "openapi.json")): return d
    return here

def _point():
    d = _locate(); net.HERE = d; node.HERE = d

def node_main(argv=None):
    _point(); node.main(argv)

def net_main(argv=None):
    _point(); net.main(argv)

def mcp_main(argv=None):
    _point(); import srcx5_mcp; srcx5_mcp.main(argv)

if __name__ == "__main__":
    node_main()
