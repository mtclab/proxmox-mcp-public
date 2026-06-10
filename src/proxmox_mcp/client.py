from __future__ import annotations

import asyncio
import logging
import re
import ssl
from typing import Any, Optional

from proxmoxer import ProxmoxAPI
from proxmoxer.core import ResourceException
from requests.exceptions import Timeout as RequestsTimeout

from proxmox_mcp.config import Config
from proxmox_mcp.exceptions import (
    ProxmoxConnectionError,
    ProxmoxNodeError,
    ProxmoxNotFoundError,
    ProxmoxPermissionError,
    ProxmoxTaskError,
)


class ResolvedNode:
    def __init__(self, endpoint: str, node: str):
        self.endpoint = endpoint
        self.node = node

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ResolvedNode):
            return NotImplemented
        return self.endpoint == other.endpoint and self.node == other.node

    def __repr__(self) -> str:
        return f"ResolvedNode(endpoint={self.endpoint!r}, node={self.node!r})"


class ResolvedGuest:
    def __init__(self, endpoint: str, node: str, vmid: int):
        self.endpoint = endpoint
        self.node = node
        self.vmid = vmid

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ResolvedGuest):
            return NotImplemented
        return self.endpoint == other.endpoint and self.node == other.node and self.vmid == other.vmid

    def __repr__(self) -> str:
        return f"ResolvedGuest(endpoint={self.endpoint!r}, node={self.node!r}, vmid={self.vmid!r})"


logger = logging.getLogger(__name__)

PVE_UPLOAD_FILE_FIELD = "filename"


class ProxmoxClient:
    def __init__(self, config: Config) -> None:
        self.config = config
        self._nodes_cache: Optional[list[dict[str, Any]]] = None

        monitor_user = config.monitor_token_id.split("!")[0]
        monitor_token_name = config.monitor_token_id.split("!")[1]
        self.monitor_client = ProxmoxAPI(
            config.host,
            port=config.port,
            user=monitor_user,
            token_name=monitor_token_name,
            token_value=config.monitor_token_secret,
            verify_ssl=config.verify,
            backend="https",
            timeout=config.timeout,
        )

        admin_user = config.admin_token_id.split("!")[0]
        admin_token_name = config.admin_token_id.split("!")[1]
        self.admin_client = ProxmoxAPI(
            config.host,
            port=config.port,
            user=admin_user,
            token_name=admin_token_name,
            token_value=config.admin_token_secret,
            verify_ssl=config.verify,
            backend="https",
            timeout=config.timeout,
        )

    def get_client(self, elevated: bool = False) -> ProxmoxAPI:
        if elevated:
            self.raise_if_not_elevated()
            return self.admin_client
        return self.monitor_client

    def raise_if_not_elevated(self) -> None:
        if not self.config.allow_elevated:
            raise ValueError(
                "Elevated operations are not allowed. Set PROXMOX_ALLOW_ELEVATED=true to enable admin-level operations."
            )

    _NOT_FOUND_PATTERNS = (
        "does not exist",
        "no such",
        "not found",
        "404 Not Found",
        "VM/CT does not exist",
        "config file does not exist",
    )

    @classmethod
    def _is_not_found_500(cls, exc: ResourceException) -> bool:
        if exc.status_code != 500:
            return False
        content = str(getattr(exc, "content", "") or "")
        return any(pat in content for pat in cls._NOT_FOUND_PATTERNS)

    @classmethod
    def _extract_resource_from_500(cls, exc: ResourceException) -> tuple[str, str | None]:
        content = str(getattr(exc, "content", "") or "")
        vmid = None
        node = None
        path_match = re.search(r"'(nodes/[^']+)'", content)
        if path_match:
            segments = path_match.group(1).split("/")
            if len(segments) >= 2:
                node = segments[1]
            fname = segments[-1] if segments else ""
            vmid = fname.replace(".conf", "")
        resource = f"Guest {vmid}" if vmid else "Resource"
        return resource, node

    async def retry_with_backoff(
        self,
        func,
        *args,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        elevated: bool = False,
        **kwargs,
    ) -> Any:
        delay = initial_delay
        last_exc: Exception | None = None
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except ResourceException as exc:
                last_exc = exc
                if exc.status_code == 595:
                    if attempt < max_retries:
                        logger.warning(
                            "PVE 595 error on attempt %d/%d, retrying in %.1fs: %s",
                            attempt + 1,
                            max_retries,
                            delay,
                            exc,
                        )
                        await asyncio.sleep(delay)
                        delay *= 2
                        continue
                    logger.error("PVE 595 error persisted after %d retries: %s", max_retries, exc)
                    raise ProxmoxConnectionError(f"PVE 595 error after {max_retries} retries: {exc}") from exc
                if exc.status_code == 403:
                    endpoint = getattr(exc, "content", "") or ""
                    if elevated:
                        raise ProxmoxPermissionError(
                            f"Permission denied on {endpoint} — "
                            "the admin token lacks the required PVE privilege for this operation."
                        ) from exc
                    raise ProxmoxPermissionError(
                        f"Permission denied on {endpoint} — "
                        "this operation requires elevated mode. "
                        "Set PROXMOX_ALLOW_ELEVATED=true and use an admin token "
                        "with appropriate PVE permissions."
                    ) from exc
                if self._is_not_found_500(exc):
                    resource, node = self._extract_resource_from_500(exc)
                    raise ProxmoxNotFoundError(resource, node) from exc
                raise
            except ssl.SSLCertVerificationError as exc:
                raise ProxmoxConnectionError(
                    "SSL certificate verification failed. "
                    "Set PROXMOX_VERIFY=false or provide CA path with PROXMOX_VERIFY=/path/to/ca.pem"
                ) from exc
        raise ProxmoxConnectionError(f"PVE 595 error after {max_retries} retries: {last_exc}")

    MAX_API_TIMEOUT = 300.0

    async def safe_api_call(
        self,
        func,
        *args,
        elevated: bool = False,
        timeout: float | None = None,
        **kwargs,
    ) -> Any:
        if timeout is not None:
            kwargs["timeout"] = min(timeout, self.MAX_API_TIMEOUT)
        try:
            return await self.retry_with_backoff(func, *args, elevated=elevated, **kwargs)
        except ProxmoxNodeError:
            raise
        except ProxmoxNotFoundError:
            raise
        except ProxmoxConnectionError as exc:
            original = exc.__cause__
            if isinstance(original, ResourceException) and original.status_code == 595:
                endpoint = str(getattr(original, "content", ""))
                if "/nodes/" in endpoint:
                    node_name = endpoint.split("/nodes/")[1].split("/")[0]
                    raise ProxmoxNodeError(
                        node_name,
                        "Run proxmox-list-nodes to discover available node names. "
                        "Gotcha: PVE node name may differ from hostname.",
                    ) from exc
            raise
        except ProxmoxPermissionError:
            raise
        except ProxmoxTaskError:
            raise
        except ResourceException as exc:
            if exc.status_code == 404:
                raise ProxmoxNotFoundError("Resource") from exc
            if self._is_not_found_500(exc):
                resource, node = self._extract_resource_from_500(exc)
                raise ProxmoxNotFoundError(resource, node) from exc
            raise
        except RequestsTimeout as exc:
            raise ProxmoxConnectionError(f"PVE API request timed out: {exc}") from exc

    async def wait_for_task(
        self,
        upid: str,
        elevated: bool = False,
        poll_interval: float = 1.0,
        timeout: float = 300.0,
    ) -> dict[str, Any]:
        client = self.get_client(elevated)
        elapsed = 0.0
        while elapsed < timeout:
            try:
                result = client.nodes(upid.split(":")[1]).tasks(upid).status.get()
            except ResourceException as exc:
                if exc.status_code == 595:
                    await asyncio.sleep(poll_interval)
                    elapsed += poll_interval
                    continue
                raise
            status = result.get("status", "") if isinstance(result, dict) else ""
            if status == "stopped":
                exitstatus = result.get("exitstatus", "OK") if isinstance(result, dict) else "OK"
                if exitstatus != "OK":
                    raise ProxmoxTaskError(exitstatus, str(result))
                return result
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
        raise ProxmoxTaskError("TIMEOUT", f"Task {upid} did not complete within {timeout}s")

    async def discover_nodes(self) -> list[dict[str, Any]]:
        if self._nodes_cache is not None:
            return self._nodes_cache

        result = await self.safe_api_call(self.monitor_client.nodes.get)
        self._nodes_cache = list(result) if isinstance(result, list) else [result]
        return self._nodes_cache

    async def resolve_node(self, node: Optional[str] = None) -> str:
        if node:
            return node

        if self.config.default_node:
            return self.config.default_node

        nodes = await self.discover_nodes()
        for n in nodes:
            if n.get("status") == "online" or n.get("state") == "online":
                return str(n["node"])

        raise ValueError("No online node found and PROXMOX_DEFAULT_NODE is not set")

    async def resolve_guest(self, identifier: str, node: Optional[str] = None) -> tuple[str, int]:
        resolved_node = await self.resolve_node(node)

        try:
            vmid = int(identifier)
            return resolved_node, vmid
        except ValueError:
            pass

        for vmtype in ("qemu", "lxc"):
            try:
                guests = await self.safe_api_call(
                    self.monitor_client.nodes(resolved_node).__getattr__(vmtype).get,
                )
                if not guests:
                    continue
                for guest in guests:
                    if str(guest.get("name", "")) == identifier:
                        return resolved_node, int(guest["vmid"])
            except (ProxmoxConnectionError, ProxmoxPermissionError):
                continue
            except ResourceException:
                continue
            except Exception:
                logger.warning("Unexpected error searching for guest %r as %s", identifier, vmtype, exc_info=True)
                continue

        raise ValueError(f"Guest {identifier!r} not found on node {resolved_node!r}")

    def upload(
        self,
        node: str,
        storage: str,
        content_type: str,
        file_obj: Any,
        filename: str | None = None,
        elevated: bool = True,
    ) -> Any:
        client = self.get_client(elevated)
        data = {
            "content": content_type,
            "storage": storage,
        }
        if filename:
            data[PVE_UPLOAD_FILE_FIELD] = filename
        return client.nodes(node).storage(storage).upload.post(data=data, files={PVE_UPLOAD_FILE_FIELD: file_obj})
