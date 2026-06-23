# Future: native single-binary rewrite

Decision (this session): **package now (done — Docker/uvx/pipx), rewrite later.**
The packaging makes install easy for most. A native rewrite would make it a
zero-dependency download-and-run binary — the ultimate "easy install."

## Why a rewrite
- One static binary, no Python/venv/Docker. `curl`-and-run, cross-platform.
- Faster cold start; trivial to ship in a container `FROM scratch`.

## Cost
- Reimplement the PVE client (dual-token auth, node discovery, SSL flexibility,
  UPID task polling, PVE error handling) + register all 70+ tools against an MCP
  SDK in the target language. The tool surface is the bulk of the work.

## Language options
- **Go** — `mark3labs/mcp-go` (mature MCP SDK), trivial static cross-compile
  (`CGO_ENABLED=0`), great HTTP/JSON. Recommended for an API-wrapper server.
- **Rust** — `rmcp`/`mcp-sdk`; fastest + smallest, more upfront effort.

## Approach when pulled
1. Port the client (auth/discovery/SSL/tasks) + a few tools; verify against a
   live PVE (or the existing Python server's responses as a golden reference).
2. Port tools in batches; keep the env-var config + dual-token model identical so
   the MCP config and docs don't change for users.
3. Ship static binaries (GH release) + a `FROM scratch` image; keep the Python
   version as the reference until parity.

Until then: Docker / uvx / pipx (see README) are the easy paths.
