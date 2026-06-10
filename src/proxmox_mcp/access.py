from __future__ import annotations

from typing import Any

from proxmox_mcp.multi_client import MultiClient
from proxmox_mcp.utils import confirm_required, extract_data, extract_upid


def _api(client: MultiClient, endpoint: str | None = None) -> Any:
    return client.get_client(elevated=False, endpoint=endpoint)


async def list_tfa(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(
        _api(client, endpoint=ep).access.tfa.get,
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = ["\U0001f512 **TFA Entries**\n"]
    for entry in result:
        userid = entry.get("userid", entry.get("id", "?"))
        entry_type = entry.get("type", "?")
        lines.append(f"   • {userid} ({entry_type})")
    if not result:
        lines.append("   No TFA entries found.")
    return "\n".join(lines)


async def get_user_tfa(client: MultiClient, userid: str = "", endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    if not userid:
        raise ValueError("userid is required")
    result = await client.safe_api_call(
        _api(client, endpoint=ep).access.tfa(userid).get,
    )
    lines = [f"\U0001f512 **TFA for {userid}**\n"]
    if isinstance(result, list):
        for entry in result:
            entry_id = entry.get("id", "?")
            entry_type = entry.get("type", "?")
            lines.append(f"   • {entry_id} ({entry_type})")
    elif isinstance(result, dict):
        for key, val in result.items():
            lines.append(f"   • {key}: {val}")
    if not result:
        lines.append("   No TFA entries found.")
    return "\n".join(lines)


@confirm_required
async def add_tfa_entry(
    client: MultiClient,
    userid: str = "",
    type: str = "",
    description: str | None = None,
    value: str | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not userid:
        raise ValueError("userid is required")
    if not type:
        raise ValueError("type is required for TFA entry")
    params: dict[str, Any] = {"type": type}
    if description is not None:
        params["description"] = description
    if value is not None:
        params["value"] = value
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.access.tfa(userid).post,
        elevated=True,
        **params,
    )
    return f"TFA entry added for {userid!r} (type={type!r})"


@confirm_required
async def delete_tfa_entry(
    client: MultiClient, userid: str = "", id: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not userid:
        raise ValueError("userid is required")
    if not id:
        raise ValueError("id is required for TFA entry deletion")
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.access.tfa(userid)(id).delete,
        elevated=True,
    )
    return f"TFA entry {id!r} deleted for {userid!r}"


async def get_tfa_entry(client: MultiClient, userid: str = "", id: str = "", endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    if not userid:
        raise ValueError("userid is required")
    if not id:
        raise ValueError("id is required")
    result = await client.safe_api_call(
        _api(client, endpoint=ep).access.tfa(userid)(id).get,
    )
    lines = [f"\U0001f512 **TFA Entry: {userid}/{id}**\n"]
    if isinstance(result, dict):
        for key, val in result.items():
            lines.append(f"   • {key}: {val}")
    if not result:
        lines.append("   No data returned.")
    return "\n".join(lines)


@confirm_required
async def update_tfa_entry(
    client: MultiClient,
    userid: str = "",
    id: str = "",
    description: str | None = None,
    enable: bool | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not userid:
        raise ValueError("userid is required")
    if not id:
        raise ValueError("id is required for TFA entry update")
    params: dict[str, Any] = {}
    if description is not None:
        params["description"] = description
    if enable is not None:
        params["enable"] = 1 if enable else 0
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.access.tfa(userid)(id).put,
        elevated=True,
        **params,
    )
    return f"TFA entry {id!r} updated for {userid!r}"


@confirm_required
async def unlock_tfa(client: MultiClient, userid: str = "", confirm: bool = False, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not userid:
        raise ValueError("userid is required")
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.access.users(userid)("unlock-tfa").put,
        elevated=True,
    )
    return f"TFA unlocked for {userid!r}"


async def list_domains(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(
        _api(client, endpoint=ep).access.domains.get,
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = ["\U0001f310 **Auth Domains**\n"]
    for domain in result:
        realm = domain.get("realm", "?")
        plugin = domain.get("plugin", domain.get("type", ""))
        lines.append(f"   • **{realm}** — {plugin}")
    if not result:
        lines.append("   No auth domains found.")
    return "\n".join(lines)


async def get_domain(client: MultiClient, realm: str = "", endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    if not realm:
        raise ValueError("realm is required")
    result = await client.safe_api_call(
        _api(client, endpoint=ep).access.domains(realm).get,
    )
    lines = [f"\U0001f310 **Auth Domain: {realm}**\n"]
    if isinstance(result, dict):
        for key, val in sorted(result.items()):
            lines.append(f"   • {key}: {val}")
    if not result:
        lines.append("   No data returned.")
    return "\n".join(lines)


@confirm_required
async def sync_domain(client: MultiClient, realm: str = "", confirm: bool = False, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not realm:
        raise ValueError("realm is required")
    elevated = client.get_client(elevated=True, endpoint=ep)
    result = await client.safe_api_call(
        elevated.access.domains(realm).sync.post,
        elevated=True,
    )
    upid = extract_upid(result)
    return f"Auth domain {realm!r} sync initiated. UPID: {upid}"


@confirm_required
async def create_domain(
    client: MultiClient,
    realm: str = "",
    type: str = "",
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not realm:
        raise ValueError("realm is required for domain creation")
    if not type:
        raise ValueError("type is required for domain creation")
    params: dict[str, Any] = {"realm": realm, "type": type}
    params.update(kwargs)
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.access.domains.post,
        elevated=True,
        **params,
    )
    return f"Auth domain {realm!r} created (type={type!r})"


@confirm_required
async def update_domain(
    client: MultiClient,
    realm: str = "",
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not realm:
        raise ValueError("realm is required for domain update")
    if not kwargs:
        raise ValueError("At least one parameter must be provided to update")
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.access.domains(realm).put,
        elevated=True,
        **kwargs,
    )
    opts = ", ".join(f"{k}={v!r}" for k, v in kwargs.items())
    return f"Auth domain {realm!r} updated: {opts}"


@confirm_required
async def delete_domain(
    client: MultiClient, realm: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not realm:
        raise ValueError("realm is required for domain deletion")
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.access.domains(realm).delete,
        elevated=True,
    )
    return f"Auth domain {realm!r} deleted"


async def get_user_tfa_types(client: MultiClient, userid: str = "", endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    if not userid:
        raise ValueError("userid is required")
    result = await client.safe_api_call(
        _api(client, endpoint=ep).access.users(userid).tfa.get,
    )
    lines = [f"\U0001f512 **TFA Types for {userid}**\n"]
    if isinstance(result, list):
        for entry in result:
            entry_type = entry.get("type", "?")
            lines.append(f"   • {entry_type}")
    elif isinstance(result, dict):
        for key, val in result.items():
            lines.append(f"   • {key}: {val}")
    if not result:
        lines.append("   No TFA types found.")
    return "\n".join(lines)


async def openid_auth_url(client: MultiClient, realm: str = "", endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    if not realm:
        raise ValueError("realm is required")
    result = await client.safe_api_call(
        _api(client, endpoint=ep).access.openid("auth-url").post,
        realm=realm,
    )
    lines = ["\U0001f517 **OpenID Auth URL**\n"]
    if isinstance(result, dict):
        url = extract_data(result)
        if isinstance(url, dict):
            url = url.get("url", "")
        if url:
            lines.append(f"   URL: {url}")
        else:
            for key, val in result.items():
                lines.append(f"   • {key}: {val}")
    else:
        lines.append(f"   {result}")
    return "\n".join(lines)


async def openid_login(
    client: MultiClient, realm: str = "", code: str = "", state: str = "", endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    if not realm:
        raise ValueError("realm is required")
    if not code:
        raise ValueError("code is required for OpenID login")
    params: dict[str, Any] = {"realm": realm, "code": code}
    if state:
        params["state"] = state
    result = await client.safe_api_call(
        _api(client, endpoint=ep).access.openid.login.post,
        **params,
    )
    lines = ["\U0001f511 **OpenID Login**\n"]
    if isinstance(result, dict):
        for key, val in result.items():
            lines.append(f"   • {key}: {val}")
    else:
        lines.append(f"   {result}")
    return "\n".join(lines)


@confirm_required
async def change_password(
    client: MultiClient, userid: str = "", password: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not userid:
        raise ValueError("userid is required")
    if not password:
        raise ValueError("password is required")
    elevated = client.get_client(elevated=True, endpoint=ep)
    params: dict[str, Any] = {"userid": userid, "password": password}
    await client.safe_api_call(
        elevated.access.password.put,
        elevated=True,
        **params,
    )
    return f"Password changed for {userid!r}"


async def create_ticket(
    client: MultiClient, username: str = "", password: str = "", endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    if not username:
        raise ValueError("username is required")
    if not password:
        raise ValueError("password is required")
    params: dict[str, Any] = {"username": username, "password": password}
    result = await client.safe_api_call(
        _api(client, endpoint=ep).access.ticket.post,
        **params,
    )
    lines = ["\U0001f511 **Authentication Ticket**\n"]
    if isinstance(result, dict):
        ticket = extract_data(result)
        if isinstance(ticket, dict):
            for key, value in sorted(ticket.items()):
                lines.append(f"   • {key}: {value}")
        else:
            lines.append(str(ticket))
    else:
        lines.append(str(result))
    return "\n".join(lines)


async def create_vnc_ticket(
    client: MultiClient, port: int | None = None, vnc: str | None = None, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    params: dict[str, Any] = {}
    if port is not None:
        params["port"] = port
    if vnc is not None:
        params["vnc"] = vnc
    result = await client.safe_api_call(
        _api(client, endpoint=ep).access("vncticket").post,
        **params,
    )
    lines = ["\U0001f511 **VNC Ticket**\n"]
    if isinstance(result, dict):
        for key, value in sorted(result.items()):
            lines.append(f"   • {key}: {value}")
    else:
        lines.append(str(result))
    return "\n".join(lines)
