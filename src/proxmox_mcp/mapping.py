from __future__ import annotations

from typing import Any, Optional

from proxmox_mcp.multi_client import MultiClient
from proxmox_mcp.utils import confirm_required


def _api(client: MultiClient, endpoint: str | None = None) -> Any:
    return client.get_client(elevated=False, endpoint=endpoint)


async def list_pci_mappings(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.mapping.pci.get,
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = ["🖥️ **PCI Mappings**\n"]
    for mapping in result:
        if isinstance(mapping, str):
            lines.append(f"   • **{mapping}**")
        elif isinstance(mapping, dict):
            mid = mapping.get("id", "unknown")
            mtype = mapping.get("type", "")
            lines.append(f"   • **{mid}**")
            if mtype:
                lines.append(f"     Type: {mtype}")
            description = mapping.get("description", mapping.get("comment", ""))
            if description:
                lines.append(f"     {description}")
    if not result:
        lines.append("   No PCI mappings found.")
    return "\n".join(lines)


@confirm_required
async def create_pci_mapping(
    client: MultiClient,
    id: str = "",
    description: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not id:
        raise ValueError("id is required for PCI mapping creation")
    params: dict[str, Any] = {"id": id}
    if description is not None:
        params["description"] = description
    params.update(kwargs)
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.mapping.pci.post,
        elevated=True,
        **params,
    )
    return f"PCI mapping {id!r} created"


async def get_pci_mapping(client: MultiClient, id: str = "", endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    if not id:
        raise ValueError("id is required")
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.mapping.pci(id).get,
    )
    lines = [f"🖥️ **PCI Mapping: {id}**\n"]
    if isinstance(result, dict):
        for key, value in sorted(result.items()):
            lines.append(f"   • {key}: {value}")
    return "\n".join(lines)


@confirm_required
async def update_pci_mapping(
    client: MultiClient,
    id: str = "",
    description: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not id:
        raise ValueError("id is required for PCI mapping update")
    params: dict[str, Any] = {}
    if description is not None:
        params["description"] = description
    params.update(kwargs)
    if not params:
        raise ValueError("At least one parameter must be provided to update")
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.mapping.pci(id).put,
        elevated=True,
        **params,
    )
    opts = ", ".join(f"{k}={v!r}" for k, v in params.items())
    return f"PCI mapping {id!r} updated: {opts}"


@confirm_required
async def delete_pci_mapping(
    client: MultiClient, id: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not id:
        raise ValueError("id is required for PCI mapping deletion")
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.mapping.pci(id).delete,
        elevated=True,
    )
    return f"PCI mapping {id!r} deleted"


async def list_usb_mappings(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.mapping.usb.get,
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = ["🔌 **USB Mappings**\n"]
    for mapping in result:
        if isinstance(mapping, str):
            lines.append(f"   • **{mapping}**")
        elif isinstance(mapping, dict):
            mid = mapping.get("id", "unknown")
            mtype = mapping.get("type", "")
            lines.append(f"   • **{mid}**")
            if mtype:
                lines.append(f"     Type: {mtype}")
            description = mapping.get("description", mapping.get("comment", ""))
            if description:
                lines.append(f"     {description}")
    if not result:
        lines.append("   No USB mappings found.")
    return "\n".join(lines)


@confirm_required
async def create_usb_mapping(
    client: MultiClient,
    id: str = "",
    description: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not id:
        raise ValueError("id is required for USB mapping creation")
    params: dict[str, Any] = {"id": id}
    if description is not None:
        params["description"] = description
    params.update(kwargs)
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.mapping.usb.post,
        elevated=True,
        **params,
    )
    return f"USB mapping {id!r} created"


async def get_usb_mapping(client: MultiClient, id: str = "", endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    if not id:
        raise ValueError("id is required")
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.mapping.usb(id).get,
    )
    lines = [f"🔌 **USB Mapping: {id}**\n"]
    if isinstance(result, dict):
        for key, value in sorted(result.items()):
            lines.append(f"   • {key}: {value}")
    return "\n".join(lines)


@confirm_required
async def update_usb_mapping(
    client: MultiClient,
    id: str = "",
    description: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not id:
        raise ValueError("id is required for USB mapping update")
    params: dict[str, Any] = {}
    if description is not None:
        params["description"] = description
    params.update(kwargs)
    if not params:
        raise ValueError("At least one parameter must be provided to update")
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.mapping.usb(id).put,
        elevated=True,
        **params,
    )
    opts = ", ".join(f"{k}={v!r}" for k, v in params.items())
    return f"USB mapping {id!r} updated: {opts}"


@confirm_required
async def delete_usb_mapping(
    client: MultiClient, id: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not id:
        raise ValueError("id is required for USB mapping deletion")
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.mapping.usb(id).delete,
        elevated=True,
    )
    return f"USB mapping {id!r} deleted"


async def mapping_index(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.mapping.get,
    )
    type_labels = {"pci": "PCI", "usb": "USB", "dir": "Directory"}
    lines = ["\U0001f4bb **Mapping Index**\n"]
    if isinstance(result, dict):
        for key, entries in sorted(result.items()):
            label = type_labels.get(key, key)
            if isinstance(entries, list):
                for entry in entries:
                    mid = entry.get("id", entry.get("name", "unknown")) if isinstance(entry, dict) else str(entry)
                    description = entry.get("description", entry.get("comment", "")) if isinstance(entry, dict) else ""
                    lines.append(f"   • {mid} ({label})")
                    if description:
                        lines.append(f"     {description}")
            else:
                lines.append(f"   • {entries} ({label})")
    elif isinstance(result, list):
        for entry in result:
            if isinstance(entry, dict):
                mid = entry.get("id", entry.get("name", "unknown"))
                raw_type = entry.get("type", "")
                mtype = type_labels.get(raw_type, raw_type) if raw_type else ""
                description = entry.get("description", entry.get("comment", ""))
                if mtype:
                    lines.append(f"   • {mid} ({mtype})")
                else:
                    lines.append(f"   • {mid}")
                if description:
                    lines.append(f"     {description}")
            else:
                lines.append(f"   • {entry}")
    if not result:
        lines.append("   No mappings found.")
    return "\n".join(lines)


async def list_dir_mappings(client: MultiClient, endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.mapping.dir.get,
    )
    if not isinstance(result, list):
        result = [result] if result else []
    lines = ["\U0001f4c1 **Directory Mappings**\n"]
    for mapping in result:
        if isinstance(mapping, str):
            lines.append(f"   • **{mapping}**")
        elif isinstance(mapping, dict):
            mid = mapping.get("id", "unknown")
            description = mapping.get("description", mapping.get("comment", ""))
            lines.append(f"   • **{mid}**")
            if description:
                lines.append(f"     {description}")
    if not result:
        lines.append("   No directory mappings found.")
    return "\n".join(lines)


async def get_dir_mapping(client: MultiClient, id: str = "", endpoint: str | None = None) -> str:
    ep = endpoint or client.default_endpoint
    if not id:
        raise ValueError("id is required")
    result = await client.safe_api_call(
        _api(client, endpoint=ep).cluster.mapping.dir(id).get,
    )
    lines = [f"\U0001f4c1 **Directory Mapping: {id}**\n"]
    if isinstance(result, dict):
        for key, value in sorted(result.items()):
            lines.append(f"   • {key}: {value}")
    return "\n".join(lines)


@confirm_required
async def create_dir_mapping(
    client: MultiClient,
    id: str = "",
    description: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not id:
        raise ValueError("id is required for directory mapping creation")
    params: dict[str, Any] = {"id": id}
    if description is not None:
        params["description"] = description
    params.update(kwargs)
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.mapping.dir.post,
        elevated=True,
        **params,
    )
    return f"Directory mapping {id!r} created"


@confirm_required
async def update_dir_mapping(
    client: MultiClient,
    id: str = "",
    description: Optional[str] = None,
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: Any,
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not id:
        raise ValueError("id is required for directory mapping update")
    params: dict[str, Any] = {}
    if description is not None:
        params["description"] = description
    params.update(kwargs)
    if not params:
        raise ValueError("At least one parameter must be provided to update")
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.mapping.dir(id).put,
        elevated=True,
        **params,
    )
    opts = ", ".join(f"{k}={v!r}" for k, v in params.items())
    return f"Directory mapping {id!r} updated: {opts}"


@confirm_required
async def delete_dir_mapping(
    client: MultiClient, id: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    ep = endpoint or client.default_endpoint
    client.raise_if_not_elevated()
    if not id:
        raise ValueError("id is required for directory mapping deletion")
    elevated = client.get_client(elevated=True, endpoint=ep)
    await client.safe_api_call(
        elevated.cluster.mapping.dir(id).delete,
        elevated=True,
    )
    return f"Directory mapping {id!r} deleted"
