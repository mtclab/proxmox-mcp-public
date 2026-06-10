from __future__ import annotations

from typing import Any, Optional

from proxmox_mcp.multi_client import MultiClient
from proxmox_mcp.utils import confirm_required


def _api(client: MultiClient, endpoint: str | None = None) -> Any:
    return client.get_client(elevated=False, endpoint=endpoint)


async def list_metric_servers(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.metrics.server.get,
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = ["📊 **Metric Servers**\n"]
    for server in result:
        sid = server.get("id", "unknown")
        stype = server.get("type", "unknown")
        server_addr = server.get("server", "N/A")
        lines.append(f"   • **{sid}** — type: {stype}, server: {server_addr}")
    if not result:
        lines.append("   No metric servers found.")
    return "\n".join(lines)


async def get_metric_server(client: MultiClient, id: str = "", endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    if not id:
        raise ValueError("id is required")
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.metrics.server(id).get,
    )
    lines = [f"📊 **Metric Server: {id}**\n"]
    if isinstance(result, dict):
        for key, value in sorted(result.items()):
            lines.append(f"   • {key}: {value}")
    return "\n".join(lines)


@confirm_required
async def create_metric_server(
    client: MultiClient,
    id: str = "",
    type: str = "graphite",
    server: Optional[str] = None,
    port: Optional[int] = None,
    comment: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not id:
        raise ValueError("id is required for metric server creation")
    valid_types = {"graphite", "influxdb", "opentelemetry"}
    if type not in valid_types:
        raise ValueError(f"type must be one of {valid_types}, got {type!r}")
    params: dict[str, Any] = {"id": id, "type": type}
    if server is not None:
        params["server"] = server
    if port is not None:
        params["port"] = port
    if comment is not None:
        params["comment"] = comment
    params.update(kwargs)
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.metrics.server(id).post,
        elevated=True,
        **params,
    )
    return f"Metric server {id!r} ({type}) created"


@confirm_required
async def update_metric_server(
    client: MultiClient,
    id: str = "",
    server: Optional[str] = None,
    port: Optional[int] = None,
    comment: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not id:
        raise ValueError("id is required for metric server update")
    params: dict[str, Any] = {}
    if server is not None:
        params["server"] = server
    if port is not None:
        params["port"] = port
    if comment is not None:
        params["comment"] = comment
    params.update(kwargs)
    if not params:
        raise ValueError("At least one parameter must be provided to update")
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.metrics.server(id).put,
        elevated=True,
        **params,
    )
    opts = ", ".join(f"{k}={v!r}" for k, v in params.items())
    return f"Metric server {id!r} updated: {opts}"


@confirm_required
async def delete_metric_server(
    client: MultiClient, id: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not id:
        raise ValueError("id is required for metric server deletion")
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.metrics.server(id).delete,
        elevated=True,
    )
    return f"Metric server {id!r} deleted"


async def metrics_index(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.metrics.get,
    )
    lines = ["\U0001f4ca **Metrics Index**\n"]
    if isinstance(result, dict):
        for key, value in sorted(result.items()):
            lines.append(f"   • {key}: {value}")
    else:
        lines.append(str(result))
    return "\n".join(lines)


async def export_metrics(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.metrics.export.get,
    )
    lines = ["\U0001f4ca **Cluster Metrics Export**\n"]
    if isinstance(result, list):
        for entry in result:
            if isinstance(entry, dict):
                mid = entry.get("id", entry.get("metric", "unknown"))
                value = entry.get("value", "N/A")
                lines.append(f"   • {mid}: {value}")
            else:
                lines.append(f"   {entry}")
        if not result:
            lines.append("   No metrics data found.")
    elif isinstance(result, dict):
        for key, value in sorted(result.items()):
            lines.append(f"   • {key}: {value}")
    else:
        lines.append(str(result))
    return "\n".join(lines)
