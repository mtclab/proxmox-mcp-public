from __future__ import annotations

from typing import Any, Optional

from proxmox_mcp.exceptions import ProxmoxNotFoundError, ProxmoxPermissionError
from proxmox_mcp.multi_client import MultiClient
from proxmox_mcp.utils import extract_data, format_bytes, format_uptime, validate_node_name


def _api(client: MultiClient, endpoint: str | None = None) -> Any:
    return client.get_client(elevated=False, endpoint=endpoint)


async def list_node_lxc(client: MultiClient, node: Optional[str] = None, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    result = await client.safe_api_call(_api(client, endpoint=ep).nodes(resolved_node).lxc.get)
    if not isinstance(result, list):
        result = [result] if result else []
    lines = [f"📦 **LXC Containers on {resolved_node}**\n"]
    for ct in result:
        vmid = ct.get("vmid", "?")
        name = ct.get("name", "?")
        status = ct.get("status", "unknown")
        status_icon = "🟢" if status == "running" else "🔴"
        lines.append(f"{status_icon} **{name}** (ID: {vmid}) — {status}")
        if ct.get("cpu"):
            lines.append(f"   • CPU: {ct['cpu'] * 100:.1f}%")
        if ct.get("mem"):
            lines.append(f"   • Memory: {format_bytes(ct['mem'])}")
    if not result:
        lines.append("   No LXC containers found.")
    return "\n".join(lines)


async def list_node_vms(client: MultiClient, node: Optional[str] = None, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    result = await client.safe_api_call(_api(client, endpoint=ep).nodes(resolved_node).qemu.get)
    if not isinstance(result, list):
        result = [result] if result else []
    lines = [f"💻 **VMs on {resolved_node}**\n"]
    for vm in result:
        vmid = vm.get("vmid", "?")
        name = vm.get("name", "?")
        status = vm.get("status", "unknown")
        status_icon = "🟢" if status == "running" else "🔴"
        lines.append(f"{status_icon} **{name}** (ID: {vmid}) — {status}")
        if vm.get("cpu"):
            lines.append(f"   • CPU: {vm['cpu'] * 100:.1f}%")
        if vm.get("mem"):
            lines.append(f"   • Memory: {format_bytes(vm['mem'])}")
    if not result:
        lines.append("   No VMs found.")
    return "\n".join(lines)


async def list_node_tasks(
    client: MultiClient, node: Optional[str] = None, limit: int = 50, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    params: dict[str, Any] = {"limit": limit}
    result = await client.safe_api_call(_api(client, endpoint=ep).nodes(resolved_node).tasks.get, **params)
    if not isinstance(result, list):
        result = [result] if result else []
    result = result[:limit]
    lines = [f"📋 **Tasks on {resolved_node}** (showing {len(result)})\n"]
    for t in result:
        upid = t.get("upid", "?")
        status = t.get("status", "?")
        status_icon = "✅" if status == "OK" else "❌" if status else "⏳"
        lines.append(f"{status_icon} {upid}")
    return "\n".join(lines)


async def node_index(client: MultiClient, node: Optional[str] = None, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    result = await client.safe_api_call(_api(client, endpoint=ep).nodes(resolved_node).get)
    lines = [f"📊 **Node: {resolved_node}**\n"]
    if isinstance(result, dict):
        for key, value in sorted(result.items()):
            lines.append(f"   • {key}: {value}")
    else:
        lines.append(str(result))
    return "\n".join(lines)


async def list_nodes(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    nodes = await client.safe_api_call(_api(client, endpoint=ep).nodes.get)
    if not isinstance(nodes, list):
        nodes = [nodes]
    lines = ["🖥️  **Proxmox Cluster Nodes**\n"]
    for n in nodes:
        status = "🟢" if n.get("status") in ("online",) or n.get("state") == "online" else "🔴"
        name = n.get("node", "unknown")
        lines.append(f"{status} **{name}**")
        if "cpu" in n:
            lines.append(f"   • CPU: {n['cpu'] * 100:.1f}%")
        if "mem" in n:
            lines.append(f"   • Memory: {format_bytes(n['mem'])} / {format_bytes(n.get('maxmem', 0))}")
        if "uptime" in n:
            lines.append(f"   • Uptime: {format_uptime(n['uptime'])}")
        lines.append("")
    return "\n".join(lines)


async def node_status(client: MultiClient, node: Optional[str] = None, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, node = resolved.endpoint, resolved.node
    pve = _api(client, endpoint=ep)
    result = await client.safe_api_call(pve.nodes(node).status.get)
    lines = [f"📊 **Node Status: {node}**\n"]
    if isinstance(result, dict):
        lines.append(f"   • Kernel: {result.get('kversion', 'N/A')}")
        lines.append(f"   • Uptime: {format_uptime(result.get('uptime', 0))}")
        lines.append(f"   • CPU: {result.get('cpu', 0) * 100:.1f}%")
        mem = result.get("memory", {})
        if isinstance(mem, dict):
            lines.append(f"   • Memory: {format_bytes(mem.get('used', 0))} / {format_bytes(mem.get('total', 0))}")
        lines.append(f"   • PVE Version: {result.get('version', 'N/A')}")
    return "\n".join(lines)


async def list_vms(client: MultiClient, node: Optional[str] = None, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(_api(client, endpoint=ep).cluster.resources.get)
    if not isinstance(result, list):
        result = [result] if result else []
    vms = [r for r in result if r.get("type") == "qemu"]
    if node:
        vms = [r for r in vms if r.get("node") == node]
    lines = ["💻 **Virtual Machines**\n"]
    for vm in vms:
        status_icon = "🟢" if vm.get("status") == "running" else "🔴"
        vmtype = "📦" if vm.get("type") == "lxc" else "🖥️"
        name = vm.get("name", vm.get("vmid", "unknown"))
        vmid = vm.get("vmid", "?")
        n = vm.get("node", "?")
        lines.append(f"{status_icon} {vmtype} **{name}** (ID: {vmid})")
        lines.append(f"   • Node: {n}")
        lines.append(f"   • Status: {vm.get('status', 'unknown')}")
        if vm.get("cpu"):
            lines.append(f"   • CPU: {vm['cpu'] * 100:.1f}%")
        if vm.get("mem"):
            lines.append(f"   • Memory: {format_bytes(vm['mem'])}")
        lines.append("")
    return "\n".join(lines)


async def vm_info(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    name: Optional[str] = None,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_guest(name or str(vmid), node)
    resolved_node = resolved.node
    resolved_vmid = resolved.vmid
    ep = resolved.endpoint or ep
    try:
        status_data = await client.safe_api_call(
            _api(client, endpoint=ep).nodes(resolved_node).qemu(resolved_vmid).status.current.get
        )
        config_data = await client.safe_api_call(
            _api(client, endpoint=ep).nodes(resolved_node).qemu(resolved_vmid).config.get
        )
    except ProxmoxNotFoundError:
        return f"VM {resolved_vmid} not found on node {resolved_node}"
    lines = [f"🖥️ **VM {resolved_vmid} on {resolved_node}**\n"]
    if isinstance(status_data, dict):
        lines.append(f"   • Status: {status_data.get('status', 'unknown')}")
        lines.append(f"   • Uptime: {format_uptime(status_data.get('uptime', 0))}")
        lines.append(f"   • CPU: {status_data.get('cpu', 0) * 100:.1f}%")
        mem = status_data.get("mem", 0)
        maxmem = status_data.get("maxmem", 0)
        lines.append(f"   • Memory: {format_bytes(mem)} / {format_bytes(maxmem)}")
    if isinstance(config_data, dict):
        lines.append(f"   • Cores: {config_data.get('cores', 'N/A')}")
        lines.append(f"   • Name: {config_data.get('name', 'N/A')}")
        lines.append(f"   • OS: {config_data.get('ostype', 'N/A')}")
    return "\n".join(lines)


async def list_lxc(client: MultiClient, node: Optional[str] = None, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    all_resources = await client.safe_api_call(_api(client, endpoint=ep).cluster.resources.get)
    if not isinstance(all_resources, list):
        all_resources = [all_resources] if all_resources else []
    result = [r for r in all_resources if r.get("type") == "lxc"]
    if node:
        result = [r for r in result if r.get("node") == node]
    lines = ["📦 **LXC Containers**\n"]
    for ct in result:
        status_icon = "🟢" if ct.get("status") == "running" else "🔴"
        name = ct.get("name", ct.get("vmid", "unknown"))
        vmid = ct.get("vmid", "?")
        n = ct.get("node", "?")
        lines.append(f"{status_icon} 📦 **{name}** (ID: {vmid})")
        lines.append(f"   • Node: {n}")
        lines.append(f"   • Status: {ct.get('status', 'unknown')}")
        if ct.get("cpu"):
            lines.append(f"   • CPU: {ct['cpu'] * 100:.1f}%")
        if ct.get("mem"):
            lines.append(f"   • Memory: {format_bytes(ct['mem'])}")
        lines.append("")
    return "\n".join(lines)


async def lxc_info(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    name: Optional[str] = None,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_guest(name or str(vmid), node)
    resolved_node = resolved.node
    resolved_vmid = resolved.vmid
    ep = resolved.endpoint or ep
    try:
        status_data = await client.safe_api_call(
            _api(client, endpoint=ep).nodes(resolved_node).lxc(resolved_vmid).status.current.get
        )
        config_data = await client.safe_api_call(
            _api(client, endpoint=ep).nodes(resolved_node).lxc(resolved_vmid).config.get
        )
    except ProxmoxNotFoundError:
        return f"LXC {resolved_vmid} not found on node {resolved_node}"
    lines = [f"📦 **LXC {resolved_vmid} on {resolved_node}**\n"]
    if isinstance(status_data, dict):
        lines.append(f"   • Status: {status_data.get('status', 'unknown')}")
        lines.append(f"   • Uptime: {format_uptime(status_data.get('uptime', 0))}")
        lines.append(f"   • CPU: {status_data.get('cpu', 0) * 100:.1f}%")
        mem = status_data.get("mem", 0)
        maxmem = status_data.get("maxmem", 0)
        lines.append(f"   • Memory: {format_bytes(mem)} / {format_bytes(maxmem)}")
    if isinstance(config_data, dict):
        lines.append(f"   • Hostname: {config_data.get('hostname', 'N/A')}")
        lines.append(f"   • Cores: {config_data.get('cores', 'N/A')}")
    return "\n".join(lines)


async def list_storage(client: MultiClient, node: Optional[str] = None, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(_api(client, endpoint=ep).storage.get)
    if not isinstance(result, list):
        result = [result] if result else []
    lines = ["💾 **Storage Pools**\n"]
    for s in result:
        status_icon = "🟢" if s.get("active", 0) else "🔴"
        name = s.get("storage", "unknown")
        stype = s.get("type", "?")
        used = s.get("used", 0)
        total = s.get("total", 0) or 1
        content = s.get("content", "")
        lines.append(f"{status_icon} **{name}** ({stype})")
        lines.append(f"   • Content: {content}")
        if total > 1:
            lines.append(f"   • Usage: {format_bytes(used)} / {format_bytes(total)}")
        lines.append("")
    return "\n".join(lines)


async def storage_content(
    client: MultiClient, node: Optional[str] = None, storage: str = "local", endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, node = resolved.endpoint, resolved.node
    result = await client.safe_api_call(_api(client, endpoint=ep).nodes(node).storage(storage).content.get)
    if not isinstance(result, list):
        result = [result] if result else []
    lines = [f"📁 **Storage: {storage} on {node}**\n"]
    for item in result:
        volid = item.get("volid", "unknown")
        ctype = item.get("content", "?")
        size = item.get("size", 0)
        lines.append(f"   • {volid} ({ctype}) — {format_bytes(size) if size else 'N/A'}")
    return "\n".join(lines)


async def list_tasks(
    client: MultiClient, node: Optional[str] = None, limit: int = 50, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(_api(client, endpoint=ep).cluster.tasks.get)
    if not isinstance(result, list):
        result = [result] if result else []
    result = result[:limit]
    lines = [f"📋 **Recent Tasks** (showing {len(result)})\n"]
    for t in result:
        upid = t.get("upid", "?")
        status = t.get("status", "?")
        status_icon = "✅" if status == "OK" else "❌" if status else "⏳"
        lines.append(f"{status_icon} {upid}")
    return "\n".join(lines)


async def task_status(client: MultiClient, upid: str, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    parts = upid.split(":")
    node = parts[1] if len(parts) > 1 else await client.resolve_node()
    result = await client.safe_api_call(_api(client, endpoint=ep).nodes(node).tasks(upid).status.get)
    lines = [f"📋 **Task: {upid}**\n"]
    if isinstance(result, dict):
        lines.append(f"   • Status: {result.get('status', 'unknown')}")
        exitstatus = result.get("exitstatus", "")
        if exitstatus:
            lines.append(f"   • Exit Status: {exitstatus}")
        lines.append(f"   • User: {result.get('user', 'N/A')}")
        lines.append(f"   • Node: {result.get('node', 'N/A')}")
    return "\n".join(lines)


async def node_metrics(
    client: MultiClient,
    node: Optional[str] = None,
    timeframe: str = "hour",
    cf: str = "AVERAGE",
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, node = resolved.endpoint, resolved.node
    result = await client.safe_api_call(_api(client, endpoint=ep).nodes(node).rrddata.get, timeframe=timeframe, cf=cf)
    if not isinstance(result, list):
        return f"No metrics data available for node {node}"
    lines = [f"📈 **Node Metrics: {node}** ({timeframe})\n"]
    for entry in result[:5]:
        lines.append(f"   • {entry.get('time', '?')}")
    lines.append(f"   ... {len(result)} data points total")
    return "\n".join(lines)


async def vm_metrics(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    name: Optional[str] = None,
    timeframe: str = "hour",
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_guest(name or str(vmid), node)
    resolved_node = resolved.node
    resolved_vmid = resolved.vmid
    ep = resolved.endpoint or ep
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).qemu(resolved_vmid).rrddata.get, timeframe=timeframe
    )
    if not isinstance(result, list):
        return f"No metrics data available for VM {resolved_vmid}"
    lines = [f"📈 **VM {resolved_vmid} Metrics** ({timeframe})\n"]
    lines.append(f"   {len(result)} data points available")
    return "\n".join(lines)


async def lxc_metrics(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    name: Optional[str] = None,
    timeframe: str = "hour",
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_guest(name or str(vmid), node)
    resolved_node = resolved.node
    resolved_vmid = resolved.vmid
    ep = resolved.endpoint or ep
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).lxc(resolved_vmid).rrddata.get, timeframe=timeframe
    )
    if not isinstance(result, list):
        return f"No metrics data available for LXC {resolved_vmid}"
    lines = [f"📈 **LXC {resolved_vmid} Metrics** ({timeframe})\n"]
    lines.append(f"   {len(result)} data points available")
    return "\n".join(lines)


VALID_RESOURCE_TYPES = ("vm", "storage", "node", "sdn")


async def cluster_resources(client: MultiClient, type: Optional[str] = None, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    if type is not None and type not in VALID_RESOURCE_TYPES:
        raise ValueError(f"Invalid type {type!r} — must be one of: {', '.join(VALID_RESOURCE_TYPES)}")
    params: dict[str, Any] = {}
    if type is not None:
        params["type"] = type
    result = await client.safe_api_call(_api(client, endpoint=ep).cluster.resources.get, **params)
    if not isinstance(result, list):
        result = [result] if result else []
    type_label = type or "all"
    lines = [f"📊 **Cluster Resources ({type_label})**\n"]
    for r in result:
        rtype = r.get("type", "?")
        name = r.get("name", r.get("id", "unknown"))
        vmid = r.get("vmid", "")
        node = r.get("node", "")
        status = r.get("status", "")
        status_icon = "🟢" if status == "running" else "🔴" if status else "⚪"
        label = f"{name}"
        if vmid:
            label += f" (ID: {vmid})"
        if node:
            label += f" @ {node}"
        lines.append(f"{status_icon} [{rtype}] {label}")
    if not result:
        lines.append("   No resources found.")
    return "\n".join(lines)


async def list_bridges(client: MultiClient, node: Optional[str] = None, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, node = resolved.endpoint, resolved.node
    result = await client.safe_api_call(_api(client, endpoint=ep).nodes(node).network.get)
    if not isinstance(result, list):
        result = [result] if result else []
    bridges = [iface for iface in result if iface.get("type") == "bridge" or iface.get("iface", "").startswith("vmbr")]
    lines = [f"🌐 **Network Bridges on {node}**\n"]
    for b in bridges:
        name = b.get("iface", "unknown")
        ports = b.get("bridge_ports", "none")
        lines.append(f"   • {name} — ports: {ports}")
    return "\n".join(lines)


async def list_network(client: MultiClient, node: Optional[str] = None, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, node = resolved.endpoint, resolved.node
    result = await client.safe_api_call(_api(client, endpoint=ep).nodes(node).network.get)
    if not isinstance(result, list):
        result = [result] if result else []
    lines = [f"🌐 **Network Interfaces on {node}**\n"]
    for iface in result:
        name = iface.get("iface", "unknown")
        itype = iface.get("type", "unknown")
        addr = iface.get("address", "")
        lines.append(f"   • {name} ({itype}) — {addr}")
    return "\n".join(lines)


async def node_version(client: MultiClient, node: Optional[str] = None, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    result = await client.safe_api_call(_api(client, endpoint=ep).nodes(resolved_node).version.get)
    lines = [f"📦 **Node Version: {resolved_node}**\n"]
    if isinstance(result, dict):
        data = extract_data(result)
        if isinstance(data, dict):
            for k, v in sorted(data.items()):
                lines.append(f"   • {k}: {v}")
        else:
            lines.append(str(data))
    else:
        lines.append(str(result))
    return "\n".join(lines)


async def node_dns(client: MultiClient, node: Optional[str] = None, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    result = await client.safe_api_call(_api(client, endpoint=ep).nodes(resolved_node).dns.get)
    lines = [f"🌐 **Node DNS: {resolved_node}**\n"]
    if isinstance(result, dict):
        data = extract_data(result)
        if isinstance(data, dict):
            for k, v in sorted(data.items()):
                lines.append(f"   • {k}: {v}")
        else:
            lines.append(str(data))
    else:
        lines.append(str(result))
    return "\n".join(lines)


async def node_hosts(client: MultiClient, node: Optional[str] = None, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    result = await client.safe_api_call(_api(client, endpoint=ep).nodes(resolved_node).hosts.get)
    lines = [f"📋 **Node Hosts: {resolved_node}**\n"]
    if isinstance(result, dict):
        data = extract_data(result)
        if isinstance(data, str):
            for line in data.strip().splitlines():
                lines.append(f"   {line}")
        elif isinstance(data, dict):
            for k, v in sorted(data.items()):
                lines.append(f"   • {k}: {v}")
        else:
            lines.append(str(data))
    else:
        lines.append(str(result))
    return "\n".join(lines)


async def node_time(client: MultiClient, node: Optional[str] = None, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    result = await client.safe_api_call(_api(client, endpoint=ep).nodes(resolved_node).time.get)
    lines = [f"🕐 **Node Time: {resolved_node}**\n"]
    if isinstance(result, dict):
        data = extract_data(result)
        if isinstance(data, dict):
            for k, v in sorted(data.items()):
                lines.append(f"   • {k}: {v}")
        else:
            lines.append(str(data))
    else:
        lines.append(str(result))
    return "\n".join(lines)


async def node_syslog(
    client: MultiClient,
    node: Optional[str] = None,
    limit: Optional[int] = None,
    start: Optional[int] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    params: dict[str, Any] = {}
    if limit is not None:
        params["limit"] = limit
    if start is not None:
        params["start"] = start
    if since is not None:
        params["since"] = since
    if until is not None:
        params["until"] = until
    try:
        result = await client.safe_api_call(_api(client, endpoint=ep).nodes(resolved_node).syslog.get, **params)
    except ProxmoxPermissionError:
        return (
            "⚠️ **Syslog access requires Sys.Syslog permission.**\n"
            "The monitor token (PVEAuditor role) does not have Sys.Syslog, "
            "which is required by PVE's /nodes/{node}/syslog endpoint.\n"
            "Use an elevated session or grant Sys.Syslog to the monitor token's role."
        )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = [f"📋 **Syslog: {resolved_node}** ({len(result)} entries)\n"]
    for entry in result[:50]:
        if isinstance(entry, dict):
            ts = entry.get("timestamp", entry.get("time", "?"))
            msg = entry.get("msg", entry.get("text", str(entry)))
            lines.append(f"   [{ts}] {msg}")
        else:
            lines.append(f"   {entry}")
    if len(result) > 50:
        lines.append(f"   ... {len(result) - 50} more entries")
    return "\n".join(lines)


async def node_journal(
    client: MultiClient,
    node: Optional[str] = None,
    limit: Optional[int] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    service: Optional[str] = None,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    params: dict[str, Any] = {}
    if limit is not None:
        params["lastentries"] = limit
    if since is not None:
        params["since"] = since
    if until is not None:
        params["until"] = until
    if service is not None:
        params["service"] = service
    result = await client.safe_api_call(_api(client, endpoint=ep).nodes(resolved_node).journal.get, **params)
    if not isinstance(result, list):
        result = [result] if result else []
    lines = [f"📋 **Journal: {resolved_node}** ({len(result)} entries)\n"]
    for entry in result[:50]:
        if isinstance(entry, dict):
            ts = entry.get("timestamp", entry.get("time", "?"))
            msg = entry.get("msg", entry.get("text", str(entry)))
            lines.append(f"   [{ts}] {msg}")
        else:
            lines.append(f"   {entry}")
    if len(result) > 50:
        lines.append(f"   ... {len(result) - 50} more entries")
    return "\n".join(lines)


async def cluster_log(client: MultiClient, limit: Optional[int] = None, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    params: dict[str, Any] = {}
    if limit is not None:
        params["max"] = limit
    result = await client.safe_api_call(_api(client, endpoint=ep).cluster.log.get, **params)
    if not isinstance(result, list):
        result = [result] if result else []
    lines = [f"📋 **Cluster Log** ({len(result)} entries)\n"]
    for entry in result[:50]:
        if isinstance(entry, dict):
            ts = entry.get("timestamp", entry.get("time", "?"))
            msg = entry.get("msg", entry.get("text", str(entry)))
            lines.append(f"   [{ts}] {msg}")
        else:
            lines.append(f"   {entry}")
    if len(result) > 50:
        lines.append(f"   ... {len(result) - 50} more entries")
    return "\n".join(lines)


async def task_log(
    client: MultiClient, upid: str, node: Optional[str] = None, limit: int = 50, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    if not node:
        parts = upid.split(":")
        if len(parts) > 1:
            node = parts[1]
    if not node:
        resolved = await client.resolve_node(None, endpoint=endpoint)
        ep, node = resolved.endpoint, resolved.node
    result = await client.safe_api_call(_api(client, endpoint=ep).nodes(node).tasks(upid).log.get, limit=limit)
    if not isinstance(result, list):
        result = [result] if result else []
    lines = [f"**Task Log: {upid}** (last {len(result)} lines)\n"]
    for entry in result:
        if isinstance(entry, dict):
            t = entry.get("t", entry.get("line", str(entry)))
            n = entry.get("n", "")
            lines.append(f"  {n}: {t}" if n else f"  {t}")
        else:
            lines.append(f"  {entry}")
    if not result:
        lines.append("  No log output.")
    return "\n".join(lines)


async def cluster_status(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.status.get,
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = ["**Cluster Status**\n"]
    for entry in result:
        etype = entry.get("type", "unknown")
        name = entry.get("name", entry.get("id", "unknown"))
        if etype == "cluster":
            lines.append(f"  • Cluster: {name}")
            lines.append(f"    Quorum: {'Yes' if entry.get('quorate') else 'No'}")
            lines.append(f"    Nodes: {entry.get('nodes', 'N/A')}")
            lines.append(f"    Version: {entry.get('version', 'N/A')}")
        elif etype == "node":
            online = entry.get("online", 0)
            status = "online" if online else "offline"
            lines.append(f"  • Node: {name} — {status}")
            if entry.get("ip"):
                lines.append(f"    IP: {entry['ip']}")
    if not result:
        lines.append("  No cluster status available.")
    return "\n".join(lines)


async def get_next_vmid(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(_api(client, endpoint=ep).cluster.nextid.get)
    vmid = int(result) if result else 0
    lines = ["**Next VMID**\n"]
    lines.append(f"  • {vmid}")
    return "\n".join(lines)
