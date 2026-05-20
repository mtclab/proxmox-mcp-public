from __future__ import annotations

import json
import os
import tempfile
from unittest.mock import AsyncMock, patch

import pytest

from proxmox_mcp.config import Config, EndpointConfig, MultiConfig
from proxmox_mcp.exceptions import ProxmoxConnectionError
from proxmox_mcp.multi_client import MultiClient, ResolvedGuest, ResolvedNode


class TestMultiConfigFromEnv:
    def _base_env(self):
        return {
            "PROXMOX_URL": "https://pve.example.local:8006",
            "PROXMOX_MONITOR_TOKEN_ID": "monitor@pve!monitor",
            "PROXMOX_MONITOR_TOKEN_SECRET": "secret-monitor-123",
            "PROXMOX_ADMIN_TOKEN_ID": "admin@pve!admin",
            "PROXMOX_ADMIN_TOKEN_SECRET": "secret-admin-456",
            "PROXMOX_ALLOW_ELEVATED": "true",
        }

    def test_single_node_compat_from_env(self):
        env = self._base_env()
        with patch.dict(os.environ, env, clear=True):
            mc = MultiConfig.from_env()
        assert mc.single_node_compat is True
        assert len(mc.endpoints) == 1
        assert mc.endpoints[0].name == "default"

    def test_single_node_compat_values(self):
        env = self._base_env()
        with patch.dict(os.environ, env, clear=True):
            mc = MultiConfig.from_env()
        ep = mc.endpoints[0]
        assert ep.url == "https://pve.example.local:8006"
        assert ep.monitor_token_id == "monitor@pve!monitor"
        assert ep.monitor_token_secret == "secret-monitor-123"
        assert ep.admin_token_id == "admin@pve!admin"
        assert ep.admin_token_secret == "secret-admin-456"
        assert ep.allow_elevated is True

    def test_multi_endpoint_from_json_env(self):
        data = {
            "verify": False,
            "timeout": 60,
            "endpoints": [
                {
                    "name": "pve1",
                    "url": "https://10.0.0.1:8006",
                    "monitor_token_id": "monitor@pve!mon1",
                    "admin_token_id": "admin@pve!adm1",
                },
                {
                    "name": "pve2",
                    "url": "https://10.0.0.2:8006",
                    "monitor_token_id": "monitor@pve!mon2",
                    "admin_token_id": "admin@pve!adm2",
                },
            ],
        }
        env = {"PROXMOX_ENDPOINTS_JSON": json.dumps(data)}
        with patch.dict(os.environ, env, clear=True):
            mc = MultiConfig.from_env()
        assert len(mc.endpoints) == 2
        assert mc.endpoints[0].name == "pve1"
        assert mc.endpoints[1].name == "pve2"
        assert mc.verify is False
        assert mc.timeout == 60

    def test_duplicate_endpoint_names_raises(self):
        data = {
            "endpoints": [
                {
                    "name": "pve1",
                    "url": "https://10.0.0.1:8006",
                    "monitor_token_id": "m@pve!t1",
                    "admin_token_id": "a@pve!t1",
                },
                {
                    "name": "pve1",
                    "url": "https://10.0.0.2:8006",
                    "monitor_token_id": "m@pve!t2",
                    "admin_token_id": "a@pve!t2",
                },
            ]
        }
        mc = MultiConfig._from_json(data)
        with pytest.raises(ValueError, match="Duplicate endpoint name"):
            mc.validate()

    def test_invalid_url_raises(self):
        data = {
            "endpoints": [
                {
                    "name": "pve1",
                    "url": "http://10.0.0.1:8006",
                    "monitor_token_id": "m@pve!t1",
                    "admin_token_id": "a@pve!t1",
                },
            ]
        }
        mc = MultiConfig._from_json(data)
        with pytest.raises(ValueError, match="must start with https://"):
            mc.validate()

    def test_invalid_token_format_raises(self):
        data = {
            "endpoints": [
                {
                    "name": "pve1",
                    "url": "https://10.0.0.1:8006",
                    "monitor_token_id": "bad-token",
                    "admin_token_id": "a@pve!t1",
                },
            ]
        }
        mc = MultiConfig._from_json(data)
        with pytest.raises(ValueError, match="must match user@realm!tokenid format"):
            mc.validate()

    def test_invalid_endpoint_name_raises(self):
        data = {
            "endpoints": [
                {
                    "name": "my cluster",
                    "url": "https://10.0.0.1:8006",
                    "monitor_token_id": "m@pve!t1",
                    "admin_token_id": "a@pve!t1",
                },
            ]
        }
        mc = MultiConfig._from_json(data)
        with pytest.raises(ValueError, match="name must match"):
            mc.validate()

    def test_file_permission_check(self):
        data = {
            "endpoints": [
                {
                    "name": "pve1",
                    "url": "https://10.0.0.1:8006",
                    "monitor_token_id": "m@pve!t1",
                    "admin_token_id": "a@pve!t1",
                },
            ]
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            f.flush()
            tmp_path = f.name

        os.chmod(tmp_path, 0o644)
        env = {"PROXMOX_ENDPOINTS_FILE": tmp_path}
        try:
            with patch.dict(os.environ, env, clear=True):
                with pytest.raises(ValueError, match="permissive permissions"):
                    MultiConfig.from_env()
        finally:
            os.unlink(tmp_path)

    def test_no_config_raises(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="No Proxmox configuration found"):
                MultiConfig.from_env()


class TestEndpointConfigToConfig:
    def test_to_config_basic(self):
        ep = EndpointConfig(
            name="test1",
            url="https://10.0.0.1:8006",
            verify=False,
            monitor_token_id="monitor@pve!mon",
            monitor_token_secret="s1",
            admin_token_id="admin@pve!adm",
            admin_token_secret="s2",
            allow_elevated=True,
        )
        config = ep.to_config()
        assert isinstance(config, Config)
        assert config.url == "https://10.0.0.1:8006"
        assert config.verify is False
        assert config.monitor_token_id == "monitor@pve!mon"
        assert config.admin_token_id == "admin@pve!adm"
        assert config.allow_elevated is True

    def test_to_config_verify_inherit(self):
        ep = EndpointConfig(
            name="test2",
            url="https://10.0.0.2:8006",
            verify=None,
            monitor_token_id="monitor@pve!mon",
            monitor_token_secret="s1",
            admin_token_id="admin@pve!adm",
            admin_token_secret="s2",
        )
        config = ep.to_config(global_verify="/path/to/ca.pem")
        assert config.verify == "/path/to/ca.pem"

    def test_to_config_verify_explicit(self):
        ep = EndpointConfig(
            name="test3",
            url="https://10.0.0.3:8006",
            verify=False,
            monitor_token_id="monitor@pve!mon",
            monitor_token_secret="s1",
            admin_token_id="admin@pve!adm",
            admin_token_secret="s2",
        )
        config = ep.to_config(global_verify=True)
        assert config.verify is False

    def test_to_config_secrets_from_env(self):
        ep = EndpointConfig(
            name="prod",
            url="https://10.0.0.4:8006",
            monitor_token_id="monitor@pve!mon",
            monitor_token_secret="",
            admin_token_id="admin@pve!adm",
            admin_token_secret="",
        )
        env = {
            "PROXMOX_PROD_MONITOR_SECRET": "env-mon-secret",
            "PROXMOX_PROD_ADMIN_SECRET": "env-adm-secret",
        }
        with patch.dict(os.environ, env, clear=False):
            config = ep.to_config()
        assert config.monitor_token_secret == "env-mon-secret"
        assert config.admin_token_secret == "env-adm-secret"

    def test_to_config_empty_token_falls_back_to_env(self):
        ep = EndpointConfig(
            name="bad",
            url="https://10.0.0.5:8006",
            monitor_token_id="",
            admin_token_id="admin@pve!adm",
        )
        env = {
            "PROXMOX_BAD_MONITOR_TOKEN_ID": "env@pve!fallback",
        }
        with patch.dict(os.environ, env, clear=False):
            config = ep.to_config()
        assert config.monitor_token_id == "env@pve!fallback"

    def test_to_config_empty_token_defaults_to_empty(self):
        ep = EndpointConfig(
            name="bad",
            url="https://10.0.0.5:8006",
            monitor_token_id="",
            admin_token_id="admin@pve!adm",
        )
        config = ep.to_config()
        assert config.monitor_token_id == ""
        assert config.admin_token_id == "admin@pve!adm"


class TestMultiClientResolveNode:
    def _make_config(self, endpoints=None):
        if endpoints is None:
            endpoints = [
                EndpointConfig(
                    name="pve1",
                    url="https://10.0.0.1:8006",
                    monitor_token_id="monitor@pve!mon1",
                    monitor_token_secret="s1",
                    admin_token_id="admin@pve!adm1",
                    admin_token_secret="s2",
                )
            ]
        return MultiConfig(endpoints=endpoints, verify=False)

    async def test_resolve_node_default(self):
        mc = self._make_config()
        client = MultiClient(mc)
        mock_resolve = AsyncMock(return_value="pve")
        client.clients["pve1"].resolve_node = mock_resolve
        result = await client.resolve_node(None)
        assert result == ResolvedNode(endpoint="pve1", node="pve")

    async def test_resolve_node_by_name(self):
        endpoints = [
            EndpointConfig(
                name="ep-alpha",
                url="https://10.0.0.1:8006",
                monitor_token_id="monitor@pve!mon1",
                monitor_token_secret="s1",
                admin_token_id="admin@pve!adm1",
                admin_token_secret="s2",
            )
        ]
        mc = MultiConfig(endpoints=endpoints, verify=False)
        client = MultiClient(mc)
        mock_resolve = AsyncMock(return_value="node-a")
        client.clients["ep-alpha"].resolve_node = mock_resolve
        client._node_to_endpoint["node-a"] = "ep-alpha"
        result = await client.resolve_node("node-a")
        assert result.endpoint == "ep-alpha"
        assert result.node == "node-a"

    async def test_resolve_node_by_endpoint_name(self):
        endpoints = [
            EndpointConfig(
                name="cluster-west",
                url="https://10.0.0.1:8006",
                monitor_token_id="monitor@pve!mon1",
                monitor_token_secret="s1",
                admin_token_id="admin@pve!adm1",
                admin_token_secret="s2",
            )
        ]
        mc = MultiConfig(endpoints=endpoints, verify=False)
        client = MultiClient(mc)
        mock_resolve = AsyncMock(return_value="real-node")
        client.clients["cluster-west"].resolve_node = mock_resolve
        result = await client.resolve_node("cluster-west")
        assert result.endpoint == "cluster-west"
        assert result.node == "real-node"

    async def test_single_node_compat_property(self):
        mc = MultiConfig(
            endpoints=[
                EndpointConfig(
                    name="pve1",
                    url="https://10.0.0.1:8006",
                    monitor_token_id="monitor@pve!mon1",
                    monitor_token_secret="s1",
                    admin_token_id="admin@pve!adm1",
                    admin_token_secret="s2",
                )
            ],
            verify=False,
            single_node_compat=True,
        )
        client = MultiClient(mc)
        assert client.is_single_node is True

    async def test_multi_node_not_single(self):
        endpoints = [
            EndpointConfig(
                name="pve1",
                url="https://10.0.0.1:8006",
                monitor_token_id="monitor@pve!mon1",
                monitor_token_secret="s1",
                admin_token_id="admin@pve!adm1",
                admin_token_secret="s2",
            ),
            EndpointConfig(
                name="pve2",
                url="https://10.0.0.2:8006",
                monitor_token_id="monitor@pve!mon2",
                monitor_token_secret="s3",
                admin_token_id="admin@pve!adm2",
                admin_token_secret="s4",
            ),
        ]
        mc = MultiConfig(endpoints=endpoints, verify=False)
        client = MultiClient(mc)
        assert client.is_single_node is False


class TestMultiClientClusterCall:
    def _make_multi_config(self):
        return MultiConfig(
            endpoints=[
                EndpointConfig(
                    name="pve1",
                    url="https://10.0.0.1:8006",
                    monitor_token_id="monitor@pve!mon1",
                    monitor_token_secret="s1",
                    admin_token_id="admin@pve!adm1",
                    admin_token_secret="s2",
                ),
                EndpointConfig(
                    name="pve2",
                    url="https://10.0.0.2:8006",
                    monitor_token_id="monitor@pve!mon2",
                    monitor_token_secret="s3",
                    admin_token_id="admin@pve!adm2",
                    admin_token_secret="s4",
                ),
            ],
            verify=False,
        )

    async def test_cluster_call_failover_to_secondary(self):
        mc = self._make_multi_config()
        client = MultiClient(mc)
        mock_func = AsyncMock()

        client.clients["pve1"].safe_api_call = AsyncMock(side_effect=ProxmoxConnectionError("pve1 down"))
        client.clients["pve2"].safe_api_call = AsyncMock(return_value={"nodes": []})
        client._healthy = {"pve1": True, "pve2": True}

        result = await client.cluster_call(mock_func)
        assert result == {"nodes": []}
        client.clients["pve1"].safe_api_call.assert_called_once()
        client.clients["pve2"].safe_api_call.assert_called_once()

    async def test_cluster_call_all_endpoints_fail(self):
        mc = self._make_multi_config()
        client = MultiClient(mc)

        client.clients["pve1"].safe_api_call = AsyncMock(side_effect=ProxmoxConnectionError("pve1 down"))
        client.clients["pve2"].safe_api_call = AsyncMock(side_effect=ProxmoxConnectionError("pve2 down"))
        client._healthy = {"pve1": True, "pve2": True}

        with pytest.raises(ProxmoxConnectionError, match="All endpoints unreachable"):
            await client.cluster_call(lambda: None)

    async def test_cluster_call_primary_succeeds(self):
        mc = self._make_multi_config()
        client = MultiClient(mc)

        client.clients["pve1"].safe_api_call = AsyncMock(return_value={"status": "ok"})
        client.clients["pve2"].safe_api_call = AsyncMock(return_value={"status": "ok"})
        client._healthy = {"pve1": True, "pve2": True}

        result = await client.cluster_call(lambda: None)
        assert result == {"status": "ok"}
        client.clients["pve1"].safe_api_call.assert_called_once()
        client.clients["pve2"].safe_api_call.assert_not_called()

    async def test_cluster_call_skips_unhealthy(self):
        mc = self._make_multi_config()
        client = MultiClient(mc)

        client.clients["pve1"].safe_api_call = AsyncMock()
        client.clients["pve2"].safe_api_call = AsyncMock(return_value={"nodes": []})
        client._healthy = {"pve1": False, "pve2": True}

        result = await client.cluster_call(lambda: None)
        assert result == {"nodes": []}
        client.clients["pve1"].safe_api_call.assert_not_called()
        client.clients["pve2"].safe_api_call.assert_called_once()

    async def test_cluster_call_marks_endpoint_unhealthy(self):
        mc = self._make_multi_config()
        client = MultiClient(mc)

        call_count = 0

        async def fake_call(func, *args, elevated=False, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ProxmoxConnectionError("fail")
            return "ok"

        client.clients["pve1"].safe_api_call = fake_call
        client.clients["pve2"].safe_api_call = AsyncMock(return_value="fallback-ok")
        client._healthy = {"pve1": True, "pve2": True}

        result = await client.cluster_call(lambda: None)
        assert result == "fallback-ok"
        assert client._healthy["pve1"] is False


class TestMultiConfigValidate:
    def test_validate_passes_with_good_config(self):
        mc = MultiConfig(
            endpoints=[
                EndpointConfig(
                    name="pve1",
                    url="https://10.0.0.1:8006",
                    monitor_token_id="monitor@pve!mon1",
                    admin_token_id="admin@pve!adm1",
                    monitor_token_secret="s1",
                    admin_token_secret="s2",
                )
            ],
            verify=False,
        )
        mc.validate()

    def test_validate_bad_url(self):
        data = {
            "endpoints": [
                {
                    "name": "pve1",
                    "url": "http://insecure:8006",
                    "monitor_token_id": "m@pve!t1",
                    "admin_token_id": "a@pve!t1",
                }
            ]
        }
        mc = MultiConfig._from_json(data)
        with pytest.raises(ValueError, match="must start with https://"):
            mc.validate()

    def test_validate_bad_token_format(self):
        data = {
            "endpoints": [
                {
                    "name": "pve1",
                    "url": "https://10.0.0.1:8006",
                    "monitor_token_id": "bad-format",
                    "admin_token_id": "a@pve!t1",
                }
            ]
        }
        mc = MultiConfig._from_json(data)
        with pytest.raises(ValueError, match="user@realm!tokenid format"):
            mc.validate()


class TestIsSingleNode:
    def test_single_endpoint_is_single_node(self):
        mc = MultiConfig(
            endpoints=[
                EndpointConfig(
                    name="pve1",
                    url="https://10.0.0.1:8006",
                    monitor_token_id="monitor@pve!mon1",
                    monitor_token_secret="s1",
                    admin_token_id="admin@pve!adm1",
                    admin_token_secret="s2",
                )
            ],
            verify=False,
        )
        client = MultiClient(mc)
        assert client.is_single_node is True

    def test_multi_endpoint_not_single_node(self):
        mc = MultiConfig(
            endpoints=[
                EndpointConfig(
                    name="pve1",
                    url="https://10.0.0.1:8006",
                    monitor_token_id="monitor@pve!mon1",
                    monitor_token_secret="s1",
                    admin_token_id="admin@pve!adm1",
                    admin_token_secret="s2",
                ),
                EndpointConfig(
                    name="pve2",
                    url="https://10.0.0.2:8006",
                    monitor_token_id="monitor@pve!mon2",
                    monitor_token_secret="s3",
                    admin_token_id="admin@pve!adm2",
                    admin_token_secret="s4",
                ),
            ],
            verify=False,
        )
        client = MultiClient(mc)
        assert client.is_single_node is False

    def test_single_node_compat_flag(self):
        mc = MultiConfig(
            endpoints=[
                EndpointConfig(
                    name="pve1",
                    url="https://10.0.0.1:8006",
                    monitor_token_id="monitor@pve!mon1",
                    monitor_token_secret="s1",
                    admin_token_id="admin@pve!adm1",
                    admin_token_secret="s2",
                )
            ],
            verify=False,
            single_node_compat=True,
        )
        client = MultiClient(mc)
        assert client.is_single_node is True


class TestResolvedNodeResolvedGuest:
    def test_resolved_node_fields(self):
        rn = ResolvedNode(endpoint="ep1", node="pve")
        assert rn.endpoint == "ep1"
        assert rn.node == "pve"

    def test_resolved_guest_fields(self):
        rg = ResolvedGuest(endpoint="ep1", node="pve", vmid=100)
        assert rg.endpoint == "ep1"
        assert rg.node == "pve"
        assert rg.vmid == 100
