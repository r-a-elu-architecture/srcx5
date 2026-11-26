# An always-on SRC-X.5 node. Free option: a Hugging Face Space (SDK: Docker). Also runs on any container host.
FROM python:3.12-slim
WORKDIR /app
COPY srcx5.py SPEC_SRCX5.md ./
COPY log ./log
ENV PORT=7860
EXPOSE 7860
# Joins the network by syncing from the public log's node list (PEERS, comma-separated), then serves.
CMD ["sh", "-c", "python srcx5.py serve --log log --port ${PORT} $(echo ${PEERS:-} | tr ',' '\\n' | sed 's/^/--peer /')"]
