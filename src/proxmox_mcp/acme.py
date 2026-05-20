from __future__ import annotations

from typing import Any, Optional

from proxmox_mcp.multi_client import MultiClient
from proxmox_mcp.utils import confirm_required, extract_data


def _api(client: MultiClient, endpoint: str | None = None) -> Any:
    return client.get_client(elevated=False, endpoint=endpoint)


async def list_acme_accounts(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.acme.account.get,
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = ["\U0001f512 **ACME Accounts**\n"]
    for acct in result:
        name = acct.get("name", acct.get("id", "unknown"))
        contact = acct.get("contact", "")
        directory = acct.get("directory", "")
        lines.append(f"   • **{name}**")
        if contact:
            lines.append(f"     Contact: {contact}")
        if directory:
            lines.append(f"     Directory: {directory}")
    if not result:
        lines.append("   No ACME accounts found.")
    return "\n".join(lines)


async def get_acme_account(client: MultiClient, name: str = "", endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    if not name:
        raise ValueError("name is required")
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.acme.account(name).get,
    )
    lines = [f"\U0001f512 **ACME Account: {name}**\n"]
    if isinstance(result, dict):
        for key, value in sorted(result.items()):
            lines.append(f"   • {key}: {value}")
    return "\n".join(lines)


@confirm_required
async def create_acme_account(
    client: MultiClient,
    name: str = "",
    contact: str = "",
    directory: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not name:
        raise ValueError("name is required for ACME account creation")
    if not contact:
        raise ValueError("contact is required for ACME account creation")
    params: dict[str, Any] = {"name": name, "contact": contact}
    if directory is not None:
        params["directory"] = directory
    params.update(kwargs)
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.acme.account.post,
        elevated=True,
        **params,
    )
    return f"ACME account {name!r} created"


@confirm_required
async def update_acme_plugin(
    client: MultiClient,
    id: str = "",
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not id:
        raise ValueError("id is required for ACME plugin update")
    if not kwargs:
        raise ValueError("At least one parameter must be provided to update")
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.acme.plugins(id).put,
        elevated=True,
        **kwargs,
    )
    opts = ", ".join(f"{k}={v!r}" for k, v in kwargs.items())
    return f"ACME plugin {id!r} updated: {opts}"


async def get_acme_plugin(client: MultiClient, id: str = "", endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    if not id:
        raise ValueError("id is required")
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.acme.plugins(id).get,
    )
    lines = [f"\U0001f50c **ACME Plugin: {id}**\n"]
    if isinstance(result, dict):
        for key, value in sorted(result.items()):
            lines.append(f"   • {key}: {value}")
    return "\n".join(lines)


async def acme_meta(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.acme.meta.get,
    )
    lines = ["\U0001f512 **ACME Meta**\n"]
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
async def delete_acme_account(
    client: MultiClient, name: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not name:
        raise ValueError("name is required for ACME account deletion")
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.acme.account(name).delete,
        elevated=True,
    )
    return f"ACME account {name!r} deleted"


@confirm_required
async def update_acme_account(
    client: MultiClient,
    name: str = "",
    contact: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not name:
        raise ValueError("name is required for ACME account update")
    params: dict[str, Any] = {}
    if contact is not None:
        params["contact"] = contact
    params.update(kwargs)
    if not params:
        raise ValueError("At least one parameter must be provided to update")
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.acme.account(name).put,
        elevated=True,
        **params,
    )
    opts = ", ".join(f"{k}={v!r}" for k, v in params.items())
    return f"ACME account {name!r} updated: {opts}"


async def list_acme_directories(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.acme.directories.get,
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = ["\U0001f4c2 **ACME Directories**\n"]
    for entry in result:
        name = entry.get("name", entry.get("id", "unknown"))
        url = entry.get("url", "")
        lines.append(f"   • **{name}**")
        if url:
            lines.append(f"     URL: {url}")
    if not result:
        lines.append("   No ACME directories found.")
    return "\n".join(lines)


async def list_acme_plugins(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.acme.plugins.get,
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = ["\U0001f50c **ACME Plugins**\n"]
    for plugin in result:
        pid = plugin.get("plugin", plugin.get("id", "unknown"))
        ptype = plugin.get("type", "unknown")
        lines.append(f"   • **{pid}** (type: {ptype})")
    if not result:
        lines.append("   No ACME plugins found.")
    return "\n".join(lines)


@confirm_required
async def create_acme_plugin(
    client: MultiClient,
    id: str = "",
    type: str = "",
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not id:
        raise ValueError("id is required for ACME plugin creation")
    if not type:
        raise ValueError("type is required for ACME plugin creation")
    params: dict[str, Any] = {"id": id, "type": type}
    params.update(kwargs)
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.acme.plugins.post,
        elevated=True,
        **params,
    )
    return f"ACME plugin {id!r} created"


@confirm_required
async def delete_acme_plugin(
    client: MultiClient, id: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not id:
        raise ValueError("id is required for ACME plugin deletion")
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.acme.plugins(id).delete,
        elevated=True,
    )
    return f"ACME plugin {id!r} deleted"


async def get_acme_challenge_schema(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.acme("challenge-schema").get,
    )
    lines = ["\U0001f512 **ACME Challenge Schema**\n"]
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


async def list_acme_tos(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.acme.tos.get,
    )
    lines = ["\U0001f512 **ACME Terms of Service**\n"]
    if isinstance(result, dict):
        data = extract_data(result)
        if isinstance(data, dict):
            for key, value in sorted(data.items()):
                lines.append(f"   • {key}: {value}")
        else:
            lines.append(str(data))
    elif isinstance(result, list):
        for entry in result:
            url = entry.get("url", entry.get("tos", "unknown"))
            lines.append(f"   • {url}")
    else:
        lines.append(str(result))
    return "\n".join(lines)
