from __future__ import annotations

import functools
import ipaddress
import re
import socket
from typing import Any, Callable
from urllib.parse import urlparse

from proxmox_mcp.exceptions import ProxmoxPermissionError

_NODE_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9.\-]*$")
_STORAGE_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._\-]*$")
_IFACE_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._:\-]*$")


def confirm_required(func: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        confirm = kwargs.get("confirm", False)
        if isinstance(confirm, str):
            confirm = confirm.lower() in ("true", "1", "yes")
        if not confirm:
            raise ValueError(
                f"Operation {func.__name__!r} requires confirm=true to execute. "
                "This is a destructive operation — pass confirm=true to proceed."
            )
        return await func(*args, **kwargs)

    return wrapper


def resolve_node_for(func: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        if "node" not in kwargs or kwargs["node"] is None:
            from proxmox_mcp.multi_client import MultiClient

            client = kwargs.get("client") or args[0] if args else None
            if isinstance(client, MultiClient):
                kwargs["node"] = await client.resolve_node()
        return await func(*args, **kwargs)

    return wrapper


def format_bytes(value: int | float) -> str:
    if value < 0:
        return f"{value} B"
    for unit in ("B", "KiB", "MiB", "GiB", "TiB", "PiB"):
        if abs(value) < 1024:
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} EiB"


def format_uptime(seconds: int) -> str:
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, secs = divmod(remainder, 60)
    parts: list[str] = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if secs or not parts:
        parts.append(f"{secs}s")
    return " ".join(parts)


def validate_node_name(name: str) -> None:
    if not isinstance(name, str) or not _NODE_RE.match(name):
        raise ValueError(f"Invalid node name: {name!r}")


def validate_vmid(vmid: int | None) -> None:
    if vmid is None:
        return
    if not isinstance(vmid, int) or vmid <= 0:
        raise ValueError(f"Invalid vmid: {vmid!r} — must be a positive integer")


def validate_storage_name(name: str) -> None:
    if not isinstance(name, str) or not _STORAGE_RE.match(name):
        raise ValueError(f"Invalid storage name: {name!r}")


def validate_disk_size(disk_size: int | str) -> str:
    if isinstance(disk_size, int):
        return str(disk_size)
    if isinstance(disk_size, str):
        stripped = disk_size.strip()
        for suffix in ("GiB", "TiB", "G", "T"):
            if stripped.endswith(suffix):
                num = stripped[: -len(suffix)].strip()
                try:
                    val = int(num)
                except ValueError:
                    raise ValueError(f"Invalid disk_size {disk_size!r}: numeric part {num!r} is not an integer")
                if suffix in ("TiB", "T"):
                    val *= 1024
                return str(val)
        try:
            return str(int(stripped))
        except ValueError:
            raise ValueError(
                f"Invalid disk_size {disk_size!r}: expected integer or string like '32G', '1T', '10GiB'. "
                "PVE requires size in integer GiB."
            )
    raise ValueError(f"Invalid disk_size {disk_size!r}: must be int or str")


def validate_iface_name(name: str) -> None:
    if not isinstance(name, str) or not _IFACE_RE.match(name):
        raise ValueError(f"Invalid interface name: {name!r}")


def extract_upid(result: Any) -> str:
    if result is None:
        return "N/A"
    if isinstance(result, str):
        return result if result else "N/A"
    if isinstance(result, dict):
        data = result.get("data", result)
        if data is None or data == "":
            return "N/A"
        return str(data)
    return str(result)


def extract_data(result: Any) -> Any:
    if result is None:
        return None
    if isinstance(result, str):
        return result
    if isinstance(result, dict):
        return result.get("data", result)
    return result


def format_error(exc: Exception) -> str:
    msg = str(exc)
    if hasattr(exc, "response") and hasattr(exc.response, "text"):
        msg = f"{msg}: {exc.response.text}"
    return msg


_PRIVATE_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fd00::/8"),
    ipaddress.ip_network("fe80::/10"),
]


def validate_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ProxmoxPermissionError(f"URL must use https scheme, got {parsed.scheme!r}")
    hostname = parsed.hostname
    if not hostname:
        raise ProxmoxPermissionError("URL must have a hostname")
    try:
        addr = ipaddress.ip_address(hostname)
        for network in _PRIVATE_NETWORKS:
            if addr in network:
                raise ProxmoxPermissionError(f"URL hostname {hostname!r} resolves to a private/internal IP")
    except ValueError:
        pass
    try:
        addr_infos = socket.getaddrinfo(hostname, None)
        for _, _, _, _, addr_tuple in addr_infos:
            ip_str = addr_tuple[0]
            addr = ipaddress.ip_address(ip_str)
            for network in _PRIVATE_NETWORKS:
                if addr in network:
                    raise ProxmoxPermissionError(f"URL hostname {hostname!r} resolves to private/internal IP {ip_str}")
    except socket.gaierror:
        pass
