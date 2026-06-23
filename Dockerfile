# homepilot-proxmox-mcp — Proxmox VE MCP server
FROM python:3.11-slim
LABEL org.opencontainers.image.source="https://github.com/mtclab/proxmox-mcp-public"
LABEL org.opencontainers.image.description="MCP server for Proxmox VE — full API coverage, dual-token auth"
LABEL org.opencontainers.image.licenses="MIT"
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir . && adduser --disabled-password --gecos "" mcp
USER mcp
# MCP runs over stdio — attach with `docker run -i`
ENTRYPOINT ["homepilot-proxmox-mcp"]
