from __future__ import annotations

from typing import Any, Optional

from proxmox_mcp.multi_client import MultiClient
from proxmox_mcp.utils import confirm_required, extract_upid, validate_node_name, validate_vmid

ALLOWED_VMTYPES = ("qemu", "lxc")


def _validate_vmtype(vmtype: str) -> None:
    if vmtype not in ALLOWED_VMTYPES:
        raise ValueError(f"Invalid vmtype {vmtype!r}. Must be one of {ALLOWED_VMTYPES}")


def _api(client: MultiClient, endpoint: str | None = None) -> Any:
    return client.get_client(elevated=False, endpoint=endpoint)


async def snapshot_config(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    snapname: str = "",
    vmtype: str = "qemu",
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    _validate_vmtype(vmtype)
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    result = await client.safe_api_call(
        getattr(_api(client, endpoint=ep).nodes(resolved_node), vmtype)(vmid).snapshot(snapname).config.get
    )
    if not isinstance(result, dict):
        return f"Snapshot {snapname!r} config for {vmtype} {vmid} on {resolved_node}: {result}"
    lines = [f"**Snapshot {snapname!r} config for {vmtype} {vmid} on {resolved_node}**\n"]
    for key, val in sorted(result.items()):
        lines.append(f"  • **{key}**: {val}")
    return "\n".join(lines)


async def list_snapshots(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    vmtype: str = "qemu",
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    _validate_vmtype(vmtype)
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    result = await client.safe_api_call(
        getattr(_api(client, endpoint=ep).nodes(resolved_node), vmtype)(vmid).snapshot.get
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = [f"\U0001f4f8 **Snapshots for {vmtype} {vmid} on {resolved_node}**\n"]
    for snap in result:
        name = snap.get("name", "unknown")
        description = snap.get("description", "")
        parent = snap.get("parent", "")
        snaptime = snap.get("snaptime", "")
        lines.append(f"   • **{name}** (parent: {parent})")
        if description:
            lines.append(f"     {description}")
        if snaptime:
            lines.append(f"     Created: {snaptime}")
    if not result:
        lines.append("   No snapshots found.")
    return "\n".join(lines)


@confirm_required
async def create_snapshot(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    snapname: str = "",
    vmtype: str = "qemu",
    description: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    _validate_vmtype(vmtype)
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    params: dict[str, Any] = {"snapname": snapname}
    if description:
        params["description"] = description
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        getattr(elevated.nodes(resolved_node), vmtype)(vmid).snapshot.post,
        elevated=True,
        **params,
    )
    upid = extract_upid(result)
    return f"Snapshot {snapname!r} creation initiated for {vmtype} {vmid} on {resolved_node}. UPID: {upid}"


@confirm_required
async def delete_snapshot(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    snapname: str = "",
    vmtype: str = "qemu",
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    """Delete a snapshot for a VM or LXC container (elevated, confirm required).

    Note: For qemu VMs, PVE requires the VM.Snapshot permission even when
    using an elevated/admin token. If you encounter "Permission denied
    (/vms/<vmid>, VM.Snapshot)", grant VM.Snapshot to the elevated token's
    user via PVE ACL: Datacenter → Permissions → Add: path=/vms/<vmid>,
    role=Administrator (or a custom role with VM.Snapshot), user=<token_user>.
    """
    client.raise_if_not_elevated()
    _validate_vmtype(vmtype)
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        getattr(elevated.nodes(resolved_node), vmtype)(vmid).snapshot(snapname).delete,
        elevated=True,
    )
    upid = extract_upid(result)
    return f"Snapshot {snapname!r} deletion initiated for {vmtype} {vmid} on {resolved_node}. UPID: {upid}"


@confirm_required
async def update_snapshot_config(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    snapname: str = "",
    vmtype: str = "qemu",
    description: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    _validate_vmtype(vmtype)
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    params: dict[str, Any] = {}
    if description is not None:
        params["description"] = description
    params.update(kwargs)
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        getattr(elevated.nodes(resolved_node), vmtype)(vmid).snapshot(snapname).config.put,
        elevated=True,
        **params,
    )
    return f"Snapshot {snapname!r} config updated for {vmtype} {vmid} on {resolved_node}"


@confirm_required
async def rollback_snapshot(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    snapname: str = "",
    vmtype: str = "qemu",
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    _validate_vmtype(vmtype)
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        getattr(elevated.nodes(resolved_node), vmtype)(vmid).snapshot(snapname).rollback.post,
        elevated=True,
    )
    upid = extract_upid(result)
    return f"Rollback to snapshot {snapname!r} initiated for {vmtype} {vmid} on {resolved_node}. UPID: {upid}"
