from __future__ import annotations

import asyncio

import pytest

from proxmox_mcp.discovery import list_lxc, list_vms, lxc_info, vm_info
from proxmox_mcp.lifecycle import (
    create_lxc,
    create_vm,
    delete_lxc,
    delete_vm,
    shutdown_lxc,
    start_lxc,
    start_vm,
    stop_lxc,
    stop_vm,
)
from proxmox_mcp.multi_client import MultiClient

NODE = "pve"


async def wait_for_guest_status(
    client: MultiClient, vmid: int, expected_status: str, is_lxc: bool = False, timeout: int = 60, interval: int = 3
) -> None:
    import asyncio

    for _ in range(timeout // interval):
        try:
            if is_lxc:
                result = await lxc_info(client, node=NODE, vmid=vmid)
            else:
                result = await vm_info(client, node=NODE, vmid=vmid)
            if expected_status.lower() in result.lower():
                return
        except Exception:
            pass
        await asyncio.sleep(interval)
    raise TimeoutError(f"Guest {vmid} did not reach status '{expected_status}' within {timeout}s")


class TestLXCLifecycle:
    _vmid: int = 0

    @pytest.fixture(autouse=True)
    async def cleanup_lxc(self, pve_client: MultiClient):
        yield
        vmid = getattr(self, "_vmid", 0)
        if vmid:
            try:
                await stop_lxc(pve_client, node=NODE, vmid=vmid, confirm=True)
            except Exception:
                pass
            try:
                await delete_lxc(pve_client, node=NODE, vmid=vmid, confirm=True)
            except Exception:
                pass

    async def test_lxc_create_start_stop_delete(self, pve_client: MultiClient):
        result = await create_lxc(
            pve_client,
            node=NODE,
            hostname="mcp-test-lxc",
            password="testpass123",
            ostemplate="local:vztmpl/ubuntu-24.04-standard_24.04-2_amd64.tar.zst",
            storage="local-lvm",
            cores=1,
            memory=512,
            confirm=True,
        )
        assert "UPID" in result, f"Expected UPID in result: {result}"
        vmid = int([w for w in result.split() if w.isdigit() and int(w) > 100][0])
        self._vmid = vmid

        result = await start_lxc(pve_client, node=NODE, vmid=vmid, confirm=True)
        assert isinstance(result, str)

        await wait_for_guest_status(pve_client, vmid, "running", is_lxc=True)

        listing = await list_lxc(pve_client)
        assert str(vmid) in listing

        result = await shutdown_lxc(pve_client, node=NODE, vmid=vmid, confirm=True)
        assert isinstance(result, str)

        await wait_for_guest_status(pve_client, vmid, "stopped", is_lxc=True, timeout=60)

        result = await delete_lxc(pve_client, node=NODE, vmid=vmid, confirm=True)
        assert isinstance(result, str)
        self._vmid = 0  # Prevent cleanup from trying again


class TestVMLifecycle:
    _vmid: int = 0

    @pytest.fixture(autouse=True)
    async def cleanup_vm(self, pve_client: MultiClient):
        yield
        vmid = getattr(self, "_vmid", 0)
        if vmid:
            try:
                await stop_vm(pve_client, node=NODE, vmid=vmid, confirm=True)
            except Exception:
                pass
            await asyncio.sleep(10)
            try:
                await delete_vm(pve_client, node=NODE, vmid=vmid, confirm=True)
            except Exception:
                pass

    async def test_vm_create_start_stop_delete(self, pve_client: MultiClient):
        result = await create_vm(
            pve_client,
            node=NODE,
            name="mcp-test-vm",
            cores=1,
            memory=512,
            disk_size="4G",
            storage="local-lvm",
            confirm=True,
        )
        assert "UPID" in result, f"Expected UPID in result: {result}"
        vmid = int([w for w in result.split() if w.isdigit() and int(w) > 100][0])
        self._vmid = vmid

        result = await start_vm(pve_client, node=NODE, vmid=vmid, confirm=True)
        assert isinstance(result, str)

        await wait_for_guest_status(pve_client, vmid, "running")

        listing = await list_vms(pve_client)
        assert str(vmid) in listing

        result = await stop_vm(pve_client, node=NODE, vmid=vmid, confirm=True)
        assert isinstance(result, str)

        await wait_for_guest_status(pve_client, vmid, "stopped", timeout=90)

        result = await delete_vm(pve_client, node=NODE, vmid=vmid, confirm=True)
        assert isinstance(result, str)
        self._vmid = 0  # Prevent cleanup from trying again
