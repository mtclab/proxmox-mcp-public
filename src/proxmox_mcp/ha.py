from __future__ import annotations

import warnings
from typing import Any, Optional

from proxmoxer.core import ResourceException

from proxmox_mcp.multi_client import MultiClient
from proxmox_mcp.utils import confirm_required


def _api(client: MultiClient, endpoint: str | None = None) -> Any:
    return client.get_client(elevated=False, endpoint=endpoint)


async def list_ha_resources(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.ha.resources.get,
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = ["🔴 **HA Resources**\n"]
    for res in result:
        sid = res.get("sid", "unknown")
        group = res.get("group", "")
        state = res.get("state", "unknown")
        rtype = res.get("type", "unknown")
        lines.append(f"   • **{sid}** — type: {rtype}, state: {state}, group: {group}")
    if not result:
        lines.append("   No HA resources found.")
    return "\n".join(lines)


@confirm_required
async def create_ha_resource(
    client: MultiClient,
    sid: str = "",
    group: Optional[str] = None,
    comment: Optional[str] = None,
    max_relocate: Optional[int] = None,
    max_restart: Optional[int] = None,
    state: Optional[str] = None,
    type: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not sid:
        raise ValueError("sid is required for HA resource creation")
    params: dict[str, Any] = {"sid": sid}
    if group is not None:
        params["group"] = group
    if comment is not None:
        params["comment"] = comment
    if max_relocate is not None:
        params["max_relocate"] = max_relocate
    if max_restart is not None:
        params["max_restart"] = max_restart
    if state is not None:
        params["state"] = state
    if type is not None:
        params["type"] = type
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.ha.resources.post,
        elevated=True,
        **params,
    )
    return f"HA resource {sid!r} created"


async def get_ha_resource(client: MultiClient, sid: str = "", endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    if not sid:
        raise ValueError("sid is required")
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.ha.resources(sid).get,
    )
    lines = [f"🔴 **HA Resource: {sid}**\n"]
    if isinstance(result, dict):
        for key, value in sorted(result.items()):
            lines.append(f"   • {key}: {value}")
    return "\n".join(lines)


@confirm_required
async def update_ha_resource(
    client: MultiClient,
    sid: str = "",
    group: Optional[str] = None,
    comment: Optional[str] = None,
    max_relocate: Optional[int] = None,
    max_restart: Optional[int] = None,
    state: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not sid:
        raise ValueError("sid is required for HA resource update")
    params: dict[str, Any] = {}
    if group is not None:
        params["group"] = group
    if comment is not None:
        params["comment"] = comment
    if max_relocate is not None:
        params["max_relocate"] = max_relocate
    if max_restart is not None:
        params["max_restart"] = max_restart
    if state is not None:
        params["state"] = state
    if not params:
        raise ValueError("At least one parameter must be provided to update")
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.ha.resources(sid).put,
        elevated=True,
        **params,
    )
    opts = ", ".join(f"{k}={v!r}" for k, v in params.items())
    return f"HA resource {sid!r} updated: {opts}"


@confirm_required
async def delete_ha_resource(
    client: MultiClient, sid: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not sid:
        raise ValueError("sid is required for HA resource deletion")
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.ha.resources(sid).delete,
        elevated=True,
    )
    return f"HA resource {sid!r} deleted"


@confirm_required
async def migrate_ha_resource(
    client: MultiClient, sid: str = "", node: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not sid:
        raise ValueError("sid is required")
    if not node:
        raise ValueError("node is required for migration")
    params: dict[str, Any] = {"node": node}
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.ha.resources(sid).migrate.post,
        elevated=True,
        **params,
    )
    return f"HA resource {sid!r} migration to {node!r} initiated"


@confirm_required
async def relocate_ha_resource(
    client: MultiClient, sid: str = "", node: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not sid:
        raise ValueError("sid is required")
    if not node:
        raise ValueError("node is required for relocation")
    params: dict[str, Any] = {"node": node}
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.ha.resources(sid).relocate.post,
        elevated=True,
        **params,
    )
    return f"HA resource {sid!r} relocation to {node!r} initiated"


async def list_ha_groups(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    """List HA groups.

    .. deprecated::
        PVE 9.x has migrated HA groups to HA rules. This endpoint may
        return a 500 error on PVE 9.x clusters. Use :func:`list_ha_rules`
        instead.
    """
    warnings.warn(
        "list_ha_groups is deprecated: PVE 9.x migrated HA groups to rules; use list_ha_rules instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    try:
        result = await client.safe_api_call(
            _api(client, endpoint=ep).cluster.ha.groups.get,
        )
    except ResourceException as exc:
        if exc.status_code == 500 and "migrated to rules" in str(exc):
            return "⚠️ **HA groups have been migrated to rules in PVE 9.x.**\nUse `list_ha_rules` instead."
        raise
    if not isinstance(result, list):
        result = [result] if result else []
    lines = ["🔴 **HA Groups**\n"]
    for grp in result:
        group = grp.get("group", "unknown")
        nodes = grp.get("nodes", "")
        comment = grp.get("comment", "")
        lines.append(f"   • **{group}** — nodes: {nodes}")
        if comment:
            lines.append(f"     {comment}")
    if not result:
        lines.append("   No HA groups found.")
    return "\n".join(lines)


async def ha_status(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.ha.status.current.get,
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = ["🔴 **HA Status**\n"]
    for entry in result:
        etype = entry.get("type", "unknown")
        sid = entry.get("id", entry.get("sid", "unknown"))
        status = entry.get("status", entry.get("state", "unknown"))
        lines.append(f"   • {etype}: {sid} — {status}")
    if not result:
        lines.append("   No HA status available.")
    return "\n".join(lines)


async def list_ha_rules(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.ha.rules.get,
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = ["🔴 **HA Rules**\n"]
    for rule in result:
        rid = rule.get("id", "unknown")
        rtype = rule.get("type", "")
        lines.append(f"   • **{rid}** — type: {rtype}" if rtype else f"   • **{rid}**")
    if not result:
        lines.append("   No HA rules found.")
    return "\n".join(lines)


@confirm_required
async def create_ha_rule(
    client: MultiClient,
    group: str = "",
    comment: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not group:
        raise ValueError("group is required for HA rule creation")
    params: dict[str, Any] = {"group": group}
    if comment is not None:
        params["comment"] = comment
    params.update(kwargs)
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.ha.rules.post,
        elevated=True,
        **params,
    )
    return f"HA rule created for group {group!r}"


async def get_ha_rule(client: MultiClient, rule: str = "", endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    if not rule:
        raise ValueError("rule is required")
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.ha.rules(rule).get,
    )
    lines = [f"🔴 **HA Rule: {rule}**\n"]
    if isinstance(result, dict):
        for key, value in sorted(result.items()):
            lines.append(f"   • {key}: {value}")
    return "\n".join(lines)


@confirm_required
async def update_ha_rule(
    client: MultiClient,
    rule: str = "",
    comment: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not rule:
        raise ValueError("rule is required for HA rule update")
    params: dict[str, Any] = {}
    if comment is not None:
        params["comment"] = comment
    params.update(kwargs)
    if not params:
        raise ValueError("At least one parameter must be provided to update")
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.ha.rules(rule).put,
        elevated=True,
        **params,
    )
    opts = ", ".join(f"{k}={v!r}" for k, v in params.items())
    return f"HA rule {rule!r} updated: {opts}"


@confirm_required
async def delete_ha_rule(
    client: MultiClient, rule: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not rule:
        raise ValueError("rule is required for HA rule deletion")
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.ha.rules(rule).delete,
        elevated=True,
    )
    return f"HA rule {rule!r} deleted"


async def get_ha_group(client: MultiClient, group: str = "", endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    if not group:
        raise ValueError("group is required")
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.ha.groups(group).get,
    )
    lines = [f"🔴 **HA Group: {group}**\n"]
    if isinstance(result, dict):
        for key, value in sorted(result.items()):
            lines.append(f"   • {key}: {value}")
    return "\n".join(lines)


@confirm_required
async def update_ha_group(
    client: MultiClient,
    group: str = "",
    comment: Optional[str] = None,
    nodes: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not group:
        raise ValueError("group is required for HA group update")
    params: dict[str, Any] = {}
    if comment is not None:
        params["comment"] = comment
    if nodes is not None:
        params["nodes"] = nodes
    params.update(kwargs)
    if not params:
        raise ValueError("At least one parameter must be provided to update")
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.ha.groups(group).put,
        elevated=True,
        **params,
    )
    opts = ", ".join(f"{k}={v!r}" for k, v in params.items())
    return f"HA group {group!r} updated: {opts}"


@confirm_required
async def delete_ha_group(
    client: MultiClient, group: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not group:
        raise ValueError("group is required for HA group deletion")
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.ha.groups(group).delete,
        elevated=True,
    )
    return f"HA group {group!r} deleted"


@confirm_required
async def arm_ha(client: MultiClient, confirm: bool = False, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.ha.status("arm-ha").post,
        elevated=True,
    )
    return "HA manager armed"


@confirm_required
async def disarm_ha(client: MultiClient, confirm: bool = False, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.ha.status("disarm-ha").post,
        elevated=True,
    )
    return "HA manager disarmed"


async def ha_manager_status(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.ha.status.manager_status.get,
    )
    lines = ["🔴 **HA Manager Status**\n"]
    if isinstance(result, dict):
        for key, value in sorted(result.items()):
            lines.append(f"   • {key}: {value}")
    else:
        lines.append(str(result))
    return "\n".join(lines)
