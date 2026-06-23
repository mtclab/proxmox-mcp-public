# homepilot-proxmox-mcp

HomePilot MCP server for Proxmox VE — full API coverage, dual-token auth, SSL handling, node discovery.

## Features

- **70+ tools** covering full PVE API (VMs, LXC, storage, templates, snapshots, backups, networking, ACL)
- **Dual-token auth** — read-only monitor token (PVEAuditor) + admin token (PVEAdmin)
- **Read-only by default** — elevated ops require `PROXMOX_ALLOW_ELEVATED=true` AND `confirm=true`
- **Auto node discovery** — queries `/nodes`, never assumes node name
- **SSL flexible** — `verify=True/False/path/to/ca.pem`
- **Task tracking** — UPID polling with exitstatus checking
- **Error aware** — handles PVE 595, SSL mismatch, token permission errors

## Install & run

The server speaks MCP over **stdio**. Pick whichever is easiest:

### Docker — no Python needed
```bash
docker run -i --rm \
  -e PROXMOX_URL=https://pve.example.local:8006 -e PROXMOX_VERIFY=false \
  -e PROXMOX_ADMIN_TOKEN_ID='homepilot@pve!homepilot' -e PROXMOX_ADMIN_TOKEN_SECRET=... \
  ghcr.io/mtclab/proxmox-mcp:latest
```
Or build locally: `docker build -t proxmox-mcp . && docker run -i --rm -e PROXMOX_URL=... proxmox-mcp`

### uvx — run without installing (needs [uv](https://docs.astral.sh/uv/))
```bash
uvx --from git+https://github.com/mtclab/proxmox-mcp-public homepilot-proxmox-mcp
```

### pipx — install the command
```bash
pipx install git+https://github.com/mtclab/proxmox-mcp-public
homepilot-proxmox-mcp
```

### pip
```bash
pip install git+https://github.com/mtclab/proxmox-mcp-public
```

### From source (contributors)
```bash
git clone https://github.com/mtclab/proxmox-mcp-public.git && cd proxmox-mcp-public
python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"
```

## Configuration

```json
{
  "mcpServers": {
    "proxmox": {
      "command": "homepilot-proxmox-mcp",
      "env": {
        "PROXMOX_URL": "https://pve.example.local:8006",
        "PROXMOX_VERIFY": "false",
        "PROXMOX_MONITOR_TOKEN_ID": "monitor@pam!monitoring",
        "PROXMOX_MONITOR_TOKEN_SECRET": "",
        "PROXMOX_ADMIN_TOKEN_ID": "admin@pam!tokenid",
        "PROXMOX_ADMIN_TOKEN_SECRET": "",
        "PROXMOX_ALLOW_ELEVATED": "false",
        "PROXMOX_DEFAULT_NODE": "pve"
      }
    }
  }
}
```
`command` is the installed entry point (pipx/pip). For the **Docker** image, point
the client at `docker` instead:
```json
{ "mcpServers": { "proxmox": {
  "command": "docker",
  "args": ["run","-i","--rm",
    "-e","PROXMOX_URL","-e","PROXMOX_VERIFY",
    "-e","PROXMOX_ADMIN_TOKEN_ID","-e","PROXMOX_ADMIN_TOKEN_SECRET",
    "ghcr.io/mtclab/proxmox-mcp:latest"],
  "env": { "PROXMOX_URL": "https://pve.example.local:8006", "PROXMOX_VERIFY": "false",
           "PROXMOX_ADMIN_TOKEN_ID": "admin@pam!tokenid", "PROXMOX_ADMIN_TOKEN_SECRET": "" }
}}}
```

## Development

```bash
pytest
```

## Architecture

```
proxmox_mcp/
├── server.py          # MCP server, tool registration
├── client.py          # PVE API client (dual token, node discovery, SSL)
├── config.py          # Environment config, validation
├── discovery.py       # Read-only discovery tools
├── lifecycle.py       # VM/LXC create/start/stop/delete
├── templates.py       # Template catalog, download, upload
├── snapshots.py       # Snapshot management
├── backups.py         # Backup/restore
├── networking.py      # Network config
├── permissions.py     # ACL/roles/users/tokens
├── storage.py         # Storage content, ISOs
└── utils.py           # confirm_required, node_resolver, error handling
```
## Multi-Node Support

The server supports multi-node PVE clusters. Configure one or more endpoints:

```json
{
  "mcpServers": {
    "proxmox": {
      "command": "homepilot-proxmox-mcp",
      "env": {
        "PROXMOX_URL": "https://pve.example.local:8006",
        "PROXMOX_VERIFY": "false",
        "PROXMOX_MONITOR_TOKEN_ID": "monitor@pam!monitoring",
        "PROXMOX_MONITOR_TOKEN_SECRET": "",
        "PROXMOX_ADMIN_TOKEN_ID": "admin@pam!tokenid",
        "PROXMOX_ADMIN_TOKEN_SECRET": "",
        "PROXMOX_ALLOW_ELEVATED": "false"
      }
    }
  }
}
```

For multi-node clusters, set `PROXMOX_URL` to any cluster node. The server auto-discovers all nodes.

## Deployment

The MCP server runs as a long-running process (stdio or HTTP transport) managed by your agent framework. No Docker container needed.

Key env vars:
- `PROXMOX_URL` — PVE API endpoint
- `PROXMOX_MONITOR_TOKEN_ID` / `SECRET` — read-only PVEAuditor token
- `PROXMOX_ADMIN_TOKEN_ID` / `SECRET` — admin PVEAdmin token
- `PROXMOX_ALLOW_ELEVATED` — set `true` to enable destructive ops
- `PROXMOX_DEFAULT_NODE` — default node name (optional)
- `PROXMOX_VERIFY` — SSL verification (`true`, `false`, or path to CA PEM)

## Integration with Zabbix

PVE nodes can be monitored via the Proxmox API HTTP agent template in Zabbix — no zabbix-agent2 needed on the PVE hosts. The agent stack (database, monitoring, proxy, app, agent hosts) all run zabbix-agent2 with Docker plugin.

## API References

- **PVE API Viewer**: https://pve.proxmox.com/pve-docs/api-viewer/index.html
- **PVE Docs Repo**: https://github.com/proxmox/pve-docs
- **PVE API Wiki**: https://pve.proxmox.com/wiki/Proxmox_VE_API