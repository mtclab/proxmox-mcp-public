from __future__ import annotations


class ProxmoxError(Exception):
    pass


class ProxmoxConnectionError(ProxmoxError):
    pass


class ProxmoxPermissionError(ProxmoxError):
    pass


class ProxmoxTaskError(ProxmoxError):
    def __init__(self, exitstatus: str, output: str | None = None) -> None:
        self.exitstatus = exitstatus
        self.output = output
        msg = f"Task failed with exitstatus={exitstatus!r}"
        if output:
            msg += f": {output}"
        super().__init__(msg)


class ProxmoxNodeError(ProxmoxError):
    def __init__(self, node: str, reason: str = "") -> None:
        self.node = node
        msg = f"Node {node!r} error"
        if reason:
            msg += f": {reason}"
        super().__init__(msg)


class ProxmoxNotFoundError(ProxmoxError):
    def __init__(self, resource: str, node: str | None = None) -> None:
        self.resource = resource
        self.node = node
        if node:
            msg = f"{resource} not found on node {node}"
        else:
            msg = f"{resource} not found"
        super().__init__(msg)
