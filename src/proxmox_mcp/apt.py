from __future__ import annotations

from typing import Any, Optional

from proxmox_mcp.multi_client import MultiClient
from proxmox_mcp.utils import confirm_required, extract_data, extract_upid, validate_node_name


def _api(client: MultiClient, endpoint: str | None = None) -> Any:
    return client.get_client(elevated=False, endpoint=endpoint)


async def list_updates(client: MultiClient, node: Optional[str] = None, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).apt.update.get,
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = [f"📦 **APT Updates on {resolved_node}**\n"]
    for pkg in result:
        package = pkg.get("Package", pkg.get("package", "unknown"))
        version = pkg.get("Version", pkg.get("version", "N/A"))
        oldver = pkg.get("OldVersion", pkg.get("oldversion", ""))
        description = pkg.get("Description", pkg.get("description", ""))
        lines.append(f"   • **{package}** → {version}")
        if oldver:
            lines.append(f"     From: {oldver}")
        if description and len(description) <= 120:
            lines.append(f"     {description}")
    if not result:
        lines.append("   No updates available.")
    return "\n".join(lines)


@confirm_required
async def refresh_updates(
    client: MultiClient, node: Optional[str] = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.nodes(resolved_node).apt.update.post,
        elevated=True,
    )
    upid = extract_upid(result)
    return f"APT update refresh initiated on {resolved_node}. UPID: {upid}"


async def list_repositories(client: MultiClient, node: Optional[str] = None, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).apt.repositories.get,
    )
    lines = [f"📦 **APT Repositories on {resolved_node}**\n"]
    if isinstance(result, dict):
        data = extract_data(result)
        if isinstance(data, list):
            for repo in data:
                path = repo.get("Path", repo.get("path", "N/A"))
                suite = repo.get("Suite", repo.get("suite", "N/A"))
                components = repo.get("Components", repo.get("components", ""))
                enabled = repo.get("Enabled", repo.get("enabled", True))
                comment = repo.get("Comment", repo.get("comment", ""))
                lines.append(f"   • **{path} {suite}** {'(enabled)' if enabled else '(disabled)'}")
                if components:
                    lines.append(f"     Components: {components}")
                if comment:
                    lines.append(f"     {comment}")
        elif isinstance(data, dict):
            for key, value in sorted(data.items()):
                lines.append(f"   • {key}: {value}")
    elif isinstance(result, list):
        for repo in result:
            path = repo.get("Path", repo.get("path", "N/A"))
            suite = repo.get("Suite", repo.get("suite", "N/A"))
            enabled = repo.get("Enabled", repo.get("enabled", True))
            lines.append(f"   • **{path} {suite}** {'(enabled)' if enabled else '(disabled)'}")
    if len(lines) == 1:
        lines.append("   No repository information available.")
    return "\n".join(lines)


async def list_versions(client: MultiClient, node: Optional[str] = None, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).apt.versions.get,
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = [f"📦 **APT Versions on {resolved_node}**\n"]
    for pkg in result:
        package = pkg.get("Package", pkg.get("package", "unknown"))
        version = pkg.get("Version", pkg.get("version", "N/A"))
        oldver = pkg.get("OldVersion", pkg.get("oldversion", ""))
        origin = pkg.get("Origin", pkg.get("origin", ""))
        lines.append(f"   • **{package}** {version}")
        if origin:
            lines.append(f"     Origin: {origin}")
        if oldver:
            lines.append(f"     Old: {oldver}")
    if not result:
        lines.append("   No version information available.")
    return "\n".join(lines)


@confirm_required
async def add_apt_repo(
    client: MultiClient,
    node: Optional[str] = None,
    path: Optional[str] = None,
    index: Optional[int] = None,
    enabled: Optional[bool] = None,
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
    params: dict[str, Any] = {}
    if path is not None:
        params["path"] = path
    if index is not None:
        params["index"] = index
    if enabled is not None:
        params["enabled"] = 1 if enabled else 0
    params.update(kwargs)
    await client.safe_api_call(
        elevated.nodes(resolved_node).apt.repositories.post,
        elevated=True,
        **params,
    )
    return f"APT repository added on {resolved_node}"


@confirm_required
async def update_apt_repo(
    client: MultiClient,
    node: Optional[str] = None,
    path: Optional[str] = None,
    index: Optional[int] = None,
    enabled: Optional[bool] = None,
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
    params: dict[str, Any] = {}
    if path is not None:
        params["path"] = path
    if index is not None:
        params["index"] = index
    if enabled is not None:
        params["enabled"] = 1 if enabled else 0
    params.update(kwargs)
    await client.safe_api_call(
        elevated.nodes(resolved_node).apt.repositories.put,
        elevated=True,
        **params,
    )
    return f"APT repository updated on {resolved_node}"


async def list_apt_changelog(
    client: MultiClient,
    node: Optional[str] = None,
    name: Optional[str] = None,
    version: Optional[str] = None,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    resolved = await client.resolve_node(node, endpoint=endpoint)
    ep, resolved_node = resolved.endpoint, resolved.node
    validate_node_name(resolved_node)
    params: dict[str, Any] = {}
    if name is not None:
        params["name"] = name
    if version is not None:
        params["version"] = version
    params.update(kwargs)
    result = await client.safe_api_call(
        _api(client, endpoint=ep).nodes(resolved_node).apt.changelog.get,
        **params,
    )
    lines = [f"📦 **APT Changelog on {resolved_node}**\n"]
    if isinstance(result, dict):
        data = extract_data(result)
        if isinstance(data, str):
            for line in data.strip().splitlines()[:100]:
                lines.append(f"   {line}")
        elif isinstance(data, dict):
            for key, value in sorted(data.items()):
                lines.append(f"   • {key}: {value}")
        else:
            lines.append(str(data))
    elif isinstance(result, str):
        for line in result.strip().splitlines()[:100]:
            lines.append(f"   {line}")
    else:
        lines.append(str(result))
    return "\n".join(lines)
