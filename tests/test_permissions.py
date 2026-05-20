from __future__ import annotations

import pytest

from proxmox_mcp.access import list_domains, list_tfa
from proxmox_mcp.multi_client import MultiClient
from proxmox_mcp.permissions import (
    check_permissions,
    list_acl,
    list_groups,
    list_roles,
    list_users,
)
from proxmox_mcp.pools import list_pools

pytestmark = pytest.mark.asyncio


class TestPermissions:
    async def test_list_acl(self, pve_client: MultiClient):
        result = await list_acl(pve_client)
        assert isinstance(result, str)

    async def test_list_roles(self, pve_client: MultiClient):
        result = await list_roles(pve_client)
        assert isinstance(result, str)

    async def test_list_users(self, pve_client: MultiClient):
        result = await list_users(pve_client)
        assert isinstance(result, str)

    async def test_list_groups(self, pve_client: MultiClient):
        result = await list_groups(pve_client)
        assert isinstance(result, str)

    async def test_check_permissions(self, pve_client: MultiClient):
        result = await check_permissions(pve_client, userid="root@pam", path="/")
        assert isinstance(result, str)


class TestAccess:
    async def test_list_tfa(self, pve_client: MultiClient):
        result = await list_tfa(pve_client)
        assert isinstance(result, str)

    async def test_list_domains(self, pve_client: MultiClient):
        result = await list_domains(pve_client)
        assert isinstance(result, str)


class TestPools:
    async def test_list_pools(self, pve_client: MultiClient):
        result = await list_pools(pve_client)
        assert isinstance(result, str)
