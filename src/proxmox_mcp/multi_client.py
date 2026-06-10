from __future__ import annotations

import logging
from typing import Any

from proxmox_mcp.client import ProxmoxClient, ResolvedGuest, ResolvedNode
from proxmox_mcp.config import MultiConfig
from proxmox_mcp.exceptions import ProxmoxConnectionError

logger = logging.getLogger(__name__)


class MultiClient:
    """Routes API calls to the correct ProxmoxClient based on endpoint/node context."""

    def __init__(self, config: MultiConfig) -> None:
        self.config = config
        self.clients: dict[str, ProxmoxClient] = {}
        self._healthy: dict[str, bool] = {}
        self._nodes_cache: dict[str, list[dict[str, Any]]] = {}
        self._node_to_endpoint: dict[str, str] = {}

        for ep in config.endpoints:
            single_config = ep.to_config(global_verify=config.verify, global_timeout=config.timeout)
            self.clients[ep.name] = ProxmoxClient(single_config)
            self._healthy[ep.name] = True

        self.default_endpoint = config.endpoints[0].name

    async def initialize(self) -> None:
        await self.health_check()
        for name, client in self.clients.items():
            if self._healthy.get(name):
                try:
                    nodes = await client.discover_nodes()
                    self._nodes_cache[name] = list(nodes) if isinstance(nodes, list) else [nodes]
                    for node_info in self._nodes_cache[name]:
                        node_name = node_info.get("node")
                        if node_name:
                            existing = self._node_to_endpoint.get(node_name)
                            if existing is None:
                                self._node_to_endpoint[node_name] = name
                            elif existing != name and name == self.default_endpoint:
                                self._node_to_endpoint[node_name] = name
                except ProxmoxConnectionError:
                    self._nodes_cache[name] = []

    async def health_check(self) -> dict[str, bool]:
        results = {}
        for name, client in self.clients.items():
            try:
                await client.safe_api_call(client.monitor_client.nodes.get)
                results[name] = True
            except Exception:
                results[name] = False
                logger.warning("Endpoint %r is unreachable", name)
        self._healthy = results
        return results

    @property
    def healthy_endpoints(self) -> list[str]:
        return [n for n, ok in self._healthy.items() if ok] or [self.default_endpoint]

    def get_client(self, elevated: bool = False, endpoint: str | None = None) -> Any:
        ep = endpoint or self.default_endpoint
        return self.clients[ep].get_client(elevated=elevated)

    def _endpoint_for_node(self, node: str) -> str | None:
        return self._node_to_endpoint.get(node)

    async def resolve_node(self, node: str | None = None, endpoint: str | None = None) -> ResolvedNode:
        if node and node in self.clients:
            resolved = await self.clients[node].resolve_node(None)
            return ResolvedNode(endpoint=node, node=resolved)

        if node:
            ep = self._endpoint_for_node(node)
            if ep:
                return ResolvedNode(endpoint=ep, node=node)

        ep = endpoint or self.default_endpoint
        client = self.clients[ep]
        resolved = await client.resolve_node(node)
        return ResolvedNode(endpoint=ep, node=resolved)

    async def resolve_guest(
        self,
        identifier: str,
        node: str | None = None,
        endpoint: str | None = None,
    ) -> ResolvedGuest:
        resolved = await self.resolve_node(node, endpoint)
        client = self.clients[resolved.endpoint]
        _, vmid = await client.resolve_guest(identifier, resolved.node)
        return ResolvedGuest(endpoint=resolved.endpoint, node=resolved.node, vmid=vmid)

    async def safe_api_call(
        self,
        func,
        *args,
        endpoint: str | None = None,
        elevated: bool = False,
        **kwargs,
    ) -> Any:
        ep = endpoint or self.default_endpoint
        return await self.clients[ep].safe_api_call(func, *args, elevated=elevated, **kwargs)

    async def cluster_call(self, api_call_func, *args, elevated: bool = False, **kwargs) -> Any:
        tried = []
        for ep in [self.default_endpoint] + [e for e in self.healthy_endpoints if e != self.default_endpoint]:
            if not self._healthy.get(ep):
                continue
            tried.append(ep)
            try:
                return await self.clients[ep].safe_api_call(api_call_func, *args, elevated=elevated, **kwargs)
            except ProxmoxConnectionError:
                self._healthy[ep] = False
                logger.warning("Endpoint %r failed, trying next", ep)
                continue
        raise ProxmoxConnectionError(f"All endpoints unreachable (tried: {tried})")

    @property
    def is_single_node(self) -> bool:
        return self.config.single_node_compat or len(self.clients) == 1

    def list_endpoints(self) -> str:
        lines = []
        for name, cli in self.clients.items():
            cfg = cli.config
            healthy = name in self._healthy
            default = " (default)" if name == self.default_endpoint else ""
            elevated = "elevated" if cfg.allow_elevated else "monitor-only"
            lines.append(
                f"- {name}: url={cfg.url}, node={cfg.default_node or 'auto'}, "
                f"status={'healthy' if healthy else 'unhealthy'}, "
                f"access={elevated}{default}"
            )
        if self.is_single_node:
            lines.append("\nSingle-node mode (backward compatible)")
        return "\n".join(lines)

    async def wait_for_task(
        self,
        upid: str,
        elevated: bool = False,
        endpoint: str | None = None,
        poll_interval: float = 1.0,
        timeout: float = 300.0,
    ) -> dict[str, Any]:
        ep = endpoint or self.default_endpoint
        return await self.clients[ep].wait_for_task(
            upid, elevated=elevated, poll_interval=poll_interval, timeout=timeout
        )

    def raise_if_not_elevated(self) -> None:
        self.clients[self.default_endpoint].raise_if_not_elevated()

    def upload(
        self,
        node: str,
        storage: str,
        content_type: str,
        file_obj: Any,
        filename: str | None = None,
        elevated: bool = True,
        endpoint: str | None = None,
    ) -> Any:
        ep = endpoint or self.default_endpoint
        return self.clients[ep].upload(node, storage, content_type, file_obj, filename=filename, elevated=elevated)
