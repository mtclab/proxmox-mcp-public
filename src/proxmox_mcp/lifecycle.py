from __future__ import annotations

from typing import Any, Optional

from proxmox_mcp.exceptions import ProxmoxNotFoundError
from proxmox_mcp.multi_client import MultiClient
from proxmox_mcp.utils import confirm_required, extract_upid, validate_disk_size, validate_node_name, validate_vmid


def _api(client: MultiClient, endpoint: str | None = None) -> Any:
    return client.get_client(elevated=False, endpoint=endpoint)


async def _get_next_vmid(client: MultiClient, endpoint: str | None = None) -> int:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(_api(client, endpoint=ep).cluster.nextid.get)
    if result is None:
        raise ProxmoxNotFoundError("Failed to get next VMID from cluster")
    return int(result)


async def _validate_ostemplate(client: MultiClient, node: str, ostemplate: str, endpoint: str | None = None) -> None:
    ep = endpoint or client.default_endpoint
    storage_name = ostemplate.split(":")[0] if ":" in ostemplate else "local"
    try:
        content = await client.safe_api_call(_api(client, endpoint=ep).nodes(node).storage(storage_name).content.get)
        if isinstance(content, list):
            volids = [item.get("volid", "") for item in content]
            if ostemplate not in volids:
                raise ValueError(
                    f"OSTemplate {ostemplate!r} not found in storage {storage_name!r}. "
                    f"Available: {', '.join(v for v in volids if 'vztmpl' in v)}"
                )
    except ValueError:
        raise
    except Exception:
        pass


@confirm_required
async def create_lxc(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    ostemplate: str = "",
    hostname: Optional[str] = None,
    memory: Optional[int] = None,
    cores: Optional[int] = None,
    rootfs: Optional[str] = None,
    storage: Optional[str] = None,
    password: Optional[str] = None,
    swap: Optional[int] = None,
    features: Optional[str] = None,
    unprivileged: Optional[bool] = None,
    onboot: Optional[bool] = None,
    description: Optional[str] = None,
    pool: Optional[str] = None,
    net0: Optional[str] = None,
    nameserver: Optional[str] = None,
    searchdomain: Optional[str] = None,
    ssh_public_keys: Optional[str] = None,
    tags: Optional[str] = None,
    start: bool = False,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)

    if not vmid:
        vmid = await _get_next_vmid(client)
    validate_vmid(vmid)

    if ostemplate:
        await _validate_ostemplate(client, resolved_node, ostemplate)

    params: dict[str, Any] = {
        "vmid": vmid,
        "ostemplate": ostemplate,
    }
    if hostname:
        params["hostname"] = hostname
    if memory is not None:
        params["memory"] = memory
    if cores is not None:
        params["cores"] = cores
    if rootfs:
        params["rootfs"] = rootfs
    if storage:
        params["storage"] = storage
    if password:
        params["password"] = password
    if swap is not None:
        params["swap"] = swap
    if features:
        params["features"] = features
    if unprivileged is not None:
        params["unprivileged"] = 1 if unprivileged else 0
    if onboot is not None:
        params["onboot"] = 1 if onboot else 0
    if description:
        params["description"] = description
    if pool:
        params["pool"] = pool
    if net0:
        params["net0"] = net0
    if nameserver:
        params["nameserver"] = nameserver
    if searchdomain:
        params["searchdomain"] = searchdomain
    if ssh_public_keys:
        params["ssh-public-keys"] = ssh_public_keys
    if tags:
        params["tags"] = tags
    if start:
        params["start"] = 1

    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(elevated.nodes(resolved_node).lxc.post, elevated=True, **params)
    upid = extract_upid(result)
    return f"LXC container {vmid} created on {resolved_node}. UPID: {upid}"


@confirm_required
async def start_lxc(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).lxc(vmid).status.start.post, elevated=True, endpoint=ep
    )
    upid = extract_upid(result)
    return f"LXC {vmid} start initiated on {resolved_node}. UPID: {upid}"


@confirm_required
async def stop_lxc(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).lxc(vmid).status.stop.post, elevated=True, endpoint=ep
    )
    upid = extract_upid(result)
    return f"LXC {vmid} stop initiated on {resolved_node}. UPID: {upid}"


@confirm_required
async def shutdown_lxc(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).lxc(vmid).status.shutdown.post, elevated=True, endpoint=ep
    )
    upid = extract_upid(result)
    return f"LXC {vmid} shutdown initiated on {resolved_node}. UPID: {upid}"


@confirm_required
async def reboot_lxc(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).lxc(vmid).status.reboot.post, elevated=True, endpoint=ep
    )
    upid = extract_upid(result)
    return f"LXC {vmid} reboot initiated on {resolved_node}. UPID: {upid}"


@confirm_required
async def delete_lxc(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(elevated.nodes(resolved_node).lxc(vmid).delete, elevated=True, endpoint=ep)
    upid = extract_upid(result)
    return f"LXC {vmid} deleted on {resolved_node}. UPID: {upid}"


@confirm_required
async def configure_lxc(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    cores: Optional[int] = None,
    memory: Optional[int] = None,
    onboot: Optional[bool] = None,
    description: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)

    params: dict[str, Any] = {}
    if cores is not None:
        params["cores"] = cores
    if memory is not None:
        params["memory"] = memory
    if onboot is not None:
        params["onboot"] = 1 if onboot else 0
    if description is not None:
        params["description"] = description
    parsed = _parse_kwargs(kwargs)
    params.update(parsed)

    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(elevated.nodes(resolved_node).lxc(vmid).config.put, elevated=True, **params)
    upid = extract_upid(result)
    return f"LXC {vmid} configured on {resolved_node}. UPID: {upid}"


@confirm_required
async def create_vm(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    name: Optional[str] = None,
    memory: Optional[str] = None,
    cores: Optional[int] = None,
    sockets: Optional[int] = None,
    disk_size: Optional[str] = None,
    storage: Optional[str] = None,
    iso: Optional[str] = None,
    ostype: Optional[str] = None,
    net0: Optional[str] = None,
    description: Optional[str] = None,
    boot: Optional[str] = None,
    scsihw: Optional[str] = None,
    onboot: Optional[bool] = None,
    start: Optional[bool] = None,
    pool: Optional[str] = None,
    cpu: Optional[str] = None,
    bios: Optional[str] = None,
    agent: Optional[str] = None,
    tags: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)

    if not vmid:
        vmid = await _get_next_vmid(client)
    validate_vmid(vmid)

    params: dict[str, Any] = {"vmid": vmid}
    if name:
        params["name"] = name
    if memory is not None:
        params["memory"] = memory
    if cores is not None:
        params["cores"] = cores
    if sockets is not None:
        params["sockets"] = sockets
    if disk_size:
        validated_size = validate_disk_size(disk_size)
        if storage:
            params["scsi0"] = f"{storage}:{validated_size}"
        else:
            raise ValueError(
                "storage is required when disk_size is specified (PVE requires 'storage:size' format for scsi0)"
            )
    if storage and not disk_size:
        params["storage"] = storage
    if iso:
        if ":" in iso:
            params["cdrom"] = f"{iso},media=cdrom"
        elif storage:
            params["cdrom"] = f"{storage}:iso/{iso},media=cdrom"
        else:
            params["cdrom"] = f"{iso},media=cdrom"
    if ostype:
        params["ostype"] = ostype
    if net0:
        params["net0"] = net0
    if description is not None:
        params["description"] = description
    if boot is not None:
        params["boot"] = boot
    if scsihw is not None:
        params["scsihw"] = scsihw
    if onboot is not None:
        params["onboot"] = 1 if onboot else 0
    if start is not None:
        params["start"] = 1 if start else 0
    if pool is not None:
        params["pool"] = pool
    if cpu is not None:
        params["cpu"] = cpu
    if bios is not None:
        params["bios"] = bios
    if agent is not None:
        params["agent"] = agent
    if tags is not None:
        params["tags"] = tags

    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(elevated.nodes(resolved_node).qemu.post, elevated=True, **params)
    upid = extract_upid(result)
    return f"VM {vmid} created on {resolved_node}. UPID: {upid}"


@confirm_required
async def start_vm(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).qemu(vmid).status.start.post, elevated=True, endpoint=ep
    )
    upid = extract_upid(result)
    return f"VM {vmid} start initiated on {resolved_node}. UPID: {upid}"


@confirm_required
async def stop_vm(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).qemu(vmid).status.stop.post, elevated=True, endpoint=ep
    )
    upid = extract_upid(result)
    return f"VM {vmid} stop initiated on {resolved_node}. UPID: {upid}"


@confirm_required
async def shutdown_vm(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).qemu(vmid).status.shutdown.post, elevated=True, endpoint=ep
    )
    upid = extract_upid(result)
    return f"VM {vmid} shutdown initiated on {resolved_node}. UPID: {upid}"


@confirm_required
async def reboot_vm(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).qemu(vmid).status.reboot.post, elevated=True, endpoint=ep
    )
    upid = extract_upid(result)
    return f"VM {vmid} reboot initiated on {resolved_node}. UPID: {upid}"


@confirm_required
async def delete_vm(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(elevated.nodes(resolved_node).qemu(vmid).delete, elevated=True, endpoint=ep)
    upid = extract_upid(result)
    return f"VM {vmid} deleted on {resolved_node}. UPID: {upid}"


@confirm_required
async def clone_vm(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    newid: Optional[int] = None,
    name: Optional[str] = None,
    full: bool = True,
    target: Optional[str] = None,
    snapname: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)

    if not newid:
        newid = await _get_next_vmid(client)
    validate_vmid(newid)

    params: dict[str, Any] = {"newid": newid}
    if name:
        params["name"] = name
    params["full"] = 1 if full else 0
    if target is not None:
        params["target"] = target
    if snapname is not None:
        params["snapname"] = snapname

    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(elevated.nodes(resolved_node).qemu(vmid).clone.post, elevated=True, **params)
    upid = extract_upid(result)
    return f"VM {vmid} clone initiated → {newid} on {resolved_node}. UPID: {upid}"


@confirm_required
async def migrate_vm(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    target: Optional[str] = None,
    online: Optional[bool] = None,
    with_local_disks: Optional[bool] = None,
    targetstorage: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)

    params: dict[str, Any] = {"target": target}
    if online is not None:
        params["online"] = 1 if online else 0
    if with_local_disks is not None:
        params["with-local-disks"] = 1 if with_local_disks else 0
    if targetstorage is not None:
        params["targetstorage"] = targetstorage

    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(elevated.nodes(resolved_node).qemu(vmid).migrate.post, elevated=True, **params)
    upid = extract_upid(result)
    return f"VM {vmid} migration to {target} initiated. UPID: {upid}"


@confirm_required
async def resize_lxc(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    disk: str = "rootfs",
    size: str = "+10G",
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)

    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).lxc(vmid).resize.put, elevated=True, disk=disk, size=size
    )
    upid = extract_upid(result)
    return f"LXC {vmid} disk {disk} resize to {size} initiated on {resolved_node}. UPID: {upid}"


@confirm_required
async def suspend_lxc(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).lxc(vmid).status.suspend.post, elevated=True, endpoint=ep
    )
    upid = extract_upid(result)
    return f"LXC {vmid} suspend initiated on {resolved_node}. UPID: {upid}"


@confirm_required
async def resume_lxc(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).lxc(vmid).status.resume.post, elevated=True, endpoint=ep
    )
    upid = extract_upid(result)
    return f"LXC {vmid} resume initiated on {resolved_node}. UPID: {upid}"


@confirm_required
async def clone_lxc(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    newid: Optional[int] = None,
    hostname: Optional[str] = None,
    full: bool = True,
    target: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)

    if not newid:
        newid = await _get_next_vmid(client)
    validate_vmid(newid)

    params: dict[str, Any] = {"newid": newid}
    if hostname:
        params["hostname"] = hostname
    params["full"] = 1 if full else 0
    if target:
        params["target"] = target

    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(elevated.nodes(resolved_node).lxc(vmid).clone.post, elevated=True, **params)
    upid = extract_upid(result)
    return f"LXC {vmid} clone initiated → {newid} on {resolved_node}. UPID: {upid}"


@confirm_required
async def migrate_lxc(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    target: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)

    params: dict[str, Any] = {"target": target}

    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(elevated.nodes(resolved_node).lxc(vmid).migrate.post, elevated=True, **params)
    upid = extract_upid(result)
    return f"LXC {vmid} migration to {target} initiated. UPID: {upid}"


async def lxc_interfaces(
    client: MultiClient, node: Optional[str] = None, vmid: Optional[int] = None, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    result = await client.safe_api_call(_api(client, endpoint=ep).nodes(resolved_node).lxc(vmid).interfaces.get)
    if not isinstance(result, list):
        result = [result] if result else []
    lines = [f"**Interfaces for LXC {vmid} on {resolved_node}**\n"]
    for iface in result:
        name = iface.get("name", "unknown")
        hwaddr = iface.get("hwaddr", "")
        lines.append(f"  • **{name}** (HW: {hwaddr})")
        for addr in iface.get("ip-addresses", []):
            ip = addr.get("ip-address", "")
            prefix = addr.get("ip-prefix-length", "")
            proto = addr.get("ip-address-type", "")
            lines.append(f"    - {proto}: {ip}/{prefix}")
    if not result:
        lines.append("  No interfaces found.")
    return "\n".join(lines)


@confirm_required
async def configure_vm(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    cores: Optional[int] = None,
    memory: Optional[str] = None,
    onboot: Optional[bool] = None,
    description: Optional[str] = None,
    tags: Optional[str] = None,
    kwargs: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)

    params: dict[str, Any] = {}
    if cores is not None:
        params["cores"] = cores
    if memory is not None:
        params["memory"] = memory
    if onboot is not None:
        params["onboot"] = 1 if onboot else 0
    if description is not None:
        params["description"] = description
    if tags is not None:
        params["tags"] = tags
    parsed = _parse_kwargs(kwargs)
    params.update(parsed)

    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(elevated.nodes(resolved_node).qemu(vmid).config.put, elevated=True, **params)
    if result is None:
        return f"VM {vmid} configuration updated on {resolved_node} (no pending changes)"
    upid = extract_upid(result)
    return f"VM {vmid} configured on {resolved_node}. UPID: {upid}"


@confirm_required
async def resize_vm(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    disk: str = "scsi0",
    size: str = "+10G",
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).qemu(vmid).resize.put, elevated=True, disk=disk, size=size
    )
    upid = extract_upid(result)
    return f"VM {vmid} disk {disk} resize to {size} initiated on {resolved_node}. UPID: {upid}"


@confirm_required
async def reset_vm(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).qemu(vmid).status.reset.post, elevated=True, endpoint=ep
    )
    upid = extract_upid(result)
    return f"VM {vmid} reset initiated on {resolved_node}. UPID: {upid}"


@confirm_required
async def suspend_vm(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).qemu(vmid).status.suspend.post, elevated=True, endpoint=ep
    )
    upid = extract_upid(result)
    return f"VM {vmid} suspend initiated on {resolved_node}. UPID: {upid}"


@confirm_required
async def resume_vm(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).qemu(vmid).status.resume.post, elevated=True, endpoint=ep
    )
    upid = extract_upid(result)
    return f"VM {vmid} resume initiated on {resolved_node}. UPID: {upid}"


@confirm_required
async def move_vm_disk(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    disk: str = "scsi0",
    storage: Optional[str] = None,
    format: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)

    params: dict[str, Any] = {"disk": disk, "storage": storage}
    if format:
        params["format"] = format

    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).qemu(vmid).move_disk.post, elevated=True, **params
    )
    upid = extract_upid(result)
    return f"VM {vmid} disk {disk} move to {storage} initiated on {resolved_node}. UPID: {upid}"


@confirm_required
async def convert_to_template(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).qemu(vmid).template.post, elevated=True, endpoint=ep
    )
    upid = extract_upid(result)
    return f"VM {vmid} convert to template initiated on {resolved_node}. UPID: {upid}"


@confirm_required
async def convert_lxc_to_template(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).lxc(vmid).template.post, elevated=True, endpoint=ep
    )
    upid = extract_upid(result)
    return f"LXC {vmid} convert to template initiated on {resolved_node}. UPID: {upid}"


async def lxc_migrate_preconditions(
    client: MultiClient, node: Optional[str] = None, vmid: Optional[int] = None, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    result = await client.safe_api_call(_api(client, endpoint=ep).nodes(resolved_node).lxc(vmid).migrate.get)
    lines = [f"**LXC {vmid} migrate preconditions on {resolved_node}**\n"]
    if isinstance(result, dict):
        for key, value in sorted(result.items()):
            lines.append(f"  • {key}: {value}")
    else:
        lines.append(str(result))
    return "\n".join(lines)


async def vm_migrate_preconditions(
    client: MultiClient, node: Optional[str] = None, vmid: Optional[int] = None, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    result = await client.safe_api_call(_api(client, endpoint=ep).nodes(resolved_node).qemu(vmid).migrate.get)
    lines = [f"**VM {vmid} migrate preconditions on {resolved_node}**\n"]
    if isinstance(result, dict):
        for key, value in sorted(result.items()):
            lines.append(f"  • {key}: {value}")
    else:
        lines.append(str(result))
    return "\n".join(lines)


async def lxc_feature_check(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    feature: str = "",
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).lxc(vmid).feature.get, feature=feature
    )
    lines = [f"**LXC {vmid} feature check on {resolved_node}**\n"]
    if isinstance(result, dict):
        for key, value in result.items():
            lines.append(f"  • {key}: {value}")
    else:
        lines.append(f"  {result}")
    return "\n".join(lines)


async def vm_feature_check(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    feature: str = "",
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).qemu(vmid).feature.get, feature=feature
    )
    lines = [f"**VM {vmid} feature check on {resolved_node}**\n"]
    if isinstance(result, dict):
        for key, value in result.items():
            lines.append(f"  • {key}: {value}")
    else:
        lines.append(f"  {result}")
    return "\n".join(lines)


async def vm_pending_config(
    client: MultiClient, node: Optional[str] = None, vmid: Optional[int] = None, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    result = await client.safe_api_call(_api(client, endpoint=ep).nodes(resolved_node).qemu(vmid).pending.get)
    if not isinstance(result, list):
        result = [result] if result else []
    lines = [f"**VM {vmid} pending config on {resolved_node}**\n"]
    for item in result:
        key = item.get("key", "?")
        value = item.get("value", item.get("pending", ""))
        delete = item.get("delete", 0)
        if delete:
            lines.append(f"  • {key}: [DELETE]")
        else:
            lines.append(f"  • {key}: {value}")
    if not result:
        lines.append("  No pending changes.")
    return "\n".join(lines)


async def lxc_pending_config(
    client: MultiClient, node: Optional[str] = None, vmid: Optional[int] = None, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    result = await client.safe_api_call(_api(client, endpoint=ep).nodes(resolved_node).lxc(vmid).pending.get)
    if not isinstance(result, list):
        result = [result] if result else []
    lines = [f"**LXC {vmid} pending config on {resolved_node}**\n"]
    for item in result:
        key = item.get("key", "?")
        value = item.get("value", item.get("pending", ""))
        delete = item.get("delete", 0)
        if delete:
            lines.append(f"  • {key}: [DELETE]")
        else:
            lines.append(f"  • {key}: {value}")
    if not result:
        lines.append("  No pending changes.")
    return "\n".join(lines)


@confirm_required
async def send_vm_key(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    key: str = "",
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    if not key:
        raise ValueError("key is required")
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(elevated.nodes(resolved_node).qemu(vmid).sendkey.put, elevated=True, key=key)
    upid = extract_upid(result)
    return f"Key {key!r} sent to VM {vmid} on {resolved_node}. UPID: {upid}"


@confirm_required
async def vm_monitor_command(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    command: str = "",
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    """WARNING: This sends a raw QEMU monitor command directly to the VM.
    Extremely powerful and dangerous — can crash or corrupt the guest.
    Use with extreme caution.

    SECURITY: If PROXMOX_ALLOWED_MONITOR_COMMANDS is set, only commands
    starting with entries in that allowlist are permitted. If not set,
    all commands are allowed (require elevated token + confirm)."""
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    if not command:
        raise ValueError("command is required")
    if client.config.allowed_monitor_commands is not None:
        allowed = False
        for prefix in client.config.allowed_monitor_commands:
            if command.strip().lower().startswith(prefix.lower()):
                allowed = True
                break
        if not allowed:
            raise ValueError(
                f"Monitor command {command!r} is not in PROXMOX_ALLOWED_MONITOR_COMMANDS allowlist. "
                f"Allowed prefixes: {client.config.allowed_monitor_commands}"
            )
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).qemu(vmid).monitor.post, elevated=True, command=command
    )
    lines = [f"**VM {vmid} monitor command on {resolved_node}**\n"]
    if isinstance(result, dict):
        for key, value in sorted(result.items()):
            lines.append(f"  • {key}: {value}")
    else:
        lines.append(str(result))
    return "\n".join(lines)


@confirm_required
async def unlink_vm_disk(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    idlist: str = "",
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    if not idlist:
        raise ValueError("idlist is required (comma-separated disk IDs)")
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).qemu(vmid).unlink.put, elevated=True, idlist=idlist
    )
    upid = extract_upid(result)
    return f"VM {vmid} disks {idlist!r} unlinked on {resolved_node}. UPID: {upid}"


@confirm_required
async def vm_dbus_vmstate(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.nodes(resolved_node).qemu(vmid).dbus_vmstate.post,
        elevated=True,
    )
    return f"DBus VMstate triggered for VM {vmid} on {resolved_node}"


async def vm_rrd(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    timeframe: str = "hour",
    cf: str = "AVERAGE",
    ds: Optional[str] = None,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    params: dict[str, Any] = {"timeframe": timeframe, "cf": cf}
    if ds is not None:
        params["ds"] = ds
    try:
        result = await client.safe_api_call(
            _api(client, endpoint=ep).nodes(resolved_node).qemu(vmid).rrd.get,
            **params,
        )
    except Exception as exc:
        return f"VM {vmid} RRD unavailable on {resolved_node} (use vm_rrddata for structured data): {exc}"
    if isinstance(result, dict) and "image" in result:
        img_data = result.get("image", "")
        return f"VM {vmid} RRD image returned ({len(img_data)} bytes) on {resolved_node}"
    lines = [f"📈 **VM {vmid} RRD on {resolved_node}**\n"]
    if isinstance(result, dict):
        for key, value in sorted(result.items()):
            lines.append(f"   • {key}: {value}")
    elif isinstance(result, str):
        lines.append(f"   Binary/image data ({len(result)} bytes)")
    else:
        lines.append(str(result))
    return "\n".join(lines)


async def get_lxc_config(
    client: MultiClient, node: Optional[str] = None, vmid: Optional[int] = None, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    try:
        result = await client.safe_api_call(_api(client, endpoint=ep).nodes(resolved_node).lxc(vmid).config.get)
    except ProxmoxNotFoundError:
        return f"LXC {vmid} not found on node {resolved_node}"
    lines = [f"**LXC {vmid} config on {resolved_node}**\n"]
    if isinstance(result, dict):
        for key, val in sorted(result.items()):
            lines.append(f"  • {key}: {val}")
    else:
        lines.append(str(result))
    if not isinstance(result, dict) or not result:
        lines.append("  No config data returned.")
    return "\n".join(lines)


async def get_lxc_status(
    client: MultiClient, node: Optional[str] = None, vmid: Optional[int] = None, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    try:
        result = await client.safe_api_call(_api(client, endpoint=ep).nodes(resolved_node).lxc(vmid).status.current.get)
    except ProxmoxNotFoundError:
        return f"LXC {vmid} not found on node {resolved_node}"
    lines = [f"**LXC {vmid} status on {resolved_node}**\n"]
    if isinstance(result, dict):
        for key, val in sorted(result.items()):
            lines.append(f"  • {key}: {val}")
    else:
        lines.append(str(result))
    return "\n".join(lines)


@confirm_required
async def remote_migrate_lxc(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    target: Optional[str] = None,
    target_endpoint: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    if not target:
        raise ValueError("target is required for remote migration")
    if not target_endpoint:
        raise ValueError("target_endpoint is required for remote migration")
    params: dict[str, Any] = {"target": target, "target-endpoint": target_endpoint}
    params.update(kwargs)
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).lxc(vmid).remote_migrate.post, elevated=True, endpoint=ep, **params
    )
    upid = extract_upid(result)
    return f"LXC {vmid} remote migration to {target} via {target_endpoint} initiated. UPID: {upid}"


@confirm_required
async def move_lxc_volume(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    volume: str = "rootfs",
    storage: Optional[str] = None,
    target_vmid: Optional[int] = None,
    target_volume: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    params: dict[str, Any] = {"volume": volume}
    if storage is not None:
        params["storage"] = storage
    if target_vmid is not None:
        params["target_vmid"] = target_vmid
    if target_volume is not None:
        params["target-volume"] = target_volume
    params.update(kwargs)
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).lxc(vmid).move_volume.post, elevated=True, **params
    )
    upid = extract_upid(result)
    return f"LXC {vmid} volume {volume} move initiated on {resolved_node}. UPID: {upid}"


async def lxc_rrddata(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    timeframe: str = "hour",
    cf: str = "AVERAGE",
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    params: dict[str, Any] = {"timeframe": timeframe, "cf": cf}
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).lxc(vmid).rrddata.get,
        **params,
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = [f"📈 **LXC {vmid} RRDdata on {resolved_node} ({timeframe}/{cf})**\n"]
    for entry in result:
        if isinstance(entry, dict):
            ts = entry.get("time", "?")
            parts = [f"t={ts}"]
            for k, v in sorted(entry.items()):
                if k != "time":
                    parts.append(f"{k}={v}")
            lines.append(f"  • {' | '.join(parts)}")
        else:
            lines.append(f"  • {entry}")
    if not result:
        lines.append("  No data returned.")
    return "\n".join(lines)


async def lxc_rrd(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    timeframe: str = "hour",
    cf: str = "AVERAGE",
    ds: Optional[str] = None,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    params: dict[str, Any] = {"timeframe": timeframe, "cf": cf}
    if ds is not None:
        params["ds"] = ds
    try:
        result = await client.safe_api_call(
            _api(client, endpoint=ep).nodes(resolved_node).lxc(vmid).rrd.get,
            **params,
        )
    except Exception as exc:
        return f"LXC {vmid} RRD unavailable on {resolved_node} (use lxc_rrddata for structured data): {exc}"
    if isinstance(result, dict) and "image" in result:
        img_data = result.get("image", "")
        return f"LXC {vmid} RRD image returned ({len(img_data)} bytes) on {resolved_node}"
    lines = [f"📈 **LXC {vmid} RRD on {resolved_node}**\n"]
    if isinstance(result, dict):
        for key, value in sorted(result.items()):
            lines.append(f"   • {key}: {value}")
    elif isinstance(result, str):
        lines.append(f"   Binary/image data ({len(result)} bytes)")
    else:
        lines.append(str(result))
    return "\n".join(lines)


async def get_vm_config(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    current: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    params: dict[str, Any] = {}
    if current:
        params["current"] = 1
    try:
        result = await client.safe_api_call(
            _api(client, endpoint=ep).nodes(resolved_node).qemu(vmid).config.get, **params
        )
    except ProxmoxNotFoundError:
        return f"VM {vmid} not found on node {resolved_node}"
    lines = [f"**VM {vmid} config on {resolved_node}**\n"]
    if isinstance(result, dict):
        for key, val in sorted(result.items()):
            lines.append(f"  • {key}: {val}")
    else:
        lines.append(str(result))
    return "\n".join(lines)


def _parse_kwargs(kwargs: Any) -> dict[str, Any]:
    import json

    if isinstance(kwargs, dict):
        return kwargs
    if isinstance(kwargs, str):
        try:
            parsed = json.loads(kwargs)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
        try:
            return {k: v for k, v in (pair.split("=", 1) for pair in kwargs.split() if "=" in pair)}
        except ValueError:
            return {}
    return {}


@confirm_required
async def update_vm_config(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    parsed = _parse_kwargs(kwargs)
    if not parsed:
        raise ValueError("At least one parameter must be provided to update")
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(elevated.nodes(resolved_node).qemu(vmid).config.put, elevated=True, **parsed)
    if result is None:
        return f"VM {vmid} config updated on {resolved_node} (no pending changes)"
    upid = extract_upid(result)
    return f"VM {vmid} config updated on {resolved_node}. UPID: {upid}"


async def vm_rrddata(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    timeframe: str = "hour",
    cf: str = "AVERAGE",
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    params: dict[str, Any] = {"timeframe": timeframe, "cf": cf}
    result = await client.safe_api_call(_api(client, endpoint=ep).nodes(resolved_node).qemu(vmid).rrddata.get, **params)
    if not isinstance(result, list):
        result = [result] if result else []
    lines = [f"📈 **VM {vmid} RRD data on {resolved_node} (timeframe={timeframe}, cf={cf})**\n"]
    for entry in result:
        if isinstance(entry, dict):
            parts = [f"{k}={v}" for k, v in sorted(entry.items())]
            lines.append(f"   • {' | '.join(parts)}")
        else:
            lines.append(f"   • {entry}")
    if not result:
        lines.append("   No data found.")
    return "\n".join(lines)


@confirm_required
async def remote_migrate_vm(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    target_address: Optional[str] = None,
    target_node: Optional[str] = None,
    target_storage: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    if not target_address:
        raise ValueError("target_address is required for remote migration")
    params: dict[str, Any] = {"target-address": target_address}
    if target_node:
        params["target-node"] = target_node
    if target_storage:
        params["target-storage"] = target_storage
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).qemu(vmid).remote_migrate.post, elevated=True, endpoint=ep, **params
    )
    upid = extract_upid(result)
    return f"VM {vmid} remote migration to {target_address} initiated. UPID: {upid}"


@confirm_required
async def lxc_sendkey(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    key: str = "",
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    if not key:
        raise ValueError("key is required")
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(elevated.nodes(resolved_node).lxc(vmid).sendkey.put, elevated=True, key=key)
    upid = extract_upid(result)
    return f"Key {key!r} sent to LXC {vmid} on {resolved_node}. UPID: {upid}"
