from __future__ import annotations

import pytest

from proxmox_mcp.discovery import (
    cluster_resources,
    list_bridges,
    list_lxc,
    list_node_lxc,
    list_node_tasks,
    list_node_vms,
    list_nodes,
    list_storage,
    list_tasks,
    list_vms,
    node_index,
    node_status,
    storage_content,
)
from proxmox_mcp.multi_client import MultiClient

pytestmark = pytest.mark.asyncio


class TestDiscovery:
    async def test_list_nodes(self, pve_client: MultiClient):
        result = await list_nodes(pve_client)
        assert isinstance(result, str)
        assert "pve" in result.lower() or "node" in result.lower()

    async def test_node_status(self, pve_client: MultiClient):
        result = await node_status(pve_client, node="pve")
        assert isinstance(result, str)
        assert "cpu" in result.lower() or "uptime" in result.lower()

    async def test_cluster_resources(self, pve_client: MultiClient):
        result = await cluster_resources(pve_client)
        assert isinstance(result, str)

    async def test_cluster_resources_by_type(self, pve_client: MultiClient):
        result = await cluster_resources(pve_client, type="vm")
        assert isinstance(result, str)

    async def test_list_vms(self, pve_client: MultiClient):
        result = await list_vms(pve_client)
        assert isinstance(result, str)

    async def test_list_lxc(self, pve_client: MultiClient):
        result = await list_lxc(pve_client)
        assert isinstance(result, str)

    async def test_list_storage(self, pve_client: MultiClient):
        result = await list_storage(pve_client)
        assert isinstance(result, str)
        assert "local" in result.lower()

    async def test_storage_content(self, pve_client: MultiClient):
        result = await storage_content(pve_client, storage="local")
        assert isinstance(result, str)

    async def test_list_tasks(self, pve_client: MultiClient):
        result = await list_tasks(pve_client, limit=5)
        assert isinstance(result, str)

    async def test_list_bridges(self, pve_client: MultiClient):
        result = await list_bridges(pve_client, node="pve")
        assert isinstance(result, str)

    async def test_node_index(self, pve_client: MultiClient):
        result = await node_index(pve_client, node="pve")
        assert isinstance(result, str)

    async def test_list_node_vms(self, pve_client: MultiClient):
        result = await list_node_vms(pve_client, node="pve")
        assert isinstance(result, str)

    async def test_list_node_lxc(self, pve_client: MultiClient):
        result = await list_node_lxc(pve_client, node="pve")
        assert isinstance(result, str)

    async def test_list_node_tasks(self, pve_client: MultiClient):
        result = await list_node_tasks(pve_client, node="pve", limit=5)
        assert isinstance(result, str)
