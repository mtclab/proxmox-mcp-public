from __future__ import annotations

from typing import Any, Optional

from proxmox_mcp.multi_client import MultiClient
from proxmox_mcp.utils import validate_node_name


def _api(client: MultiClient, endpoint: str | None = None) -> Any:
    return client.get_client(elevated=False, endpoint=endpoint)


async def list_cpu_models(client: MultiClient, node: Optional[str] = None, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).capabilities.qemu.cpu.get,
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = [f"🖥️ **QEMU CPU Models on {resolved_node}**\n"]
    for model in result:
        if isinstance(model, str):
            lines.append(f"   • **{model}**")
        elif isinstance(model, dict):
            name = model.get("name", "unknown")
            model_type = model.get("type", "")
            lines.append(f"   • **{name}**")
            if model_type:
                lines.append(f"     Type: {model_type}")
    if not result:
        lines.append("   No CPU models found.")
    return "\n".join(lines)


async def list_cpu_flags(client: MultiClient, node: Optional[str] = None, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).capabilities.qemu("cpu-flags").get,
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = [f"🖥️ **QEMU CPU Flags on {resolved_node}**\n"]
    for flag in result:
        if isinstance(flag, str):
            lines.append(f"   • **{flag}**")
        elif isinstance(flag, dict):
            name = flag.get("name", "unknown")
            flag_type = flag.get("type", "")
            lines.append(f"   • **{name}**")
            if flag_type:
                lines.append(f"     Type: {flag_type}")
    if not result:
        lines.append("   No CPU flags found.")
    return "\n".join(lines)


async def list_machine_types(client: MultiClient, node: Optional[str] = None, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).capabilities.qemu.machines.get,
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = [f"🖥️ **QEMU Machine Types on {resolved_node}**\n"]
    for machine in result:
        if isinstance(machine, str):
            lines.append(f"   • **{machine}**")
        else:
            name = machine.get("name", machine.get("id", "unknown"))
            mtype = machine.get("type", "")
            version = machine.get("version", "")
            lines.append(f"   • **{name}**")
            if mtype:
                lines.append(f"     Type: {mtype}")
            if version:
                lines.append(f"     Version: {version}")
    if not result:
        lines.append("   No machine types found.")
    return "\n".join(lines)


async def list_capabilities(client: MultiClient, node: Optional[str] = None, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).capabilities.get,
    )
    lines = [f"🖥️ **Node Capabilities: {resolved_node}**\n"]
    if isinstance(result, dict):
        for key, value in sorted(result.items()):
            lines.append(f"   • {key}: {value}")
    elif isinstance(result, list):
        for entry in result:
            lines.append(f"   • {entry}")
    else:
        lines.append(str(result))
    return "\n".join(lines)


async def list_capabilities_qemu(client: MultiClient, node: Optional[str] = None, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).capabilities.qemu.get,
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = [f"🖥️ **QEMU Capabilities on {resolved_node}**\n"]
    for entry in result:
        if isinstance(entry, str):
            lines.append(f"   • {entry}")
        elif isinstance(entry, dict):
            name = entry.get("name", entry.get("id", "unknown"))
            lines.append(f"   • {name}")
    if not result:
        lines.append("   No QEMU capabilities found.")
    return "\n".join(lines)


async def get_capability_qemu_migrations(
    client: MultiClient, node: Optional[str] = None, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).capabilities.qemu.migration.get,
    )
    lines = [f"🖥️ **QEMU Migration Capabilities on {resolved_node}**\n"]
    if isinstance(result, dict):
        for key, value in sorted(result.items()):
            lines.append(f"   • {key}: {value}")
    else:
        lines.append(str(result))
    return "\n".join(lines)
