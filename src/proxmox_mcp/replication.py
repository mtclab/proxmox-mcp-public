from __future__ import annotations

from typing import Any, Optional

from proxmox_mcp.multi_client import MultiClient
from proxmox_mcp.utils import confirm_required, validate_node_name


def _api(client: MultiClient, endpoint: str | None = None) -> Any:
    return client.get_client(elevated=False, endpoint=endpoint)


async def list_replication(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.replication.get,
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = ["🔄 **Replication Jobs**\n"]
    for job in result:
        jobid = job.get("id", "unknown")
        source = job.get("source", "N/A")
        target = job.get("target", "N/A")
        schedule = job.get("schedule", "N/A")
        state = job.get("state", "N/A")
        disable = job.get("disable", 0)
        status = "disabled" if disable else state
        lines.append(f"   • **{jobid}**")
        lines.append(f"     Source: {source} | Target: {target} | Schedule: {schedule} | Status: {status}")
    if not result:
        lines.append("   No replication jobs found.")
    return "\n".join(lines)


@confirm_required
async def create_replication(
    client: MultiClient,
    id: str = "",
    source: Optional[str] = None,
    target: Optional[str] = None,
    schedule: Optional[str] = None,
    comment: Optional[str] = None,
    disable: Optional[bool] = None,
    rate: Optional[float] = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not id:
        raise ValueError("id is required for replication job creation")
    params: dict[str, Any] = {"id": id}
    if source is not None:
        params["source"] = source
    if target is not None:
        params["target"] = target
    if schedule is not None:
        params["schedule"] = schedule
    if comment is not None:
        params["comment"] = comment
    if disable is not None:
        params["disable"] = 1 if disable else 0
    if rate is not None:
        params["rate"] = rate
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.replication.post,
        elevated=True,
        **params,
    )
    return f"Replication job {id!r} created"


async def get_replication(client: MultiClient, id: str = "", endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    if not id:
        raise ValueError("id is required")
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.replication(id).get,
    )
    lines = [f"🔄 **Replication Job: {id}**\n"]
    if isinstance(result, dict):
        for key, value in sorted(result.items()):
            lines.append(f"   • {key}: {value}")
    return "\n".join(lines)


@confirm_required
async def update_replication(
    client: MultiClient,
    id: str = "",
    source: Optional[str] = None,
    target: Optional[str] = None,
    schedule: Optional[str] = None,
    comment: Optional[str] = None,
    disable: Optional[bool] = None,
    rate: Optional[float] = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not id:
        raise ValueError("id is required for replication job update")
    params: dict[str, Any] = {}
    if source is not None:
        params["source"] = source
    if target is not None:
        params["target"] = target
    if schedule is not None:
        params["schedule"] = schedule
    if comment is not None:
        params["comment"] = comment
    if disable is not None:
        params["disable"] = 1 if disable else 0
    if rate is not None:
        params["rate"] = rate
    if not params:
        raise ValueError("At least one parameter must be provided to update")
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.replication(id).put,
        elevated=True,
        **params,
    )
    opts = ", ".join(f"{k}={v!r}" for k, v in params.items())
    return f"Replication job {id!r} updated: {opts}"


@confirm_required
async def delete_replication(
    client: MultiClient, id: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not id:
        raise ValueError("id is required for replication job deletion")
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.replication(id).delete,
        elevated=True,
    )
    return f"Replication job {id!r} deleted"


async def list_node_replication(client: MultiClient, node: Optional[str] = None, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).replication.get,
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = [f"🔄 **Replication on {resolved_node}**\n"]
    for job in result:
        jobid = job.get("id", "unknown")
        source = job.get("source", "N/A")
        target = job.get("target", "N/A")
        state = job.get("state", "N/A")
        lines.append(f"   • **{jobid}** — source: {source}, target: {target}, state: {state}")
    if not result:
        lines.append("   No replication jobs found.")
    return "\n".join(lines)


@confirm_required
async def schedule_replication(
    client: MultiClient, node: Optional[str] = None, id: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not id:
        raise ValueError("id is required for scheduling replication")
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.nodes(resolved_node).replication(id).schedule_now.post,
        elevated=True,
    )
    return f"Replication job {id!r} scheduled on {resolved_node}"


async def get_replication_status(
    client: MultiClient, node: Optional[str] = None, id: str = "", endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    if not id:
        raise ValueError("id is required")
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).replication(id).status.get,
    )
    lines = [f"🔄 **Replication Status: {id} on {resolved_node}**\n"]
    if isinstance(result, list):
        for entry in result:
            if isinstance(entry, dict):
                for key, val in sorted(entry.items()):
                    lines.append(f"   • {key}: {val}")
            else:
                lines.append(f"   • {entry}")
    elif isinstance(result, dict):
        for key, val in sorted(result.items()):
            lines.append(f"   • {key}: {val}")
    else:
        lines.append(str(result))
    return "\n".join(lines)


async def get_replication_log(
    client: MultiClient, node: Optional[str] = None, id: str = "", endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    if not id:
        raise ValueError("id is required")
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).replication(id).log.get,
    )
    lines = [f"🔄 **Replication Log: {id} on {resolved_node}**\n"]
    if isinstance(result, list):
        for entry in result:
            if isinstance(entry, dict):
                t = entry.get("t", "")
                n = entry.get("n", "")
                lines.append(f"   • [{n}] {t}" if n else f"   • {t}")
            else:
                lines.append(f"   • {entry}")
    elif isinstance(result, dict):
        for key, val in sorted(result.items()):
            lines.append(f"   • {key}: {val}")
    else:
        lines.append(str(result))
    if not result:
        lines.append("   No log entries found.")
    return "\n".join(lines)
