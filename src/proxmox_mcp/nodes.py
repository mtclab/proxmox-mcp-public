from __future__ import annotations

from typing import Any, Optional

from proxmox_mcp.utils import confirm_required, extract_data, extract_upid, validate_iface_name, validate_node_name


def _api(client: Any, endpoint: str | None = None) -> Any:
    return client.get_client(elevated=False, endpoint=endpoint)


async def node_config(client: Any, node: Optional[str] = None, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    result = await client.safe_api_call(_api(client, endpoint=ep).nodes(resolved_node).config.get)
    lines = [f"⚙️ **Node Config: {resolved_node}**\n"]
    if isinstance(result, dict):
        for key, value in sorted(result.items()):
            lines.append(f"   • {key}: {value}")
    return "\n".join(lines)


@confirm_required
async def update_node_config(
    client: Any,
    node: Optional[str] = None,
    description: Optional[str] = None,
    keyboard: Optional[str] = None,
    time_zone: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    params: dict[str, Any] = {}
    if description is not None:
        params["description"] = description
    if keyboard is not None:
        params["keyboard"] = keyboard
    if time_zone is not None:
        params["timezone"] = time_zone
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(elevated.nodes(resolved_node).config.put, elevated=True, **params)
    upid = extract_upid(result)
    return f"Node {resolved_node} config updated. UPID: {upid}"


@confirm_required
async def reboot_node(
    client: Any, node: Optional[str] = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(elevated.nodes(resolved_node).status.post, elevated=True, command="reboot")
    upid = extract_upid(result)
    return f"Node {resolved_node} reboot initiated. UPID: {upid}"


@confirm_required
async def shutdown_node(
    client: Any, node: Optional[str] = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(elevated.nodes(resolved_node).status.post, elevated=True, command="shutdown")
    upid = extract_upid(result)
    return f"Node {resolved_node} shutdown initiated. UPID: {upid}"


@confirm_required
async def start_all(client: Any, node: Optional[str] = None, confirm: bool = False, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(elevated.nodes(resolved_node).startall.post, elevated=True, endpoint=ep)
    upid = extract_upid(result)
    return f"Start all on node {resolved_node} initiated. UPID: {upid}"


@confirm_required
async def stop_all(client: Any, node: Optional[str] = None, confirm: bool = False, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(elevated.nodes(resolved_node).stopall.post, elevated=True, endpoint=ep)
    upid = extract_upid(result)
    return f"Stop all on node {resolved_node} initiated. UPID: {upid}"


@confirm_required
async def suspend_all(
    client: Any, node: Optional[str] = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(elevated.nodes(resolved_node).suspendall.post, elevated=True, endpoint=ep)
    upid = extract_upid(result)
    return f"Suspend all on node {resolved_node} initiated. UPID: {upid}"


@confirm_required
async def migrate_all(
    client: Any,
    node: Optional[str] = None,
    target: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    params: dict[str, Any] = {}
    if target is not None:
        params["target"] = target
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(elevated.nodes(resolved_node).migrateall.post, elevated=True, **params)
    upid = extract_upid(result)
    return f"Migrate all on node {resolved_node} initiated. UPID: {upid}"


async def get_node_detailed_status(client: Any, node: Optional[str] = None, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    result = await client.safe_api_call(_api(client, endpoint=ep).nodes(resolved_node).status.get)
    lines = [f"📊 **Node Status: {resolved_node}**\n"]
    if isinstance(result, dict):
        for key, val in sorted(result.items()):
            lines.append(f"   • {key}: {val}")
    return "\n".join(lines)


async def list_services(client: Any, node: Optional[str] = None, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    result = await client.safe_api_call(_api(client, endpoint=ep).nodes(resolved_node).services.get)
    if not isinstance(result, list):
        result = [result] if result else []
    lines = [f"🔧 **Services on {resolved_node}**\n"]
    for svc in result:
        name = svc.get("service", svc.get("name", "unknown"))
        desc = svc.get("description", "")
        state = svc.get("state", "unknown")
        lines.append(f"   • {name} — {state}")
        if desc:
            lines.append(f"     {desc}")
    if not result:
        lines.append("   No services found.")
    return "\n".join(lines)


async def service_state(client: Any, node: Optional[str] = None, service: str = "", endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    if not service:
        raise ValueError("service is required")
    result = await client.safe_api_call(_api(client, endpoint=ep).nodes(resolved_node).services(service).state.get)
    lines = [f"🔧 **Service: {service} on {resolved_node}**\n"]
    if isinstance(result, dict):
        for key, value in sorted(result.items()):
            lines.append(f"   • {key}: {value}")
    return "\n".join(lines)


@confirm_required
async def start_service(
    client: Any, node: Optional[str] = None, service: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    if not service:
        raise ValueError("service is required")
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).services(service).start.post, elevated=True, endpoint=ep
    )
    upid = extract_upid(result)
    return f"Service {service!r} start initiated on {resolved_node}. UPID: {upid}"


@confirm_required
async def stop_service(
    client: Any, node: Optional[str] = None, service: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    if not service:
        raise ValueError("service is required")
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).services(service).stop.post, elevated=True, endpoint=ep
    )
    upid = extract_upid(result)
    return f"Service {service!r} stop initiated on {resolved_node}. UPID: {upid}"


@confirm_required
async def restart_service(
    client: Any, node: Optional[str] = None, service: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    if not service:
        raise ValueError("service is required")
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).services(service).restart.post, elevated=True, endpoint=ep
    )
    upid = extract_upid(result)
    return f"Service {service!r} restart initiated on {resolved_node}. UPID: {upid}"


async def node_dns(client: Any, node: Optional[str] = None, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    result = await client.safe_api_call(_api(client, endpoint=ep).nodes(resolved_node).dns.get)
    lines = [f"🌐 **DNS Settings: {resolved_node}**\n"]
    if isinstance(result, dict):
        for key, value in sorted(result.items()):
            lines.append(f"   • {key}: {value}")
    return "\n".join(lines)


async def node_hosts(client: Any, node: Optional[str] = None, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    result = await client.safe_api_call(_api(client, endpoint=ep).nodes(resolved_node).hosts.get)
    lines = [f"📋 **Hosts File: {resolved_node}**\n"]
    if isinstance(result, dict):
        data = extract_data(result)
        if isinstance(data, str):
            for line in data.strip().splitlines():
                lines.append(f"   {line}")
        else:
            for key, value in sorted(result.items()):
                lines.append(f"   • {key}: {value}")
    return "\n".join(lines)


async def node_report(client: Any, node: Optional[str] = None, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    result = await client.safe_api_call(_api(client, endpoint=ep).nodes(resolved_node).report.get, timeout=30)
    lines = [f"📋 **Node Report: {resolved_node}**\n"]
    if isinstance(result, dict):
        data = extract_data(result)
        if isinstance(data, str):
            for line in data.strip().splitlines()[:100]:
                lines.append(f"   {line}")
            total = len(data.strip().splitlines())
            if total > 100:
                lines.append(f"   ... {total - 100} more lines")
        else:
            for key, value in sorted(result.items()):
                lines.append(f"   • {key}: {value}")
    elif isinstance(result, str):
        for line in result.strip().splitlines()[:100]:
            lines.append(f"   {line}")
        total = len(result.strip().splitlines())
        if total > 100:
            lines.append(f"   ... {total - 100} more lines")
    return "\n".join(lines)


async def node_netstat(client: Any, node: Optional[str] = None, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    result = await client.safe_api_call(_api(client, endpoint=ep).nodes(resolved_node).netstat.get)
    lines = [f"🌐 **Netstat: {resolved_node}**\n"]
    if isinstance(result, list):
        for entry in result[:50]:
            if isinstance(entry, dict):
                name = entry.get("name", entry.get("iface", "unknown"))
                lines.append(f"   • **{name}**")
                for key, value in sorted(entry.items()):
                    if key not in ("name", "iface"):
                        lines.append(f"     {key}: {value}")
            else:
                lines.append(f"   {entry}")
        if len(result) > 50:
            lines.append(f"   ... {len(result) - 50} more entries")
    elif isinstance(result, dict):
        data = extract_data(result)
        if isinstance(data, list):
            for entry in data[:50]:
                if isinstance(entry, dict):
                    name = entry.get("name", entry.get("iface", "unknown"))
                    lines.append(f"   • **{name}**")
                    for key, value in sorted(entry.items()):
                        if key not in ("name", "iface"):
                            lines.append(f"     {key}: {value}")
                else:
                    lines.append(f"   {entry}")
            if len(data) > 50:
                lines.append(f"   ... {len(data) - 50} more entries")
        else:
            for key, value in sorted(result.items()):
                lines.append(f"   • {key}: {value}")
    if not result:
        lines.append("   No network stats available.")
    return "\n".join(lines)


async def scan_nfs(client: Any, node: Optional[str] = None, server: str = "", endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    if not server:
        raise ValueError("server is required")
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).scan.nfs.get,
        server=server,
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = [f"🔍 **NFS Scan: {server} on {resolved_node}**\n"]
    for entry in result:
        path = entry.get("path", entry.get("export", "unknown"))
        lines.append(f"   • {path}")
    if not result:
        lines.append("   No NFS exports found.")
    return "\n".join(lines)


async def scan_iscsi(client: Any, node: Optional[str] = None, server: str = "", endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    if not server:
        raise ValueError("server is required")
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).scan.iscsi.get,
        server=server,
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = [f"🔍 **iSCSI Scan: {server} on {resolved_node}**\n"]
    for entry in result:
        target = entry.get("target", entry.get("target_iqn", "unknown"))
        lines.append(f"   • {target}")
    if not result:
        lines.append("   No iSCSI targets found.")
    return "\n".join(lines)


async def scan_lvm(client: Any, node: Optional[str] = None, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).scan.lvm.get,
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = [f"🔍 **LVM VGs on {resolved_node}**\n"]
    for entry in result:
        vg = entry.get("vg", entry.get("name", "unknown"))
        lines.append(f"   • {vg}")
    if not result:
        lines.append("   No LVM volume groups found.")
    return "\n".join(lines)


async def scan_lvmthin(client: Any, node: Optional[str] = None, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).scan.lvmthin.get,
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = [f"🔍 **LVM Thin Pools on {resolved_node}**\n"]
    for entry in result:
        vg = entry.get("vg", entry.get("lvmthin", "unknown"))
        lines.append(f"   • {vg}")
    if not result:
        lines.append("   No LVM thin pools found.")
    return "\n".join(lines)


async def scan_cifs(client: Any, node: Optional[str] = None, server: str = "", endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    if not server:
        raise ValueError("server is required")
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).scan.cifs.get,
        server=server,
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = [f"🔍 **CIFS Scan: {server} on {resolved_node}**\n"]
    for entry in result:
        share = entry.get("share", entry.get("name", "unknown"))
        desc = entry.get("description", "")
        line = f"   • {share}"
        if desc:
            line += f" — {desc}"
        lines.append(line)
    if not result:
        lines.append("   No CIFS shares found.")
    return "\n".join(lines)


async def scan_zfs(client: Any, node: Optional[str] = None, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).scan.zfs.get,
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = [f"🔍 **ZFS Pools on {resolved_node}**\n"]
    for entry in result:
        pool = entry.get("pool", entry.get("name", "unknown"))
        lines.append(f"   • {pool}")
    if not result:
        lines.append("   No ZFS pools found.")
    return "\n".join(lines)


async def scan_pbs(
    client: Any,
    node: Optional[str] = None,
    server: str = "",
    username: Optional[str] = None,
    password: Optional[str] = None,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    if not server:
        raise ValueError("server is required")
    params: dict[str, Any] = {"server": server}
    if username is not None:
        params["username"] = username
    if password is not None:
        params["password"] = password
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).scan.pbs.get,
        **params,
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = [f"🔍 **PBS Scan: {server} on {resolved_node}**\n"]
    for entry in result:
        datastore = entry.get("store", entry.get("datastore", "unknown"))
        lines.append(f"   • {datastore}")
    if not result:
        lines.append("   No PBS datastores found.")
    return "\n".join(lines)


async def query_url_metadata(
    client: Any, node: Optional[str] = None, url: str = "", endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    if not url:
        raise ValueError("url is required")
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).query_url_metadata.get,
        url=url,
    )
    lines = [f"🔗 **URL Metadata: {url}**\n"]
    if isinstance(result, dict):
        data = extract_data(result)
        if isinstance(data, dict):
            for key, value in sorted(data.items()):
                lines.append(f"   • {key}: {value}")
        else:
            lines.append(str(data))
    else:
        lines.append(str(result))
    return "\n".join(lines)


@confirm_required
async def wake_on_lan(
    client: Any, node: Optional[str] = None, macaddr: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    if not macaddr:
        raise ValueError("macaddr is required")
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).wakeonlan.post,
        elevated=True,
        macaddr=macaddr,
    )
    upid = extract_upid(result)
    return f"Wake-on-LAN sent to {macaddr} via {resolved_node}. UPID: {upid}"


async def get_subscription(client: Any, node: Optional[str] = None, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).subscription.get,
    )
    lines = [f"📋 **Subscription: {resolved_node}**\n"]
    if isinstance(result, dict):
        data = extract_data(result)
        if isinstance(data, dict):
            for key, value in sorted(data.items()):
                lines.append(f"   • {key}: {value}")
        else:
            for key, value in sorted(result.items()):
                lines.append(f"   • {key}: {value}")
    return "\n".join(lines)


@confirm_required
async def update_subscription(
    client: Any, node: Optional[str] = None, key: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    if not key:
        raise ValueError("key is required")
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).subscription.post,
        elevated=True,
        key=key,
    )
    upid = extract_upid(result)
    return f"Subscription key updated on {resolved_node}. UPID: {upid}"


@confirm_required
async def delete_subscription(
    client: Any, node: Optional[str] = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.nodes(resolved_node).subscription.delete,
        elevated=True,
    )
    return f"Subscription deleted on {resolved_node}"


@confirm_required
async def check_subscription(
    client: Any, node: Optional[str] = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).subscription.post,
        elevated=True,
    )
    upid = extract_upid(result)
    return f"Subscription check initiated on {resolved_node}. UPID: {upid}"


@confirm_required
async def reload_service(
    client: Any, node: Optional[str] = None, service: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    if not service:
        raise ValueError("service is required")
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).services(service).reload.post, elevated=True, endpoint=ep
    )
    upid = extract_upid(result)
    return f"Service {service!r} reload initiated on {resolved_node}. UPID: {upid}"


@confirm_required
async def node_execute(
    client: Any,
    node: Optional[str] = None,
    commands: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    if not commands:
        raise ValueError("commands is required")
    if client.config.allowed_node_commands is not None:
        allowed = False
        for prefix in client.config.allowed_node_commands:
            if commands.strip().lower().startswith(prefix.lower()):
                allowed = True
                break
        if not allowed:
            raise ValueError(
                f"Command {commands!r} is not in PROXMOX_ALLOWED_NODE_COMMANDS allowlist. "
                f"Allowed prefixes: {client.config.allowed_node_commands}"
            )
    elevated = client.get_client(elevated=True, endpoint=ep)
    params: dict[str, Any] = {"command": commands}
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).execute.post,
        elevated=True,
        **params,
    )
    lines = [f"⚡ **Execute on {resolved_node}**\n"]
    if isinstance(result, dict):
        data = extract_data(result)
        if isinstance(data, dict):
            for key, value in sorted(data.items()):
                lines.append(f"   • {key}: {value}")
        else:
            lines.append(str(data))
    else:
        lines.append(str(result))
    return "\n".join(lines)


async def get_network_interface(
    client: Any, node: Optional[str] = None, iface: str = "", endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    if not iface:
        raise ValueError("iface is required")
    validate_iface_name(iface)
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).network(iface).get,
    )
    lines = [f"🌐 **Network Interface: {iface} on {resolved_node}**\n"]
    if isinstance(result, dict):
        for key, value in sorted(result.items()):
            lines.append(f"   • {key}: {value}")
    return "\n".join(lines)


@confirm_required
async def update_dns(
    client: Any,
    node: Optional[str] = None,
    dns1: Optional[str] = None,
    dns2: Optional[str] = None,
    search: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    params: dict[str, Any] = {}
    if dns1 is not None:
        params["dns1"] = dns1
    if dns2 is not None:
        params["dns2"] = dns2
    if search is not None:
        params["search"] = search
    params.update(kwargs)
    if not params:
        raise ValueError("At least one parameter must be provided to update DNS")
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.nodes(resolved_node).dns.put,
        elevated=True,
        **params,
    )
    opts = ", ".join(f"{k}={v!r}" for k, v in params.items())
    return f"DNS settings for {resolved_node} updated: {opts}"


@confirm_required
async def update_hosts(
    client: Any, node: Optional[str] = None, data: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    if not data:
        raise ValueError("data is required for hosts update")
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.nodes(resolved_node).hosts.post,
        elevated=True,
        data=data,
    )
    return f"Hosts file for {resolved_node} updated"


@confirm_required
async def update_time(
    client: Any,
    node: Optional[str] = None,
    timezone: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    if not timezone:
        raise ValueError("timezone is required for time update")
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.nodes(resolved_node).time.put,
        elevated=True,
        timezone=timezone,
    )
    return f"Timezone for {resolved_node} updated to {timezone!r}"


async def vzdump_defaults(
    client: Any, node: Optional[str] = None, storage: Optional[str] = None, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    params: dict[str, Any] = {}
    if storage is not None:
        params["storage"] = storage
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).vzdump.defaults.get,
        **params,
    )
    lines = [f"\U0001f4be **VZDump Defaults: {resolved_node}**\n"]
    if isinstance(result, dict):
        data = extract_data(result)
        if isinstance(data, dict):
            for key, value in sorted(data.items()):
                lines.append(f"   • {key}: {value}")
        else:
            lines.append(str(data))
    else:
        lines.append(str(result))
    return "\n".join(lines)


async def extract_backup_config(
    client: Any, node: Optional[str] = None, archive: str = "", endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    if not archive:
        raise ValueError("archive is required")
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).vzdump.extractconfig.get,
        archive=archive,
    )
    lines = [f"\U0001f4be **Backup Config: {archive} ({resolved_node})**\n"]
    if isinstance(result, dict):
        data = extract_data(result)
        if isinstance(data, dict):
            for key, value in sorted(data.items()):
                lines.append(f"   • {key}: {value}")
        elif isinstance(data, str):
            for line in data.strip().splitlines():
                lines.append(f"   {line}")
        else:
            lines.append(str(data))
    elif isinstance(result, str):
        for line in result.strip().splitlines():
            lines.append(f"   {line}")
    else:
        lines.append(str(result))
    return "\n".join(lines)
