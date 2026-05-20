from __future__ import annotations

from typing import Any, Optional

from proxmox_mcp.multi_client import MultiClient
from proxmox_mcp.utils import confirm_required, extract_data, extract_upid, validate_node_name


def _api(client: MultiClient, endpoint: str | None = None) -> Any:
    return client.get_client(elevated=False, endpoint=endpoint)


async def ceph_status(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.ceph.status.get,
    )
    lines = ["🐟 **Ceph Cluster Status**\n"]
    if isinstance(result, dict):
        health = result.get("health", {})
        if isinstance(health, dict):
            status = health.get("status", "N/A")
            lines.append(f"   • Health: {status}")
            summary = health.get("summary", "")
            if summary:
                lines.append(f"   • Summary: {summary}")
        lines.append(f"   • FSID: {result.get('fsid', 'N/A')}")
        quorum = result.get("quorum", [])
        if quorum:
            lines.append(f"   • Quorum Monitors: {len(quorum)}")
        osdmap = result.get("osdmap", {})
        if isinstance(osdmap, dict):
            osdmap_data = osdmap.get("osdmap", osdmap)
            if isinstance(osdmap_data, dict):
                num_osds = osdmap_data.get("num_osds", "N/A")
                num_up = osdmap_data.get("num_up_osds", "N/A")
                lines.append(f"   • OSDs: {num_osds} total, {num_up} up")
        pgmap = result.get("pgmap", {})
        if isinstance(pgmap, dict):
            lines.append(f"   • PGs: {pgmap.get('num_pgs', 'N/A')}")
            bytes_used = pgmap.get("bytes_used", 0)
            bytes_total = pgmap.get("bytes_total", 0)
            if bytes_total:
                pct = (bytes_used / bytes_total) * 100
                lines.append(f"   • Usage: {pct:.1f}%")
    else:
        lines.append("   No Ceph status available (Ceph not configured?).")
    return "\n".join(lines)


async def ceph_metadata(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.ceph.metadata.get,
    )
    lines = ["📋 **Ceph Metadata**\n"]
    if isinstance(result, dict):
        for key, value in sorted(result.items()):
            lines.append(f"   • {key}: {value}")
    elif isinstance(result, list):
        for item in result[:50]:
            if isinstance(item, dict):
                name = item.get("name", item.get("id", "unknown"))
                lines.append(f"   • {name}")
                for k, v in sorted(item.items()):
                    if k not in ("name", "id"):
                        lines.append(f"     {k}: {v}")
            else:
                lines.append(f"   • {item}")
    if not result:
        lines.append("   No Ceph metadata available.")
    return "\n".join(lines)


async def node_ceph_status(client: MultiClient, node: Optional[str] = None, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).ceph.status.get,
    )
    lines = [f"🐟 **Ceph Status on {resolved_node}**\n"]
    if isinstance(result, dict):
        health = result.get("health", {})
        if isinstance(health, dict):
            status = health.get("status", "N/A")
            lines.append(f"   • Health: {status}")
        fsid = result.get("fsid", "")
        if fsid:
            lines.append(f"   • FSID: {fsid}")
        quorum = result.get("quorum", [])
        if quorum:
            lines.append(f"   • Quorum Monitors: {len(quorum)}")
        osdmap = result.get("osdmap", {})
        if isinstance(osdmap, dict):
            osdmap_data = osdmap.get("osdmap", osdmap)
            if isinstance(osdmap_data, dict):
                num_osds = osdmap_data.get("num_osds", "N/A")
                num_up = osdmap_data.get("num_up_osds", "N/A")
                lines.append(f"   • OSDs: {num_osds} total, {num_up} up")
    else:
        lines.append("   No Ceph status available on this node.")
    return "\n".join(lines)


async def node_ceph_fs(client: MultiClient, node: Optional[str] = None, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).ceph.fs.get,
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = [f"🐟 **Ceph Filesystems on {resolved_node}**\n"]
    for fs in result:
        name = fs.get("name", "unknown")
        metadata_pool = fs.get("metadata_pool", "N/A")
        data_pool = fs.get("data_pool", "N/A")
        lines.append(f"   • **{name}**")
        if metadata_pool != "N/A":
            lines.append(f"     Metadata Pool: {metadata_pool}")
        if data_pool != "N/A":
            lines.append(f"     Data Pool: {data_pool}")
    if not result:
        lines.append("   No Ceph filesystems found.")
    return "\n".join(lines)


@confirm_required
async def create_ceph_fs(
    client: MultiClient,
    node: Optional[str] = None,
    name: str = "",
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    if not name:
        raise ValueError("Ceph filesystem name is required")
    elevated = client.get_client(elevated=True, endpoint=ep)
    params = {"name": name}
    for k, v in kwargs.items():
        if v is not None:
            params[k] = v
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).ceph.fs(name).post,
        elevated=True,
        **params,
    )
    upid = extract_upid(result)
    return f"Ceph filesystem {name!r} created on {resolved_node}. UPID: {upid}"


async def list_ceph_osd(client: MultiClient, node: Optional[str] = None, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).ceph.osd.get,
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = [f"🐟 **Ceph OSDs on {resolved_node}**\n"]
    for osd in result:
        osdid = osd.get("id", osd.get("osdid", "unknown"))
        name = osd.get("name", "")
        status = osd.get("status", osd.get("state", "N/A"))
        host = osd.get("host", osd.get("crush_location", ""))
        lines.append(f"   • **OSD {osdid}**")
        if name:
            lines.append(f"     Name: {name}")
        if status:
            lines.append(f"     Status: {status}")
        if host:
            lines.append(f"     Host: {host}")
    if not result:
        lines.append("   No Ceph OSDs found.")
    return "\n".join(lines)


async def list_ceph_mon(client: MultiClient, node: Optional[str] = None, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).ceph.mon.get,
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = [f"🐟 **Ceph Monitors on {resolved_node}**\n"]
    for mon in result:
        name = mon.get("name", "unknown")
        addr = mon.get("addr", mon.get("host", "N/A"))
        rank = mon.get("rank", "")
        lines.append(f"   • **{name}**")
        lines.append(f"     Address: {addr}")
        if rank != "":
            lines.append(f"     Rank: {rank}")
    if not result:
        lines.append("   No Ceph monitors found.")
    return "\n".join(lines)


async def list_ceph_mgr(client: MultiClient, node: Optional[str] = None, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).ceph.mgr.get,
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = [f"🐟 **Ceph Managers on {resolved_node}**\n"]
    for mgr in result:
        name = mgr.get("name", mgr.get("id", "unknown"))
        addr = mgr.get("addr", "N/A")
        state = mgr.get("state", "N/A")
        lines.append(f"   • **{name}**")
        lines.append(f"     Address: {addr}")
        lines.append(f"     State: {state}")
    if not result:
        lines.append("   No Ceph managers found.")
    return "\n".join(lines)


async def ceph_config(client: MultiClient, node: Optional[str] = None, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).ceph.cfg.raw.get,
    )
    lines = [f"🐟 **Ceph Configuration on {resolved_node}**\n"]
    if isinstance(result, dict):
        data = extract_data(result)
        if isinstance(data, str):
            lines.append(data)
        elif isinstance(data, dict):
            for key, value in sorted(data.items()):
                lines.append(f"   • {key}: {value}")
        else:
            lines.append(str(data))
    elif isinstance(result, str):
        lines.append(result)
    else:
        lines.append("   No Ceph configuration available.")
    return "\n".join(lines)


async def ceph_flags(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.ceph.flags.get,
    )
    lines = ["🏴 **Ceph Cluster Flags**\n"]
    if isinstance(result, dict):
        for key, value in sorted(result.items()):
            lines.append(f"   • {key}: {value}")
    elif isinstance(result, list):
        for flag in result:
            if isinstance(flag, dict):
                name = flag.get("name", flag.get("id", "unknown"))
                lines.append(f"   • {name}")
                for k, v in sorted(flag.items()):
                    if k not in ("name", "id"):
                        lines.append(f"     {k}: {v}")
            else:
                lines.append(f"   • {flag}")
    else:
        lines.append("   No Ceph flags available.")
    return "\n".join(lines)


@confirm_required
async def set_ceph_flags(
    client: MultiClient,
    flags: str = "",
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not flags:
        raise ValueError("Flags string is required")
    elevated = client.get_client(elevated=True, endpoint=ep)
    params = {"flags": flags}
    for k, v in kwargs.items():
        if v is not None:
            params[k] = v
    await client.safe_api_call(
        elevated.cluster.ceph.flags.put,
        elevated=True,
        **params,
    )
    return f"Ceph flags set to {flags!r}."


async def get_ceph_flag(client: MultiClient, flag: str, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    if not flag:
        raise ValueError("Flag name is required")
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.ceph.flags(flag).get,
    )
    lines = [f"🏴 **Ceph Flag: {flag}**\n"]
    if isinstance(result, dict):
        data = extract_data(result)
        if isinstance(data, dict):
            for key, value in sorted(data.items()):
                lines.append(f"   • {key}: {value}")
        elif isinstance(data, bool):
            lines.append(f"   Value: {data}")
        else:
            lines.append(f"   Value: {data}")
    elif isinstance(result, bool):
        lines.append(f"   Value: {result}")
    else:
        lines.append(f"   Value: {result}")
    return "\n".join(lines)


@confirm_required
async def set_ceph_flag(
    client: MultiClient, flag: str = "", value: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not flag:
        raise ValueError("Flag name is required")
    elevated = client.get_client(elevated=True, endpoint=ep)
    params: dict[str, Any] = {}
    if value.lower() in ("1", "true", "yes"):
        params["value"] = "1"
    elif value.lower() in ("0", "false", "no"):
        params["value"] = "0"
    else:
        params["value"] = value
    await client.safe_api_call(
        elevated.cluster.ceph.flags(flag).put,
        elevated=True,
        **params,
    )
    return f"Ceph flag {flag!r} set to {value!r}."


async def list_ceph_osd_detail(
    client: MultiClient, node: Optional[str] = None, osdid: int = 0, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).ceph.osd(osdid).get,
    )
    lines = [f"🐟 **Ceph OSD {osdid} on {resolved_node}**\n"]
    if isinstance(result, dict):
        data = extract_data(result)
        if isinstance(data, dict):
            for key, value in sorted(data.items()):
                lines.append(f"   • {key}: {value}")
        elif isinstance(data, list):
            for item in data[:50]:
                if isinstance(item, dict):
                    lines.append(f"   • {item.get('name', item.get('id', 'unknown'))}")
                else:
                    lines.append(f"   • {item}")
        else:
            lines.append(str(data))
    elif isinstance(result, list):
        for item in result[:50]:
            if isinstance(item, dict):
                lines.append(f"   • {item.get('name', item.get('id', 'unknown'))}")
            else:
                lines.append(f"   • {item}")
    else:
        lines.append("   No OSD detail available.")
    return "\n".join(lines)


@confirm_required
async def create_ceph_osd(
    client: MultiClient,
    node: Optional[str] = None,
    dev: str = "",
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    if not dev:
        raise ValueError("Device path is required")
    elevated = client.get_client(elevated=True, endpoint=ep)
    params = {"dev": dev}
    for k, v in kwargs.items():
        if v is not None:
            params[k] = v
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).ceph.osd.post,
        elevated=True,
        **params,
    )
    upid = extract_upid(result)
    return f"Ceph OSD created on {resolved_node} from device {dev!r}. UPID: {upid}"


@confirm_required
async def destroy_ceph_osd(
    client: MultiClient,
    node: Optional[str] = None,
    osdid: int = 0,
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    elevated = client.get_client(elevated=True, endpoint=ep)
    params = {}
    for k, v in kwargs.items():
        if v is not None:
            params[k] = v
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).ceph.osd(osdid).delete,
        elevated=True,
        **params,
    )
    upid = extract_upid(result)
    return f"Ceph OSD {osdid} destroyed on {resolved_node}. UPID: {upid}"


@confirm_required
async def ceph_osd_in(
    client: MultiClient, node: Optional[str] = None, osdid: int = 0, confirm: bool = False, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).ceph.osd(osdid)("in").post,
        elevated=True,
    )
    upid = extract_upid(result)
    return f"Ceph OSD {osdid} marked in on {resolved_node}. UPID: {upid}"


@confirm_required
async def ceph_osd_out(
    client: MultiClient, node: Optional[str] = None, osdid: int = 0, confirm: bool = False, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).ceph.osd(osdid)("out").post,
        elevated=True,
    )
    upid = extract_upid(result)
    return f"Ceph OSD {osdid} marked out on {resolved_node}. UPID: {upid}"


@confirm_required
async def ceph_osd_scrub(
    client: MultiClient, node: Optional[str] = None, osdid: int = 0, confirm: bool = False, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).ceph.osd(osdid).scrub.post,
        elevated=True,
    )
    upid = extract_upid(result)
    return f"Ceph OSD {osdid} scrub started on {resolved_node}. UPID: {upid}"


async def ceph_osd_metadata(
    client: MultiClient, node: Optional[str] = None, osdid: int = 0, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).ceph.osd(osdid).metadata.get,
    )
    lines = [f"🐟 **Ceph OSD {osdid} Metadata on {resolved_node}**\n"]
    if isinstance(result, dict):
        data = extract_data(result)
        if isinstance(data, dict):
            for key, value in sorted(data.items()):
                lines.append(f"   • {key}: {value}")
        elif isinstance(data, list):
            for item in data[:50]:
                if isinstance(item, dict):
                    lines.append(f"   • {item.get('name', item.get('id', 'unknown'))}")
                else:
                    lines.append(f"   • {item}")
        else:
            lines.append(str(data))
    else:
        lines.append("   No OSD metadata available.")
    return "\n".join(lines)


async def list_ceph_pools(client: MultiClient, node: Optional[str] = None, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).ceph.pool.get,
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = [f"🐟 **Ceph Pools on {resolved_node}**\n"]
    for pool in result:
        name = pool.get("pool_name", pool.get("pool", "unknown"))
        lines.append(f"   • **{name}**")
        for k in ("pg_num", "pgp_num", "size", "min_size", "crush_rule", "used", "percent_used"):
            v = pool.get(k)
            if v is not None:
                lines.append(f"     {k}: {v}")
    if not result:
        lines.append("   No Ceph pools found.")
    return "\n".join(lines)


@confirm_required
async def create_ceph_pool(
    client: MultiClient,
    node: Optional[str] = None,
    name: str = "",
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    if not name:
        raise ValueError("Pool name is required")
    elevated = client.get_client(elevated=True, endpoint=ep)
    params = {"name": name}
    for k, v in kwargs.items():
        if v is not None:
            params[k] = v
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).ceph.pool.post,
        elevated=True,
        **params,
    )
    upid = extract_upid(result)
    return f"Ceph pool {name!r} created on {resolved_node}. UPID: {upid}"


async def get_ceph_pool(
    client: MultiClient, node: Optional[str] = None, name: str = "", endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    if not name:
        raise ValueError("Pool name is required")
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).ceph.pool(name).get,
    )
    lines = [f"🐟 **Ceph Pool: {name} on {resolved_node}**\n"]
    if isinstance(result, dict):
        data = extract_data(result)
        if isinstance(data, dict):
            for key, value in sorted(data.items()):
                lines.append(f"   • {key}: {value}")
        else:
            lines.append(str(data))
    else:
        lines.append("   No pool data available.")
    return "\n".join(lines)


@confirm_required
async def update_ceph_pool(
    client: MultiClient,
    node: Optional[str] = None,
    name: str = "",
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    if not name:
        raise ValueError("Pool name is required")
    elevated = client.get_client(elevated=True, endpoint=ep)
    params = {}
    for k, v in kwargs.items():
        if v is not None:
            params[k] = v
    await client.safe_api_call(
        elevated.nodes(resolved_node).ceph.pool(name).put,
        elevated=True,
        **params,
    )
    return f"Ceph pool {name!r} updated on {resolved_node}."


@confirm_required
async def destroy_ceph_pool(
    client: MultiClient,
    node: Optional[str] = None,
    name: str = "",
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    if not name:
        raise ValueError("Pool name is required")
    elevated = client.get_client(elevated=True, endpoint=ep)
    params = {}
    for k, v in kwargs.items():
        if v is not None:
            params[k] = v
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).ceph.pool(name).delete,
        elevated=True,
        **params,
    )
    upid = extract_upid(result)
    return f"Ceph pool {name!r} destroyed on {resolved_node}. UPID: {upid}"


async def ceph_pool_status(
    client: MultiClient, node: Optional[str] = None, name: str = "", endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    if not name:
        raise ValueError("Pool name is required")
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).ceph.pool(name).status.get,
    )
    lines = [f"🐟 **Ceph Pool Status: {name} on {resolved_node}**\n"]
    if isinstance(result, dict):
        data = extract_data(result)
        if isinstance(data, dict):
            for key, value in sorted(data.items()):
                lines.append(f"   • {key}: {value}")
        else:
            lines.append(str(data))
    else:
        lines.append("   No pool status available.")
    return "\n".join(lines)


async def list_ceph_mds_detail(client: MultiClient, node: Optional[str] = None, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).ceph.mds.get,
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = [f"🐟 **Ceph MDS on {resolved_node}**\n"]
    for mds in result:
        name = mds.get("name", mds.get("id", "unknown"))
        state = mds.get("state", "N/A")
        lines.append(f"   • **{name}**")
        lines.append(f"     State: {state}")
        for k in ("rank", "addr"):
            v = mds.get(k)
            if v is not None:
                lines.append(f"     {k}: {v}")
    if not result:
        lines.append("   No Ceph MDS found.")
    return "\n".join(lines)


@confirm_required
async def create_ceph_mds(
    client: MultiClient,
    node: Optional[str] = None,
    name: str = "",
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    if not name:
        raise ValueError("MDS name is required")
    elevated = client.get_client(elevated=True, endpoint=ep)
    params = {}
    for k, v in kwargs.items():
        if v is not None:
            params[k] = v
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).ceph.mds(name).post,
        elevated=True,
        **params,
    )
    upid = extract_upid(result)
    return f"Ceph MDS {name!r} created on {resolved_node}. UPID: {upid}"


@confirm_required
async def destroy_ceph_mds(
    client: MultiClient,
    node: Optional[str] = None,
    name: str = "",
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    if not name:
        raise ValueError("MDS name is required")
    elevated = client.get_client(elevated=True, endpoint=ep)
    params = {}
    for k, v in kwargs.items():
        if v is not None:
            params[k] = v
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).ceph.mds(name).delete,
        elevated=True,
        **params,
    )
    upid = extract_upid(result)
    return f"Ceph MDS {name!r} destroyed on {resolved_node}. UPID: {upid}"


@confirm_required
async def create_ceph_mgr(
    client: MultiClient,
    node: Optional[str] = None,
    id: str = "",
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    if not id:
        raise ValueError("MGR id is required")
    elevated = client.get_client(elevated=True, endpoint=ep)
    params = {}
    for k, v in kwargs.items():
        if v is not None:
            params[k] = v
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).ceph.mgr(id).post,
        elevated=True,
        **params,
    )
    upid = extract_upid(result)
    return f"Ceph MGR {id!r} created on {resolved_node}. UPID: {upid}"


@confirm_required
async def destroy_ceph_mgr(
    client: MultiClient,
    node: Optional[str] = None,
    id: str = "",
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    if not id:
        raise ValueError("MGR id is required")
    elevated = client.get_client(elevated=True, endpoint=ep)
    params = {}
    for k, v in kwargs.items():
        if v is not None:
            params[k] = v
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).ceph.mgr(id).delete,
        elevated=True,
        **params,
    )
    upid = extract_upid(result)
    return f"Ceph MGR {id!r} destroyed on {resolved_node}. UPID: {upid}"


@confirm_required
async def create_ceph_mon(
    client: MultiClient,
    node: Optional[str] = None,
    monid: str = "",
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    if not monid:
        raise ValueError("Monitor id is required")
    elevated = client.get_client(elevated=True, endpoint=ep)
    params = {}
    for k, v in kwargs.items():
        if v is not None:
            params[k] = v
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).ceph.mon(monid).post,
        elevated=True,
        **params,
    )
    upid = extract_upid(result)
    return f"Ceph MON {monid!r} created on {resolved_node}. UPID: {upid}"


@confirm_required
async def destroy_ceph_mon(
    client: MultiClient,
    node: Optional[str] = None,
    monid: str = "",
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    if not monid:
        raise ValueError("Monitor id is required")
    elevated = client.get_client(elevated=True, endpoint=ep)
    params = {}
    for k, v in kwargs.items():
        if v is not None:
            params[k] = v
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).ceph.mon(monid).delete,
        elevated=True,
        **params,
    )
    upid = extract_upid(result)
    return f"Ceph MON {monid!r} destroyed on {resolved_node}. UPID: {upid}"


@confirm_required
async def start_ceph(
    client: MultiClient, node: Optional[str] = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).ceph.start.post,
        elevated=True,
    )
    upid = extract_upid(result)
    return f"Ceph services started on {resolved_node}. UPID: {upid}"


@confirm_required
async def stop_ceph(
    client: MultiClient, node: Optional[str] = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).ceph.stop.post,
        elevated=True,
    )
    upid = extract_upid(result)
    return f"Ceph services stopped on {resolved_node}. UPID: {upid}"


@confirm_required
async def restart_ceph(
    client: MultiClient, node: Optional[str] = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).ceph.restart.post,
        elevated=True,
    )
    upid = extract_upid(result)
    return f"Ceph services restarted on {resolved_node}. UPID: {upid}"


async def ceph_cfg_db(client: MultiClient, node: Optional[str] = None, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).ceph.cfg.db.get,
    )
    lines = [f"🐟 **Ceph Config DB on {resolved_node}**\n"]
    if isinstance(result, dict):
        data = extract_data(result)
        if isinstance(data, list):
            for entry in data[:50]:
                if isinstance(entry, dict):
                    key = entry.get("key", entry.get("name", "unknown"))
                    val = entry.get("value", entry.get("val", ""))
                    lines.append(f"   • {key}: {val}")
                else:
                    lines.append(f"   • {entry}")
        elif isinstance(data, dict):
            for key, value in sorted(data.items()):
                lines.append(f"   • {key}: {value}")
        else:
            lines.append(str(data))
    elif isinstance(result, list):
        for entry in result[:50]:
            if isinstance(entry, dict):
                key = entry.get("key", entry.get("name", "unknown"))
                val = entry.get("value", entry.get("val", ""))
                lines.append(f"   • {key}: {val}")
            else:
                lines.append(f"   • {entry}")
    else:
        lines.append("   No Ceph config DB available.")
    return "\n".join(lines)


endpoint: str | None = None


async def ceph_cfg_value(client: MultiClient, node: Optional[str] = None, **kwargs: Any) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    params = {}
    for k, v in kwargs.items():
        if v is not None:
            params[k] = v
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).ceph.cfg.value.get,
        **params,
    )
    lines = [f"🐟 **Ceph Config Value on {resolved_node}**\n"]
    if isinstance(result, dict):
        data = extract_data(result)
        if isinstance(data, dict):
            for key, value in sorted(data.items()):
                lines.append(f"   • {key}: {value}")
        else:
            lines.append(str(data))
    else:
        lines.append(str(result) if result else "   No config value available.")
    return "\n".join(lines)


async def ceph_crush(client: MultiClient, node: Optional[str] = None, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).ceph.crush.get,
    )
    lines = [f"🐟 **Ceph CRUSH Map on {resolved_node}**\n"]
    if isinstance(result, dict):
        data = extract_data(result)
        if isinstance(data, dict):
            for key, value in sorted(data.items()):
                lines.append(f"   • {key}: {value}")
        elif isinstance(data, list):
            for item in data[:50]:
                if isinstance(item, dict):
                    name = item.get("name", item.get("id", "unknown"))
                    lines.append(f"   • {name}")
                    for k, v in sorted(item.items()):
                        if k not in ("name", "id"):
                            lines.append(f"     {k}: {v}")
                else:
                    lines.append(f"   • {item}")
        elif isinstance(data, str):
            lines.append(data)
        else:
            lines.append(str(data))
    elif isinstance(result, str):
        lines.append(result)
    else:
        lines.append("   No CRUSH map available.")
    return "\n".join(lines)


async def ceph_log(client: MultiClient, node: Optional[str] = None, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).ceph.log.get,
    )
    lines = [f"🐟 **Ceph Log on {resolved_node}**\n"]
    if isinstance(result, list):
        for entry in result[:100]:
            if isinstance(entry, dict):
                ts = entry.get("timestamp", entry.get("time", ""))
                msg = entry.get("message", entry.get("msg", str(entry)))
                lines.append(f"   [{ts}] {msg}" if ts else f"   {msg}")
            else:
                lines.append(f"   {entry}")
    elif isinstance(result, str):
        lines.append(result)
    elif isinstance(result, dict):
        data = extract_data(result)
        if isinstance(data, list):
            for entry in data[:100]:
                if isinstance(entry, dict):
                    ts = entry.get("timestamp", entry.get("time", ""))
                    msg = entry.get("message", entry.get("msg", str(entry)))
                    lines.append(f"   [{ts}] {msg}" if ts else f"   {msg}")
                else:
                    lines.append(f"   {entry}")
        elif isinstance(data, str):
            lines.append(data)
        else:
            lines.append(str(data))
    else:
        lines.append("   No Ceph log available.")
    return "\n".join(lines)


@confirm_required
async def init_ceph(
    client: MultiClient,
    node: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    elevated = client.get_client(elevated=True, endpoint=ep)
    params = {}
    for k, v in kwargs.items():
        if v is not None:
            params[k] = v
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).ceph.init.post,
        elevated=True,
        **params,
    )
    upid = extract_upid(result)
    return f"Ceph initialized on {resolved_node}. UPID: {upid}"
