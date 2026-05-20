from __future__ import annotations

from typing import Any, Optional

from proxmoxer.core import ResourceException

from proxmox_mcp.multi_client import MultiClient
from proxmox_mcp.utils import confirm_required, extract_upid, validate_node_name, validate_vmid

ALLOWED_VMTYPES = ("qemu", "lxc")


def _validate_vmtype(vmtype: str) -> None:
    if vmtype not in ALLOWED_VMTYPES:
        raise ValueError(f"Invalid vmtype {vmtype!r}. Must be one of {ALLOWED_VMTYPES}")


def _api(client: MultiClient, endpoint: str | None = None) -> Any:
    return client.get_client(elevated=False, endpoint=endpoint)


async def list_cluster_firewall_rules(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(_api(client, endpoint=ep).cluster.firewall.rules.get)
    if not isinstance(result, list):
        result = [result] if result else []
    lines = ["\U0001f6e1 **Cluster Firewall Rules**\n"]
    for rule in result:
        pos = rule.get("pos", "?")
        action = rule.get("action", "?")
        dptype = rule.get("type", "?")
        dport = rule.get("dport", "")
        sport = rule.get("sport", "")
        proto = rule.get("proto", "")
        source = rule.get("source", "")
        dest = rule.get("dest", "")
        iface = rule.get("iface", "")
        comment = rule.get("comment", "")
        parts = [f"pos={pos}", f"action={action}"]
        if dptype != "?":
            parts.append(f"type={dptype}")
        if dport:
            parts.append(f"dport={dport}")
        if sport:
            parts.append(f"sport={sport}")
        if proto:
            parts.append(f"proto={proto}")
        if source:
            parts.append(f"src={source}")
        if dest:
            parts.append(f"dst={dest}")
        if iface:
            parts.append(f"iface={iface}")
        lines.append(f"   • {' | '.join(parts)}")
        if comment:
            lines.append(f"     {comment}")
    if not result:
        lines.append("   No rules found.")
    return "\n".join(lines)


@confirm_required
async def create_cluster_firewall_rule(
    client: MultiClient,
    action: str = "ACCEPT",
    dptype: str = "in",
    dport: str | None = None,
    sport: str | None = None,
    proto: str | None = None,
    source: str | None = None,
    dest: str | None = None,
    iface: str | None = None,
    comment: str | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    params: dict[str, Any] = {"action": action, "type": dptype}
    if dport is not None:
        params["dport"] = dport
    if sport is not None:
        params["sport"] = sport
    if proto is not None:
        params["proto"] = proto
    if source is not None:
        params["source"] = source
    if dest is not None:
        params["dest"] = dest
    if iface is not None:
        params["iface"] = iface
    if comment is not None:
        params["comment"] = comment
    params.update(kwargs)
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.cluster.firewall.rules.post,
        elevated=True,
        **params,
    )
    pos = extract_upid(result)
    return f"Cluster firewall rule created: action={action}, pos={pos}"


async def get_cluster_firewall_rule(client: MultiClient, pos: int = 0, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(_api(client, endpoint=ep).cluster.firewall.rules(pos).get)
    if isinstance(result, dict):
        lines = [f"\U0001f6e1 **Cluster Firewall Rule {pos}**\n"]
        for key, val in sorted(result.items()):
            lines.append(f"   • {key}: {val}")
        return "\n".join(lines)
    return f"Cluster firewall rule {pos}: {result}"


@confirm_required
async def update_cluster_firewall_rule(
    client: MultiClient,
    pos: int = 0,
    action: str | None = None,
    dptype: str | None = None,
    dport: str | None = None,
    sport: str | None = None,
    proto: str | None = None,
    source: str | None = None,
    dest: str | None = None,
    iface: str | None = None,
    comment: str | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    params: dict[str, Any] = {}
    if action is not None:
        params["action"] = action
    if dptype is not None:
        params["type"] = dptype
    if dport is not None:
        params["dport"] = dport
    if sport is not None:
        params["sport"] = sport
    if proto is not None:
        params["proto"] = proto
    if source is not None:
        params["source"] = source
    if dest is not None:
        params["dest"] = dest
    if iface is not None:
        params["iface"] = iface
    if comment is not None:
        params["comment"] = comment
    params.update(kwargs)
    if not params:
        raise ValueError("At least one parameter must be provided to update")
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.firewall.rules(pos).put,
        elevated=True,
        **params,
    )
    return f"Cluster firewall rule {pos} updated"


@confirm_required
async def delete_cluster_firewall_rule(
    client: MultiClient, pos: int = 0, confirm: bool = False, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.firewall.rules(pos).delete,
        elevated=True,
    )
    return f"Cluster firewall rule {pos} deleted"


async def get_cluster_firewall_options(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(_api(client, endpoint=ep).cluster.firewall.options.get)
    lines = ["\U0001f6e1 **Cluster Firewall Options**\n"]
    if isinstance(result, dict):
        for key, val in sorted(result.items()):
            lines.append(f"   • {key}: {val}")
    if not isinstance(result, dict) or not result:
        lines.append("   No options found.")
    return "\n".join(lines)


@confirm_required
async def set_cluster_firewall_options(
    client: MultiClient,
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not kwargs:
        raise ValueError("At least one option must be provided to update")
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.firewall.options.put,
        elevated=True,
        **kwargs,
    )
    opts = ", ".join(f"{k}={v!r}" for k, v in kwargs.items())
    return f"Cluster firewall options updated: {opts}"


async def list_cluster_firewall_aliases(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(_api(client, endpoint=ep).cluster.firewall.aliases.get)
    if not isinstance(result, list):
        result = [result] if result else []
    lines = ["\U0001f6e1 **Cluster Firewall Aliases**\n"]
    for alias in result:
        name = alias.get("name", "unknown")
        cidr = alias.get("cidr", "")
        comment = alias.get("comment", "")
        lines.append(f"   • **{name}**: {cidr}")
        if comment:
            lines.append(f"     {comment}")
    if not result:
        lines.append("   No aliases found.")
    return "\n".join(lines)


@confirm_required
async def create_cluster_firewall_alias(
    client: MultiClient,
    name: str = "",
    cidr: str = "",
    comment: str | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not name:
        raise ValueError("name is required for alias creation")
    if not cidr:
        raise ValueError("cidr is required for alias creation")
    params: dict[str, Any] = {"name": name, "cidr": cidr}
    if comment is not None:
        params["comment"] = comment
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.firewall.aliases.post,
        elevated=True,
        **params,
    )
    return f"Cluster firewall alias {name!r} created"


@confirm_required
async def delete_cluster_firewall_alias(
    client: MultiClient, name: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not name:
        raise ValueError("name is required for alias deletion")
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.firewall.aliases(name).delete,
        elevated=True,
    )
    return f"Cluster firewall alias {name!r} deleted"


async def list_cluster_firewall_ipsets(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(_api(client, endpoint=ep).cluster.firewall.ipset.get)
    if not isinstance(result, list):
        result = [result] if result else []
    lines = ["\U0001f6e1 **Cluster Firewall IPSets**\n"]
    for ipset in result:
        name = ipset.get("name", "unknown")
        comment = ipset.get("comment", "")
        lines.append(f"   • **{name}**")
        if comment:
            lines.append(f"     {comment}")
    if not result:
        lines.append("   No IPSets found.")
    return "\n".join(lines)


async def list_cluster_firewall_refs(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(_api(client, endpoint=ep).cluster.firewall.refs.get)
    if not isinstance(result, list):
        result = [result] if result else []
    lines = ["\U0001f6e1 **Cluster Firewall References**\n"]
    for ref in result:
        ref_name = ref.get("ref", "unknown")
        rtype = ref.get("type", "?")
        comment = ref.get("comment", "")
        lines.append(f"   • **{ref_name}** ({rtype})")
        if comment:
            lines.append(f"     {comment}")
    if not result:
        lines.append("   No references found.")
    return "\n".join(lines)


async def list_node_firewall_rules(client: MultiClient, node: Optional[str] = None, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    result = await client.safe_api_call(_api(client, endpoint=ep).nodes(resolved_node).firewall.rules.get)
    if not isinstance(result, list):
        result = [result] if result else []
    lines = [f"\U0001f6e1 **Node Firewall Rules ({resolved_node})**\n"]
    for rule in result:
        pos = rule.get("pos", "?")
        action = rule.get("action", "?")
        dptype = rule.get("type", "?")
        dport = rule.get("dport", "")
        proto = rule.get("proto", "")
        source = rule.get("source", "")
        dest = rule.get("dest", "")
        comment = rule.get("comment", "")
        parts = [f"pos={pos}", f"action={action}"]
        if dptype != "?":
            parts.append(f"type={dptype}")
        if dport:
            parts.append(f"dport={dport}")
        if proto:
            parts.append(f"proto={proto}")
        if source:
            parts.append(f"src={source}")
        if dest:
            parts.append(f"dst={dest}")
        lines.append(f"   • {' | '.join(parts)}")
        if comment:
            lines.append(f"     {comment}")
    if not result:
        lines.append("   No rules found.")
    return "\n".join(lines)


@confirm_required
async def create_node_firewall_rule(
    client: MultiClient,
    node: Optional[str] = None,
    action: str = "ACCEPT",
    dptype: str = "in",
    dport: str | None = None,
    sport: str | None = None,
    proto: str | None = None,
    source: str | None = None,
    dest: str | None = None,
    iface: str | None = None,
    comment: str | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    params: dict[str, Any] = {"action": action, "type": dptype}
    if dport is not None:
        params["dport"] = dport
    if sport is not None:
        params["sport"] = sport
    if proto is not None:
        params["proto"] = proto
    if source is not None:
        params["source"] = source
    if dest is not None:
        params["dest"] = dest
    if iface is not None:
        params["iface"] = iface
    if comment is not None:
        params["comment"] = comment
    params.update(kwargs)
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).firewall.rules.post,
        elevated=True,
        **params,
    )
    pos = extract_upid(result)
    return f"Node {resolved_node} firewall rule created: action={action}, pos={pos}"


@confirm_required
async def delete_node_firewall_rule(
    client: MultiClient, node: Optional[str] = None, pos: int = 0, confirm: bool = False, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.nodes(resolved_node).firewall.rules(pos).delete,
        elevated=True,
    )
    return f"Node {resolved_node} firewall rule {pos} deleted"


async def get_node_firewall_options(
    client: MultiClient, node: Optional[str] = None, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    result = await client.safe_api_call(_api(client, endpoint=ep).nodes(resolved_node).firewall.options.get)
    lines = [f"\U0001f6e1 **Node Firewall Options ({resolved_node})**\n"]
    if isinstance(result, dict):
        for key, val in sorted(result.items()):
            lines.append(f"   • {key}: {val}")
    if not isinstance(result, dict) or not result:
        lines.append("   No options found.")
    return "\n".join(lines)


async def list_vm_firewall_rules(
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
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    result = await client.safe_api_call(
        getattr(_api(client, endpoint=ep).nodes(resolved_node), vmtype)(vmid).firewall.rules.get
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = [f"\U0001f6e1 **VM Firewall Rules ({vmtype} {vmid} on {resolved_node})**\n"]
    for rule in result:
        pos = rule.get("pos", "?")
        action = rule.get("action", "?")
        dptype = rule.get("type", "?")
        dport = rule.get("dport", "")
        proto = rule.get("proto", "")
        source = rule.get("source", "")
        dest = rule.get("dest", "")
        comment = rule.get("comment", "")
        parts = [f"pos={pos}", f"action={action}"]
        if dptype != "?":
            parts.append(f"type={dptype}")
        if dport:
            parts.append(f"dport={dport}")
        if proto:
            parts.append(f"proto={proto}")
        if source:
            parts.append(f"src={source}")
        if dest:
            parts.append(f"dst={dest}")
        lines.append(f"   • {' | '.join(parts)}")
        if comment:
            lines.append(f"     {comment}")
    if not result:
        lines.append("   No rules found.")
    return "\n".join(lines)


@confirm_required
async def create_vm_firewall_rule(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    vmtype: str = "qemu",
    action: str = "ACCEPT",
    dptype: str = "in",
    dport: str | None = None,
    sport: str | None = None,
    proto: str | None = None,
    source: str | None = None,
    dest: str | None = None,
    iface: str | None = None,
    comment: str | None = None,
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
    params: dict[str, Any] = {"action": action, "type": dptype}
    if dport is not None:
        params["dport"] = dport
    if sport is not None:
        params["sport"] = sport
    if proto is not None:
        params["proto"] = proto
    if source is not None:
        params["source"] = source
    if dest is not None:
        params["dest"] = dest
    if iface is not None:
        params["iface"] = iface
    if comment is not None:
        params["comment"] = comment
    params.update(kwargs)
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        getattr(elevated.nodes(resolved_node), vmtype)(vmid).firewall.rules.post,
        elevated=True,
        **params,
    )
    pos = extract_upid(result)
    return f"VM firewall rule created for {vmtype} {vmid} on {resolved_node}: action={action}, pos={pos}"


@confirm_required
async def delete_vm_firewall_rule(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    pos: int = 0,
    vmtype: str = "qemu",
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    _validate_vmtype(vmtype)
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        getattr(elevated.nodes(resolved_node), vmtype)(vmid).firewall.rules(pos).delete,
        elevated=True,
    )
    return f"VM firewall rule {pos} deleted for {vmtype} {vmid} on {resolved_node}"


async def get_vm_firewall_options(
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
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    result = await client.safe_api_call(
        getattr(_api(client, endpoint=ep).nodes(resolved_node), vmtype)(vmid).firewall.options.get
    )
    lines = [f"\U0001f6e1 **VM Firewall Options ({vmtype} {vmid} on {resolved_node})**\n"]
    if isinstance(result, dict):
        for key, val in sorted(result.items()):
            lines.append(f"   • {key}: {val}")
    if not isinstance(result, dict) or not result:
        lines.append("   No options found.")
    return "\n".join(lines)


async def get_vm_firewall_alias(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    name: str = "",
    vmtype: str = "qemu",
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    _validate_vmtype(vmtype)
    if not name:
        raise ValueError("name is required")
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    result = await client.safe_api_call(
        getattr(_api(client, endpoint=ep).nodes(resolved_node), vmtype)(vmid).firewall.aliases(name).get
    )
    lines = [f"\U0001f6e1 **VM Firewall Alias: {name} ({vmtype} {vmid} on {resolved_node})**\n"]
    if isinstance(result, dict):
        for key, val in sorted(result.items()):
            lines.append(f"   • {key}: {val}")
    if not result:
        lines.append("   No data returned.")
    return "\n".join(lines)


@confirm_required
async def create_vm_firewall_alias(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    name: str = "",
    cidr: str = "",
    vmtype: str = "qemu",
    comment: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    _validate_vmtype(vmtype)
    if not name:
        raise ValueError("name is required for alias creation")
    if not cidr:
        raise ValueError("cidr is required for alias creation")
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    params: dict[str, Any] = {"name": name, "cidr": cidr}
    if comment is not None:
        params["comment"] = comment
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        getattr(elevated.nodes(resolved_node), vmtype)(vmid).firewall.aliases.post,
        elevated=True,
        **params,
    )
    return f"VM firewall alias {name!r} created for {vmtype} {vmid} on {resolved_node}"


@confirm_required
async def delete_vm_firewall_alias(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    name: str = "",
    vmtype: str = "qemu",
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    _validate_vmtype(vmtype)
    if not name:
        raise ValueError("name is required for alias deletion")
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        getattr(elevated.nodes(resolved_node), vmtype)(vmid).firewall.aliases(name).delete,
        elevated=True,
    )
    return f"VM firewall alias {name!r} deleted for {vmtype} {vmid} on {resolved_node}"


async def list_cluster_firewall_ipset_content(client: MultiClient, name: str = "", endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    if not name:
        raise ValueError("name is required")
    result = await client.safe_api_call(_api(client, endpoint=ep).cluster.firewall.ipset(name).get)
    if not isinstance(result, list):
        result = [result] if result else []
    lines = [f"\U0001f6e1 **Cluster Firewall IPSet Content: {name}**\n"]
    for entry in result:
        cidr = entry.get("cidr", "?")
        comment = entry.get("comment", "")
        lines.append(f"   • {cidr}")
        if comment:
            lines.append(f"     {comment}")
    if not result:
        lines.append("   No entries found.")
    return "\n".join(lines)


@confirm_required
async def create_cluster_firewall_ipset(
    client: MultiClient,
    name: str = "",
    comment: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not name:
        raise ValueError("name is required for IPSet creation")
    params: dict[str, Any] = {"name": name}
    if comment is not None:
        params["comment"] = comment
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.firewall.ipset.post,
        elevated=True,
        **params,
    )
    return f"Cluster firewall IPSet {name!r} created"


@confirm_required
async def delete_cluster_firewall_ipset(
    client: MultiClient, name: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not name:
        raise ValueError("name is required for IPSet deletion")
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.firewall.ipset(name).delete,
        elevated=True,
    )
    return f"Cluster firewall IPSet {name!r} deleted"


async def list_node_firewall_aliases(
    client: MultiClient, node: Optional[str] = None, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    try:
        result = await client.safe_api_call(_api(client, endpoint=ep).nodes(resolved_node).firewall.aliases.get)
    except ResourceException as exc:
        if exc.status_code == 501:
            return (
                f"🛡️ **Node Firewall Aliases ({resolved_node})**\n\n"
                "   Node-level firewall aliases are not supported by this PVE version."
            )
        raise
    if not isinstance(result, list):
        result = [result] if result else []
    lines = [f"\U0001f6e1 **Node Firewall Aliases ({resolved_node})**\n"]
    for alias in result:
        alias_name = alias.get("name", "unknown")
        cidr = alias.get("cidr", "")
        comment = alias.get("comment", "")
        lines.append(f"   • **{alias_name}**: {cidr}")
        if comment:
            lines.append(f"     {comment}")
    if not result:
        lines.append("   No aliases found.")
    return "\n".join(lines)


async def node_firewall_log(client: MultiClient, node: Optional[str] = None, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    result = await client.safe_api_call(_api(client, endpoint=ep).nodes(resolved_node).firewall.log.get)
    if not isinstance(result, list):
        result = [result] if result else []
    lines = [f"\U0001f6e1 **Node Firewall Log ({resolved_node})**\n"]
    for entry in result:
        if isinstance(entry, dict):
            proto = entry.get("proto", "?")
            action = entry.get("action", "?")
            src = entry.get("src", "")
            dst = entry.get("dst", "")
            dport = entry.get("dport", "")
            lines.append(f"   • {proto}/{action} {src} → {dst}:{dport}")
        else:
            lines.append(f"   • {entry}")
    if not result:
        lines.append("   No log entries found.")
    return "\n".join(lines)


async def get_cluster_firewall_alias(client: MultiClient, name: str = "", endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    if not name:
        raise ValueError("name is required")
    result = await client.safe_api_call(_api(client, endpoint=ep).cluster.firewall.aliases(name).get)
    lines = [f"\U0001f6e1 **Cluster Firewall Alias: {name}**\n"]
    if isinstance(result, dict):
        for key, val in sorted(result.items()):
            lines.append(f"   • {key}: {val}")
    if not isinstance(result, dict) or not result:
        lines.append("   No data returned.")
    return "\n".join(lines)


@confirm_required
async def update_cluster_firewall_alias(
    client: MultiClient,
    name: str = "",
    cidr: str | None = None,
    comment: str | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not name:
        raise ValueError("name is required for alias update")
    params: dict[str, Any] = {}
    if cidr is not None:
        params["cidr"] = cidr
    if comment is not None:
        params["comment"] = comment
    params.update(kwargs)
    if not params:
        raise ValueError("At least one parameter must be provided to update")
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.firewall.aliases(name).put,
        elevated=True,
        **params,
    )
    return f"Cluster firewall alias {name!r} updated"


@confirm_required
async def update_cluster_firewall_ipset(
    client: MultiClient,
    name: str = "",
    comment: str | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not name:
        raise ValueError("name is required for IPSet update")
    params: dict[str, Any] = {}
    if comment is not None:
        params["comment"] = comment
    params.update(kwargs)
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.firewall.ipset(name).put,
        elevated=True,
        **params,
    )
    return f"Cluster firewall IPSet {name!r} updated"


@confirm_required
async def add_cluster_firewall_ipset_entry(
    client: MultiClient,
    name: str = "",
    cidr: str = "",
    comment: str | None = None,
    nomatch: int | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not name:
        raise ValueError("name is required")
    if not cidr:
        raise ValueError("cidr is required")
    params: dict[str, Any] = {"cidr": cidr}
    if comment is not None:
        params["comment"] = comment
    if nomatch is not None:
        params["nomatch"] = nomatch
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.firewall.ipset(name).post,
        elevated=True,
        **params,
    )
    return f"Added {cidr} to cluster IPSet {name!r}"


async def get_cluster_firewall_ipset_entry(
    client: MultiClient, name: str = "", cidr: str = "", endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    if not name:
        raise ValueError("name is required")
    if not cidr:
        raise ValueError("cidr is required")
    result = await client.safe_api_call(_api(client, endpoint=ep).cluster.firewall.ipset(name)(cidr).get)
    lines = [f"\U0001f6e1 **Cluster IPSet Entry: {name}/{cidr}**\n"]
    if isinstance(result, dict):
        for key, val in sorted(result.items()):
            lines.append(f"   • {key}: {val}")
    if not isinstance(result, dict) or not result:
        lines.append("   No data returned.")
    return "\n".join(lines)


@confirm_required
async def delete_cluster_firewall_ipset_entry(
    client: MultiClient, name: str = "", cidr: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not name:
        raise ValueError("name is required")
    if not cidr:
        raise ValueError("cidr is required")
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.firewall.ipset(name)(cidr).delete,
        elevated=True,
    )
    return f"Removed {cidr} from cluster IPSet {name!r}"


async def list_cluster_firewall_macros(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(_api(client, endpoint=ep).cluster.firewall.macros.get)
    if not isinstance(result, list):
        result = [result] if result else []
    lines = ["\U0001f6e1 **Cluster Firewall Macros**\n"]
    for macro in result:
        macro_name = macro.get("macro", macro.get("name", "unknown"))
        desc = macro.get("description", "")
        lines.append(f"   • **{macro_name}**")
        if desc:
            lines.append(f"     {desc}")
    if not result:
        lines.append("   No macros found.")
    return "\n".join(lines)


async def get_node_firewall_rule(
    client: MultiClient, node: Optional[str] = None, pos: int = 0, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    result = await client.safe_api_call(_api(client, endpoint=ep).nodes(resolved_node).firewall.rules(pos).get)
    if isinstance(result, dict):
        lines = [f"\U0001f6e1 **Node Firewall Rule {pos} ({resolved_node})**\n"]
        for key, val in sorted(result.items()):
            lines.append(f"   • {key}: {val}")
        return "\n".join(lines)
    return f"Node {resolved_node} firewall rule {pos}: {result}"


@confirm_required
async def update_node_firewall_rule(
    client: MultiClient,
    node: Optional[str] = None,
    pos: int = 0,
    action: str | None = None,
    dptype: str | None = None,
    dport: str | None = None,
    sport: str | None = None,
    proto: str | None = None,
    source: str | None = None,
    dest: str | None = None,
    iface: str | None = None,
    comment: str | None = None,
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
    if action is not None:
        params["action"] = action
    if dptype is not None:
        params["type"] = dptype
    if dport is not None:
        params["dport"] = dport
    if sport is not None:
        params["sport"] = sport
    if proto is not None:
        params["proto"] = proto
    if source is not None:
        params["source"] = source
    if dest is not None:
        params["dest"] = dest
    if iface is not None:
        params["iface"] = iface
    if comment is not None:
        params["comment"] = comment
    params.update(kwargs)
    if not params:
        raise ValueError("At least one parameter must be provided to update")
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.nodes(resolved_node).firewall.rules(pos).put,
        elevated=True,
        **params,
    )
    return f"Node {resolved_node} firewall rule {pos} updated"


@confirm_required
async def set_node_firewall_options(
    client: MultiClient,
    node: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not kwargs:
        raise ValueError("At least one option must be provided to update")
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.nodes(resolved_node).firewall.options.put,
        elevated=True,
        **kwargs,
    )
    opts = ", ".join(f"{k}={v!r}" for k, v in kwargs.items())
    return f"Node {resolved_node} firewall options updated: {opts}"


async def list_node_firewall_ipsets(
    client: MultiClient, node: Optional[str] = None, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    try:
        result = await client.safe_api_call(_api(client, endpoint=ep).nodes(resolved_node).firewall.ipset.get)
    except ResourceException as exc:
        if exc.status_code == 501:
            return (
                f"🛡️ **Node Firewall IPSets ({resolved_node})**\n\n"
                "   Node-level firewall IPSets are not supported by this PVE version."
            )
        raise
    if not isinstance(result, list):
        result = [result] if result else []
    lines = [f"\U0001f6e1 **Node Firewall IPSets ({resolved_node})**\n"]
    for ipset in result:
        ipset_name = ipset.get("name", "unknown")
        comment = ipset.get("comment", "")
        lines.append(f"   • **{ipset_name}**")
        if comment:
            lines.append(f"     {comment}")
    if not result:
        lines.append("   No IPSets found.")
    return "\n".join(lines)


async def get_vm_firewall_rule(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    pos: int = 0,
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
        getattr(_api(client, endpoint=ep).nodes(resolved_node), vmtype)(vmid).firewall.rules(pos).get
    )
    if isinstance(result, dict):
        lines = [f"\U0001f6e1 **VM Firewall Rule {pos} ({vmtype} {vmid} on {resolved_node})**\n"]
        for key, val in sorted(result.items()):
            lines.append(f"   • {key}: {val}")
        return "\n".join(lines)
    return f"VM firewall rule {pos} for {vmtype} {vmid} on {resolved_node}: {result}"


@confirm_required
async def update_vm_firewall_rule(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    pos: int = 0,
    vmtype: str = "qemu",
    action: str | None = None,
    dptype: str | None = None,
    dport: str | None = None,
    sport: str | None = None,
    proto: str | None = None,
    source: str | None = None,
    dest: str | None = None,
    iface: str | None = None,
    comment: str | None = None,
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
    if action is not None:
        params["action"] = action
    if dptype is not None:
        params["type"] = dptype
    if dport is not None:
        params["dport"] = dport
    if sport is not None:
        params["sport"] = sport
    if proto is not None:
        params["proto"] = proto
    if source is not None:
        params["source"] = source
    if dest is not None:
        params["dest"] = dest
    if iface is not None:
        params["iface"] = iface
    if comment is not None:
        params["comment"] = comment
    params.update(kwargs)
    if not params:
        raise ValueError("At least one parameter must be provided to update")
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        getattr(elevated.nodes(resolved_node), vmtype)(vmid).firewall.rules(pos).put,
        elevated=True,
        **params,
    )
    return f"VM firewall rule {pos} updated for {vmtype} {vmid} on {resolved_node}"


@confirm_required
async def set_vm_firewall_options(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    vmtype: str = "qemu",
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    _validate_vmtype(vmtype)
    if not kwargs:
        raise ValueError("At least one option must be provided to update")
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        getattr(elevated.nodes(resolved_node), vmtype)(vmid).firewall.options.put,
        elevated=True,
        **kwargs,
    )
    opts = ", ".join(f"{k}={v!r}" for k, v in kwargs.items())
    return f"VM firewall options updated for {vmtype} {vmid} on {resolved_node}: {opts}"


async def list_vm_firewall_aliases(
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
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    result = await client.safe_api_call(
        getattr(_api(client, endpoint=ep).nodes(resolved_node), vmtype)(vmid).firewall.aliases.get
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = [f"\U0001f6e1 **VM Firewall Aliases ({vmtype} {vmid} on {resolved_node})**\n"]
    for alias in result:
        alias_name = alias.get("name", "unknown")
        cidr = alias.get("cidr", "")
        comment = alias.get("comment", "")
        lines.append(f"   • **{alias_name}**: {cidr}")
        if comment:
            lines.append(f"     {comment}")
    if not result:
        lines.append("   No aliases found.")
    return "\n".join(lines)


@confirm_required
async def update_vm_firewall_alias(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    name: str = "",
    cidr: str | None = None,
    vmtype: str = "qemu",
    comment: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    _validate_vmtype(vmtype)
    if not name:
        raise ValueError("name is required for alias update")
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    params: dict[str, Any] = {}
    if cidr is not None:
        params["cidr"] = cidr
    if comment is not None:
        params["comment"] = comment
    if not params:
        raise ValueError("At least one parameter must be provided to update")
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        getattr(elevated.nodes(resolved_node), vmtype)(vmid).firewall.aliases(name).put,
        elevated=True,
        **params,
    )
    return f"VM firewall alias {name!r} updated for {vmtype} {vmid} on {resolved_node}"


async def vm_firewall_log(
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
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    result = await client.safe_api_call(
        getattr(_api(client, endpoint=ep).nodes(resolved_node), vmtype)(vmid).firewall.log.get
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = [f"\U0001f6e1 **VM Firewall Log ({vmtype} {vmid} on {resolved_node})**\n"]
    for entry in result:
        if isinstance(entry, dict):
            proto = entry.get("proto", "?")
            action = entry.get("action", "?")
            src = entry.get("src", "")
            dst = entry.get("dst", "")
            dport = entry.get("dport", "")
            lines.append(f"   • {proto}/{action} {src} \u2192 {dst}:{dport}")
        else:
            lines.append(f"   • {entry}")
    if not result:
        lines.append("   No log entries found.")
    return "\n".join(lines)


async def vm_firewall_refs(
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
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    result = await client.safe_api_call(
        getattr(_api(client, endpoint=ep).nodes(resolved_node), vmtype)(vmid).firewall.refs.get
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = [f"\U0001f6e1 **VM Firewall References ({vmtype} {vmid} on {resolved_node})**\n"]
    for ref in result:
        ref_name = ref.get("ref", "unknown")
        rtype = ref.get("type", "?")
        comment = ref.get("comment", "")
        lines.append(f"   • **{ref_name}** ({rtype})")
        if comment:
            lines.append(f"     {comment}")
    if not result:
        lines.append("   No references found.")
    return "\n".join(lines)


async def list_vm_firewall_ipset_content(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    name: str = "",
    vmtype: str = "qemu",
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    _validate_vmtype(vmtype)
    if not name:
        raise ValueError("name is required")
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    result = await client.safe_api_call(
        getattr(_api(client, endpoint=ep).nodes(resolved_node), vmtype)(vmid).firewall.ipset(name).get
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = [f"\U0001f6e1 **VM Firewall IPSet Content: {name} ({vmtype} {vmid} on {resolved_node})**\n"]
    for entry in result:
        cidr = entry.get("cidr", "?")
        comment = entry.get("comment", "")
        lines.append(f"   • {cidr}")
        if comment:
            lines.append(f"     {comment}")
    if not result:
        lines.append("   No entries found.")
    return "\n".join(lines)


@confirm_required
async def create_vm_firewall_ipset(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    name: str = "",
    vmtype: str = "qemu",
    comment: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    _validate_vmtype(vmtype)
    if not name:
        raise ValueError("name is required for IPSet creation")
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    params: dict[str, Any] = {"name": name}
    if comment is not None:
        params["comment"] = comment
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        getattr(elevated.nodes(resolved_node), vmtype)(vmid).firewall.ipset.post,
        elevated=True,
        **params,
    )
    return f"VM firewall IPSet {name!r} created for {vmtype} {vmid} on {resolved_node}"


@confirm_required
async def delete_vm_firewall_ipset(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    name: str = "",
    vmtype: str = "qemu",
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    _validate_vmtype(vmtype)
    if not name:
        raise ValueError("name is required for IPSet deletion")
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        getattr(elevated.nodes(resolved_node), vmtype)(vmid).firewall.ipset(name).delete,
        elevated=True,
    )
    return f"VM firewall IPSet {name!r} deleted for {vmtype} {vmid} on {resolved_node}"


@confirm_required
async def add_vm_firewall_ipset_entry(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    name: str = "",
    cidr: str = "",
    vmtype: str = "qemu",
    comment: Optional[str] = None,
    nomatch: Optional[int] = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    _validate_vmtype(vmtype)
    if not name:
        raise ValueError("name is required")
    if not cidr:
        raise ValueError("cidr is required")
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    params: dict[str, Any] = {"cidr": cidr}
    if comment is not None:
        params["comment"] = comment
    if nomatch is not None:
        params["nomatch"] = nomatch
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        getattr(elevated.nodes(resolved_node), vmtype)(vmid).firewall.ipset(name).post,
        elevated=True,
        **params,
    )
    return f"added {cidr} to VM IPSet {name!r} for {vmtype} {vmid} on {resolved_node}"


async def get_vm_firewall_ipset_entry(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    name: str = "",
    cidr: str = "",
    vmtype: str = "qemu",
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    _validate_vmtype(vmtype)
    if not name:
        raise ValueError("name is required")
    if not cidr:
        raise ValueError("cidr is required")
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    result = await client.safe_api_call(
        getattr(_api(client, endpoint=ep).nodes(resolved_node), vmtype)(vmid).firewall.ipset(name)(cidr).get
    )
    lines = [f"\U0001f6e1 **VM IPSet Entry: {name}/{cidr} ({vmtype} {vmid} on {resolved_node})**\n"]
    if isinstance(result, dict):
        for key, val in sorted(result.items()):
            lines.append(f"   • {key}: {val}")
    if not isinstance(result, dict) or not result:
        lines.append("   No data returned.")
    return "\n".join(lines)


@confirm_required
async def update_vm_firewall_ipset_entry(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    name: str = "",
    cidr: str = "",
    vmtype: str = "qemu",
    comment: Optional[str] = None,
    nomatch: Optional[int] = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    _validate_vmtype(vmtype)
    if not name:
        raise ValueError("name is required")
    if not cidr:
        raise ValueError("cidr is required")
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    params: dict[str, Any] = {}
    if comment is not None:
        params["comment"] = comment
    if nomatch is not None:
        params["nomatch"] = nomatch
    if not params:
        raise ValueError("At least one parameter must be provided to update")
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        getattr(elevated.nodes(resolved_node), vmtype)(vmid).firewall.ipset(name)(cidr).put,
        elevated=True,
        **params,
    )
    return f"VM IPSet entry {name}/{cidr} updated for {vmtype} {vmid} on {resolved_node}"


@confirm_required
async def delete_vm_firewall_ipset_entry(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    name: str = "",
    cidr: str = "",
    vmtype: str = "qemu",
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    _validate_vmtype(vmtype)
    if not name:
        raise ValueError("name is required")
    if not cidr:
        raise ValueError("cidr is required")
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        getattr(elevated.nodes(resolved_node), vmtype)(vmid).firewall.ipset(name)(cidr).delete,
        elevated=True,
    )
    return f"deleted {cidr} from VM IPSet {name!r} for {vmtype} {vmid} on {resolved_node}"


async def list_vm_firewall_ipsets(
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
    validate_node_name(resolved_node)
    validate_vmid(vmid)
    result = await client.safe_api_call(
        getattr(_api(client, endpoint=ep).nodes(resolved_node), vmtype)(vmid).firewall.ipset.get
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = [f"\U0001f6e1 **VM Firewall IPSets ({vmtype} {vmid} on {resolved_node})**\n"]
    for ipset in result:
        ipset_name = ipset.get("name", "unknown")
        comment = ipset.get("comment", "")
        lines.append(f"   • **{ipset_name}**")
        if comment:
            lines.append(f"     {comment}")
    if not result:
        lines.append("   No IPSets found.")
    return "\n".join(lines)


async def get_vm_firewall_ipset(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    name: str = "",
    cidr: str = "",
    vmtype: str = "qemu",
    endpoint: str | None = None,
) -> str:
    return await get_vm_firewall_ipset_entry(
        client, node=node, vmid=vmid, name=name, cidr=cidr, vmtype=vmtype, endpoint=endpoint
    )


async def update_vm_firewall_ipset(
    client: MultiClient,
    node: Optional[str] = None,
    vmid: Optional[int] = None,
    name: str = "",
    cidr: str = "",
    vmtype: str = "qemu",
    comment: Optional[str] = None,
    nomatch: Optional[int] = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    return await update_vm_firewall_ipset_entry(
        client,
        node=node,
        vmid=vmid,
        name=name,
        cidr=cidr,
        vmtype=vmtype,
        comment=comment,
        nomatch=nomatch,
        confirm=confirm,
        endpoint=endpoint,
    )
