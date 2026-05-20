from __future__ import annotations

import os

import pytest

from proxmox_mcp.config import Config
from proxmox_mcp.exceptions import ProxmoxPermissionError


def _make_config(
    allowed_commands: list[str] | None = None,
    allowed_monitor_commands: list[str] | None = None,
    allowed_node_commands: list[str] | None = None,
) -> Config:
    return Config(
        url="https://10.0.0.1:8006",
        verify=False,
        monitor_token_id="user@pve!monitor",
        monitor_token_secret="secret",
        admin_token_id="user@pve!admin",
        admin_token_secret="secret",
        allow_elevated=True,
        allowed_commands=allowed_commands,
        allowed_monitor_commands=allowed_monitor_commands,
        allowed_node_commands=allowed_node_commands,
    )


class TestConfigParsing:
    def test_allowed_commands_not_set(self):
        os.environ.pop("PROXMOX_ALLOWED_COMMANDS", None)
        os.environ.pop("PROXMOX_ALLOWED_MONITOR_COMMANDS", None)
        os.environ.pop("PROXMOX_ALLOWED_NODE_COMMANDS", None)
        config = _make_config()
        assert config.allowed_commands is None
        assert config.allowed_monitor_commands is None
        assert config.allowed_node_commands is None

    def test_allowed_commands_empty_string(self):
        config = _make_config(allowed_commands=None)
        assert config.allowed_commands is None

    def test_allowed_commands_populated(self):
        config = _make_config(allowed_commands=["cat", "ls"])
        assert config.allowed_commands == ["cat", "ls"]

    def test_allowed_node_commands_populated(self):
        config = _make_config(allowed_node_commands=["ip", "systemctl"])
        assert config.allowed_node_commands == ["ip", "systemctl"]

    def test_allowed_monitor_commands_populated(self):
        config = _make_config(allowed_monitor_commands=["info", "help"])
        assert config.allowed_monitor_commands == ["info", "help"]

    def test_from_env_parsing(self, monkeypatch):
        monkeypatch.setenv("PROXMOX_URL", "https://10.0.0.1:8006")
        monkeypatch.setenv("PROXMOX_MONITOR_TOKEN_ID", "user@pve!monitor")
        monkeypatch.setenv("PROXMOX_MONITOR_TOKEN_SECRET", "secret")
        monkeypatch.setenv("PROXMOX_ADMIN_TOKEN_ID", "user@pve!admin")
        monkeypatch.setenv("PROXMOX_ADMIN_TOKEN_SECRET", "secret")
        monkeypatch.setenv("PROXMOX_ALLOW_ELEVATED", "true")
        monkeypatch.setenv("PROXMOX_ALLOWED_COMMANDS", "cat,ls,echo")
        monkeypatch.setenv("PROXMOX_ALLOWED_NODE_COMMANDS", "ip,systemctl")
        monkeypatch.setenv("PROXMOX_ALLOWED_MONITOR_COMMANDS", "info,help")

        config = Config.from_env()
        assert config.allowed_commands == ["cat", "ls", "echo"]
        assert config.allowed_node_commands == ["ip", "systemctl"]
        assert config.allowed_monitor_commands == ["info", "help"]

    def test_from_env_not_set(self, monkeypatch):
        monkeypatch.setenv("PROXMOX_URL", "https://10.0.0.1:8006")
        monkeypatch.setenv("PROXMOX_MONITOR_TOKEN_ID", "user@pve!monitor")
        monkeypatch.setenv("PROXMOX_MONITOR_TOKEN_SECRET", "secret")
        monkeypatch.setenv("PROXMOX_ADMIN_TOKEN_ID", "user@pve!admin")
        monkeypatch.setenv("PROXMOX_ADMIN_TOKEN_SECRET", "secret")
        monkeypatch.setenv("PROXMOX_ALLOW_ELEVATED", "true")
        monkeypatch.delenv("PROXMOX_ALLOWED_COMMANDS", raising=False)
        monkeypatch.delenv("PROXMOX_ALLOWED_NODE_COMMANDS", raising=False)
        monkeypatch.delenv("PROXMOX_ALLOWED_MONITOR_COMMANDS", raising=False)

        config = Config.from_env()
        assert config.allowed_commands is None
        assert config.allowed_node_commands is None
        assert config.allowed_monitor_commands is None

    def test_from_env_whitespace_trim(self, monkeypatch):
        monkeypatch.setenv("PROXMOX_URL", "https://10.0.0.1:8006")
        monkeypatch.setenv("PROXMOX_MONITOR_TOKEN_ID", "user@pve!monitor")
        monkeypatch.setenv("PROXMOX_MONITOR_TOKEN_SECRET", "secret")
        monkeypatch.setenv("PROXMOX_ADMIN_TOKEN_ID", "user@pve!admin")
        monkeypatch.setenv("PROXMOX_ADMIN_TOKEN_SECRET", "secret")
        monkeypatch.setenv("PROXMOX_ALLOW_ELEVATED", "true")
        monkeypatch.setenv("PROXMOX_ALLOWED_COMMANDS", " cat , ls , echo ")

        config = Config.from_env()
        assert config.allowed_commands == ["cat", "ls", "echo"]


class TestNodeExecuteAllowlist:
    """Test node_execute command allowlist validation."""

    @pytest.mark.asyncio
    async def test_blocked_when_no_allowlist(self):
        from unittest.mock import AsyncMock, MagicMock

        from proxmox_mcp.nodes import node_execute

        config = _make_config()
        mock_client = MagicMock()
        mock_client.config = config
        mock_client.default_endpoint = "default"
        mock_client.raise_if_not_elevated = MagicMock(
            side_effect=ProxmoxPermissionError("blocked: elevated token required")
        )
        mock_client.resolve_node = AsyncMock(return_value=MagicMock(endpoint="pve", node="pve"))
        with pytest.raises(ProxmoxPermissionError, match="blocked"):
            await node_execute(mock_client, node="pve", commands="rm -rf /", confirm=True)

    @pytest.mark.asyncio
    async def test_blocked_when_empty_list(self):
        from unittest.mock import AsyncMock, MagicMock

        from proxmox_mcp.nodes import node_execute

        config = _make_config(allowed_node_commands=[])
        mock_client = MagicMock()
        mock_client.config = config
        mock_client.default_endpoint = "default"
        mock_client.raise_if_not_elevated = MagicMock()
        mock_client.resolve_node = AsyncMock(return_value=MagicMock(endpoint="pve", node="pve"))
        with pytest.raises(ValueError, match="not in PROXMOX_ALLOWED_NODE_COMMANDS allowlist"):
            await node_execute(mock_client, node="pve", commands="ls", confirm=True)

    @pytest.mark.asyncio
    async def test_blocked_with_nonmatching_prefix(self):
        from unittest.mock import AsyncMock, MagicMock

        from proxmox_mcp.nodes import node_execute

        config = _make_config(allowed_node_commands=["ls", "cat"])
        mock_client = MagicMock()
        mock_client.config = config
        mock_client.default_endpoint = "default"
        mock_client.raise_if_not_elevated = MagicMock()
        mock_client.resolve_node = AsyncMock(return_value=MagicMock(endpoint="pve", node="pve"))
        with pytest.raises(ValueError, match="not in PROXMOX_ALLOWED_NODE_COMMANDS allowlist"):
            await node_execute(mock_client, node="pve", commands="rm -rf /", confirm=True)

    @pytest.mark.asyncio
    async def test_allowed_with_matching_prefix(self):
        from unittest.mock import AsyncMock, MagicMock

        from proxmox_mcp.nodes import node_execute

        config = _make_config(allowed_commands=["ls", "cat"])
        mock_client = MagicMock()
        mock_client.config = config
        mock_client.default_endpoint = "default"
        mock_client.raise_if_not_elevated = MagicMock()
        mock_client.resolve_node = AsyncMock(return_value=MagicMock(endpoint="pve", node="pve"))
        mock_client.get_client = MagicMock(return_value=MagicMock())
        mock_client.safe_api_call = AsyncMock(return_value={"data": {"exitcode": 0}})
        result = await node_execute(mock_client, node="pve", commands="ls /tmp", confirm=True)
        assert "pve" in result

    @pytest.mark.asyncio
    async def test_node_commands_override_general(self):
        from unittest.mock import AsyncMock, MagicMock

        from proxmox_mcp.nodes import node_execute

        config = _make_config(allowed_commands=["ls"], allowed_node_commands=["ip", "systemctl"])
        mock_client = MagicMock()
        mock_client.config = config
        mock_client.default_endpoint = "default"
        mock_client.raise_if_not_elevated = MagicMock()
        mock_client.resolve_node = AsyncMock(return_value=MagicMock(endpoint="pve", node="pve"))
        with pytest.raises(ValueError, match="not in PROXMOX_ALLOWED_NODE_COMMANDS allowlist"):
            await node_execute(mock_client, node="pve", commands="ls", confirm=True)

    @pytest.mark.asyncio
    async def test_node_commands_allows_matching(self):
        from unittest.mock import AsyncMock, MagicMock

        from proxmox_mcp.nodes import node_execute

        config = _make_config(allowed_commands=["ls"], allowed_node_commands=["ip", "systemctl"])
        mock_client = MagicMock()
        mock_client.config = config
        mock_client.default_endpoint = "default"
        mock_client.raise_if_not_elevated = MagicMock()
        mock_client.resolve_node = AsyncMock(return_value=MagicMock(endpoint="pve", node="pve"))
        mock_client.get_client = MagicMock(return_value=MagicMock())
        mock_client.safe_api_call = AsyncMock(return_value={"data": {"exitcode": 0}})
        result = await node_execute(mock_client, node="pve", commands="ip addr", confirm=True)
        assert "pve" in result

    @pytest.mark.asyncio
    async def test_case_insensitive_match(self):
        from unittest.mock import AsyncMock, MagicMock

        from proxmox_mcp.nodes import node_execute

        config = _make_config(allowed_commands=["LS"])
        mock_client = MagicMock()
        mock_client.config = config
        mock_client.default_endpoint = "default"
        mock_client.raise_if_not_elevated = MagicMock()
        mock_client.resolve_node = AsyncMock(return_value=MagicMock(endpoint="pve", node="pve"))
        mock_client.get_client = MagicMock(return_value=MagicMock())
        mock_client.safe_api_call = AsyncMock(return_value={"data": {"exitcode": 0}})
        result = await node_execute(mock_client, node="pve", commands="ls /tmp", confirm=True)
        assert "pve" in result


class TestVmMonitorAllowlist:
    """Test vm_monitor_command allowlist validation."""

    @pytest.mark.asyncio
    async def test_blocked_when_no_allowlist(self):
        from unittest.mock import AsyncMock, MagicMock

        from proxmox_mcp.lifecycle import vm_monitor_command

        config = _make_config()
        mock_client = MagicMock()
        mock_client.config = config
        mock_client.default_endpoint = "default"
        mock_client.raise_if_not_elevated = MagicMock(
            side_effect=ProxmoxPermissionError("blocked: elevated token required")
        )
        mock_client.resolve_node = AsyncMock(return_value=MagicMock(endpoint="pve", node="pve"))
        with pytest.raises(ProxmoxPermissionError, match="blocked"):
            await vm_monitor_command(mock_client, node="pve", vmid=100, command="info", confirm=True)

    @pytest.mark.asyncio
    async def test_blocked_when_empty_list(self):
        from unittest.mock import AsyncMock, MagicMock

        from proxmox_mcp.lifecycle import vm_monitor_command

        config = _make_config(allowed_monitor_commands=[])
        mock_client = MagicMock()
        mock_client.config = config
        mock_client.default_endpoint = "default"
        mock_client.raise_if_not_elevated = MagicMock()
        mock_client.resolve_node = AsyncMock(return_value=MagicMock(endpoint="pve", node="pve"))
        with pytest.raises(ValueError, match="not in PROXMOX_ALLOWED_MONITOR_COMMANDS allowlist"):
            await vm_monitor_command(mock_client, node="pve", vmid=100, command="info", confirm=True)

    @pytest.mark.asyncio
    async def test_monitor_commands_override_general(self):
        config = _make_config(allowed_commands=["ls"], allowed_monitor_commands=["info"])
        assert config.allowed_monitor_commands == ["info"]

    @pytest.mark.asyncio
    async def test_allowed_with_matching_prefix(self):
        from unittest.mock import AsyncMock, MagicMock

        from proxmox_mcp.lifecycle import vm_monitor_command

        config = _make_config(allowed_commands=["info", "help"])
        mock_client = MagicMock()
        mock_client.config = config
        mock_client.default_endpoint = "default"
        mock_client.raise_if_not_elevated = MagicMock()
        mock_client.resolve_node = AsyncMock(return_value=MagicMock(endpoint="pve", node="pve"))
        mock_client.get_client = MagicMock(return_value=MagicMock())
        mock_client.safe_api_call = AsyncMock(return_value={"data": {"result": "ok"}})
        result = await vm_monitor_command(mock_client, node="pve", vmid=100, command="info blockstats", confirm=True)
        assert "100" in result


class TestExecVmAllowlist:
    """Test exec_vm (QEMU guest agent) command allowlist validation."""

    @pytest.mark.asyncio
    async def test_blocked_when_no_allowlist(self):
        from unittest.mock import MagicMock

        from proxmox_mcp.cloudinit import exec_vm

        config = _make_config()
        mock_client = MagicMock()
        mock_client.config = config
        mock_client.default_endpoint = "default"
        mock_client.raise_if_not_elevated = MagicMock(
            side_effect=ProxmoxPermissionError("blocked: elevated token required")
        )
        with pytest.raises(ProxmoxPermissionError, match="blocked"):
            await exec_vm(mock_client, node="pve", vmid=100, command="cat /etc/hosts", confirm=True)

    @pytest.mark.asyncio
    async def test_blocked_when_empty_list(self):
        from unittest.mock import AsyncMock, MagicMock

        from proxmox_mcp.cloudinit import exec_vm

        config = _make_config(allowed_commands=[])
        mock_client = MagicMock()
        mock_client.config = config
        mock_client.default_endpoint = "default"
        mock_client.raise_if_not_elevated = MagicMock()
        mock_client.resolve_node = AsyncMock(return_value=MagicMock(endpoint="pve", node="pve"))
        with pytest.raises(ProxmoxPermissionError, match="not in allowed list"):
            await exec_vm(mock_client, node="pve", vmid=100, command="cat /etc/hosts", confirm=True)

    @pytest.mark.asyncio
    async def test_blocked_with_nonmatching_prefix(self):
        from unittest.mock import AsyncMock, MagicMock

        from proxmox_mcp.cloudinit import exec_vm

        config = _make_config(allowed_commands=["ls"])
        mock_client = MagicMock()
        mock_client.config = config
        mock_client.default_endpoint = "default"
        mock_client.raise_if_not_elevated = MagicMock()
        mock_client.resolve_node = AsyncMock(return_value=MagicMock(endpoint="pve", node="pve"))
        with pytest.raises(ProxmoxPermissionError, match="not in allowed list"):
            await exec_vm(mock_client, node="pve", vmid=100, command="rm -rf /", confirm=True)

    @pytest.mark.asyncio
    async def test_allowed_with_matching_prefix(self):
        from proxmox_mcp.cloudinit import exec_vm

        config = _make_config(allowed_commands=["cat", "ls"])
        from unittest.mock import AsyncMock, MagicMock

        mock_client = MagicMock()
        mock_client.config = config
        mock_client.default_endpoint = "default"
        mock_client.raise_if_not_elevated = MagicMock()
        mock_client.resolve_node = AsyncMock(return_value=MagicMock(endpoint="pve", node="pve"))
        mock_client.get_client = MagicMock(return_value=MagicMock())
        mock_client.safe_api_call = AsyncMock(return_value={"data": {"pid": 42}})
        result = await exec_vm(mock_client, node="pve", vmid=100, command="cat /etc/hosts", confirm=True)
        assert "42" in result
