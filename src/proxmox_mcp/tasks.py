from __future__ import annotations

from typing import Any, Optional

from proxmox_mcp.multi_client import MultiClient
from proxmox_mcp.utils import confirm_required, extract_data, validate_node_name


def _api(client: MultiClient, endpoint: str | None = None) -> Any:
    return client.get_client(elevated=False, endpoint=endpoint)


async def task_log(
    client: MultiClient, upid: str, node: Optional[str] = None, limit: Optional[int] = None, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    parts = upid.split(":")
    if node:
        resolved_node = node
    elif len(parts) > 1:
        resolved_node = parts[1]
    else:
        resolved = await client.resolve_node()
        resolved_node = resolved.node
    validate_node_name(resolved_node)
    params: dict[str, Any] = {}
    if limit is not None:
        params["limit"] = limit
    result = await client.safe_api_call(_api(client, endpoint=ep).nodes(resolved_node).tasks(upid).log.get, **params)
    if not isinstance(result, list):
        result = [result] if result else []
    lines = [f"📋 **Task Log: {upid}** ({len(result)} entries)\n"]
    for entry in result[:50]:
        if isinstance(entry, dict):
            t = entry.get("t", entry.get("msg", str(entry)))
            n = entry.get("n", entry.get("line", ""))
            lines.append(f"   {n}: {t}" if n else f"   {t}")
        else:
            lines.append(f"   {entry}")
    if len(result) > 50:
        lines.append(f"   ... {len(result) - 50} more entries")
    return "\n".join(lines)


@confirm_required
async def stop_task(
    client: MultiClient, node: Optional[str] = None, upid: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not upid:
        raise ValueError("upid is required")
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(elevated.nodes(resolved_node).tasks(upid).delete, elevated=True, endpoint=ep)
    data = extract_data(result)
    return f"Task {upid} stopped on {resolved_node}: {data}"
