from __future__ import annotations

from typing import Any, Optional

from proxmox_mcp.multi_client import MultiClient
from proxmox_mcp.utils import confirm_required


def _api(client: MultiClient, endpoint: str | None = None) -> Any:
    return client.get_client(elevated=False, endpoint=endpoint)


async def list_notification_targets(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.notifications.targets.get,
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = ["🔔 **Notification Targets**\n"]
    for target in result:
        name = target.get("name", target.get("id", "unknown"))
        ttype = target.get("type", "unknown")
        comment = target.get("comment", "")
        lines.append(f"   • **{name}** — type: {ttype}")
        if comment:
            lines.append(f"     {comment}")
    if not result:
        lines.append("   No notification targets found.")
    return "\n".join(lines)


async def list_notification_matchers(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.notifications.matchers.get,
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = ["🔔 **Notification Matchers**\n"]
    for matcher in result:
        name = matcher.get("name", "unknown")
        comment = matcher.get("comment", "")
        lines.append(f"   • **{name}**")
        if comment:
            lines.append(f"     {comment}")
    if not result:
        lines.append("   No notification matchers found.")
    return "\n".join(lines)


async def get_notification_matcher(client: MultiClient, name: str = "", endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    if not name:
        raise ValueError("name is required")
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.notifications.matchers(name).get,
    )
    lines = [f"🔔 **Notification Matcher: {name}**\n"]
    if isinstance(result, dict):
        for key, value in sorted(result.items()):
            lines.append(f"   • {key}: {value}")
    return "\n".join(lines)


async def list_sendmail_endpoints(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.notifications.endpoints.sendmail.get,
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = ["📧 **Sendmail Endpoints**\n"]
    for ep in result:
        name = ep.get("name", "unknown")
        comment = ep.get("comment", "")
        lines.append(f"   • **{name}**")
        if comment:
            lines.append(f"     {comment}")
    if not result:
        lines.append("   No sendmail endpoints found.")
    return "\n".join(lines)


@confirm_required
async def create_sendmail_endpoint(
    client: MultiClient,
    name: str = "",
    mailto: Optional[str] = None,
    comment: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not name:
        raise ValueError("name is required for sendmail endpoint creation")
    params: dict[str, Any] = {"name": name}
    if mailto is not None:
        params["mailto"] = mailto
    if comment is not None:
        params["comment"] = comment
    params.update(kwargs)
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.notifications.endpoints.sendmail.post,
        elevated=True,
        **params,
    )
    return f"Sendmail endpoint {name!r} created"


@confirm_required
async def delete_sendmail_endpoint(
    client: MultiClient, name: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not name:
        raise ValueError("name is required for sendmail endpoint deletion")
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.notifications.endpoints.sendmail(name).delete,
        elevated=True,
    )
    return f"Sendmail endpoint {name!r} deleted"


async def list_smtp_endpoints(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.notifications.endpoints.smtp.get,
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = ["📧 **SMTP Endpoints**\n"]
    for ep in result:
        name = ep.get("name", "unknown")
        server = ep.get("server", "N/A")
        comment = ep.get("comment", "")
        lines.append(f"   • **{name}** — server: {server}")
        if comment:
            lines.append(f"     {comment}")
    if not result:
        lines.append("   No SMTP endpoints found.")
    return "\n".join(lines)


@confirm_required
async def create_smtp_endpoint(
    client: MultiClient,
    name: str = "",
    server: Optional[str] = None,
    comment: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not name:
        raise ValueError("name is required for SMTP endpoint creation")
    params: dict[str, Any] = {"name": name}
    if server is not None:
        params["server"] = server
    if comment is not None:
        params["comment"] = comment
    params.update(kwargs)
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.notifications.endpoints.smtp.post,
        elevated=True,
        **params,
    )
    return f"SMTP endpoint {name!r} created"


@confirm_required
async def delete_smtp_endpoint(
    client: MultiClient, name: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not name:
        raise ValueError("name is required for SMTP endpoint deletion")
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.notifications.endpoints.smtp(name).delete,
        elevated=True,
    )
    return f"SMTP endpoint {name!r} deleted"


async def list_gotify_endpoints(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.notifications.endpoints.gotify.get,
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = ["🔔 **Gotify Endpoints**\n"]
    for ep in result:
        name = ep.get("name", "unknown")
        comment = ep.get("comment", "")
        lines.append(f"   • **{name}**")
        if comment:
            lines.append(f"     {comment}")
    if not result:
        lines.append("   No Gotify endpoints found.")
    return "\n".join(lines)


@confirm_required
async def create_gotify_endpoint(
    client: MultiClient,
    name: str = "",
    server: Optional[str] = None,
    token: Optional[str] = None,
    comment: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not name:
        raise ValueError("name is required for Gotify endpoint creation")
    params: dict[str, Any] = {"name": name}
    if server is not None:
        params["server"] = server
    if token is not None:
        params["token"] = token
    if comment is not None:
        params["comment"] = comment
    params.update(kwargs)
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.notifications.endpoints.gotify.post,
        elevated=True,
        **params,
    )
    return f"Gotify endpoint {name!r} created"


@confirm_required
async def delete_gotify_endpoint(
    client: MultiClient, name: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not name:
        raise ValueError("name is required for Gotify endpoint deletion")
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.notifications.endpoints.gotify(name).delete,
        elevated=True,
    )
    return f"Gotify endpoint {name!r} deleted"


async def list_webhook_endpoints(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.notifications.endpoints.webhook.get,
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = ["🔗 **Webhook Endpoints**\n"]
    for ep in result:
        name = ep.get("name", "unknown")
        comment = ep.get("comment", "")
        lines.append(f"   • **{name}**")
        if comment:
            lines.append(f"     {comment}")
    if not result:
        lines.append("   No webhook endpoints found.")
    return "\n".join(lines)


@confirm_required
async def create_webhook_endpoint(
    client: MultiClient,
    name: str = "",
    url: Optional[str] = None,
    comment: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not name:
        raise ValueError("name is required for webhook endpoint creation")
    params: dict[str, Any] = {"name": name}
    if url is not None:
        params["url"] = url
    if comment is not None:
        params["comment"] = comment
    params.update(kwargs)
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.notifications.endpoints.webhook.post,
        elevated=True,
        **params,
    )
    return f"Webhook endpoint {name!r} created"


@confirm_required
async def delete_webhook_endpoint(
    client: MultiClient, name: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not name:
        raise ValueError("name is required for webhook endpoint deletion")
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.notifications.endpoints.webhook(name).delete,
        elevated=True,
    )
    return f"Webhook endpoint {name!r} deleted"


async def notification_index(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.notifications.get,
    )
    lines = ["\U0001f514 **Notification Index**\n"]
    if isinstance(result, dict):
        for key, value in sorted(result.items()):
            lines.append(f"   • {key}: {value}")
    else:
        lines.append(str(result))
    return "\n".join(lines)


async def notification_endpoints_index(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.notifications.endpoints.get,
    )
    lines = ["\U0001f514 **Notification Endpoints Index**\n"]
    if isinstance(result, dict):
        for key, value in sorted(result.items()):
            lines.append(f"   • {key}: {value}")
    else:
        lines.append(str(result))
    return "\n".join(lines)


async def get_notification_target(client: MultiClient, name: str = "", endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    if not name:
        raise ValueError("name is required")
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.notifications.targets(name).get,
    )
    lines = [f"\U0001f514 **Notification Target: {name}**\n"]
    if isinstance(result, dict):
        for key, value in sorted(result.items()):
            lines.append(f"   • {key}: {value}")
    return "\n".join(lines)


@confirm_required
async def test_notification_target(
    client: MultiClient, name: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not name:
        raise ValueError("name is required for notification target test")
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.notifications.targets(name).test.post,
        elevated=True,
    )
    return f"Test notification sent to target {name!r}"


async def notification_matcher_fields(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.notifications("matcher-fields").get,
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = ["\U0001f514 **Notification Matcher Fields**\n"]
    for entry in result:
        if isinstance(entry, dict):
            name = entry.get("name", entry.get("id", "unknown"))
            lines.append(f"   • {name}")
        else:
            lines.append(f"   • {entry}")
    if not result:
        lines.append("   No matcher fields found.")
    return "\n".join(lines)


async def notification_matcher_field_values(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.notifications("matcher-field-values").get,
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = ["\U0001f514 **Notification Matcher Field Values**\n"]
    for entry in result:
        if isinstance(entry, dict):
            name = entry.get("name", entry.get("id", "unknown"))
            lines.append(f"   • {name}")
        else:
            lines.append(f"   • {entry}")
    if not result:
        lines.append("   No matcher field values found.")
    return "\n".join(lines)


@confirm_required
async def create_notification_matcher(
    client: MultiClient,
    name: str = "",
    comment: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not name:
        raise ValueError("name is required for notification matcher creation")
    params: dict[str, Any] = {"name": name}
    if comment is not None:
        params["comment"] = comment
    params.update(kwargs)
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.notifications.matchers.post,
        elevated=True,
        **params,
    )
    return f"Notification matcher {name!r} created"


@confirm_required
async def update_notification_matcher(
    client: MultiClient,
    name: str = "",
    comment: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not name:
        raise ValueError("name is required for notification matcher update")
    params: dict[str, Any] = {}
    if comment is not None:
        params["comment"] = comment
    params.update(kwargs)
    if not params:
        raise ValueError("At least one parameter must be provided to update")
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.notifications.matchers(name).put,
        elevated=True,
        **params,
    )
    opts = ", ".join(f"{k}={v!r}" for k, v in params.items())
    return f"Notification matcher {name!r} updated: {opts}"


@confirm_required
async def delete_notification_matcher(
    client: MultiClient, name: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not name:
        raise ValueError("name is required for notification matcher deletion")
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.notifications.matchers(name).delete,
        elevated=True,
    )
    return f"Notification matcher {name!r} deleted"


async def get_sendmail_endpoint(client: MultiClient, name: str = "", endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    if not name:
        raise ValueError("name is required")
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.notifications.endpoints.sendmail(name).get,
    )
    lines = [f"\U0001f4e7 **Sendmail Endpoint: {name}**\n"]
    if isinstance(result, dict):
        for key, value in sorted(result.items()):
            lines.append(f"   • {key}: {value}")
    return "\n".join(lines)


@confirm_required
async def update_sendmail_endpoint(
    client: MultiClient,
    name: str = "",
    comment: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not name:
        raise ValueError("name is required for sendmail endpoint update")
    params: dict[str, Any] = {}
    if comment is not None:
        params["comment"] = comment
    params.update(kwargs)
    if not params:
        raise ValueError("At least one parameter must be provided to update")
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.notifications.endpoints.sendmail(name).put,
        elevated=True,
        **params,
    )
    opts = ", ".join(f"{k}={v!r}" for k, v in params.items())
    return f"Sendmail endpoint {name!r} updated: {opts}"


async def get_smtp_endpoint(client: MultiClient, name: str = "", endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    if not name:
        raise ValueError("name is required")
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.notifications.endpoints.smtp(name).get,
    )
    lines = [f"\U0001f4e7 **SMTP Endpoint: {name}**\n"]
    if isinstance(result, dict):
        for key, value in sorted(result.items()):
            lines.append(f"   • {key}: {value}")
    return "\n".join(lines)


@confirm_required
async def update_smtp_endpoint(
    client: MultiClient,
    name: str = "",
    comment: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not name:
        raise ValueError("name is required for SMTP endpoint update")
    params: dict[str, Any] = {}
    if comment is not None:
        params["comment"] = comment
    params.update(kwargs)
    if not params:
        raise ValueError("At least one parameter must be provided to update")
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.notifications.endpoints.smtp(name).put,
        elevated=True,
        **params,
    )
    opts = ", ".join(f"{k}={v!r}" for k, v in params.items())
    return f"SMTP endpoint {name!r} updated: {opts}"


async def get_gotify_endpoint(client: MultiClient, name: str = "", endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    if not name:
        raise ValueError("name is required")
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.notifications.endpoints.gotify(name).get,
    )
    lines = [f"\U0001f514 **Gotify Endpoint: {name}**\n"]
    if isinstance(result, dict):
        for key, value in sorted(result.items()):
            lines.append(f"   • {key}: {value}")
    return "\n".join(lines)


@confirm_required
async def update_gotify_endpoint(
    client: MultiClient,
    name: str = "",
    comment: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not name:
        raise ValueError("name is required for Gotify endpoint update")
    params: dict[str, Any] = {}
    if comment is not None:
        params["comment"] = comment
    params.update(kwargs)
    if not params:
        raise ValueError("At least one parameter must be provided to update")
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.notifications.endpoints.gotify(name).put,
        elevated=True,
        **params,
    )
    opts = ", ".join(f"{k}={v!r}" for k, v in params.items())
    return f"Gotify endpoint {name!r} updated: {opts}"


async def get_webhook_endpoint(client: MultiClient, name: str = "", endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    if not name:
        raise ValueError("name is required")
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.notifications.endpoints.webhook(name).get,
    )
    lines = [f"\U0001f517 **Webhook Endpoint: {name}**\n"]
    if isinstance(result, dict):
        for key, value in sorted(result.items()):
            lines.append(f"   • {key}: {value}")
    return "\n".join(lines)


@confirm_required
async def update_webhook_endpoint(
    client: MultiClient,
    name: str = "",
    comment: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not name:
        raise ValueError("name is required for webhook endpoint update")
    params: dict[str, Any] = {}
    if comment is not None:
        params["comment"] = comment
    params.update(kwargs)
    if not params:
        raise ValueError("At least one parameter must be provided to update")
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.notifications.endpoints.webhook(name).put,
        elevated=True,
        **params,
    )
    opts = ", ".join(f"{k}={v!r}" for k, v in params.items())
    return f"Webhook endpoint {name!r} updated: {opts}"
