from __future__ import annotations

import logging
import os
from typing import Any, Optional

from proxmox_mcp.exceptions import ProxmoxPermissionError
from proxmox_mcp.multi_client import MultiClient
from proxmox_mcp.utils import (
    confirm_required,
    extract_data,
    extract_upid,
    format_bytes,
    validate_node_name,
    validate_storage_name,
)


def _api(client: MultiClient, endpoint: str | None = None) -> Any:
    return client.get_client(elevated=False, endpoint=endpoint)


async def list_isos(
    client: MultiClient, node: Optional[str] = None, storage: str = "local", endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_storage_name(storage)
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).storage(storage).content.get,
        content="iso",
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = [f"\U0001f4bf **ISOs on {storage} ({resolved_node})**\n"]
    for item in result:
        volid = item.get("volid", "unknown")
        size = item.get("size", 0)
        lines.append(f"   • {volid} — {format_bytes(size) if size else 'N/A'}")
    if not result:
        lines.append("   No ISOs found.")
    return "\n".join(lines)


@confirm_required
async def upload_iso(
    client: MultiClient,
    node: Optional[str] = None,
    storage: str = "local",
    filepath: str = "",
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_storage_name(storage)
    if not filepath:
        raise ValueError("filepath is required for ISO upload")
    allowed_dir = client.config.upload_dir
    if allowed_dir is None:
        logging.warning("PROXMOX_UPLOAD_DIR not set; file path validation is disabled")
    else:
        os.makedirs(allowed_dir, exist_ok=True)
        real_path = os.path.realpath(filepath)
        real_dir = os.path.realpath(allowed_dir)
        if not real_path.startswith(real_dir + os.sep) and real_path != real_dir:
            raise ProxmoxPermissionError(f"filepath {filepath!r} is outside allowed upload directory {allowed_dir!r}")
    filename = os.path.basename(filepath)
    with open(filepath, "rb") as f:
        result = client.upload(
            node=resolved_node,
            storage=storage,
            content_type="iso",
            file_obj=f,
            filename=filename,
            elevated=True,
            endpoint=ep,
        )
    upid = extract_upid(result)
    return f"ISO upload initiated to {resolved_node}/{storage}. UPID: {upid}"


async def get_storage(
    client: MultiClient, storage: str, node: Optional[str] = None, endpoint: str | None = None
) -> str:
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).storage(storage).get,
        elevated=True,
    )
    lines = [f"\U0001f4be **Storage: {storage} on {resolved_node}**\n"]
    if isinstance(result, dict):
        lines.append(f"   • Type: {result.get('type', 'N/A')}")
        lines.append(f"   • Content: {result.get('content', 'N/A')}")
        lines.append(f"   • Path: {result.get('path', 'N/A')}")
        lines.append(f"   • Shared: {result.get('shared', 0)}")
        lines.append(f"   • Active: {result.get('active', 0)}")
        if result.get("nodes"):
            lines.append(f"   • Nodes: {result.get('nodes')}")
    return "\n".join(lines)


@confirm_required
async def create_storage(
    client: MultiClient,
    storage: str,
    type: str = "dir",
    path: Optional[str] = None,
    content: Optional[str] = None,
    nodes: Optional[str] = None,
    server: Optional[str] = None,
    pool: Optional[str] = None,
    monhost: Optional[str] = None,
    fs_name: Optional[str] = None,
    blocksize: Optional[str] = None,
    compression: Optional[str] = None,
    thinpool: Optional[str] = None,
    share: Optional[str] = None,
    subdir: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    data_pool: Optional[str] = None,
    keyring: Optional[str] = None,
    krbd: Optional[bool] = None,
    prefech: Optional[int] = None,
    target: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    validate_storage_name(storage)
    if not type:
        raise ValueError("type is required for storage creation")
    params: dict[str, Any] = {
        "storage": storage,
        "type": type,
    }
    if path is not None:
        params["path"] = path
    if content is not None:
        params["content"] = content
    if nodes is not None:
        params["nodes"] = nodes
    if server is not None:
        params["server"] = server
    if pool is not None:
        params["pool"] = pool
    if monhost is not None:
        params["monhost"] = monhost
    if fs_name is not None:
        params["fs_name"] = fs_name
    if blocksize is not None:
        params["blocksize"] = blocksize
    if compression is not None:
        params["compression"] = compression
    if thinpool is not None:
        params["thinpool"] = thinpool
    if share is not None:
        params["share"] = share
    if subdir is not None:
        params["subdir"] = subdir
    if username is not None:
        params["username"] = username
    if password is not None:
        params["password"] = password
    if data_pool is not None:
        params["data_pool"] = data_pool
    if keyring is not None:
        params["keyring"] = keyring
    if krbd is not None:
        params["krbd"] = 1 if krbd else 0
    if prefech is not None:
        params["prefech"] = prefech
    if target is not None:
        params["target"] = target
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.storage.post,
        elevated=True,
        **params,
    )
    return f"Storage {storage!r} ({type}) created"


@confirm_required
async def update_storage(
    client: MultiClient,
    storage: str,
    content: Optional[str] = None,
    nodes: Optional[str] = None,
    delete: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    validate_storage_name(storage)
    params: dict[str, Any] = {}
    if content is not None:
        params["content"] = content
    if nodes is not None:
        params["nodes"] = nodes
    if delete is not None:
        params["delete"] = delete
    params.update(kwargs)
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.storage(storage).put,
        elevated=True,
        **params,
    )
    return f"Storage {storage!r} updated"


@confirm_required
async def delete_storage(client: MultiClient, storage: str, confirm: bool = False, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    validate_storage_name(storage)
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.storage(storage).delete,
        elevated=True,
    )
    return f"Storage {storage!r} deleted"


@confirm_required
async def delete_volume(
    client: MultiClient,
    node: Optional[str] = None,
    storage: str = "local",
    volume: str = "",
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_storage_name(storage)
    if not volume:
        raise ValueError("volume is required for volume deletion")
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.nodes(resolved_node).storage(storage).content(volume).delete,
        elevated=True,
    )
    return f"Volume {volume!r} deleted from {resolved_node}/{storage}"


@confirm_required
async def prune_backups(
    client: MultiClient,
    node: Optional[str] = None,
    storage: str = "local",
    prune_type: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_storage_name(storage)
    params: dict[str, Any] = {}
    if prune_type is not None:
        params["prune_type"] = prune_type
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).storage(storage).prunebackups.delete,
        elevated=True,
        **params,
    )
    upid = extract_upid(result)
    return f"Backup prune initiated on {resolved_node}/{storage}. UPID: {upid}"


async def storage_status(
    client: MultiClient, node: Optional[str] = None, storage: str = "local", endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_storage_name(storage)
    validate_node_name(resolved_node)
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).storage(storage).status.get,
    )
    lines = [f"\U0001f4be **Storage Status: {storage} on {resolved_node}**\n"]
    if isinstance(result, dict):
        total = result.get("total", 0)
        used = result.get("used", 0)
        avail = result.get("avail", 0)
        lines.append(f"   • Total: {format_bytes(total)}")
        lines.append(f"   • Used: {format_bytes(used)}")
        lines.append(f"   • Available: {format_bytes(avail)}")
        lines.append(f"   • Content: {result.get('content', 'N/A')}")
        lines.append(f"   • Active: {result.get('active', 0)}")
        if total > 0:
            pct = (used / total) * 100
            lines.append(f"   • Usage: {pct:.1f}%")
    return "\n".join(lines)


async def get_volume_info(
    client: MultiClient,
    node: Optional[str] = None,
    storage: str = "local",
    volume: str = "",
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    if not volume:
        raise ValueError("volume is required")
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_storage_name(storage)
    validate_node_name(resolved_node)
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).storage(storage).content(volume).get,
    )
    lines = [f"\U0001f4be **Volume: {volume}**\n"]
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


async def storage_metrics(
    client: MultiClient,
    node: Optional[str] = None,
    storage: str = "local",
    timeframe: str = "hour",
    cf: str = "AVERAGE",
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_storage_name(storage)
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).storage(storage).rrddata.get,
        timeframe=timeframe,
        cf=cf,
    )
    if not isinstance(result, list):
        return f"No metrics data available for storage {storage} on {resolved_node}"
    lines = [f"📈 **Storage Metrics: {storage} on {resolved_node}** ({timeframe})\n"]
    lines.append(f"   {len(result)} data points available")
    return "\n".join(lines)


async def storage_identity(
    client: MultiClient, node: Optional[str] = None, storage: str = "local", endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_storage_name(storage)
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).storage(storage).identity.get,
    )
    lines = [f"💾 **Storage Identity: {storage} on {resolved_node}**\n"]
    if isinstance(result, dict):
        for key, value in sorted(result.items()):
            lines.append(f"   • {key}: {value}")
    else:
        lines.append(str(result))
    return "\n".join(lines)


@confirm_required
async def allocate_disk(
    client: MultiClient,
    node: Optional[str] = None,
    storage: str = "local",
    vmid: Optional[int] = None,
    filename: Optional[str] = None,
    size: str = "1G",
    format: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_storage_name(storage)
    params: dict[str, Any] = {"size": size}
    if vmid is not None:
        params["vmid"] = vmid
    if filename is not None:
        params["filename"] = filename
    if format is not None:
        params["format"] = format
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).storage(storage).content.post,
        elevated=True,
        **params,
    )
    upid = extract_upid(result)
    return f"Disk allocation initiated on {resolved_node}/{storage}. UPID: {upid}"


async def get_storage_on_node(
    client: MultiClient, node: Optional[str] = None, storage: str = "local", endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_storage_name(storage)
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).storage(storage).get,
        elevated=True,
    )
    lines = [f"💾 **Storage Detail: {storage} on {resolved_node}**\n"]
    if isinstance(result, dict):
        for key, value in sorted(result.items()):
            lines.append(f"   • {key}: {value}")
    else:
        lines.append(str(result))
    return "\n".join(lines)


@confirm_required
async def copy_volume(
    client: MultiClient,
    node: Optional[str] = None,
    storage: str = "local",
    volume: str = "",
    target: str = "",
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_storage_name(storage)
    if not volume:
        raise ValueError("volume is required")
    if not target:
        raise ValueError("target is required")
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).storage(storage).content(volume).post,
        elevated=True,
        target=target,
    )
    upid = extract_upid(result)
    return f"Volume {volume!r} copy to {target} initiated on {resolved_node}/{storage}. UPID: {upid}"


@confirm_required
async def update_volume_attributes(
    client: MultiClient,
    node: Optional[str] = None,
    storage: str = "local",
    volume: str = "",
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_storage_name(storage)
    if not volume:
        raise ValueError("volume is required")
    if not kwargs:
        raise ValueError("At least one attribute must be provided to update")
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.nodes(resolved_node).storage(storage).content(volume).put,
        elevated=True,
        **kwargs,
    )
    opts = ", ".join(f"{k}={v!r}" for k, v in kwargs.items())
    return f"Volume {volume!r} attributes updated on {resolved_node}/{storage}: {opts}"


async def file_restore_list(
    client: MultiClient, node: Optional[str] = None, storage: str = "local", endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_storage_name(storage)
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).storage(storage)("file-restore").list.get,
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = [f"📂 **File Restore List: {storage} on {resolved_node}**\n"]
    for entry in result:
        if isinstance(entry, dict):
            name = entry.get("filename", entry.get("path", "unknown"))
            ftype = entry.get("type", "?")
            size = entry.get("size", "")
            line = f"   • {name} ({ftype})"
            if size:
                line += f" — {format_bytes(size) if isinstance(size, int) else size}"
            lines.append(line)
        else:
            lines.append(f"   {entry}")
    if not result:
        lines.append("   No file restore entries found.")
    return "\n".join(lines)


async def file_restore_download(
    client: MultiClient,
    node: Optional[str] = None,
    storage: str = "local",
    filepath: str = "",
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_storage_name(storage)
    if not filepath:
        raise ValueError("filepath is required")
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).storage(storage)("file-restore").download.get,
        filepath=filepath,
    )
    lines = [f"📥 **File Restore Download: {filepath}**\n"]
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


async def storage_import_metadata(
    client: MultiClient,
    node: Optional[str] = None,
    storage: str = "local",
    volume: str = "",
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_storage_name(storage)
    if not volume:
        raise ValueError("volume is required for import metadata")
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).storage(storage).content(volume).importmetadata.get,
    )
    lines = [f"📦 **Storage Import Metadata: {storage} on {resolved_node}**\n"]
    if isinstance(result, list):
        for entry in result:
            if isinstance(entry, dict):
                name = entry.get("filename", entry.get("name", "unknown"))
                lines.append(f"   • {name}")
            else:
                lines.append(f"   {entry}")
        if not result:
            lines.append("   No import metadata found.")
    elif isinstance(result, dict):
        data = extract_data(result)
        if isinstance(data, list):
            for entry in data:
                if isinstance(entry, dict):
                    name = entry.get("filename", entry.get("name", "unknown"))
                    lines.append(f"   • {name}")
                else:
                    lines.append(f"   {entry}")
            if not data:
                lines.append("   No import metadata found.")
        elif isinstance(data, dict):
            for key, value in sorted(data.items()):
                lines.append(f"   • {key}: {value}")
        else:
            lines.append(str(data))
    else:
        lines.append(str(result))
    return "\n".join(lines)


@confirm_required
async def oci_registry_pull(
    client: MultiClient,
    node: Optional[str] = None,
    storage: str = "local",
    image: str = "",
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    validate_storage_name(storage)
    if not image:
        raise ValueError("image is required")
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).storage(storage)("oci-registry-pull").post,
        elevated=True,
        image=image,
    )
    upid = extract_upid(result)
    return f"OCI registry pull of {image!r} initiated on {resolved_node}/{storage}. UPID: {upid}"


async def node_storage_list(client: MultiClient, node: Optional[str] = None, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    from proxmox_mcp.utils import validate_node_name

    resolved = await client.resolve_node(node, endpoint=endpoint)

    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).storage.get,
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = [f"\U0001f4be **Storage on {resolved_node}**\n"]
    for entry in result:
        sname = entry.get("storage", "unknown")
        stype = entry.get("type", "unknown")
        active = "\U0001f7e2" if entry.get("active", 0) else "\U0001f534"
        lines.append(f"   {active} **{sname}** ({stype})")
    if not result:
        lines.append("   No storage found on this node.")
    return "\n".join(lines)
