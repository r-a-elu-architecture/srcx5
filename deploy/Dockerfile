# An always-on SRC-X.5 node. Free option: a Hugging Face Space (SDK: Docker). Also runs on any container host.
FROM python:3.12-slim
WORKDIR /app
COPY srcx5.py srcx5_net.py srcx5_mcp.py SPEC_SRCX5_1_4.md openapi.json context.jsonld MIRRORS.json llms.txt ./
COPY schema ./schema
COPY log ./log
ENV PORT=7860
EXPOSE 7860
# Joins by syncing from the mirrors (and any PEERS, comma-separated), then serves both shapes and the interfaces.
CMD ["sh", "-c", "python srcx5_net.py serve --log log --port ${PORT} $(for m in $(python -c 'import json;print(\" \".join(m[\"url\"] for m in json.load(open(\"MIRRORS.json\"))[\"mirrors\"]))') $(echo ${PEERS:-} | tr ',' ' '); do echo --peer $m; done)"]
