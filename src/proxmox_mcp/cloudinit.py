from __future__ import annotations

import urllib.parse
from typing import Any, Optional

from proxmox_mcp.exceptions import ProxmoxPermissionError
from proxmox_mcp.multi_client import MultiClient
from proxmox_mcp.utils import confirm_required, extract_data, extract_upid, validate_node_name, validate_vmid


def _api(client: MultiClient, endpoint: str | None = None) -> Any:
    return client.get_client(elevated=False, endpoint=endpoint)


async def cloudinit_dump(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    type: Optional[str] = None,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    params: dict[str, Any] = {}
    if type:
        params["type"] = type
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).qemu(vmid).cloudinit.dump.get, **params
    )
    data = extract_data(result)
    return str(data)


@confirm_required
async def set_cloudinit(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    ciuser: Optional[str] = None,
    cipassword: Optional[str] = None,
    ipconfig0: Optional[str] = None,
    sshkeys: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_vmid(vmid)

    params: dict[str, Any] = {}
    if ciuser:
        params["ciuser"] = ciuser
    if cipassword:
        params["cipassword"] = cipassword
    if ipconfig0:
        params["ipconfig0"] = ipconfig0
    if sshkeys:
        formatted_keys = "\n".join(k.strip() for k in sshkeys.strip().splitlines() if k.strip())
        params["sshkeys"] = urllib.parse.quote(formatted_keys, safe="")

    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(elevated.nodes(resolved_node).qemu(vmid).config.put, elevated=True, **params)
    upid = extract_upid(result)
    return f"Cloud-init configured for VM {vmid} on {resolved_node}. UPID: {upid}"


@confirm_required
async def regenerate_cloudinit(
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
        elevated.nodes(resolved_node).qemu(vmid).cloudinit.put, elevated=True, endpoint=ep
    )
    upid = extract_upid(result)
    return f"Cloud-init drive regenerated for VM {vmid} on {resolved_node}. UPID: {upid}"


@confirm_required
async def exec_vm(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    command: Optional[str] = None,
    confirm: bool = False,
    allowed_commands: Optional[list[str]] = None,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_vmid(vmid)

    if not command:
        raise ValueError("command is required for guest execution")

    allowed = allowed_commands if allowed_commands is not None else client.config.allowed_commands
    if allowed is not None:
        if not any(command.strip().startswith(prefix) for prefix in allowed):
            raise ProxmoxPermissionError(f"Command {command!r} not in allowed list. Allowed prefixes: {allowed}")

    params: dict[str, Any] = {"command": command}

    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).qemu(vmid).agent("exec").post, elevated=True, **params
    )
    pid = extract_upid(result)
    return f"Command executed in VM {vmid} on {resolved_node}. PID: {pid}"


async def agent_ping(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    confirm: bool = True,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_vmid(vmid)

    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).qemu(vmid).agent("ping").post, elevated=True, endpoint=ep
    )
    data = extract_data(result)
    return f"Agent ping for VM {vmid} on {resolved_node}: {data}"


async def agent_info(
    client: MultiClient, node: Optional[str] = None, vmid: Optional[int] = None, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_vmid(vmid)

    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).qemu(vmid).agent("info").get, elevated=True, endpoint=ep
    )
    data = extract_data(result)
    lines = []
    if isinstance(data, dict):
        for k, v in data.items():
            lines.append(f"  {k}: {v}")
    else:
        lines.append(str(data))
    return f"Agent info for VM {vmid} on {resolved_node}:\n" + "\n".join(lines)


async def agent_network_interfaces(
    client: MultiClient, node: Optional[str] = None, vmid: Optional[int] = None, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_vmid(vmid)

    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).qemu(vmid).agent("network-get-interfaces").get, elevated=True
    )
    data = extract_data(result)
    if not isinstance(data, list):
        return f"Network interfaces for VM {vmid} on {resolved_node}: {data}"

    lines = [f"Network interfaces for VM {vmid} on {resolved_node}:"]
    for iface in data:
        name = iface.get("name", "unknown")
        hwaddr = iface.get("hardware-address", "N/A")
        lines.append(f"  {name} (MAC: {hwaddr})")
        for addr in iface.get("ip-addresses", []):
            ip = addr.get("ip-address", "?")
            prefix = addr.get("prefix", "?")
            iptype = addr.get("ip-address-type", "?")
            lines.append(f"    {ip}/{prefix} ({iptype})")
    return "\n".join(lines)


async def agent_osinfo(
    client: MultiClient, node: Optional[str] = None, vmid: Optional[int] = None, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_vmid(vmid)

    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).qemu(vmid).agent("get-osinfo").get, elevated=True, endpoint=ep
    )
    data = extract_data(result)
    lines = [f"OS info for VM {vmid} on {resolved_node}:"]
    if isinstance(data, dict):
        for k, v in data.items():
            lines.append(f"  {k}: {v}")
    else:
        lines.append(str(data))
    return "\n".join(lines)


async def agent_fsinfo(
    client: MultiClient, node: Optional[str] = None, vmid: Optional[int] = None, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_vmid(vmid)

    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).qemu(vmid).agent("get-fsinfo").get, elevated=True, endpoint=ep
    )
    data = extract_data(result)
    if not isinstance(data, list):
        return f"Filesystem info for VM {vmid} on {resolved_node}: {data}"

    lines = [f"Filesystem info for VM {vmid} on {resolved_node}:"]
    for fs in data:
        name = fs.get("name", "unknown")
        fstype = fs.get("type", "unknown")
        mount = fs.get("mountpoint", "unknown")
        total = fs.get("total-bytes", 0)
        used = fs.get("used-bytes", 0)
        free = fs.get("free-bytes", 0)
        lines.append(f"  {mount} ({fstype}) on {name}: {used}/{total} used, {free} free")
    return "\n".join(lines)


async def agent_exec_status(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    pid: Optional[int] = None,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_vmid(vmid)

    if pid is None:
        raise ValueError("pid is required for agent exec-status")

    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).qemu(vmid).agent("exec-status").get,
        elevated=True,
        pid=pid,
    )
    data = extract_data(result)
    lines = [f"Exec status for PID {pid} in VM {vmid} on {resolved_node}:"]
    if isinstance(data, dict):
        for k, v in data.items():
            lines.append(f"  {k}: {v}")
    else:
        lines.append(str(data))
    return "\n".join(lines)


@confirm_required
async def agent_fsfreeze(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    confirm: bool = True,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_vmid(vmid)

    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).qemu(vmid).agent("fsfreeze-freeze").post, elevated=True
    )
    data = extract_data(result)
    return f"Filesystem frozen for VM {vmid} on {resolved_node}: {data}"


@confirm_required
async def agent_fsthaw(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    confirm: bool = True,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_vmid(vmid)

    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).qemu(vmid).agent("fsfreeze-thaw").post, elevated=True
    )
    data = extract_data(result)
    return f"Filesystem thawed for VM {vmid} on {resolved_node}: {data}"


@confirm_required
async def agent_fstrim(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    confirm: bool = True,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_vmid(vmid)

    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).qemu(vmid).agent("fstrim").post, elevated=True, endpoint=ep
    )
    data = extract_data(result)
    return f"Fstrim executed for VM {vmid} on {resolved_node}: {data}"


async def agent_fsfreeze_status(
    client: MultiClient, node: Optional[str] = None, vmid: Optional[int] = None, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_vmid(vmid)

    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).qemu(vmid).agent("fsfreeze-status").post, elevated=True
    )
    data = extract_data(result)
    lines = [f"**Fsfreeze status for VM {vmid} on {resolved_node}:**"]
    if isinstance(data, dict):
        for k, v in data.items():
            lines.append(f"  {k}: {v}")
    else:
        lines.append(str(data))
    return "\n".join(lines)


async def agent_get_host_name(
    client: MultiClient, node: Optional[str] = None, vmid: Optional[int] = None, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_vmid(vmid)

    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).qemu(vmid).agent("get-host-name").get, elevated=True
    )
    data = extract_data(result)
    lines = [f"**Host name for VM {vmid} on {resolved_node}:**"]
    if isinstance(data, dict):
        for k, v in data.items():
            lines.append(f"  {k}: {v}")
    else:
        lines.append(str(data))
    return "\n".join(lines)


async def agent_get_memory_block_info(
    client: MultiClient, node: Optional[str] = None, vmid: Optional[int] = None, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_vmid(vmid)

    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).qemu(vmid).agent("get-memory-block-info").get, elevated=True
    )
    data = extract_data(result)
    lines = [f"**Memory block info for VM {vmid} on {resolved_node}:**"]
    if isinstance(data, dict):
        for k, v in data.items():
            lines.append(f"  {k}: {v}")
    else:
        lines.append(str(data))
    return "\n".join(lines)


async def agent_get_memory_blocks(
    client: MultiClient, node: Optional[str] = None, vmid: Optional[int] = None, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_vmid(vmid)

    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).qemu(vmid).agent("get-memory-blocks").get, elevated=True
    )
    data = extract_data(result)
    lines = [f"**Memory blocks for VM {vmid} on {resolved_node}:**"]
    if isinstance(data, dict):
        for k, v in data.items():
            lines.append(f"  {k}: {v}")
    else:
        lines.append(str(data))
    return "\n".join(lines)


async def agent_get_time(
    client: MultiClient, node: Optional[str] = None, vmid: Optional[int] = None, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_vmid(vmid)

    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).qemu(vmid).agent("get-time").get, elevated=True, endpoint=ep
    )
    data = extract_data(result)
    lines = [f"**Time for VM {vmid} on {resolved_node}:**"]
    if isinstance(data, dict):
        for k, v in data.items():
            lines.append(f"  {k}: {v}")
    else:
        lines.append(str(data))
    return "\n".join(lines)


async def agent_get_timezone(
    client: MultiClient, node: Optional[str] = None, vmid: Optional[int] = None, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_vmid(vmid)

    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).qemu(vmid).agent("get-timezone").get, elevated=True
    )
    data = extract_data(result)
    lines = [f"**Timezone for VM {vmid} on {resolved_node}:**"]
    if isinstance(data, dict):
        for k, v in data.items():
            lines.append(f"  {k}: {v}")
    else:
        lines.append(str(data))
    return "\n".join(lines)


async def agent_get_users(
    client: MultiClient, node: Optional[str] = None, vmid: Optional[int] = None, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_vmid(vmid)

    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).qemu(vmid).agent("get-users").get, elevated=True, endpoint=ep
    )
    data = extract_data(result)
    if not isinstance(data, list):
        data = [data] if data else []
    lines = [f"**Users for VM {vmid} on {resolved_node}:**"]
    for user in data:
        if isinstance(user, dict):
            name = user.get("name", user.get("username", "unknown"))
            lines.append(f"  • {name}")
        else:
            lines.append(f"  • {user}")
    if not data:
        lines.append("  No users found.")
    return "\n".join(lines)


async def agent_get_vcpus(
    client: MultiClient, node: Optional[str] = None, vmid: Optional[int] = None, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_vmid(vmid)

    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).qemu(vmid).agent("get-vcpus").get, elevated=True, endpoint=ep
    )
    data = extract_data(result)
    lines = [f"**VCPUs for VM {vmid} on {resolved_node}:**"]
    if isinstance(data, list):
        for vcpu in data:
            if isinstance(vcpu, dict):
                cpu_id = vcpu.get("id", vcpu.get("cpu-id", "?"))
                online = vcpu.get("online", "?")
                lines.append(f"  • CPU {cpu_id}: online={online}")
            else:
                lines.append(f"  • {vcpu}")
    elif isinstance(data, dict):
        for k, v in data.items():
            lines.append(f"  {k}: {v}")
    else:
        lines.append(str(data))
    return "\n".join(lines)


@confirm_required
async def agent_set_user_password(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    username: str = "",
    password: str = "",
    confirm: bool = True,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_vmid(vmid)
    if not username:
        raise ValueError("username is required")
    if not password:
        raise ValueError("password is required")

    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).qemu(vmid).agent("set-user-password").post,
        elevated=True,
        username=username,
        password=password,
    )
    data = extract_data(result)
    return f"Password set for user {username!r} on VM {vmid} on {resolved_node}: {data}"


async def agent_file_read(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    filepath: str = "",
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_vmid(vmid)
    if not filepath:
        raise ValueError("filepath is required")

    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).qemu(vmid).agent("file-read").get,
        elevated=True,
        file=filepath,
    )
    data = extract_data(result)
    lines = [f"**File read from VM {vmid} on {resolved_node}:**"]
    if isinstance(data, dict):
        lines.append(f"  Path: {filepath}")
        content = data.get("content", data.get("data", ""))
        if content:
            lines.append(f"  Content: {content[:2000]}")
    else:
        lines.append(str(data))
    return "\n".join(lines)


@confirm_required
async def agent_file_write(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    filepath: str = "",
    content: str = "",
    confirm: bool = True,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_vmid(vmid)
    if not filepath:
        raise ValueError("filepath is required")

    elevated = client.get_client(elevated=True, endpoint=ep)
    params: dict[str, Any] = {"path": filepath}
    if content:
        params["content"] = content
    await client.safe_api_call(
        elevated.nodes(resolved_node).qemu(vmid).agent("file-write").post,
        elevated=True,
        **params,
    )
    return f"File written to {filepath!r} on VM {vmid} on {resolved_node}"


@confirm_required
async def agent_shutdown(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    confirm: bool = True,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_vmid(vmid)

    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).qemu(vmid).agent("shutdown").post, elevated=True, endpoint=ep
    )
    data = extract_data(result)
    return f"Agent shutdown initiated for VM {vmid} on {resolved_node}: {data}"


@confirm_required
async def agent_suspend_disk(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    confirm: bool = True,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_vmid(vmid)

    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).qemu(vmid).agent("suspend-disk").post, elevated=True
    )
    data = extract_data(result)
    return f"Agent suspend-to-disk initiated for VM {vmid} on {resolved_node}: {data}"


@confirm_required
async def agent_suspend_ram(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    confirm: bool = True,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_vmid(vmid)

    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).qemu(vmid).agent("suspend-ram").post, elevated=True
    )
    data = extract_data(result)
    return f"Agent suspend-to-RAM initiated for VM {vmid} on {resolved_node}: {data}"


@confirm_required
async def agent_suspend_hybrid(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    confirm: bool = True,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_vmid(vmid)

    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).qemu(vmid).agent("suspend-hybrid").post, elevated=True
    )
    data = extract_data(result)
    return f"Agent hybrid suspend initiated for VM {vmid} on {resolved_node}: {data}"
