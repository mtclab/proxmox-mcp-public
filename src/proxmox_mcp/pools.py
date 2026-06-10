from __future__ import annotations

from typing import Any, Optional

from proxmox_mcp.multi_client import MultiClient
from proxmox_mcp.utils import confirm_required


def _api(client: MultiClient, endpoint: str | None = None) -> Any:
    return client.get_client(elevated=False, endpoint=endpoint)


async def list_pools(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(_api(client, endpoint=ep).pools.get)
    if not isinstance(result, list):
        result = [result] if result else []
    lines = ["**Pool List**\n"]
    for pool in result:
        poolid = pool.get("poolid", "?")
        comment = pool.get("comment", "")
        lines.append(f"  • {poolid}")
        if comment:
            lines.append(f"    {comment}")
    if not result:
        lines.append("  No pools found.")
    return "\n".join(lines)


async def get_pool(client: MultiClient, poolid: str, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(_api(client, endpoint=ep).pools(poolid).get)
    lines = [f"**Pool: {poolid}**\n"]
    if isinstance(result, dict):
        comment = result.get("comment", "")
        if comment:
            lines.append(f"  Comment: {comment}")
        members = result.get("members", [])
        if isinstance(members, list):
            for member in members:
                vmid = member.get("vmid", "?")
                vmtype = member.get("type", "?")
                name = member.get("name", "")
                lines.append(f"  • {vmid} ({vmtype}) {name}")
    if not isinstance(result, dict) or not result.get("members"):
        if not isinstance(result, dict) or not members:
            lines.append("  No members.")
    return "\n".join(lines)


@confirm_required
async def create_pool(
    client: MultiClient,
    poolid: str = "",
    comment: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not poolid:
        raise ValueError("poolid is required for pool creation")
    params: dict[str, Any] = {"poolid": poolid}
    if comment is not None:
        params["comment"] = comment
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(elevated.pools.post, elevated=True, **params)
    return f"Pool {poolid!r} created"


@confirm_required
async def update_pool(
    client: MultiClient,
    poolid: str = "",
    comment: Optional[str] = None,
    delete: Optional[str] = None,
    members: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not poolid:
        raise ValueError("poolid is required for pool update")
    params: dict[str, Any] = {}
    if comment is not None:
        params["comment"] = comment
    if delete is not None:
        params["delete"] = delete
    if members is not None:
        params["members"] = members
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(elevated.pools(poolid).put, elevated=True, **params)
    return f"Pool {poolid!r} updated"


@confirm_required
async def delete_pool(client: MultiClient, poolid: str = "", confirm: bool = False, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not poolid:
        raise ValueError("poolid is required for pool deletion")
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(elevated.pools(poolid).delete, elevated=True, endpoint=ep)
    return f"Pool {poolid!r} deleted"
