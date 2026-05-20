from __future__ import annotations

import pytest

from proxmox_mcp.cluster import (
    cluster_config,
    cluster_config_nodes,
    cluster_options,
)
from proxmox_mcp.discovery import (
    cluster_log,
    cluster_status,
    node_time,
    node_version,
)
from proxmox_mcp.multi_client import MultiClient
from proxmox_mcp.nodes import (
    get_node_detailed_status,
    list_services,
    node_config,
    node_dns,
)

pytestmark = pytest.mark.asyncio


class TestCluster:
    async def test_cluster_options(self, pve_client: MultiClient):
        result = await cluster_options(pve_client)
        assert isinstance(result, str)

    async def test_cluster_status(self, pve_client: MultiClient):
        result = await cluster_status(pve_client)
        assert isinstance(result, str)

    async def test_cluster_config(self, pve_client: MultiClient):
        result = await cluster_config(pve_client)
        assert isinstance(result, str)

    async def test_cluster_config_nodes(self, pve_client: MultiClient):
        result = await cluster_config_nodes(pve_client)
        assert isinstance(result, str)

    async def test_cluster_log(self, pve_client: MultiClient):
        result = await cluster_log(pve_client, limit=5)
        assert isinstance(result, str)


class TestNodeInfo:
    async def test_node_config(self, pve_client: MultiClient):
        result = await node_config(pve_client, node="pve")
        assert isinstance(result, str)

    async def test_node_dns(self, pve_client: MultiClient):
        result = await node_dns(pve_client, node="pve")
        assert isinstance(result, str)

    async def test_node_time(self, pve_client: MultiClient):
        result = await node_time(pve_client, node="pve")
        assert isinstance(result, str)

    async def test_node_version(self, pve_client: MultiClient):
        result = await node_version(pve_client, node="pve")
        assert isinstance(result, str)
        assert "version" in result.lower()

    async def test_list_services(self, pve_client: MultiClient):
        result = await list_services(pve_client, node="pve")
        assert isinstance(result, str)

    async def test_get_node_detailed_status(self, pve_client: MultiClient):
        result = await get_node_detailed_status(pve_client, node="pve")
        assert isinstance(result, str)
