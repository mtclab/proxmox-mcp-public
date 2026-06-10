from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv

_TOKEN_RE = re.compile(r"^.+@.+\!.+$")
_ENDPOINT_NAME_RE = re.compile(r"^[a-zA-Z0-9_-]+$")


class Config:
    def __init__(
        self,
        url: str,
        verify: str | bool,
        monitor_token_id: str,
        monitor_token_secret: str,
        admin_token_id: str,
        admin_token_secret: str,
        allow_elevated: bool = False,
        default_node: Optional[str] = None,
        allowed_commands: Optional[list[str]] = None,
        allowed_monitor_commands: Optional[list[str]] = None,
        allowed_node_commands: Optional[list[str]] = None,
        upload_dir: Optional[str] = None,
        timeout: int = 30,
    ) -> None:
        self.url = url
        self.verify = verify
        self.monitor_token_id = monitor_token_id
        self.monitor_token_secret = monitor_token_secret
        self.admin_token_id = admin_token_id
        self.admin_token_secret = admin_token_secret
        self.allow_elevated = allow_elevated
        self.default_node = default_node
        self.allowed_commands = allowed_commands
        self.allowed_monitor_commands = allowed_monitor_commands
        self.allowed_node_commands = allowed_node_commands
        self.upload_dir = upload_dir
        self.timeout = timeout

        self._validate()

    def _validate(self) -> None:
        if not self.url.startswith("https://"):
            raise ValueError(f"PROXMOX_URL must start with https:// — got {self.url!r}")

        for label, tid in [
            ("PROXMOX_MONITOR_TOKEN_ID", self.monitor_token_id),
            ("PROXMOX_ADMIN_TOKEN_ID", self.admin_token_id),
        ]:
            if tid and not _TOKEN_RE.match(tid):
                raise ValueError(f"{label} must match user@realm!tokenid format — got {tid!r}")

    @classmethod
    def from_env(cls, dotenv_path: Optional[str | Path] = None) -> Config:
        if dotenv_path is not None:
            load_dotenv(dotenv_path)
        else:
            load_dotenv()

        url = os.environ.get("PROXMOX_URL")
        if not url:
            raise ValueError("PROXMOX_URL is required")

        monitor_token_id = os.environ.get("PROXMOX_MONITOR_TOKEN_ID")
        if not monitor_token_id:
            raise ValueError("PROXMOX_MONITOR_TOKEN_ID is required")

        monitor_token_secret = os.environ.get("PROXMOX_MONITOR_TOKEN_SECRET")
        if not monitor_token_secret:
            raise ValueError("PROXMOX_MONITOR_TOKEN_SECRET is required")

        admin_token_id = os.environ.get("PROXMOX_ADMIN_TOKEN_ID")
        if not admin_token_id:
            raise ValueError("PROXMOX_ADMIN_TOKEN_ID is required")

        admin_token_secret = os.environ.get("PROXMOX_ADMIN_TOKEN_SECRET")
        if not admin_token_secret:
            raise ValueError("PROXMOX_ADMIN_TOKEN_SECRET is required")

        allow_elevated = os.environ.get("PROXMOX_ALLOW_ELEVATED", "false").strip().lower() in (
            "true",
            "1",
            "yes",
        )

        default_node = os.environ.get("PROXMOX_DEFAULT_NODE") or None

        allowed_commands_raw = os.environ.get("PROXMOX_ALLOWED_COMMANDS", "")
        allowed_commands = [c.strip() for c in allowed_commands_raw.split(",") if c.strip()] or None

        allowed_monitor_commands_raw = os.environ.get("PROXMOX_ALLOWED_MONITOR_COMMANDS", "")
        allowed_monitor_commands = [c.strip() for c in allowed_monitor_commands_raw.split(",") if c.strip()] or None

        allowed_node_commands_raw = os.environ.get("PROXMOX_ALLOWED_NODE_COMMANDS", "")
        allowed_node_commands = [c.strip() for c in allowed_node_commands_raw.split(",") if c.strip()] or None

        upload_dir = os.environ.get("PROXMOX_UPLOAD_DIR") or None

        timeout = int(os.environ.get("PROXMOX_TIMEOUT", "30"))

        verify_raw = os.environ.get("PROXMOX_VERIFY", "true").strip().lower()
        if verify_raw in ("false", "0", "no"):
            verify: str | bool = False
        elif verify_raw in ("true", "1", "yes"):
            verify = True
        else:
            verify = verify_raw

        return cls(
            url=url,
            verify=verify,
            monitor_token_id=monitor_token_id,
            monitor_token_secret=monitor_token_secret,
            admin_token_id=admin_token_id,
            admin_token_secret=admin_token_secret,
            allow_elevated=allow_elevated,
            default_node=default_node,
            allowed_commands=allowed_commands,
            allowed_monitor_commands=allowed_monitor_commands,
            allowed_node_commands=allowed_node_commands,
            upload_dir=upload_dir,
            timeout=timeout,
        )

    @property
    def host(self) -> str:
        return self.url.replace("https://", "").split(":")[0]

    @property
    def port(self) -> int:
        parts = self.url.replace("https://", "").split(":")
        if len(parts) > 1:
            try:
                return int(parts[1].rstrip("/"))
            except ValueError:
                pass
        return 8006


class EndpointConfig:
    def __init__(
        self,
        name: str,
        url: str,
        monitor_token_id: str = "",
        monitor_token_secret: str = "",
        admin_token_id: str = "",
        admin_token_secret: str = "",
        verify: str | bool | None = None,
        allow_elevated: bool = False,
        default_node: str | None = None,
        allowed_commands: list[str] | None = None,
        allowed_monitor_commands: list[str] | None = None,
        allowed_node_commands: list[str] | None = None,
        upload_dir: str | None = None,
        timeout: int = 30,
    ) -> None:
        self.name = name
        self.url = url
        self.verify = verify
        self.monitor_token_id = monitor_token_id
        self.monitor_token_secret = monitor_token_secret
        self.admin_token_id = admin_token_id
        self.admin_token_secret = admin_token_secret
        self.allow_elevated = allow_elevated
        self.default_node = default_node
        self.allowed_commands = allowed_commands
        self.allowed_monitor_commands = allowed_monitor_commands
        self.allowed_node_commands = allowed_node_commands
        self.upload_dir = upload_dir
        self.timeout = timeout

    def to_config(self, global_verify: str | bool | None = None, global_timeout: int | None = None) -> Config:
        mon_secret = self.monitor_token_secret or os.environ.get(f"PROXMOX_{self.name.upper()}_MONITOR_SECRET", "")
        adm_secret = self.admin_token_secret or os.environ.get(f"PROXMOX_{self.name.upper()}_ADMIN_SECRET", "")
        tok_id = self.monitor_token_id
        if not tok_id:
            tok_id = os.environ.get(f"PROXMOX_{self.name.upper()}_MONITOR_TOKEN_ID", "")
        adm_id = self.admin_token_id
        if not adm_id:
            adm_id = os.environ.get(f"PROXMOX_{self.name.upper()}_ADMIN_TOKEN_ID", "")

        effective_verify = self.verify if self.verify is not None else global_verify
        if effective_verify is None:
            effective_verify = True

        return Config(
            url=self.url,
            verify=effective_verify,
            monitor_token_id=tok_id,
            monitor_token_secret=mon_secret,
            admin_token_id=adm_id,
            admin_token_secret=adm_secret,
            allow_elevated=self.allow_elevated,
            default_node=self.default_node,
            allowed_commands=self.allowed_commands,
            allowed_monitor_commands=self.allowed_monitor_commands,
            allowed_node_commands=self.allowed_node_commands,
            upload_dir=self.upload_dir,
            timeout=global_timeout if global_timeout is not None else self.timeout,
        )


class MultiConfig:
    def __init__(
        self,
        endpoints: list[EndpointConfig],
        verify: str | bool = True,
        timeout: int = 30,
        single_node_compat: bool = False,
    ) -> None:
        self.endpoints = endpoints
        self.verify = verify
        self.timeout = timeout
        self._single_node_compat = single_node_compat

    @property
    def single_node_compat(self) -> bool:
        return self._single_node_compat

    def validate(self) -> None:
        names = [ep.name for ep in self.endpoints]
        if len(names) != len(set(names)):
            raise ValueError(f"Duplicate endpoint name: {names}")
        for ep in self.endpoints:
            if not ep.url.startswith("https://"):
                raise ValueError(f"Endpoint {ep.name!r} URL must start with https:// — got {ep.url!r}")
            if ep.monitor_token_id and not _TOKEN_RE.match(ep.monitor_token_id):
                raise ValueError(
                    f"Endpoint {ep.name!r} monitor_token_id must match "
                    f"user@realm!tokenid format — got {ep.monitor_token_id!r}"
                )
            if ep.admin_token_id and not _TOKEN_RE.match(ep.admin_token_id):
                raise ValueError(
                    f"Endpoint {ep.name!r} admin_token_id must match "
                    f"user@realm!tokenid format — got {ep.admin_token_id!r}"
                )
            if not _ENDPOINT_NAME_RE.match(ep.name):
                raise ValueError(f"Endpoint name must match {_ENDPOINT_NAME_RE.pattern!r} — got {ep.name!r}")

    @classmethod
    def _from_json(cls, data: dict[str, Any]) -> MultiConfig:
        endpoints = []
        for ep_data in data.get("endpoints", []):
            ep = EndpointConfig(
                name=ep_data["name"],
                url=ep_data["url"],
                monitor_token_id=ep_data.get("monitor_token_id", ""),
                monitor_token_secret=ep_data.get("monitor_token_secret", ""),
                admin_token_id=ep_data.get("admin_token_id", ""),
                admin_token_secret=ep_data.get("admin_token_secret", ""),
                allow_elevated=ep_data.get("allow_elevated", False),
            )
            endpoints.append(ep)
        return cls(
            endpoints=endpoints,
            verify=data.get("verify", True),
            timeout=data.get("timeout", 30),
        )

    @classmethod
    def from_env(cls, dotenv_path: str | Path | None = None) -> MultiConfig:
        if dotenv_path is not None:
            load_dotenv(dotenv_path)
        else:
            load_dotenv()

        json_str = os.environ.get("PROXMOX_ENDPOINTS_JSON")
        file_path = os.environ.get("PROXMOX_ENDPOINTS_FILE")

        if json_str:
            data = json.loads(json_str)
            mc = cls._from_json(data)
            mc.validate()
            return mc

        if file_path:
            p = Path(file_path)
            mode = p.stat().st_mode
            if mode & 0o077:
                raise ValueError(
                    f"Endpoints file {file_path} has permissive permissions ({oct(mode)[-3:]}). "
                    "Run: chmod 600 " + file_path
                )
            data = json.loads(p.read_text())
            mc = cls._from_json(data)
            mc.validate()
            return mc

        url = os.environ.get("PROXMOX_URL")
        if not url:
            raise ValueError("No Proxmox configuration found. Set PROXMOX_URL or PROXMOX_ENDPOINTS_JSON.")

        config = Config.from_env()
        return cls.from_config(config)

    @classmethod
    def from_config(cls, config: Config) -> MultiConfig:
        ep = EndpointConfig(
            name="default",
            url=config.url,
            verify=config.verify,
            monitor_token_id=config.monitor_token_id,
            monitor_token_secret=config.monitor_token_secret,
            admin_token_id=config.admin_token_id,
            admin_token_secret=config.admin_token_secret,
            allow_elevated=config.allow_elevated,
            default_node=config.default_node,
            allowed_commands=config.allowed_commands,
            allowed_monitor_commands=config.allowed_monitor_commands,
            allowed_node_commands=config.allowed_node_commands,
            upload_dir=config.upload_dir,
            timeout=config.timeout,
        )
        return cls(
            endpoints=[ep],
            verify=config.verify,
            timeout=config.timeout,
            single_node_compat=True,
        )

    @property
    def upload_dir(self) -> str | None:
        return self.endpoints[0].upload_dir

    @property
    def allowed_commands(self) -> list[str] | None:
        return self.endpoints[0].allowed_commands

    @property
    def allowed_monitor_commands(self) -> list[str] | None:
        return self.endpoints[0].allowed_monitor_commands

    @property
    def host(self) -> str:
        return self.endpoints[0].url.replace("https://", "").split(":")[0]
