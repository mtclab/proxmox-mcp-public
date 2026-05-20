from __future__ import annotations

import pytest

from proxmox_mcp.capabilities import (
    list_capabilities,
    list_capabilities_qemu,
    list_cpu_models,
    list_machine_types,
)
from proxmox_mcp.disks import list_disks, list_lvm, list_zfs
from proxmox_mcp.hardware import list_pci, list_usb
from proxmox_mcp.mapping import list_dir_mappings, list_pci_mappings, list_usb_mappings
from proxmox_mcp.multi_client import MultiClient
from proxmox_mcp.networking import list_network
from proxmox_mcp.storage import (
    get_storage,
    list_isos,
    storage_status,
)

pytestmark = pytest.mark.asyncio


class TestStorage:
    async def test_list_isos(self, pve_client: MultiClient):
        result = await list_isos(pve_client, storage="local")
        assert isinstance(result, str)

    async def test_get_storage(self, pve_client: MultiClient):
        result = await get_storage(pve_client, storage="local")
        assert isinstance(result, str)

    async def test_storage_status(self, pve_client: MultiClient):
        result = await storage_status(pve_client, node="pve", storage="local")
        assert isinstance(result, str)


class TestDisks:
    async def test_list_disks(self, pve_client: MultiClient):
        result = await list_disks(pve_client, node="pve")
        assert isinstance(result, str)

    async def test_list_lvm(self, pve_client: MultiClient):
        result = await list_lvm(pve_client, node="pve")
        assert isinstance(result, str)

    async def test_list_zfs(self, pve_client: MultiClient):
        result = await list_zfs(pve_client, node="pve")
        assert isinstance(result, str)


class TestCapabilities:
    async def test_list_cpu_models(self, pve_client: MultiClient):
        result = await list_cpu_models(pve_client, node="pve")
        assert isinstance(result, str)

    async def test_list_machine_types(self, pve_client: MultiClient):
        result = await list_machine_types(pve_client, node="pve")
        assert isinstance(result, str)

    async def test_list_capabilities(self, pve_client: MultiClient):
        result = await list_capabilities(pve_client, node="pve")
        assert isinstance(result, str)

    async def test_list_capabilities_qemu(self, pve_client: MultiClient):
        result = await list_capabilities_qemu(pve_client, node="pve")
        assert isinstance(result, str)


class TestHardware:
    async def test_list_pci(self, pve_client: MultiClient):
        result = await list_pci(pve_client, node="pve")
        assert isinstance(result, str)

    async def test_list_usb(self, pve_client: MultiClient):
        result = await list_usb(pve_client, node="pve")
        assert isinstance(result, str)


class TestMapping:
    async def test_list_pci_mappings(self, pve_client: MultiClient):
        result = await list_pci_mappings(pve_client)
        assert isinstance(result, str)

    async def test_list_usb_mappings(self, pve_client: MultiClient):
        result = await list_usb_mappings(pve_client)
        assert isinstance(result, str)

    async def test_list_dir_mappings(self, pve_client: MultiClient):
        result = await list_dir_mappings(pve_client)
        assert isinstance(result, str)


class TestNetworking:
    async def test_list_network(self, pve_client: MultiClient):
        result = await list_network(pve_client, node="pve")
        assert isinstance(result, str)
