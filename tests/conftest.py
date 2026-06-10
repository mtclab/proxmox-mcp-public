from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from proxmox_mcp.config import Config, MultiConfig
from proxmox_mcp.multi_client import MultiClient

SECRETS_PATH = Path(os.environ.get("PROXMOX_SECRETS", "$HOME/.config/opencode/secrets/proxmox.json"))

_DUMMY_TOKEN_ID = "ci-runner@pve!ci-token"
_DUMMY_TOKEN_SECRET = "00000000-0000-0000-0000-000000000000"


def _has_live_pve() -> bool:
    pve_url = os.environ.get("PROXMOX_URL", "")
    return bool(pve_url) or SECRETS_PATH.exists()


def _load_secrets() -> dict[str, str]:
    if SECRETS_PATH.exists():
        with open(SECRETS_PATH) as f:
            return json.load(f)
    return {
        "PVE_URL": os.environ.get("PROXMOX_URL", "https://pve.example.local:8006"),
        "PVE_MONITOR_TOKEN_ID": os.environ.get("PROXMOX_MONITOR_TOKEN_ID", _DUMMY_TOKEN_ID),
        "PVE_MONITOR_TOKEN_SECRET": os.environ.get("PROXMOX_MONITOR_TOKEN_SECRET", _DUMMY_TOKEN_SECRET),
        "PVE_ADMIN_TOKEN_ID": os.environ.get("PROXMOX_ADMIN_TOKEN_ID", _DUMMY_TOKEN_ID),
        "PVE_ADMIN_TOKEN_SECRET": os.environ.get("PROXMOX_ADMIN_TOKEN_SECRET", _DUMMY_TOKEN_SECRET),
        "PVE_NODE": os.environ.get("PROXMOX_DEFAULT_NODE", "pve"),
    }


def _make_config() -> Config:
    secrets = _load_secrets()
    url = secrets.get("PVE_URL", secrets.get("PROXMOX_URL", "https://pve.example.local:8006"))
    url = url.replace("http://", "https://")
    if not url.startswith("https://"):
        url = f"https://{url}"
    if ":8006" not in url:
        url = f"{url}:8006"
    return Config(
        url=url,
        verify=False,
        monitor_token_id=secrets.get("PVE_MONITOR_TOKEN_ID", secrets.get("PROXMOX_MONITOR_TOKEN_ID", _DUMMY_TOKEN_ID)),
        monitor_token_secret=secrets.get(
            "PVE_MONITOR_TOKEN_SECRET", secrets.get("PROXMOX_MONITOR_TOKEN_SECRET", _DUMMY_TOKEN_SECRET)
        ),
        admin_token_id=secrets.get("PVE_ADMIN_TOKEN_ID", secrets.get("PROXMOX_ADMIN_TOKEN_ID", _DUMMY_TOKEN_ID)),
        admin_token_secret=secrets.get(
            "PVE_ADMIN_TOKEN_SECRET", secrets.get("PROXMOX_ADMIN_TOKEN_SECRET", _DUMMY_TOKEN_SECRET)
        ),
        allow_elevated=True,
        default_node=secrets.get("PVE_NODE", secrets.get("PROXMOX_DEFAULT_NODE", "pve")),
    )


@pytest.fixture(scope="session")
def pve_client() -> MultiClient:
    if not _has_live_pve():
        pytest.skip("No live Proxmox server available (set PROXMOX_URL or provide secrets file)")
    config = _make_config()
    multi_config = MultiConfig.from_config(config)
    client = MultiClient(multi_config)
    return client


@pytest.fixture(scope="session")
async def pve_client_ready(pve_client: MultiClient) -> MultiClient:
    await pve_client.initialize()
    return pve_client
