from __future__ import annotations

from typing import Any, Optional

from proxmox_mcp.multi_client import MultiClient
from proxmox_mcp.utils import confirm_required, extract_data, extract_upid, validate_node_name


def _api(client: MultiClient, endpoint: str | None = None) -> Any:
    return client.get_client(elevated=False, endpoint=endpoint)


async def cluster_options(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.options.get,
    )
    lines = ["\U0001f527 **Cluster Options**\n"]
    if isinstance(result, dict):
        for key, value in sorted(result.items()):
            lines.append(f"   • {key}: {value}")
    if not isinstance(result, dict) or not result:
        lines.append("   No cluster options found.")
    return "\n".join(lines)


@confirm_required
async def update_cluster_options(
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
        elevated.cluster.options.put,
        elevated=True,
        **kwargs,
    )
    opts = ", ".join(f"{k}={v!r}" for k, v in kwargs.items())
    return f"Cluster options updated: {opts}"


async def list_backup_jobs(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.backup.get,
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = ["\U0001f4be **Backup Jobs**\n"]
    for job in result:
        jobid = job.get("id", "unknown")
        schedule = job.get("schedule", "N/A")
        vmid = job.get("vmid", "N/A")
        storage = job.get("storage", "N/A")
        mode = job.get("mode", "N/A")
        lines.append(f"   • **{jobid}**")
        lines.append(f"     Schedule: {schedule} | VMs: {vmid} | Storage: {storage} | Mode: {mode}")
    if not result:
        lines.append("   No backup jobs found.")
    return "\n".join(lines)


@confirm_required
async def create_backup_job(
    client: MultiClient,
    id: str = "",
    schedule: Optional[str] = None,
    vmid: Optional[str] = None,
    storage: Optional[str] = None,
    mode: Optional[str] = None,
    compress: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not id:
        raise ValueError("id is required for backup job creation")
    params: dict[str, Any] = {"id": id}
    if schedule is not None:
        params["schedule"] = schedule
    if vmid is not None:
        params["vmid"] = vmid
    if storage is not None:
        params["storage"] = storage
    if mode is not None:
        params["mode"] = mode
    if compress is not None:
        params["compress"] = compress
    params.update(kwargs)
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.backup.post,
        elevated=True,
        **params,
    )
    return f"Backup job {id!r} created"


@confirm_required
async def delete_backup_job(
    client: MultiClient, id: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not id:
        raise ValueError("id is required for backup job deletion")
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.backup(id).delete,
        elevated=True,
    )
    return f"Backup job {id!r} deleted"


async def get_backup_job(client: MultiClient, id: str = "", endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    if not id:
        raise ValueError("id is required")
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.backup(id).get,
    )
    lines = [f"\U0001f4be **Backup Job: {id}**\n"]
    if isinstance(result, dict):
        for key, value in sorted(result.items()):
            lines.append(f"   • {key}: {value}")
    return "\n".join(lines)


@confirm_required
async def update_backup_job(
    client: MultiClient,
    id: str = "",
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not id:
        raise ValueError("id is required for backup job update")
    if not kwargs:
        raise ValueError("At least one parameter must be provided to update")
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.backup(id).put,
        elevated=True,
        **kwargs,
    )
    opts = ", ".join(f"{k}={v!r}" for k, v in kwargs.items())
    return f"Backup job {id!r} updated: {opts}"


async def cluster_config(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.config.get,
    )
    lines = ["\u2699\ufe0f **Cluster Config (Corosync)**\n"]
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


async def cluster_config_nodes(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.config.nodes.get,
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = ["\U0001f5a5\ufe0f **Cluster Config Nodes**\n"]
    for entry in result:
        name = entry.get("name", entry.get("node", "unknown"))
        votes = entry.get("votes", "N/A")
        nodeid = entry.get("nodeid", "N/A")
        lines.append(f"   • **{name}** — nodeid: {nodeid}, votes: {votes}")
    if not result:
        lines.append("   No cluster config nodes found.")
    return "\n".join(lines)


async def cluster_config_join(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.config.join.get,
    )
    lines = ["\U0001f517 **Cluster Join Info**\n"]
    if isinstance(result, dict):
        for key, value in sorted(result.items()):
            lines.append(f"   • {key}: {value}")
    return "\n".join(lines)


async def backup_info_not_backed_up(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster("backup-info")("not-backed-up").get,
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = ["\u26a0\ufe0f **Guests Not Backed Up**\n"]
    for entry in result:
        vmid = entry.get("vmid", "unknown")
        name = entry.get("name", "unknown")
        vtype = entry.get("type", "unknown")
        lines.append(f"   • {vmid} ({name}) — type: {vtype}")
    if not result:
        lines.append("   All guests have backups.")
    return "\n".join(lines)


@confirm_required
async def bulk_migrate_guests(
    client: MultiClient,
    vmids: str = "",
    target: str = "",
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not vmids:
        raise ValueError("vmids is required")
    if not target:
        raise ValueError("target node is required")
    validate_node_name(target)
    params: dict[str, Any] = {"vmids": vmids, "target": target}
    params.update(kwargs)
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.cluster("bulk-action").guest.migrate.post,
        elevated=True,
        **params,
    )
    upid = extract_upid(result)
    return f"Bulk migrate initiated: {vmids} → {target}. UPID: {upid}"


@confirm_required
async def bulk_shutdown_guests(
    client: MultiClient,
    vmids: str = "",
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not vmids:
        raise ValueError("vmids is required")
    params: dict[str, Any] = {"vmids": vmids}
    params.update(kwargs)
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.cluster("bulk-action").guest.shutdown.post,
        elevated=True,
        **params,
    )
    upid = extract_upid(result)
    return f"Bulk shutdown initiated: {vmids}. UPID: {upid}"


@confirm_required
async def bulk_start_guests(
    client: MultiClient,
    vmids: str = "",
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not vmids:
        raise ValueError("vmids is required")
    params: dict[str, Any] = {"vmids": vmids}
    params.update(kwargs)
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.cluster("bulk-action").guest.start.post,
        elevated=True,
        **params,
    )
    upid = extract_upid(result)
    return f"Bulk start initiated: {vmids}. UPID: {upid}"


@confirm_required
async def bulk_suspend_guests(
    client: MultiClient,
    vmids: str = "",
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not vmids:
        raise ValueError("vmids is required")
    params: dict[str, Any] = {"vmids": vmids}
    params.update(kwargs)
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.cluster("bulk-action").guest.suspend.post,
        elevated=True,
        **params,
    )
    upid = extract_upid(result)
    return f"Bulk suspend initiated: {vmids}. UPID: {upid}"


async def cluster_config_apiversion(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.config.apiversion.get,
    )
    lines = ["📋 **Cluster API Version**\n"]
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


async def cluster_jobs_index(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.jobs.get,
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = [f"📋 **Cluster Jobs** ({len(result)})\n"]
    for entry in result:
        if isinstance(entry, dict):
            jid = entry.get("id", entry.get("type", "unknown"))
            jtype = entry.get("type", "")
            lines.append(f"   • {jid} ({jtype})" if jtype else f"   • {jid}")
        else:
            lines.append(f"   {entry}")
    if not result:
        lines.append("   No cluster jobs found.")
    return "\n".join(lines)


async def list_realm_sync_jobs(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.jobs("realm-sync").get,
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = [f"🔄 **Realm Sync Jobs** ({len(result)})\n"]
    for entry in result:
        if isinstance(entry, dict):
            jid = entry.get("id", entry.get("type", "unknown"))
            realm = entry.get("realm", "")
            schedule = entry.get("schedule", "N/A")
            lines.append(f"   • {jid} — realm: {realm}, schedule: {schedule}")
        else:
            lines.append(f"   {entry}")
    if not result:
        lines.append("   No realm sync jobs found.")
    return "\n".join(lines)


async def get_realm_sync_job(client: MultiClient, id: str = "", endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    if not id:
        raise ValueError("id is required")
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.jobs("realm-sync")(id).get,
    )
    lines = [f"🔄 **Realm Sync Job: {id}**\n"]
    if isinstance(result, dict):
        for key, value in sorted(result.items()):
            lines.append(f"   • {key}: {value}")
    else:
        lines.append(str(result))
    return "\n".join(lines)


async def api_version(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(
        _api(client, endpoint=ep).version.get,
    )
    lines = ["\U0001f4cb **API Version**\n"]
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


async def cluster_config_totem(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.config.totem.get,
    )
    lines = ["\U0001f527 **Cluster Config Totem**\n"]
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


async def cluster_config_qdevice(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.config.qdevice.get,
    )
    lines = ["\U0001f527 **Cluster QDevice Status**\n"]
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


async def backup_info_index(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster("backup-info").get,
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = ["\U0001f4be **Backup Info Index**\n"]
    for entry in result:
        if isinstance(entry, dict):
            eid = entry.get("id", entry.get("type", "unknown"))
            lines.append(f"   • {eid}")
        else:
            lines.append(f"   {entry}")
    if not result:
        lines.append("   No backup info entries found.")
    return "\n".join(lines)


async def backup_job_included_volumes(client: MultiClient, id: str = "", endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    if not id:
        raise ValueError("id is required")
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.backup(id)("included-volumes").get,
    )
    lines = [f"\U0001f4be **Backup Job Included Volumes: {id}**\n"]
    if isinstance(result, dict):
        data = extract_data(result)
        if isinstance(data, list):
            for entry in data:
                if isinstance(entry, dict):
                    vmid = entry.get("vmid", "unknown")
                    vtype = entry.get("type", "unknown")
                    lines.append(f"   • VM {vmid} ({vtype})")
                else:
                    lines.append(f"   {entry}")
            if not data:
                lines.append("   No included volumes found.")
        elif isinstance(data, dict):
            for key, value in sorted(data.items()):
                lines.append(f"   • {key}: {value}")
        else:
            lines.append(str(data))
    elif isinstance(result, list):
        for entry in result:
            if isinstance(entry, dict):
                vmid = entry.get("vmid", "unknown")
                vtype = entry.get("type", "unknown")
                lines.append(f"   • VM {vmid} ({vtype})")
            else:
                lines.append(f"   {entry}")
        if not result:
            lines.append("   No included volumes found.")
    else:
        lines.append(str(result))
    return "\n".join(lines)


@confirm_required
async def generate_cluster_config(
    client: MultiClient,
    node: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    validate_node_name(node) if node else None
    params: dict[str, Any] = {}
    if node:
        params["node"] = node
    params.update(kwargs)
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.cluster.config.post,
        elevated=True,
        **params,
    )
    upid = extract_upid(result)
    return f"Cluster config generation initiated. UPID: {upid}"


@confirm_required
async def remove_cluster_node(
    client: MultiClient, node: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not node:
        raise ValueError("node is required for cluster node removal")
    validate_node_name(node)
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.config.nodes(node).delete,
        elevated=True,
    )
    return f"Cluster node {node!r} removed"
