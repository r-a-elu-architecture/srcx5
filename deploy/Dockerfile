# An always-on SRC-X.5 node (v1.5): read API, submit, MCP over HTTP (/mcp), A2A (/a2a), agent card. Python standard library only.
# Free option: a Hugging Face Space (SDK: Docker). Also: docker run -p 7860:7860 ghcr.io/r-a-elu-architecture/srcx5
# Stdio MCP for local AI clients: docker run -i --rm ghcr.io/r-a-elu-architecture/srcx5 mcp
FROM python:3.12-slim
LABEL org.opencontainers.image.source="https://github.com/r-a-elu-architecture/srcx5" \
      org.opencontainers.image.description="SRC-X.5 node: an open record of sealed claims, verified at the source" \
      org.opencontainers.image.licenses="Apache-2.0" \
      io.modelcontextprotocol.server.name="io.github.r-a-elu-architecture/srcx5"
WORKDIR /app
COPY srcx5.py srcx5_net.py srcx5_mcp.py srcx5_anchor.py srcx5_node.py SPEC_SRCX5_1_4_1.md openapi.json context.jsonld MIRRORS.json NODES.json llms.txt ./
COPY schema ./schema
COPY log ./log
COPY deploy/entrypoint.sh /entrypoint.sh
ENV PORT=7860 PYTHONUNBUFFERED=1
EXPOSE 7860
ENTRYPOINT ["sh", "/entrypoint.sh"]
