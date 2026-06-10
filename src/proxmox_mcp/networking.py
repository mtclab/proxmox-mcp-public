from __future__ import annotations

import logging
from typing import Any, Optional

from proxmox_mcp.multi_client import MultiClient
from proxmox_mcp.utils import confirm_required, extract_upid, validate_iface_name

logger = logging.getLogger(__name__)


def _api(client: MultiClient, endpoint: str | None = None) -> Any:
    return client.get_client(elevated=False, endpoint=endpoint)


async def _is_management_interface(client: MultiClient, node: str, iface: str, endpoint: str | None = None) -> bool:
    if iface == "vmbr0":
        return True
    try:
        host = client.config.host
        result = await client.safe_api_call(
            client.get_client(elevated=False, endpoint=endpoint).nodes(node).network.get
        )
        if isinstance(result, list):
            for ent in result:
                if ent.get("iface") == iface:
                    addr = ent.get("address", "")
                    if addr and host in addr:
                        return True
    except Exception:
        logger.warning("Could not check if %s is management interface", iface)
    return False


async def _apply_network(client: MultiClient, node: str, iface: str = "", endpoint: str | None = None) -> None:
    ep = endpoint or client.default_endpoint
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.nodes(node).network.put,
        elevated=True,
    )


async def list_network(client: MultiClient, node: Optional[str] = None, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    result = await client.safe_api_call(_api(client, endpoint=ep).nodes(resolved_node).network.get)
    if not isinstance(result, list):
        result = [result] if result else []
    lines = [f"\U0001f310 **Network Interfaces on {resolved_node}**\n"]
    for iface in result:
        name = iface.get("iface", "unknown")
        itype = iface.get("type", "unknown")
        addr = iface.get("address", "")
        netmask = iface.get("netmask", "")
        gateway = iface.get("gateway", "")
        active = iface.get("active", 0)
        status = "up" if active else "down"
        lines.append(f"   • **{name}** ({itype}) [{status}]")
        if addr:
            lines.append(f"     Address: {addr}/{netmask}" if netmask else f"     Address: {addr}")
        if gateway:
            lines.append(f"     Gateway: {gateway}")
    if not result:
        lines.append("   No interfaces found.")
    return "\n".join(lines)


@confirm_required
async def create_network(
    client: MultiClient,
    node: Optional[str] = None,
    iface: str = "",
    type: str = "bridge",
    address: Optional[str] = None,
    netmask: Optional[str] = None,
    gateway: Optional[str] = None,
    bridge_ports: Optional[str] = None,
    cidr: Optional[str] = None,
    address6: Optional[str] = None,
    gateway6: Optional[str] = None,
    cidr6: Optional[str] = None,
    autostart: Optional[bool] = None,
    mtu: Optional[int] = None,
    confirm: bool = False,
    apply: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    if not iface:
        raise ValueError("iface is required for network interface creation")
    validate_iface_name(iface)
    existing = await client.safe_api_call(_api(client, endpoint=ep).nodes(resolved_node).network.get)
    if isinstance(existing, list):
        for ent in existing:
            if ent.get("iface") == iface:
                raise ValueError(f"Network interface {iface!r} already exists on {resolved_node}")
    params: dict[str, Any] = {"iface": iface, "type": type}
    if address:
        params["address"] = address
    if netmask:
        params["netmask"] = netmask
    if gateway:
        params["gateway"] = gateway
    if bridge_ports:
        params["bridge_ports"] = bridge_ports
    if cidr is not None:
        params["cidr"] = cidr
    if address6 is not None:
        params["address6"] = address6
    if gateway6 is not None:
        params["gateway6"] = gateway6
    if cidr6 is not None:
        params["cidr6"] = cidr6
    if autostart is not None:
        params["autostart"] = 1 if autostart else 0
    if mtu is not None:
        params["mtu"] = mtu
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).network.post,
        elevated=True,
        **params,
    )
    if result is None:
        upid = "staged"
    elif isinstance(result, str):
        upid = result
    elif isinstance(result, dict):
        upid = extract_upid(result)
    else:
        upid = result
    staged_suffix = " (changes staged, not yet applied)" if upid == "staged" else ""
    msg = f"Network interface {iface!r} creation initiated on {resolved_node}. UPID: {upid}{staged_suffix}"
    if apply:
        warnings: list[str] = []
        if await _is_management_interface(client, resolved_node, iface):
            warnings.append(" WARNING: Applying changes to management interface may disconnect the agent.")
        await _apply_network(client, resolved_node, iface)
        msg += " Network changes applied."
        msg += "".join(warnings)
    return msg


@confirm_required
async def update_network(
    client: MultiClient,
    node: Optional[str] = None,
    iface: str = "",
    address: Optional[str] = None,
    netmask: Optional[str] = None,
    gateway: Optional[str] = None,
    cidr: Optional[str] = None,
    address6: Optional[str] = None,
    gateway6: Optional[str] = None,
    cidr6: Optional[str] = None,
    autostart: Optional[bool] = None,
    mtu: Optional[int] = None,
    delete: Optional[str] = None,
    confirm: bool = False,
    apply: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    if not iface:
        raise ValueError("iface is required for network interface update")
    validate_iface_name(iface)
    params: dict[str, Any] = {}
    if address is not None:
        params["address"] = address
    if netmask is not None:
        params["netmask"] = netmask
    if gateway is not None:
        params["gateway"] = gateway
    if cidr is not None:
        params["cidr"] = cidr
    if address6 is not None:
        params["address6"] = address6
    if gateway6 is not None:
        params["gateway6"] = gateway6
    if cidr6 is not None:
        params["cidr6"] = cidr6
    if autostart is not None:
        params["autostart"] = 1 if autostart else 0
    if mtu is not None:
        params["mtu"] = mtu
    if delete is not None:
        params["delete"] = delete
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).network(iface).put,
        elevated=True,
        **params,
    )
    if result is None:
        upid = "staged"
    elif isinstance(result, str):
        upid = result
    elif isinstance(result, dict):
        upid = extract_upid(result)
    else:
        upid = result
    staged_suffix = " (changes staged, not yet applied)" if upid == "staged" else ""
    msg = f"Network interface {iface!r} update initiated on {resolved_node}. UPID: {upid}{staged_suffix}"
    if apply:
        warnings: list[str] = []
        if await _is_management_interface(client, resolved_node, iface):
            warnings.append(" WARNING: Applying changes to management interface may disconnect the agent.")
        await _apply_network(client, resolved_node, iface)
        msg += " Network changes applied."
        msg += "".join(warnings)
    return msg


@confirm_required
async def delete_network(
    client: MultiClient,
    node: Optional[str] = None,
    iface: str = "",
    confirm: bool = False,
    apply: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    if not iface:
        raise ValueError("iface is required for network interface deletion")
    validate_iface_name(iface)
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).network(iface).delete,
        elevated=True,
    )
    if result is None:
        upid = "staged"
    elif isinstance(result, str):
        upid = result
    elif isinstance(result, dict):
        upid = extract_upid(result)
    else:
        upid = result
    staged_suffix = " (changes staged, not yet applied)" if upid == "staged" else ""
    msg = f"Network interface {iface!r} deletion initiated on {resolved_node}. UPID: {upid}{staged_suffix}"
    if apply:
        warnings: list[str] = []
        if await _is_management_interface(client, resolved_node, iface):
            warnings.append(" WARNING: Applying changes to management interface may disconnect the agent.")
        await _apply_network(client, resolved_node, iface)
        msg += " Network changes applied."
        msg += "".join(warnings)
    return msg


@confirm_required
async def revert_network(
    client: MultiClient, node: Optional[str] = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).network.delete,
        elevated=True,
    )
    if result is None:
        upid = "staged"
    elif isinstance(result, str):
        upid = result
    elif isinstance(result, dict):
        upid = extract_upid(result)
    else:
        upid = result
    staged_suffix = " (changes staged, not yet applied)" if upid == "staged" else ""
    return f"Network changes reverted on {resolved_node}. UPID: {upid}{staged_suffix}"
