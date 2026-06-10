from __future__ import annotations

import pytest
from proxmoxer.core import ResourceException

from proxmox_mcp.acme import list_acme_accounts, list_acme_plugins
from proxmox_mcp.backups import list_backups
from proxmox_mcp.ceph import ceph_metadata, ceph_status
from proxmox_mcp.certificates import list_certificates
from proxmox_mcp.exceptions import ProxmoxNotFoundError, ProxmoxPermissionError
from proxmox_mcp.firewall import (
    get_cluster_firewall_options,
    list_cluster_firewall_aliases,
    list_cluster_firewall_ipsets,
    list_cluster_firewall_rules,
)
from proxmox_mcp.ha import ha_status, list_ha_groups, list_ha_resources, list_ha_rules
from proxmox_mcp.metrics import list_metric_servers, metrics_index
from proxmox_mcp.multi_client import MultiClient
from proxmox_mcp.notifications import list_notification_matchers, list_notification_targets
from proxmox_mcp.replication import list_replication
from proxmox_mcp.sdn import list_sdn_controllers, list_sdn_vnets, list_sdn_zones
from proxmox_mcp.templates import list_storage_templates, list_templates

pytestmark = pytest.mark.asyncio


class TestHA:
    async def test_list_ha_resources(self, pve_client: MultiClient):
        result = await list_ha_resources(pve_client)
        assert isinstance(result, str)

    async def test_list_ha_groups(self, pve_client: MultiClient):
        result = await list_ha_groups(pve_client)
        assert isinstance(result, str)

    async def test_ha_status(self, pve_client: MultiClient):
        result = await ha_status(pve_client)
        assert isinstance(result, str)

    async def test_list_ha_rules(self, pve_client: MultiClient):
        result = await list_ha_rules(pve_client)
        assert isinstance(result, str)


class TestBackups:
    async def test_list_backups(self, pve_client: MultiClient):
        result = await list_backups(pve_client, node="pve", storage="local")
        assert isinstance(result, str)


class TestTemplates:
    async def test_list_templates(self, pve_client: MultiClient):
        result = await list_templates(pve_client, node="pve")
        assert isinstance(result, str)

    async def test_list_storage_templates(self, pve_client: MultiClient):
        result = await list_storage_templates(pve_client, node="pve", storage="local")
        assert isinstance(result, str)


class TestMetrics:
    async def test_list_metric_servers(self, pve_client: MultiClient):
        result = await list_metric_servers(pve_client)
        assert isinstance(result, str)

    async def test_metrics_index(self, pve_client: MultiClient):
        result = await metrics_index(pve_client)
        assert isinstance(result, str)


class TestNotifications:
    async def test_list_notification_targets(self, pve_client: MultiClient):
        result = await list_notification_targets(pve_client)
        assert isinstance(result, str)

    async def test_list_notification_matchers(self, pve_client: MultiClient):
        result = await list_notification_matchers(pve_client)
        assert isinstance(result, str)


class TestReplication:
    async def test_list_replication(self, pve_client: MultiClient):
        result = await list_replication(pve_client)
        assert isinstance(result, str)


class TestCeph:
    async def test_ceph_status(self, pve_client: MultiClient):
        try:
            result = await ceph_status(pve_client)
            assert isinstance(result, str)
        except (ProxmoxNotFoundError, ProxmoxPermissionError, ResourceException):
            pytest.skip("Ceph not configured or not accessible on this node")

    async def test_ceph_metadata(self, pve_client: MultiClient):
        try:
            result = await ceph_metadata(pve_client)
            assert isinstance(result, str)
        except (ProxmoxNotFoundError, ProxmoxPermissionError, ResourceException):
            pytest.skip("Ceph not configured or not accessible on this node")


class TestACME:
    async def test_list_acme_accounts(self, pve_client: MultiClient):
        result = await list_acme_accounts(pve_client)
        assert isinstance(result, str)

    async def test_list_acme_plugins(self, pve_client: MultiClient):
        try:
            result = await list_acme_plugins(pve_client)
            assert isinstance(result, str)
        except ProxmoxPermissionError:
            pytest.skip("ACME plugins require elevated permissions")


class TestCertificates:
    async def test_list_certificates(self, pve_client: MultiClient):
        result = await list_certificates(pve_client, node="pve")
        assert isinstance(result, str)


class TestFirewall:
    async def test_list_cluster_firewall_rules(self, pve_client: MultiClient):
        result = await list_cluster_firewall_rules(pve_client)
        assert isinstance(result, str)

    async def test_list_cluster_firewall_aliases(self, pve_client: MultiClient):
        result = await list_cluster_firewall_aliases(pve_client)
        assert isinstance(result, str)

    async def test_list_cluster_firewall_ipsets(self, pve_client: MultiClient):
        result = await list_cluster_firewall_ipsets(pve_client)
        assert isinstance(result, str)

    async def test_get_cluster_firewall_options(self, pve_client: MultiClient):
        result = await get_cluster_firewall_options(pve_client)
        assert isinstance(result, str)


class TestSDN:
    async def test_list_sdn_zones(self, pve_client: MultiClient):
        result = await list_sdn_zones(pve_client)
        assert isinstance(result, str)

    async def test_list_sdn_vnets(self, pve_client: MultiClient):
        result = await list_sdn_vnets(pve_client)
        assert isinstance(result, str)

    async def test_list_sdn_controllers(self, pve_client: MultiClient):
        result = await list_sdn_controllers(pve_client)
        assert isinstance(result, str)
