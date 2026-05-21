from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

import pytest
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

SECRETS_PATH = Path(os.environ.get("PROXMOX_SECRETS", "$HOME/.config/opencode/secrets/proxmox.json"))

if not SECRETS_PATH.exists() and not os.environ.get("PROXMOX_URL"):
    pytest.skip("No live Proxmox server available (set PROXMOX_URL or provide secrets file)", allow_module_level=True)


def _load_secrets() -> dict[str, str]:
    if SECRETS_PATH.exists():
        with open(SECRETS_PATH) as f:
            return json.load(f)
    raise FileNotFoundError(f"Proxmox secrets not found at {SECRETS_PATH}")


def _make_env() -> dict[str, str]:
    secrets = _load_secrets()
    env = dict(os.environ)
    env["PROXMOX_URL"] = secrets.get("PVE_URL", secrets.get("PROXMOX_URL", "https://pve.example.local:8006"))
    env["PROXMOX_MONITOR_TOKEN_ID"] = secrets.get("PVE_MONITOR_TOKEN_ID", secrets.get("PROXMOX_MONITOR_TOKEN_ID", ""))
    env["PROXMOX_MONITOR_TOKEN_SECRET"] = secrets.get(
        "PVE_MONITOR_TOKEN_SECRET", secrets.get("PROXMOX_MONITOR_TOKEN_SECRET", "")
    )
    env["PROXMOX_ADMIN_TOKEN_ID"] = secrets.get("PVE_ADMIN_TOKEN_ID", secrets.get("PROXMOX_ADMIN_TOKEN_ID", ""))
    env["PROXMOX_ADMIN_TOKEN_SECRET"] = secrets.get(
        "PVE_ADMIN_TOKEN_SECRET", secrets.get("PROXMOX_ADMIN_TOKEN_SECRET", "")
    )
    env["PROXMOX_ALLOW_ELEVATED"] = "true"
    env["PROXMOX_DEFAULT_NODE"] = secrets.get("PVE_NODE", secrets.get("PROXMOX_DEFAULT_NODE", "pve"))
    env["PROXMOX_VERIFY"] = "false"
    return env


def _server_params() -> StdioServerParameters:
    venv_bin = str(Path(__file__).parent.parent / ".venv" / "bin" / "homepilot-proxmox-mcp")
    return StdioServerParameters(command=venv_bin, args=[], env=_make_env())


pytestmark = pytest.mark.asyncio


async def _call_tool(tool_name: str, args: dict | None = None) -> str:
    async with stdio_client(_server_params()) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, args or {})
            return result.content[0].text


async def _list_tools() -> list:
    async with stdio_client(_server_params()) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            return result.tools


class TestMCPServerStartup:
    async def test_server_lists_tools(self):
        tools = await _list_tools()
        assert len(tools) > 100, f"Expected 100+ tools, got {len(tools)}"
        tool_names = [t.name for t in tools]
        assert "proxmox_list_nodes" in tool_names
        assert "proxmox_node_status" in tool_names
        assert "proxmox_create_vm" in tool_names
        assert "proxmox_delete_vm" in tool_names


class TestMCPServerReadOnly:
    async def test_list_nodes(self):
        text = await _call_tool("proxmox_list_nodes", {})
        assert "pve" in text.lower() or "node" in text.lower()

    async def test_node_status(self):
        text = await _call_tool("proxmox_node_status", {"node": "pve"})
        assert "cpu" in text.lower() or "uptime" in text.lower()

    async def test_list_vms(self):
        text = await _call_tool("proxmox_list_vms", {})
        assert isinstance(text, str) and len(text) > 0

    async def test_list_lxc(self):
        text = await _call_tool("proxmox_list_lxc", {})
        assert isinstance(text, str) and len(text) > 0

    async def test_list_storage(self):
        text = await _call_tool("proxmox_list_storage", {})
        assert "local" in text.lower()

    async def test_cluster_status(self):
        text = await _call_tool("proxmox_cluster_status", {})
        assert isinstance(text, str) and len(text) > 0

    async def test_list_acl(self):
        text = await _call_tool("proxmox_list_acl", {})
        assert isinstance(text, str) and len(text) > 0

    async def test_list_network(self):
        text = await _call_tool("proxmox_list_network", {"node": "pve"})
        assert isinstance(text, str) and len(text) > 0

    async def test_list_disks(self):
        text = await _call_tool("proxmox_list_disks", {"node": "pve"})
        assert isinstance(text, str) and len(text) > 0


class TestMCPServerElevatedGuard:
    async def test_create_vm_requires_confirm(self):
        text = await _call_tool(
            "proxmox_create_vm",
            {"node": "pve", "name": "test-no-confirm", "cores": 1, "memory": 512},
        )
        assert "confirm" in text.lower() or "requires" in text.lower()

    async def test_delete_vm_requires_confirm(self):
        text = await _call_tool("proxmox_delete_vm", {"node": "pve", "vmid": 999})
        assert "confirm" in text.lower() or "requires" in text.lower()

    async def test_create_lxc_requires_confirm(self):
        text = await _call_tool(
            "proxmox_create_lxc",
            {"node": "pve", "hostname": "test-no-confirm"},
        )
        assert "confirm" in text.lower() or "requires" in text.lower()


class TestMCPServerErrorHandling:
    async def test_nonexistent_vm(self):
        text = await _call_tool("proxmox_vm_info", {"node": "pve", "vmid": 99999})
        assert "not found" in text.lower() or "error" in text.lower() or "does not exist" in text.lower()

    async def test_nonexistent_node(self):
        text = await _call_tool("proxmox_node_status", {"node": "nonexistent-node"})
        assert (
            "error" in text.lower()
            or "not found" in text.lower()
            or "does not exist" in text.lower()
            or "resolve" in text.lower()
        )


class TestMCPServerLifecycle:
    async def test_lxc_lifecycle_via_mcp(self):
        async with stdio_client(_server_params()) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                create_result = await session.call_tool(
                    "proxmox_create_lxc",
                    {
                        "node": "pve",
                        "hostname": "mcp-test-lxc",
                        "password": "testpass123",
                        "ostemplate": "local:vztmpl/ubuntu-24.04-standard_24.04-2_amd64.tar.zst",
                        "storage": "local-lvm",
                        "cores": 1,
                        "memory": 512,
                        "confirm": True,
                    },
                )
                create_text = create_result.content[0].text
                assert "UPID" in create_text or "created" in create_text.lower()
                vmid = int([w for w in create_text.split() if w.isdigit() and int(w) > 100][0])

                try:
                    await session.call_tool("proxmox_start_lxc", {"node": "pve", "vmid": vmid, "confirm": True})
                    await asyncio.sleep(8)

                    list_result = await session.call_tool("proxmox_list_lxc", {})
                    assert str(vmid) in list_result.content[0].text

                    await session.call_tool("proxmox_shutdown_lxc", {"node": "pve", "vmid": vmid, "confirm": True})
                    await asyncio.sleep(8)

                    await session.call_tool("proxmox_delete_lxc", {"node": "pve", "vmid": vmid, "confirm": True})
                except Exception:
                    try:
                        await session.call_tool("proxmox_stop_lxc", {"node": "pve", "vmid": vmid, "confirm": True})
                        await asyncio.sleep(5)
                        await session.call_tool("proxmox_delete_lxc", {"node": "pve", "vmid": vmid, "confirm": True})
                    except Exception:
                        pass
                    raise

    async def test_vm_lifecycle_via_mcp(self):
        async with stdio_client(_server_params()) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                create_result = await session.call_tool(
                    "proxmox_create_vm",
                    {
                        "node": "pve",
                        "name": "mcp-test-vm",
                        "cores": 1,
                        "memory": 512,
                        "disk_size": "4G",
                        "storage": "local-lvm",
                        "confirm": True,
                    },
                )
                create_text = create_result.content[0].text
                assert "UPID" in create_text or "created" in create_text.lower()
                vmid = int([w for w in create_text.split() if w.isdigit() and int(w) > 100][0])

                try:
                    await session.call_tool("proxmox_start_vm", {"node": "pve", "vmid": vmid, "confirm": True})

                    for _ in range(20):
                        info = await session.call_tool("proxmox_vm_info", {"node": "pve", "vmid": vmid})
                        if "running" in info.content[0].text.lower():
                            break
                        await asyncio.sleep(3)

                    await session.call_tool("proxmox_stop_vm", {"node": "pve", "vmid": vmid, "confirm": True})

                    for _ in range(30):
                        info = await session.call_tool("proxmox_vm_info", {"node": "pve", "vmid": vmid})
                        if "stopped" in info.content[0].text.lower():
                            break
                        await asyncio.sleep(3)

                    await session.call_tool("proxmox_delete_vm", {"node": "pve", "vmid": vmid, "confirm": True})
                except Exception:
                    try:
                        await session.call_tool("proxmox_stop_vm", {"node": "pve", "vmid": vmid, "confirm": True})
                        await asyncio.sleep(15)
                        await session.call_tool("proxmox_delete_vm", {"node": "pve", "vmid": vmid, "confirm": True})
                    except Exception:
                        pass
                    raise
