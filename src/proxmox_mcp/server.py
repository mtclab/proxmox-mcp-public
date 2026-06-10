import os
import sys
from typing import Any

from mcp.server.fastmcp import FastMCP

from proxmox_mcp import (
    access,
    acme,
    apt,
    backups,
    capabilities,
    ceph,
    certificates,
    cloudinit,
    cluster,
    console,
    discovery,
    disks,
    firewall,
    ha,
    hardware,
    lifecycle,
    mapping,
    metrics,
    networking,
    nodes,
    notifications,
    permissions,
    pools,
    replication,
    sdn,
    snapshots,
    tasks,
    templates,
)
from proxmox_mcp import storage as storage_mod
from proxmox_mcp.config import MultiConfig
from proxmox_mcp.multi_client import MultiClient

mcp = FastMCP("homepilot-proxmox-mcp")

client: MultiClient = None  # type: ignore[assignment]


def _parse(kwargs: str | None) -> dict:
    """Parse kwargs JSON string into a dict for PVE API calls."""
    if not kwargs:
        return {}
    import json

    try:
        result = json.loads(kwargs)
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError:
        pass
    try:
        return {k: v for k, v in (pair.split("=", 1) for pair in kwargs.split() if "=" in pair)}
    except ValueError:
        return {}


@mcp.tool()
async def proxmox_list_nodes(endpoint: str | None = None) -> str:
    """(read-only). List all nodes in the Proxmox cluster."""
    return await discovery.list_nodes(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_node_status(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). Get detailed status of a specific node."""
    return await discovery.node_status(client, node, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_vms(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). List all virtual machines in the cluster."""
    return await discovery.list_vms(client, node, endpoint=endpoint)


@mcp.tool()
async def proxmox_vm_info(
    node: str | None = None, vmid: int | None = None, name: str | None = None, endpoint: str | None = None
) -> str:
    """(read-only). Get detailed information about a specific VM."""
    return await discovery.vm_info(client, node, vmid, name, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_lxc(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). List all LXC containers in the cluster."""
    return await discovery.list_lxc(client, node, endpoint=endpoint)


@mcp.tool()
async def proxmox_lxc_info(
    node: str | None = None, vmid: int | None = None, name: str | None = None, endpoint: str | None = None
) -> str:
    """(read-only). Get detailed information about a specific LXC container."""
    return await discovery.lxc_info(client, node, vmid, name, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_storage(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). List all storage pools in the cluster."""
    return await discovery.list_storage(client, node, endpoint=endpoint)


@mcp.tool()
async def proxmox_storage_content(node: str | None = None, storage: str = "local", endpoint: str | None = None) -> str:
    """(read-only). List content in a storage pool."""
    return await discovery.storage_content(client, node, storage, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_tasks(node: str | None = None, limit: int = 50, endpoint: str | None = None) -> str:
    """(read-only). List recent cluster tasks."""
    return await discovery.list_tasks(client, node, limit, endpoint=endpoint)


@mcp.tool()
async def proxmox_task_status(upid: str, endpoint: str | None = None) -> str:
    """(read-only). Get the status of a specific task."""
    return await discovery.task_status(client, upid, endpoint=endpoint)


@mcp.tool()
async def proxmox_node_metrics(
    node: str | None = None, timeframe: str = "hour", cf: str = "AVERAGE", endpoint: str | None = None
) -> str:
    """(read-only). Get RRD metrics for a node."""
    return await discovery.node_metrics(client, node, timeframe, cf, endpoint=endpoint)


@mcp.tool()
async def proxmox_vm_metrics(
    node: str | None = None,
    vmid: int | None = None,
    name: str | None = None,
    timeframe: str = "hour",
    endpoint: str | None = None,
) -> str:
    """(read-only). Get RRD metrics for a VM."""
    return await discovery.vm_metrics(client, node, vmid, name, timeframe, endpoint=endpoint)


@mcp.tool()
async def proxmox_lxc_metrics(
    node: str | None = None,
    vmid: int | None = None,
    name: str | None = None,
    timeframe: str = "hour",
    endpoint: str | None = None,
) -> str:
    """(read-only). Get RRD metrics for an LXC container."""
    return await discovery.lxc_metrics(client, node, vmid, name, timeframe, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_bridges(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). List network bridges on a node."""
    return await discovery.list_bridges(client, node, endpoint=endpoint)


@mcp.tool()
async def proxmox_create_lxc(
    node: str | None = None,
    vmid: int | None = None,
    ostemplate: str = "",
    hostname: str | None = None,
    memory: int | None = None,
    cores: int | None = None,
    rootfs: str | None = None,
    storage: str | None = None,
    password: str | None = None,
    swap: int | None = None,
    features: str | None = None,
    unprivileged: bool | None = None,
    onboot: bool | None = None,
    description: str | None = None,
    pool: str | None = None,
    net0: str | None = None,
    nameserver: str | None = None,
    searchdomain: str | None = None,
    ssh_public_keys: str | None = None,
    tags: str | None = None,
    start: bool = False,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Create an LXC container"""
    return await lifecycle.create_lxc(
        client,
        node=node,
        vmid=vmid,
        ostemplate=ostemplate,
        hostname=hostname,
        memory=memory,
        cores=cores,
        rootfs=rootfs,
        storage=storage,
        password=password,
        swap=swap,
        features=features,
        unprivileged=unprivileged,
        onboot=onboot,
        description=description,
        pool=pool,
        net0=net0,
        nameserver=nameserver,
        searchdomain=searchdomain,
        ssh_public_keys=ssh_public_keys,
        tags=tags,
        start=start,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_start_lxc(
    node: str | None = None, vmid: int | None = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Start an LXC container"""
    return await lifecycle.start_lxc(client, node=node, vmid=vmid, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_stop_lxc(
    node: str | None = None, vmid: int | None = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Stop an LXC container"""
    return await lifecycle.stop_lxc(client, node=node, vmid=vmid, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_shutdown_lxc(
    node: str | None = None, vmid: int | None = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Shutdown an LXC container"""
    return await lifecycle.shutdown_lxc(client, node=node, vmid=vmid, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_reboot_lxc(
    node: str | None = None, vmid: int | None = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Reboot an LXC container"""
    return await lifecycle.reboot_lxc(client, node=node, vmid=vmid, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_delete_lxc(
    node: str | None = None, vmid: int | None = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Delete an LXC container"""
    return await lifecycle.delete_lxc(client, node=node, vmid=vmid, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_configure_lxc(
    node: str | None = None,
    vmid: int | None = None,
    cores: int | None = None,
    memory: int | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
    **kwargs: str | None,
) -> str:
    """(elevated, confirm required). Configure an LXC container"""
    return await lifecycle.configure_lxc(
        client,
        node=node,
        vmid=vmid,
        cores=cores,
        memory=memory,
        confirm=confirm,
        **kwargs,
    )


@mcp.tool()
async def proxmox_resize_lxc(
    node: str | None = None,
    vmid: int | None = None,
    disk: str = "rootfs",
    size: str = "+10G",
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Resize an LXC container disk"""
    return await lifecycle.resize_lxc(
        client,
        node=node,
        vmid=vmid,
        disk=disk,
        size=size,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_suspend_lxc(
    node: str | None = None, vmid: int | None = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Suspend an LXC container"""
    return await lifecycle.suspend_lxc(client, node=node, vmid=vmid, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_resume_lxc(
    node: str | None = None, vmid: int | None = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Resume a suspended LXC container"""
    return await lifecycle.resume_lxc(client, node=node, vmid=vmid, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_clone_lxc(
    node: str | None = None,
    vmid: int | None = None,
    newid: int | None = None,
    hostname: str | None = None,
    full: bool = True,
    target: str | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Clone an LXC container"""
    return await lifecycle.clone_lxc(
        client,
        node=node,
        vmid=vmid,
        newid=newid,
        hostname=hostname,
        full=full,
        target=target,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_migrate_lxc(
    node: str | None = None,
    vmid: int | None = None,
    target: str | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Migrate an LXC container to another node"""
    return await lifecycle.migrate_lxc(
        client,
        node=node,
        vmid=vmid,
        target=target,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_lxc_interfaces(node: str | None = None, vmid: int | None = None, endpoint: str | None = None) -> str:
    """(read-only). Get network interfaces and IP addresses for an LXC container."""
    return await lifecycle.lxc_interfaces(client, node=node, vmid=vmid, endpoint=endpoint)


@mcp.tool()
async def proxmox_create_vm(
    node: str | None = None,
    vmid: int | None = None,
    name: str | None = None,
    memory: int | None = None,
    cores: int | None = None,
    sockets: int | None = None,
    disk_size: str | None = None,
    storage: str | None = None,
    iso: str | None = None,
    ostype: str | None = None,
    net0: str | None = None,
    description: str | None = None,
    boot: str | None = None,
    scsihw: str | None = None,
    onboot: bool | None = None,
    start: bool | None = None,
    pool: str | None = None,
    cpu: str | None = None,
    bios: str | None = None,
    agent: str | None = None,
    tags: str | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Create a VM. disk_size uses scsi0 format."""
    return await lifecycle.create_vm(
        client,
        node=node,
        vmid=vmid,
        name=name,
        memory=str(memory) if memory is not None else None,
        cores=cores,
        sockets=sockets,
        disk_size=disk_size,
        storage=storage,
        iso=iso,
        ostype=ostype,
        net0=net0,
        description=description,
        boot=boot,
        scsihw=scsihw,
        onboot=onboot,
        start=start,
        pool=pool,
        cpu=cpu,
        bios=bios,
        agent=agent,
        tags=tags,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_start_vm(
    node: str | None = None, vmid: int | None = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Start a VM"""
    return await lifecycle.start_vm(client, node=node, vmid=vmid, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_stop_vm(
    node: str | None = None, vmid: int | None = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Stop a VM"""
    return await lifecycle.stop_vm(client, node=node, vmid=vmid, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_shutdown_vm(
    node: str | None = None, vmid: int | None = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Shutdown a VM"""
    return await lifecycle.shutdown_vm(client, node=node, vmid=vmid, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_reboot_vm(
    node: str | None = None, vmid: int | None = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Reboot a VM"""
    return await lifecycle.reboot_vm(client, node=node, vmid=vmid, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_delete_vm(
    node: str | None = None, vmid: int | None = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Delete a VM"""
    return await lifecycle.delete_vm(client, node=node, vmid=vmid, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_clone_vm(
    node: str | None = None,
    vmid: int | None = None,
    newid: int | None = None,
    name: str | None = None,
    full: bool = True,
    target: str | None = None,
    snapname: str | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Clone a VM"""
    return await lifecycle.clone_vm(
        client,
        node=node,
        vmid=vmid,
        newid=newid,
        name=name,
        full=full,
        target=target,
        snapname=snapname,
        confirm=confirm,
        endpoint=endpoint,
    )


@mcp.tool()
async def proxmox_migrate_vm(
    node: str | None = None,
    vmid: int | None = None,
    target: str | None = None,
    online: bool | None = None,
    with_local_disks: bool | None = None,
    targetstorage: str | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Migrate a VM to another node"""
    return await lifecycle.migrate_vm(
        client,
        node=node,
        vmid=vmid,
        target=target,
        online=online,
        with_local_disks=with_local_disks,
        targetstorage=targetstorage,
        confirm=confirm,
        endpoint=endpoint,
    )


@mcp.tool()
async def proxmox_configure_vm(
    node: str | None = None,
    vmid: int | None = None,
    cores: int | None = None,
    memory: str | None = None,
    kwargs: str | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Configure a VM (elevated, confirm required, asynchronous API)."""
    return await lifecycle.configure_vm(
        client,
        node=node,
        vmid=vmid,
        cores=cores,
        memory=memory,
        kwargs=kwargs,
        confirm=confirm,
        endpoint=endpoint,
    )


@mcp.tool()
async def proxmox_resize_vm(
    node: str | None = None,
    vmid: int | None = None,
    disk: str = "scsi0",
    size: str = "+10G",
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Resize a VM disk"""
    return await lifecycle.resize_vm(
        client,
        node=node,
        vmid=vmid,
        disk=disk,
        size=size,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_reset_vm(
    node: str | None = None, vmid: int | None = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Reset a VM (hardware reset)."""
    return await lifecycle.reset_vm(client, node=node, vmid=vmid, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_suspend_vm(
    node: str | None = None, vmid: int | None = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Suspend a VM"""
    return await lifecycle.suspend_vm(client, node=node, vmid=vmid, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_resume_vm(
    node: str | None = None, vmid: int | None = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Resume a suspended VM"""
    return await lifecycle.resume_vm(client, node=node, vmid=vmid, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_snapshot_config(
    node: str | None = None,
    vmid: int | None = None,
    snapname: str = "",
    vmtype: str = "qemu",
    endpoint: str | None = None,
) -> str:
    """(read-only). Get snapshot configuration"""
    return await snapshots.snapshot_config(
        client,
        node=node,
        vmid=vmid,
        snapname=snapname,
        vmtype=vmtype,
    )


@mcp.tool()
async def proxmox_list_templates(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). List PVE appliance catalog (available templates to download)."""
    return await templates.list_templates(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_storage_templates(
    node: str | None = None, storage: str = "local", endpoint: str | None = None
) -> str:
    """(read-only). List already-downloaded templates in storage."""
    return await templates.list_storage_templates(client, node=node, storage=storage, endpoint=endpoint)


@mcp.tool()
async def proxmox_download_template(
    node: str | None = None,
    storage: str = "local",
    url: str = "",
    filename: str = "",
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Download template from PVE repo URL."""
    return await templates.download_template(
        client,
        node=node,
        storage=storage,
        url=url,
        filename=filename,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_upload_template(
    node: str | None = None,
    storage: str = "local",
    filepath: str = "",
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Upload local file as vztmpl to storage"""
    return await templates.upload_template(
        client,
        node=node,
        storage=storage,
        filepath=filepath,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_list_snapshots(
    node: str | None = None, vmid: int | None = None, vmtype: str = "qemu", endpoint: str | None = None
) -> str:
    """(read-only). List snapshots for a VM or LXC container."""
    return await snapshots.list_snapshots(client, node=node, vmid=vmid, vmtype=vmtype, endpoint=endpoint)


@mcp.tool()
async def proxmox_create_snapshot(
    node: str | None = None,
    vmid: int | None = None,
    snapname: str = "",
    vmtype: str = "qemu",
    description: str | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Create a snapshot for a VM or LXC container"""
    return await snapshots.create_snapshot(
        client,
        node=node,
        vmid=vmid,
        snapname=snapname,
        vmtype=vmtype,
        description=description,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_delete_snapshot(
    node: str | None = None,
    vmid: int | None = None,
    snapname: str = "",
    vmtype: str = "qemu",
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Delete a snapshot for a VM or LXC container"""
    return await snapshots.delete_snapshot(
        client,
        node=node,
        vmid=vmid,
        snapname=snapname,
        vmtype=vmtype,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_rollback_snapshot(
    node: str | None = None,
    vmid: int | None = None,
    snapname: str = "",
    vmtype: str = "qemu",
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Rollback a snapshot for a VM or LXC container"""
    return await snapshots.rollback_snapshot(
        client,
        node=node,
        vmid=vmid,
        snapname=snapname,
        vmtype=vmtype,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_list_backups(node: str | None = None, storage: str = "local", endpoint: str | None = None) -> str:
    """(read-only). List backups in a storage pool."""
    return await backups.list_backups(client, node=node, storage=storage, endpoint=endpoint)


@mcp.tool()
async def proxmox_create_backup(
    node: str | None = None,
    vmid: int | None = None,
    vmtype: str = "qemu",
    storage: str = "local",
    mode: str = "snapshot",
    compress: str = "zstd",
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Create a backup vmtype: 'qemu' or 'lxc'."""
    return await backups.create_backup(
        client,
        node=node,
        vmid=vmid,
        vmtype=vmtype,
        storage=storage,
        mode=mode,
        compress=compress,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_restore_backup(
    node: str | None = None,
    vmid: int | None = None,
    archive: str = "",
    storage: str = "local",
    vmtype: str = "qemu",
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Restore a backup"""
    return await backups.restore_backup(
        client,
        node=node,
        vmid=vmid,
        archive=archive,
        storage=storage,
        vmtype=vmtype,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_list_network(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). List all network interfaces on a node."""
    return await networking.list_network(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_create_network(
    node: str | None = None,
    iface: str = "",
    type: str = "bridge",
    address: str | None = None,
    netmask: str | None = None,
    gateway: str | None = None,
    bridge_ports: str | None = None,
    cidr: str | None = None,
    address6: str | None = None,
    gateway6: str | None = None,
    cidr6: str | None = None,
    autostart: bool | None = None,
    mtu: int | None = None,
    confirm: bool = False,
    apply: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Create a network interface on a node"""
    return await networking.create_network(
        client,
        node=node,
        iface=iface,
        type=type,
        address=address,
        netmask=netmask,
        gateway=gateway,
        bridge_ports=bridge_ports,
        cidr=cidr,
        address6=address6,
        gateway6=gateway6,
        cidr6=cidr6,
        autostart=autostart,
        mtu=mtu,
        confirm=confirm,
        apply=apply,
    )


@mcp.tool()
async def proxmox_update_network(
    node: str | None = None,
    iface: str = "",
    address: str | None = None,
    netmask: str | None = None,
    gateway: str | None = None,
    cidr: str | None = None,
    address6: str | None = None,
    gateway6: str | None = None,
    cidr6: str | None = None,
    autostart: bool | None = None,
    mtu: int | None = None,
    delete: str | None = None,
    confirm: bool = False,
    apply: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Update a network interface on a node"""
    return await networking.update_network(
        client,
        node=node,
        iface=iface,
        address=address,
        netmask=netmask,
        gateway=gateway,
        cidr=cidr,
        address6=address6,
        gateway6=gateway6,
        cidr6=cidr6,
        autostart=autostart,
        mtu=mtu,
        delete=delete,
        confirm=confirm,
        apply=apply,
    )


@mcp.tool()
async def proxmox_delete_network(
    node: str | None = None, iface: str = "", confirm: bool = False, apply: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Delete a network interface on a node"""
    return await networking.delete_network(
        client,
        node=node,
        iface=iface,
        confirm=confirm,
        apply=apply,
    )


@mcp.tool()
async def proxmox_list_acl(endpoint: str | None = None) -> str:
    """(read-only). List ACL rules in the cluster."""
    return await permissions.list_acl(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_set_acl(
    users: str = "",
    roles: str = "",
    path: str = "",
    propagate: bool = True,
    groups: str | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Set ACL rules. Supports both users and groups."""
    return await permissions.set_acl(
        client,
        users=users,
        roles=roles,
        path=path,
        propagate=propagate,
        groups=groups,
        confirm=confirm,
        endpoint=endpoint,
    )


@mcp.tool()
async def proxmox_delete_acl(
    users: str = "",
    roles: str = "",
    path: str = "",
    propagate: bool = True,
    groups: str | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Delete ACL rules. Supports both users and groups."""
    return await permissions.delete_acl(
        client,
        users=users,
        roles=roles,
        path=path,
        propagate=propagate,
        groups=groups,
        confirm=confirm,
        endpoint=endpoint,
    )


@mcp.tool()
async def proxmox_list_roles(endpoint: str | None = None) -> str:
    """(read-only). List roles in the cluster."""
    return await permissions.list_roles(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_users(endpoint: str | None = None) -> str:
    """(read-only). List users in the cluster."""
    return await permissions.list_users(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_tokens(userid: str = "", endpoint: str | None = None) -> str:
    """(read-only). List API tokens for a user."""
    return await permissions.list_tokens(client, userid=userid, endpoint=endpoint)


@mcp.tool()
async def proxmox_create_user(
    userid: str = "",
    password: str = "",
    comment: str | None = None,
    email: str | None = None,
    firstname: str | None = None,
    lastname: str | None = None,
    enable: bool | None = None,
    expire: int | None = None,
    groups: str | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Create a new PVE user"""
    return await permissions.create_user(
        client,
        userid=userid,
        password=password,
        comment=comment,
        email=email,
        firstname=firstname,
        lastname=lastname,
        enable=enable,
        expire=expire,
        groups=groups,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_get_user(userid: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get PVE user configuration"""
    return await permissions.get_user(client, userid=userid, endpoint=endpoint)


@mcp.tool()
async def proxmox_update_user(
    userid: str = "",
    comment: str | None = None,
    email: str | None = None,
    firstname: str | None = None,
    lastname: str | None = None,
    enable: bool | None = None,
    expire: int | None = None,
    groups: str | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Update a PVE user"""
    return await permissions.update_user(
        client,
        userid=userid,
        comment=comment,
        email=email,
        firstname=firstname,
        lastname=lastname,
        enable=enable,
        expire=expire,
        groups=groups,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_delete_user(userid: str = "", confirm: bool = False, endpoint: str | None = None) -> str:
    """(elevated, confirm required). Delete a PVE user"""
    return await permissions.delete_user(client, userid=userid, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_create_role(
    roleid: str = "", privs: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Create a new PVE role"""
    return await permissions.create_role(client, roleid=roleid, privs=privs, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_get_role(roleid: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get PVE role configuration"""
    return await permissions.get_role(client, roleid=roleid, endpoint=endpoint)


@mcp.tool()
async def proxmox_update_role(
    roleid: str = "", privs: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Update a PVE role"""
    return await permissions.update_role(client, roleid=roleid, privs=privs, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_delete_role(roleid: str = "", confirm: bool = False, endpoint: str | None = None) -> str:
    """(elevated, confirm required). Delete a PVE role"""
    return await permissions.delete_role(client, roleid=roleid, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_create_token(
    userid: str = "",
    tokenid: str = "",
    comment: str | None = None,
    privsep: bool | None = None,
    expire: int | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Create an API token for a PVE user"""
    return await permissions.create_token(
        client,
        userid=userid,
        tokenid=tokenid,
        comment=comment,
        privsep=privsep,
        expire=expire,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_get_token(userid: str = "", tokenid: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get API token info"""
    return await permissions.get_token(client, userid=userid, tokenid=tokenid, endpoint=endpoint)


@mcp.tool()
async def proxmox_update_token(
    userid: str = "",
    tokenid: str = "",
    comment: str | None = None,
    privsep: bool | None = None,
    expire: int | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Update an API token"""
    return await permissions.update_token(
        client,
        userid=userid,
        tokenid=tokenid,
        comment=comment,
        privsep=privsep,
        expire=expire,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_delete_token(
    userid: str = "", tokenid: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Delete an API token"""
    return await permissions.delete_token(client, userid=userid, tokenid=tokenid, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_groups(endpoint: str | None = None) -> str:
    """(read-only). List PVE groups"""
    return await permissions.list_groups(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_create_group(
    groupid: str = "", comment: str | None = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Create a PVE group"""
    return await permissions.create_group(client, groupid=groupid, comment=comment, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_get_group(groupid: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get PVE group configuration"""
    return await permissions.get_group(client, groupid=groupid, endpoint=endpoint)


@mcp.tool()
async def proxmox_update_group(
    groupid: str = "", comment: str | None = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Update a PVE group"""
    return await permissions.update_group(client, groupid=groupid, comment=comment, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_delete_group(groupid: str = "", confirm: bool = False, endpoint: str | None = None) -> str:
    """(elevated, confirm required). Delete a PVE group"""
    return await permissions.delete_group(client, groupid=groupid, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_check_permissions(
    userid: str | None = None, path: str | None = None, endpoint: str | None = None
) -> str:
    """(read-only). Check effective permissions for a user/path"""
    return await permissions.check_permissions(client, userid=userid, path=path, endpoint=endpoint)


@mcp.tool()
async def proxmox_upload_iso(
    node: str | None = None,
    storage: str = "local",
    filepath: str = "",
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Upload an ISO file to storage"""
    return await storage_mod.upload_iso(
        client,
        node=node,
        storage=storage,
        filepath=filepath,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_list_isos(node: str | None = None, storage: str = "local", endpoint: str | None = None) -> str:
    """(read-only). List ISOs in a storage pool."""
    return await storage_mod.list_isos(client, node=node, storage=storage, endpoint=endpoint)


@mcp.tool()
async def proxmox_set_cloudinit(
    node: str | None = None,
    vmid: int | None = None,
    ciuser: str | None = None,
    cipassword: str | None = None,
    ipconfig0: str | None = None,
    sshkeys: str | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Set cloud-init parameters on a VM"""
    return await cloudinit.set_cloudinit(
        client,
        node=node,
        vmid=vmid,
        ciuser=ciuser,
        cipassword=cipassword,
        ipconfig0=ipconfig0,
        sshkeys=sshkeys,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_node_config(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). Get node configuration"""
    return await nodes.node_config(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_update_node_config(
    node: str | None = None,
    description: str | None = None,
    keyboard: str | None = None,
    time_zone: str | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Update node configuration"""
    return await nodes.update_node_config(
        client,
        node=node,
        description=description,
        keyboard=keyboard,
        time_zone=time_zone,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_reboot_node(node: str | None = None, confirm: bool = False, endpoint: str | None = None) -> str:
    """(elevated, confirm required). Reboot a node"""
    return await nodes.reboot_node(client, node=node, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_shutdown_node(node: str | None = None, confirm: bool = False, endpoint: str | None = None) -> str:
    """(elevated, confirm required). Shutdown a node"""
    return await nodes.shutdown_node(client, node=node, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_start_all(node: str | None = None, confirm: bool = False, endpoint: str | None = None) -> str:
    """(elevated, confirm required). Start all VMs/containers on a node"""
    return await nodes.start_all(client, node=node, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_stop_all(node: str | None = None, confirm: bool = False, endpoint: str | None = None) -> str:
    """(elevated, confirm required). Stop all VMs/containers on a node"""
    return await nodes.stop_all(client, node=node, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_suspend_all(node: str | None = None, confirm: bool = False, endpoint: str | None = None) -> str:
    """(elevated, confirm required). Suspend all VMs on a node"""
    return await nodes.suspend_all(client, node=node, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_migrate_all(
    node: str | None = None, target: str | None = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Migrate all VMs/containers on a node"""
    return await nodes.migrate_all(client, node=node, target=target, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_get_node_detailed_status(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). Get detailed node status"""
    return await nodes.get_node_detailed_status(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_services(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). List services on a node."""
    return await nodes.list_services(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_service_state(node: str | None = None, service: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get service state on a node."""
    return await nodes.service_state(client, node=node, service=service, endpoint=endpoint)


@mcp.tool()
async def proxmox_start_service(
    node: str | None = None, service: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Start a service on a node"""
    return await nodes.start_service(client, node=node, service=service, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_stop_service(
    node: str | None = None, service: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Stop a service on a node"""
    return await nodes.stop_service(client, node=node, service=service, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_restart_service(
    node: str | None = None, service: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Restart a service on a node"""
    return await nodes.restart_service(client, node=node, service=service, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_node_dns(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). Get DNS settings for a node."""
    return await nodes.node_dns(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_node_hosts(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). Get hosts file content for a node."""
    return await nodes.node_hosts(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_exec_vm(
    node: str | None = None,
    vmid: int | None = None,
    command: str | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """Execute a command in a VM via QEMU Guest Agent (elevated, confirm required).
    Commands restricted by PROXMOX_ALLOWED_COMMANDS allowlist if configured."""
    return await cloudinit.exec_vm(client, node=node, vmid=vmid, command=command, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_agent_ping(
    node: str | None = None, vmid: int | None = None, confirm: bool = True, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Ping QEMU Guest Agent on a VM"""
    return await cloudinit.agent_ping(client, node=node, vmid=vmid, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_agent_info(node: str | None = None, vmid: int | None = None, endpoint: str | None = None) -> str:
    """(elevated, read-only). Get QEMU Guest Agent info for a VM"""
    return await cloudinit.agent_info(client, node=node, vmid=vmid, endpoint=endpoint)


@mcp.tool()
async def proxmox_agent_network_interfaces(
    node: str | None = None, vmid: int | None = None, endpoint: str | None = None
) -> str:
    """(elevated, read-only). Get network interfaces from QEMU Guest Agent"""
    return await cloudinit.agent_network_interfaces(client, node=node, vmid=vmid, endpoint=endpoint)


@mcp.tool()
async def proxmox_agent_osinfo(node: str | None = None, vmid: int | None = None, endpoint: str | None = None) -> str:
    """(elevated, read-only). Get OS info from QEMU Guest Agent"""
    return await cloudinit.agent_osinfo(client, node=node, vmid=vmid, endpoint=endpoint)


@mcp.tool()
async def proxmox_agent_fsinfo(node: str | None = None, vmid: int | None = None, endpoint: str | None = None) -> str:
    """(elevated, read-only). Get filesystem info from QEMU Guest Agent"""
    return await cloudinit.agent_fsinfo(client, node=node, vmid=vmid, endpoint=endpoint)


@mcp.tool()
async def proxmox_agent_exec_status(
    node: str | None = None, vmid: int | None = None, pid: int | None = None, endpoint: str | None = None
) -> str:
    """(elevated, read-only). Get exec status of a command started via QEMU Guest Agent"""
    return await cloudinit.agent_exec_status(client, node=node, vmid=vmid, pid=pid, endpoint=endpoint)


@mcp.tool()
async def proxmox_agent_fsfreeze(
    node: str | None = None, vmid: int | None = None, confirm: bool = True, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Freeze filesystems on a VM via QEMU Guest Agent"""
    return await cloudinit.agent_fsfreeze(client, node=node, vmid=vmid, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_agent_fsthaw(
    node: str | None = None, vmid: int | None = None, confirm: bool = True, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Thaw filesystems on a VM via QEMU Guest Agent"""
    return await cloudinit.agent_fsthaw(client, node=node, vmid=vmid, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_agent_fstrim(
    node: str | None = None, vmid: int | None = None, confirm: bool = True, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Run fstrim on VM filesystem via QEMU Guest Agent"""
    return await cloudinit.agent_fstrim(client, node=node, vmid=vmid, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_agent_fsfreeze_status(
    node: str | None = None, vmid: int | None = None, endpoint: str | None = None
) -> str:
    """(elevated). Check filesystem freeze status via QEMU Guest Agent"""
    return await cloudinit.agent_fsfreeze_status(client, node=node, vmid=vmid, endpoint=endpoint)


@mcp.tool()
async def proxmox_agent_get_host_name(
    node: str | None = None, vmid: int | None = None, endpoint: str | None = None
) -> str:
    """(elevated). Get VM hostname via QEMU Guest Agent"""
    return await cloudinit.agent_get_host_name(client, node=node, vmid=vmid, endpoint=endpoint)


@mcp.tool()
async def proxmox_agent_get_memory_block_info(
    node: str | None = None, vmid: int | None = None, endpoint: str | None = None
) -> str:
    """(elevated). Get VM memory block info via QEMU Guest Agent"""
    return await cloudinit.agent_get_memory_block_info(client, node=node, vmid=vmid, endpoint=endpoint)


@mcp.tool()
async def proxmox_agent_get_memory_blocks(
    node: str | None = None, vmid: int | None = None, endpoint: str | None = None
) -> str:
    """(elevated). Get VM memory blocks via QEMU Guest Agent"""
    return await cloudinit.agent_get_memory_blocks(client, node=node, vmid=vmid, endpoint=endpoint)


@mcp.tool()
async def proxmox_agent_get_time(node: str | None = None, vmid: int | None = None, endpoint: str | None = None) -> str:
    """(elevated). Get VM time via QEMU Guest Agent"""
    return await cloudinit.agent_get_time(client, node=node, vmid=vmid, endpoint=endpoint)


@mcp.tool()
async def proxmox_agent_get_timezone(
    node: str | None = None, vmid: int | None = None, endpoint: str | None = None
) -> str:
    """(elevated). Get VM timezone via QEMU Guest Agent"""
    return await cloudinit.agent_get_timezone(client, node=node, vmid=vmid, endpoint=endpoint)


@mcp.tool()
async def proxmox_agent_get_users(node: str | None = None, vmid: int | None = None, endpoint: str | None = None) -> str:
    """(elevated). Get VM users via QEMU Guest Agent"""
    return await cloudinit.agent_get_users(client, node=node, vmid=vmid, endpoint=endpoint)


@mcp.tool()
async def proxmox_agent_get_vcpus(node: str | None = None, vmid: int | None = None, endpoint: str | None = None) -> str:
    """(elevated). Get VM VCPU info via QEMU Guest Agent"""
    return await cloudinit.agent_get_vcpus(client, node=node, vmid=vmid, endpoint=endpoint)


@mcp.tool()
async def proxmox_agent_set_user_password(
    node: str | None = None,
    vmid: int | None = None,
    username: str = "",
    password: str = "",
    confirm: bool = True,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Set user password in VM via QEMU Guest Agent"""
    return await cloudinit.agent_set_user_password(
        client,
        node=node,
        vmid=vmid,
        username=username,
        password=password,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_agent_file_read(
    node: str | None = None, vmid: int | None = None, filepath: str = "", endpoint: str | None = None
) -> str:
    """(elevated). Read a file from VM via QEMU Guest Agent"""
    return await cloudinit.agent_file_read(client, node=node, vmid=vmid, filepath=filepath, endpoint=endpoint)


@mcp.tool()
async def proxmox_agent_file_write(
    node: str | None = None,
    vmid: int | None = None,
    filepath: str = "",
    content: str = "",
    confirm: bool = True,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Write a file to VM via QEMU Guest Agent"""
    return await cloudinit.agent_file_write(
        client, node=node, vmid=vmid, filepath=filepath, content=content, confirm=confirm
    )


@mcp.tool()
async def proxmox_agent_shutdown(
    node: str | None = None, vmid: int | None = None, confirm: bool = True, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Shutdown VM via QEMU Guest Agent"""
    return await cloudinit.agent_shutdown(client, node=node, vmid=vmid, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_agent_suspend_disk(
    node: str | None = None, vmid: int | None = None, confirm: bool = True, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Suspend VM to disk via QEMU Guest Agent"""
    return await cloudinit.agent_suspend_disk(client, node=node, vmid=vmid, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_agent_suspend_ram(
    node: str | None = None, vmid: int | None = None, confirm: bool = True, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Suspend VM to RAM via QEMU Guest Agent"""
    return await cloudinit.agent_suspend_ram(client, node=node, vmid=vmid, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_agent_suspend_hybrid(
    node: str | None = None, vmid: int | None = None, confirm: bool = True, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Hybrid suspend VM via QEMU Guest Agent"""
    return await cloudinit.agent_suspend_hybrid(client, node=node, vmid=vmid, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_get_storage(storage: str, node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). Get detailed storage configuration"""
    return await storage_mod.get_storage(client, storage=storage, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_create_storage(
    storage: str,
    type: str = "dir",
    path: str | None = None,
    content: str | None = None,
    nodes: str | None = None,
    server: str | None = None,
    pool: str | None = None,
    monhost: str | None = None,
    fs_name: str | None = None,
    blocksize: str | None = None,
    compression: str | None = None,
    thinpool: str | None = None,
    share: str | None = None,
    subdir: str | None = None,
    username: str | None = None,
    password: str | None = None,
    data_pool: str | None = None,
    keyring: str | None = None,
    krbd: bool | None = None,
    prefech: int | None = None,
    target: str | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Create a storage pool"""
    return await storage_mod.create_storage(
        client,
        storage=storage,
        type=type,
        path=path,
        content=content,
        nodes=nodes,
        server=server,
        pool=pool,
        monhost=monhost,
        fs_name=fs_name,
        blocksize=blocksize,
        compression=compression,
        thinpool=thinpool,
        share=share,
        subdir=subdir,
        username=username,
        password=password,
        data_pool=data_pool,
        keyring=keyring,
        krbd=krbd,
        prefech=prefech,
        target=target,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_update_storage(
    storage: str,
    content: str | None = None,
    nodes: str | None = None,
    delete: str | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
    kwargs: str | None = None,
) -> str:
    """(elevated, confirm required). Update a storage pool configuration"""
    import json

    extra: dict[str, Any] = {}
    if kwargs:
        try:
            parsed = json.loads(kwargs)
            if isinstance(parsed, dict):
                extra = parsed
        except json.JSONDecodeError:
            for pair in kwargs.split():
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    extra[k.strip()] = v.strip()
    return await storage_mod.update_storage(
        client,
        storage=storage,
        content=content,
        nodes=nodes,
        delete=delete,
        confirm=confirm,
        **extra,
    )


@mcp.tool()
async def proxmox_delete_storage(storage: str, confirm: bool = False, endpoint: str | None = None) -> str:
    """(elevated, confirm required). Delete a storage pool"""
    return await storage_mod.delete_storage(client, storage=storage, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_delete_volume(
    node: str | None = None,
    storage: str = "local",
    volume: str = "",
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Delete a volume from storage"""
    return await storage_mod.delete_volume(
        client,
        node=node,
        storage=storage,
        volume=volume,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_prune_backups(
    node: str | None = None,
    storage: str = "local",
    prune_type: str | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Prune backups on storage"""
    return await storage_mod.prune_backups(
        client,
        node=node,
        storage=storage,
        prune_type=prune_type,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_storage_status(node: str | None = None, storage: str = "local", endpoint: str | None = None) -> str:
    """(read-only). Get storage status on a node"""
    return await storage_mod.storage_status(client, node=node, storage=storage, endpoint=endpoint)


@mcp.tool()
async def proxmox_cluster_options(endpoint: str | None = None) -> str:
    """(read-only). Get datacenter options"""
    return await cluster.cluster_options(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_update_cluster_options(
    confirm: bool = False, kwargs: str | None = None, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Update datacenter options"""
    return await cluster.update_cluster_options(client, confirm=confirm, **_parse(kwargs), endpoint=endpoint)


@mcp.tool()
async def proxmox_list_backup_jobs(endpoint: str | None = None) -> str:
    """(read-only). List scheduled backup jobs"""
    return await cluster.list_backup_jobs(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_create_backup_job(
    id: str = "",
    schedule: str | None = None,
    vmid: str | None = None,
    storage: str | None = None,
    mode: str | None = None,
    compress: str | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Create a backup job"""
    return await cluster.create_backup_job(
        client,
        id=id,
        schedule=schedule,
        vmid=vmid,
        storage=storage,
        mode=mode,
        compress=compress,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_delete_backup_job(id: str = "", confirm: bool = False, endpoint: str | None = None) -> str:
    """(elevated, confirm required). Delete a backup job"""
    return await cluster.delete_backup_job(client, id=id, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_move_vm_disk(
    node: str | None = None,
    vmid: int | None = None,
    disk: str = "scsi0",
    storage: str | None = None,
    format: str | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Move a VM disk to different storage"""
    return await lifecycle.move_vm_disk(
        client,
        node=node,
        vmid=vmid,
        disk=disk,
        storage=storage,
        format=format,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_convert_to_template(
    node: str | None = None, vmid: int | None = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Convert a VM to template (destructive, elevated, confirm required)."""
    return await lifecycle.convert_to_template(client, node=node, vmid=vmid, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_convert_lxc_to_template(
    node: str | None = None, vmid: int | None = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Convert an LXC container to template (destructive, elevated, confirm required)."""
    return await lifecycle.convert_lxc_to_template(client, node=node, vmid=vmid, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_lxc_feature_check(
    node: str | None = None, vmid: int | None = None, feature: str = "", endpoint: str | None = None
) -> str:
    """(read-only). Check if a feature is available for an LXC container"""
    return await lifecycle.lxc_feature_check(client, node=node, vmid=vmid, feature=feature, endpoint=endpoint)


@mcp.tool()
async def proxmox_vm_feature_check(
    node: str | None = None, vmid: int | None = None, feature: str = "", endpoint: str | None = None
) -> str:
    """(read-only). Check if a feature is available for a VM"""
    return await lifecycle.vm_feature_check(client, node=node, vmid=vmid, feature=feature, endpoint=endpoint)


@mcp.tool()
async def proxmox_vm_pending_config(
    node: str | None = None, vmid: int | None = None, endpoint: str | None = None
) -> str:
    """(read-only). Get pending configuration changes for a VM"""
    return await lifecycle.vm_pending_config(client, node=node, vmid=vmid, endpoint=endpoint)


@mcp.tool()
async def proxmox_lxc_pending_config(
    node: str | None = None, vmid: int | None = None, endpoint: str | None = None
) -> str:
    """(read-only). Get pending configuration changes for an LXC container"""
    return await lifecycle.lxc_pending_config(client, node=node, vmid=vmid, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_pools(endpoint: str | None = None) -> str:
    """(read-only). List all pools"""
    return await pools.list_pools(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_get_pool(poolid: str, endpoint: str | None = None) -> str:
    """(read-only). Get details of a pool"""
    return await pools.get_pool(client, poolid=poolid, endpoint=endpoint)


@mcp.tool()
async def proxmox_create_pool(
    poolid: str = "", comment: str | None = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Create a pool"""
    return await pools.create_pool(client, poolid=poolid, comment=comment, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_update_pool(
    poolid: str = "",
    comment: str | None = None,
    delete: str | None = None,
    members: str | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Update a pool"""
    return await pools.update_pool(
        client,
        poolid=poolid,
        comment=comment,
        delete=delete,
        members=members,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_delete_pool(poolid: str = "", confirm: bool = False, endpoint: str | None = None) -> str:
    """(elevated, confirm required). Delete a pool"""
    return await pools.delete_pool(client, poolid=poolid, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_task_log(
    upid: str, node: str | None = None, limit: int | None = None, endpoint: str | None = None
) -> str:
    """(read-only). Get task log entries"""
    return await tasks.task_log(client, upid=upid, node=node, limit=limit, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_endpoints() -> str:
    """(read-only). List all configured Proxmox endpoints with their status, node info, and health."""
    return client.list_endpoints()


@mcp.tool()
async def proxmox_cluster_status(endpoint: str | None = None) -> str:
    """(read-only). Get cluster quorum and health status"""
    return await discovery.cluster_status(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_ceph_status(endpoint: str | None = None) -> str:
    """(read-only). Get Ceph cluster status"""
    return await ceph.ceph_status(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_ceph_metadata(endpoint: str | None = None) -> str:
    """(read-only). Get Ceph cluster metadata"""
    return await ceph.ceph_metadata(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_node_ceph_status(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). Get Ceph status for a specific node"""
    return await ceph.node_ceph_status(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_cluster_resources(type: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). List all cluster resources, optionally filtered by type (vm, storage, node, sdn)."""
    return await discovery.cluster_resources(client, type=type, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_cluster_firewall_rules(endpoint: str | None = None) -> str:
    """(read-only). List cluster-level firewall rules."""
    return await firewall.list_cluster_firewall_rules(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_create_cluster_firewall_rule(
    action: str = "ACCEPT",
    dptype: str = "in",
    dport: str | None = None,
    sport: str | None = None,
    proto: str | None = None,
    source: str | None = None,
    dest: str | None = None,
    iface: str | None = None,
    comment: str | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """Create a cluster firewall rule (elevated, confirm required).
    dptype: traffic direction — 'in' (default), 'out', or 'forward'.
    Maps to PVE's 'type' field."""
    return await firewall.create_cluster_firewall_rule(
        client,
        action=action,
        dptype=dptype,
        dport=dport,
        sport=sport,
        proto=proto,
        source=source,
        dest=dest,
        iface=iface,
        comment=comment,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_get_cluster_firewall_rule(pos: int = 0, endpoint: str | None = None) -> str:
    """(read-only). Get a specific cluster firewall rule by position."""
    return await firewall.get_cluster_firewall_rule(client, pos=pos, endpoint=endpoint)


@mcp.tool()
async def proxmox_update_cluster_firewall_rule(
    pos: int = 0,
    action: str | None = None,
    dptype: str | None = None,
    dport: str | None = None,
    sport: str | None = None,
    proto: str | None = None,
    source: str | None = None,
    dest: str | None = None,
    iface: str | None = None,
    comment: str | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Update a cluster firewall rule"""
    return await firewall.update_cluster_firewall_rule(
        client,
        pos=pos,
        action=action,
        dptype=dptype,
        dport=dport,
        sport=sport,
        proto=proto,
        source=source,
        dest=dest,
        iface=iface,
        comment=comment,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_delete_cluster_firewall_rule(pos: int = 0, confirm: bool = False, endpoint: str | None = None) -> str:
    """(elevated, confirm required). Delete a cluster firewall rule"""
    return await firewall.delete_cluster_firewall_rule(client, pos=pos, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_get_cluster_firewall_options(endpoint: str | None = None) -> str:
    """(read-only). Get cluster firewall options"""
    return await firewall.get_cluster_firewall_options(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_set_cluster_firewall_options(
    confirm: bool = False, kwargs: str | None = None, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Set cluster firewall options"""
    return await firewall.set_cluster_firewall_options(client, confirm=confirm, **_parse(kwargs), endpoint=endpoint)


@mcp.tool()
async def proxmox_list_cluster_firewall_aliases(endpoint: str | None = None) -> str:
    """(read-only). List cluster firewall aliases."""
    return await firewall.list_cluster_firewall_aliases(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_create_cluster_firewall_alias(
    name: str = "", cidr: str = "", comment: str | None = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Create a cluster firewall alias"""
    return await firewall.create_cluster_firewall_alias(
        client,
        name=name,
        cidr=cidr,
        comment=comment,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_delete_cluster_firewall_alias(
    name: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Delete a cluster firewall alias"""
    return await firewall.delete_cluster_firewall_alias(client, name=name, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_cluster_firewall_ipsets(endpoint: str | None = None) -> str:
    """(read-only). List cluster firewall IPSets."""
    return await firewall.list_cluster_firewall_ipsets(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_cluster_firewall_refs(endpoint: str | None = None) -> str:
    """(read-only). List cluster firewall references (IPSet/Alias)."""
    return await firewall.list_cluster_firewall_refs(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_node_firewall_rules(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). List node-level firewall rules."""
    return await firewall.list_node_firewall_rules(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_create_node_firewall_rule(
    node: str | None = None,
    action: str = "ACCEPT",
    dptype: str = "in",
    dport: str | None = None,
    sport: str | None = None,
    proto: str | None = None,
    source: str | None = None,
    dest: str | None = None,
    iface: str | None = None,
    comment: str | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """Create a node firewall rule (elevated, confirm required).
    dptype: traffic direction — 'in' (default), 'out', or 'forward'.
    Maps to PVE's 'type' field."""
    return await firewall.create_node_firewall_rule(
        client,
        node=node,
        action=action,
        dptype=dptype,
        dport=dport,
        sport=sport,
        proto=proto,
        source=source,
        dest=dest,
        iface=iface,
        comment=comment,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_delete_node_firewall_rule(
    node: str | None = None, pos: int = 0, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Delete a node firewall rule"""
    return await firewall.delete_node_firewall_rule(client, node=node, pos=pos, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_get_node_firewall_options(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). Get node firewall options"""
    return await firewall.get_node_firewall_options(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_vm_firewall_rules(
    node: str | None = None, vmid: int | None = None, vmtype: str = "qemu", endpoint: str | None = None
) -> str:
    """(read-only). List VM-level firewall rules. vmtype: 'qemu' or 'lxc'."""
    return await firewall.list_vm_firewall_rules(client, node=node, vmid=vmid, vmtype=vmtype, endpoint=endpoint)


@mcp.tool()
async def proxmox_create_vm_firewall_rule(
    node: str | None = None,
    vmid: int | None = None,
    vmtype: str = "qemu",
    action: str = "ACCEPT",
    dptype: str = "in",
    dport: str | None = None,
    sport: str | None = None,
    proto: str | None = None,
    source: str | None = None,
    dest: str | None = None,
    iface: str | None = None,
    comment: str | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """Create a VM firewall rule (elevated, confirm required).
    vmtype: 'qemu' or 'lxc'.
    dptype: traffic direction — 'in' (default), 'out', or 'forward'.
    Maps to PVE's 'type' field."""
    return await firewall.create_vm_firewall_rule(
        client,
        node=node,
        vmid=vmid,
        vmtype=vmtype,
        action=action,
        dptype=dptype,
        dport=dport,
        sport=sport,
        proto=proto,
        source=source,
        dest=dest,
        iface=iface,
        comment=comment,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_delete_vm_firewall_rule(
    node: str | None = None,
    vmid: int | None = None,
    pos: int = 0,
    vmtype: str = "qemu",
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Delete a VM firewall rule vmtype: 'qemu' or 'lxc'."""
    return await firewall.delete_vm_firewall_rule(
        client,
        node=node,
        vmid=vmid,
        pos=pos,
        vmtype=vmtype,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_get_vm_firewall_options(
    node: str | None = None, vmid: int | None = None, vmtype: str = "qemu", endpoint: str | None = None
) -> str:
    """(read-only). Get VM firewall options vmtype: 'qemu' or 'lxc'."""
    return await firewall.get_vm_firewall_options(client, node=node, vmid=vmid, vmtype=vmtype, endpoint=endpoint)


@mcp.tool()
async def proxmox_get_vm_firewall_alias(
    node: str | None = None, vmid: int | None = None, name: str = "", vmtype: str = "qemu", endpoint: str | None = None
) -> str:
    """(read-only). Get a VM firewall alias vmtype: 'qemu' or 'lxc'."""
    return await firewall.get_vm_firewall_alias(
        client, node=node, vmid=vmid, name=name, vmtype=vmtype, endpoint=endpoint
    )


@mcp.tool()
async def proxmox_create_vm_firewall_alias(
    node: str | None = None,
    vmid: int | None = None,
    name: str = "",
    cidr: str = "",
    vmtype: str = "qemu",
    comment: str | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Create a VM firewall alias vmtype: 'qemu' or 'lxc'."""
    return await firewall.create_vm_firewall_alias(
        client,
        node=node,
        vmid=vmid,
        name=name,
        cidr=cidr,
        vmtype=vmtype,
        comment=comment,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_delete_vm_firewall_alias(
    node: str | None = None,
    vmid: int | None = None,
    name: str = "",
    vmtype: str = "qemu",
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Delete a VM firewall alias vmtype: 'qemu' or 'lxc'."""
    return await firewall.delete_vm_firewall_alias(
        client,
        node=node,
        vmid=vmid,
        name=name,
        vmtype=vmtype,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_list_vm_firewall_ipsets(
    node: str | None = None, vmid: int | None = None, vmtype: str = "qemu", endpoint: str | None = None
) -> str:
    """(read-only). List VM firewall IPSets vmtype: 'qemu' or 'lxc'."""
    return await firewall.list_vm_firewall_ipsets(client, node=node, vmid=vmid, vmtype=vmtype, endpoint=endpoint)


@mcp.tool()
async def proxmox_get_vm_firewall_rule(
    node: str | None = None, vmid: int | None = None, pos: int = 0, vmtype: str = "qemu", endpoint: str | None = None
) -> str:
    """(read-only). Get a specific VM firewall rule by position vmtype: 'qemu' or 'lxc'."""
    return await firewall.get_vm_firewall_rule(client, node=node, vmid=vmid, pos=pos, vmtype=vmtype, endpoint=endpoint)


@mcp.tool()
async def proxmox_update_vm_firewall_rule(
    node: str | None = None,
    vmid: int | None = None,
    pos: int = 0,
    vmtype: str = "qemu",
    action: str | None = None,
    dptype: str | None = None,
    dport: str | None = None,
    sport: str | None = None,
    proto: str | None = None,
    source: str | None = None,
    dest: str | None = None,
    iface: str | None = None,
    comment: str | None = None,
    confirm: bool = False,
    kwargs: str | None = None,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Update a VM firewall rule vmtype: 'qemu' or 'lxc'. Requires confirm=true."""
    return await firewall.update_vm_firewall_rule(
        client,
        node=node,
        vmid=vmid,
        pos=pos,
        vmtype=vmtype,
        action=action,
        dptype=dptype,
        dport=dport,
        sport=sport,
        proto=proto,
        source=source,
        dest=dest,
        iface=iface,
        comment=comment,
        confirm=confirm,
        **_parse(kwargs),
    )


@mcp.tool()
async def proxmox_set_vm_firewall_options(
    node: str | None = None,
    vmid: int | None = None,
    vmtype: str = "qemu",
    confirm: bool = False,
    kwargs: str | None = None,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Set VM firewall options vmtype: 'qemu' or 'lxc'. Requires confirm=true."""
    return await firewall.set_vm_firewall_options(
        client, node=node, vmid=vmid, vmtype=vmtype, confirm=confirm, **_parse(kwargs)
    )


@mcp.tool()
async def proxmox_list_vm_firewall_aliases(
    node: str | None = None, vmid: int | None = None, vmtype: str = "qemu", endpoint: str | None = None
) -> str:
    """(read-only). List VM firewall aliases vmtype: 'qemu' or 'lxc'."""
    return await firewall.list_vm_firewall_aliases(client, node=node, vmid=vmid, vmtype=vmtype, endpoint=endpoint)


@mcp.tool()
async def proxmox_update_vm_firewall_alias(
    node: str | None = None,
    vmid: int | None = None,
    name: str = "",
    cidr: str | None = None,
    vmtype: str = "qemu",
    comment: str | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Update a VM firewall alias vmtype: 'qemu' or 'lxc'. Requires confirm=true."""
    return await firewall.update_vm_firewall_alias(
        client,
        node=node,
        vmid=vmid,
        name=name,
        cidr=cidr,
        vmtype=vmtype,
        comment=comment,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_vm_firewall_log(
    node: str | None = None, vmid: int | None = None, vmtype: str = "qemu", endpoint: str | None = None
) -> str:
    """(read-only). Read VM firewall log vmtype: 'qemu' or 'lxc'."""
    return await firewall.vm_firewall_log(client, node=node, vmid=vmid, vmtype=vmtype, endpoint=endpoint)


@mcp.tool()
async def proxmox_vm_firewall_refs(
    node: str | None = None, vmid: int | None = None, vmtype: str = "qemu", endpoint: str | None = None
) -> str:
    """(read-only). List VM firewall IPSet/Alias references vmtype: 'qemu' or 'lxc'."""
    return await firewall.vm_firewall_refs(client, node=node, vmid=vmid, vmtype=vmtype, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_vm_firewall_ipset_content(
    node: str | None = None, vmid: int | None = None, name: str = "", vmtype: str = "qemu", endpoint: str | None = None
) -> str:
    """(read-only). List VM firewall IPSet content vmtype: 'qemu' or 'lxc'."""
    return await firewall.list_vm_firewall_ipset_content(
        client, node=node, vmid=vmid, name=name, vmtype=vmtype, endpoint=endpoint
    )


@mcp.tool()
async def proxmox_create_vm_firewall_ipset(
    node: str | None = None,
    vmid: int | None = None,
    name: str = "",
    vmtype: str = "qemu",
    comment: str | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Create a VM firewall IPSet vmtype: 'qemu' or 'lxc'. Requires confirm=true."""
    return await firewall.create_vm_firewall_ipset(
        client,
        node=node,
        vmid=vmid,
        name=name,
        vmtype=vmtype,
        comment=comment,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_delete_vm_firewall_ipset(
    node: str | None = None,
    vmid: int | None = None,
    name: str = "",
    vmtype: str = "qemu",
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Delete a VM firewall IPSet vmtype: 'qemu' or 'lxc'. Requires confirm=true."""
    return await firewall.delete_vm_firewall_ipset(
        client, node=node, vmid=vmid, name=name, vmtype=vmtype, confirm=confirm
    )


@mcp.tool()
async def proxmox_add_vm_firewall_ipset_entry(
    node: str | None = None,
    vmid: int | None = None,
    name: str = "",
    cidr: str = "",
    vmtype: str = "qemu",
    comment: str | None = None,
    nomatch: int | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Add IP/CIDR entry to VM firewall IPSet.

    vmtype: 'qemu' or 'lxc'. Requires confirm=true.
    """
    return await firewall.add_vm_firewall_ipset_entry(
        client,
        node=node,
        vmid=vmid,
        name=name,
        cidr=cidr,
        vmtype=vmtype,
        comment=comment,
        nomatch=nomatch,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_get_vm_firewall_ipset_entry(
    node: str | None = None,
    vmid: int | None = None,
    name: str = "",
    cidr: str = "",
    vmtype: str = "qemu",
    endpoint: str | None = None,
) -> str:
    """(read-only). Get a specific VM firewall IPSet entry vmtype: 'qemu' or 'lxc'."""
    return await firewall.get_vm_firewall_ipset_entry(
        client, node=node, vmid=vmid, name=name, cidr=cidr, vmtype=vmtype, endpoint=endpoint
    )


@mcp.tool()
async def proxmox_update_vm_firewall_ipset_entry(
    node: str | None = None,
    vmid: int | None = None,
    name: str = "",
    cidr: str = "",
    vmtype: str = "qemu",
    comment: str | None = None,
    nomatch: int | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Update a VM firewall IPSet entry vmtype: 'qemu' or 'lxc'. Requires confirm=true."""
    return await firewall.update_vm_firewall_ipset_entry(
        client,
        node=node,
        vmid=vmid,
        name=name,
        cidr=cidr,
        vmtype=vmtype,
        comment=comment,
        nomatch=nomatch,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_delete_vm_firewall_ipset_entry(
    node: str | None = None,
    vmid: int | None = None,
    name: str = "",
    cidr: str = "",
    vmtype: str = "qemu",
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Delete a VM firewall IPSet entry vmtype: 'qemu' or 'lxc'. Requires confirm=true."""
    return await firewall.delete_vm_firewall_ipset_entry(
        client,
        node=node,
        vmid=vmid,
        name=name,
        cidr=cidr,
        vmtype=vmtype,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_list_cluster_firewall_ipset_content(name: str = "", endpoint: str | None = None) -> str:
    """(read-only). List cluster firewall IPSet content"""
    return await firewall.list_cluster_firewall_ipset_content(client, name=name, endpoint=endpoint)


@mcp.tool()
async def proxmox_create_cluster_firewall_ipset(
    name: str = "", comment: str | None = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Create a cluster firewall IPSet"""
    return await firewall.create_cluster_firewall_ipset(
        client, name=name, comment=comment, confirm=confirm, endpoint=endpoint
    )


@mcp.tool()
async def proxmox_delete_cluster_firewall_ipset(
    name: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Delete a cluster firewall IPSet"""
    return await firewall.delete_cluster_firewall_ipset(client, name=name, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_get_cluster_firewall_alias(name: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get a cluster firewall alias"""
    return await firewall.get_cluster_firewall_alias(client, name=name, endpoint=endpoint)


@mcp.tool()
async def proxmox_update_cluster_firewall_alias(
    name: str = "",
    cidr: str | None = None,
    comment: str | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Update a cluster firewall alias"""
    return await firewall.update_cluster_firewall_alias(
        client, name=name, cidr=cidr, comment=comment, confirm=confirm, endpoint=endpoint
    )


@mcp.tool()
async def proxmox_update_cluster_firewall_ipset(
    name: str = "", comment: str | None = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Update a cluster firewall IPSet"""
    return await firewall.update_cluster_firewall_ipset(
        client, name=name, comment=comment, confirm=confirm, endpoint=endpoint
    )


@mcp.tool()
async def proxmox_add_cluster_firewall_ipset_entry(
    name: str = "",
    cidr: str = "",
    comment: str | None = None,
    nomatch: int | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Add an entry to a cluster firewall IPSet"""
    return await firewall.add_cluster_firewall_ipset_entry(
        client,
        name=name,
        cidr=cidr,
        comment=comment,
        nomatch=nomatch,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_get_cluster_firewall_ipset_entry(name: str = "", cidr: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get a cluster firewall IPSet entry"""
    return await firewall.get_cluster_firewall_ipset_entry(client, name=name, cidr=cidr, endpoint=endpoint)


@mcp.tool()
async def proxmox_delete_cluster_firewall_ipset_entry(
    name: str = "", cidr: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Delete an entry from a cluster firewall IPSet"""
    return await firewall.delete_cluster_firewall_ipset_entry(
        client, name=name, cidr=cidr, confirm=confirm, endpoint=endpoint
    )


@mcp.tool()
async def proxmox_list_cluster_firewall_macros(endpoint: str | None = None) -> str:
    """(read-only). List cluster firewall macros"""
    return await firewall.list_cluster_firewall_macros(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_node_firewall_aliases(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). List node firewall aliases"""
    return await firewall.list_node_firewall_aliases(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_node_firewall_log(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). Get node firewall log"""
    return await firewall.node_firewall_log(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_get_node_firewall_rule(node: str | None = None, pos: int = 0, endpoint: str | None = None) -> str:
    """(read-only). Get a specific node firewall rule"""
    return await firewall.get_node_firewall_rule(client, node=node, pos=pos, endpoint=endpoint)


@mcp.tool()
async def proxmox_update_node_firewall_rule(
    node: str | None = None,
    pos: int = 0,
    action: str | None = None,
    dptype: str | None = None,
    dport: str | None = None,
    sport: str | None = None,
    proto: str | None = None,
    source: str | None = None,
    dest: str | None = None,
    iface: str | None = None,
    comment: str | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Update a node firewall rule"""
    return await firewall.update_node_firewall_rule(
        client,
        node=node,
        pos=pos,
        action=action,
        dptype=dptype,
        dport=dport,
        sport=sport,
        proto=proto,
        source=source,
        dest=dest,
        iface=iface,
        comment=comment,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_set_node_firewall_options(
    node: str | None = None, confirm: bool = False, kwargs: str | None = None, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Set node firewall options"""
    return await firewall.set_node_firewall_options(
        client, node=node, confirm=confirm, **_parse(kwargs), endpoint=endpoint
    )


@mcp.tool()
async def proxmox_list_node_firewall_ipsets(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). List node firewall IPSets"""
    return await firewall.list_node_firewall_ipsets(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_ha_resources(endpoint: str | None = None) -> str:
    """(read-only). List HA resources in the cluster"""
    return await ha.list_ha_resources(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_create_ha_resource(
    sid: str = "",
    group: str | None = None,
    comment: str | None = None,
    max_relocate: int | None = None,
    max_restart: int | None = None,
    state: str | None = None,
    type: str | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Create an HA resource"""
    return await ha.create_ha_resource(
        client,
        sid=sid,
        group=group,
        comment=comment,
        max_relocate=max_relocate,
        max_restart=max_restart,
        state=state,
        type=type,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_get_ha_resource(sid: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get HA resource configuration"""
    return await ha.get_ha_resource(client, sid=sid, endpoint=endpoint)


@mcp.tool()
async def proxmox_update_ha_resource(
    sid: str = "",
    group: str | None = None,
    comment: str | None = None,
    max_relocate: int | None = None,
    max_restart: int | None = None,
    state: str | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Update an HA resource"""
    return await ha.update_ha_resource(
        client,
        sid=sid,
        group=group,
        comment=comment,
        max_relocate=max_relocate,
        max_restart=max_restart,
        state=state,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_delete_ha_resource(sid: str = "", confirm: bool = False, endpoint: str | None = None) -> str:
    """(elevated, confirm required). Delete an HA resource"""
    return await ha.delete_ha_resource(client, sid=sid, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_migrate_ha_resource(
    sid: str = "", node: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Migrate an HA resource to another node"""
    return await ha.migrate_ha_resource(client, sid=sid, node=node, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_relocate_ha_resource(
    sid: str = "", node: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Relocate an HA resource to another node."""
    return await ha.relocate_ha_resource(client, sid=sid, node=node, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_ha_groups(endpoint: str | None = None) -> str:
    """(read-only). List HA groups"""
    return await ha.list_ha_groups(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_ha_status(endpoint: str | None = None) -> str:
    """(read-only). Get HA manager status"""
    return await ha.ha_status(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_replication(endpoint: str | None = None) -> str:
    """(read-only). List replication jobs in the cluster"""
    return await replication.list_replication(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_create_replication(
    id: str = "",
    source: str | None = None,
    target: str | None = None,
    schedule: str | None = None,
    comment: str | None = None,
    disable: bool | None = None,
    rate: float | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Create a replication job"""
    return await replication.create_replication(
        client,
        id=id,
        source=source,
        target=target,
        schedule=schedule,
        comment=comment,
        disable=disable,
        rate=rate,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_get_replication(id: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get replication job configuration"""
    return await replication.get_replication(client, id=id, endpoint=endpoint)


@mcp.tool()
async def proxmox_update_replication(
    id: str = "",
    source: str | None = None,
    target: str | None = None,
    schedule: str | None = None,
    comment: str | None = None,
    disable: bool | None = None,
    rate: float | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Update a replication job"""
    return await replication.update_replication(
        client,
        id=id,
        source=source,
        target=target,
        schedule=schedule,
        comment=comment,
        disable=disable,
        rate=rate,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_delete_replication(id: str = "", confirm: bool = False, endpoint: str | None = None) -> str:
    """(elevated, confirm required). Delete a replication job"""
    return await replication.delete_replication(client, id=id, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_node_replication(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). List replication jobs on a node"""
    return await replication.list_node_replication(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_schedule_replication(
    node: str | None = None, id: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Schedule a replication job now"""
    return await replication.schedule_replication(client, node=node, id=id, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_get_replication_status(node: str | None = None, id: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get replication job status on a node"""
    return await replication.get_replication_status(client, node=node, id=id, endpoint=endpoint)


@mcp.tool()
async def proxmox_get_replication_log(node: str | None = None, id: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get replication job log on a node"""
    return await replication.get_replication_log(client, node=node, id=id, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_disks(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). List local disks on a node"""
    return await disks.list_disks(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_get_disk_smart(node: str | None = None, disk: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get SMART health of a disk"""
    return await disks.get_disk_smart(client, node=node, disk=disk, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_lvm(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). List LVM volume groups on a node"""
    return await disks.list_lvm(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_lvmthin(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). List LVM thin pools on a node"""
    return await disks.list_lvmthin(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_zfs(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). List ZFS pools on a node"""
    return await disks.list_zfs(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_init_gpt(
    node: str | None = None, disk: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Initialize a disk with GPT"""
    return await disks.init_gpt(client, node=node, disk=disk, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_wipe_disk(
    node: str | None = None, disk: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Wipe a disk"""
    return await disks.wipe_disk(client, node=node, disk=disk, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_zfs_detail(node: str | None = None, name: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get ZFS pool details"""
    return await disks.zfs_detail(client, node=node, name=name, endpoint=endpoint)


@mcp.tool()
async def proxmox_zfs_create(
    node: str | None = None,
    name: str = "",
    devices: str = "",
    raidlevel: str | None = None,
    ashift: int | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Create a ZFS pool."""
    return await disks.zfs_create(
        client,
        node=node,
        name=name,
        devices=devices,
        raidlevel=raidlevel,
        ashift=ashift,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_zfs_destroy(
    node: str | None = None, name: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Destroy a ZFS pool."""
    return await disks.zfs_destroy(client, node=node, name=name, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_lvm_create(
    node: str | None = None, name: str = "", devices: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Create an LVM volume group."""
    return await disks.lvm_create(client, node=node, name=name, devices=devices, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_lvm_detail(node: str | None = None, name: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get LVM volume group details"""
    return await disks.lvm_detail(client, node=node, name=name, endpoint=endpoint)


@mcp.tool()
async def proxmox_lvm_destroy(
    node: str | None = None, name: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Destroy an LVM volume group."""
    return await disks.lvm_destroy(client, node=node, name=name, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_lvmthin_create(
    node: str | None = None, name: str = "", devices: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Create an LVM thin pool."""
    return await disks.lvmthin_create(client, node=node, name=name, devices=devices, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_lvmthin_destroy(
    node: str | None = None, name: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Destroy an LVM thin pool."""
    return await disks.lvmthin_destroy(client, node=node, name=name, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_directory_list(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). List PVE managed directory storages"""
    return await disks.directory_list(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_directory_create(
    node: str | None = None, name: str = "", devices: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Create a directory storage on a disk."""
    return await disks.directory_create(
        client, node=node, name=name, devices=devices, confirm=confirm, endpoint=endpoint
    )


@mcp.tool()
async def proxmox_directory_destroy(
    node: str | None = None, name: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Destroy a directory storage."""
    return await disks.directory_destroy(client, node=node, name=name, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_pci(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). List PCI devices on a node"""
    return await hardware.list_pci(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_usb(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). List USB devices on a node"""
    return await hardware.list_usb(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_get_pci_device(node: str | None = None, pciid: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get PCI device details"""
    return await hardware.get_pci_device(client, node=node, pciid=pciid, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_pci_mdev(node: str | None = None, pciid: str = "", endpoint: str | None = None) -> str:
    """(read-only). List mediated device types for a PCI device"""
    return await hardware.list_pci_mdev(client, node=node, pciid=pciid, endpoint=endpoint)


@mcp.tool()
async def proxmox_cloudinit_dump(
    node: str | None = None, vmid: int | None = None, type: str | None = None, endpoint: str | None = None
) -> str:
    """(read-only). Dump cloud-init configuration for a VM"""
    return await cloudinit.cloudinit_dump(client, node=node, vmid=vmid, type=type, endpoint=endpoint)


@mcp.tool()
async def proxmox_node_version(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). Get Proxmox VE version on a node"""
    return await discovery.node_version(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_node_dns_discovery(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). Get DNS settings for a node via discovery"""
    return await discovery.node_dns(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_node_hosts_discovery(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). Get hosts file content for a node via discovery"""
    return await discovery.node_hosts(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_node_time(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). Get node time and timezone"""
    return await discovery.node_time(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_node_syslog(
    node: str | None = None,
    limit: int | None = None,
    start: int | None = None,
    since: str | None = None,
    until: str | None = None,
    endpoint: str | None = None,
) -> str:
    """(read-only). Get node syslog entries"""
    return await discovery.node_syslog(
        client, node=node, limit=limit, start=start, since=since, until=until, endpoint=endpoint
    )


@mcp.tool()
async def proxmox_node_journal(
    node: str | None = None,
    limit: int | None = None,
    since: str | None = None,
    until: str | None = None,
    service: str | None = None,
    endpoint: str | None = None,
) -> str:
    """(read-only). Get node journal log entries"""
    return await discovery.node_journal(
        client, node=node, limit=limit, since=since, until=until, service=service, endpoint=endpoint
    )


@mcp.tool()
async def proxmox_cluster_log(limit: int | None = None, endpoint: str | None = None) -> str:
    """(read-only). Get cluster log entries"""
    return await discovery.cluster_log(client, limit=limit, endpoint=endpoint)


@mcp.tool()
async def proxmox_stop_task(
    node: str | None = None, upid: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Stop a running task"""
    return await tasks.stop_task(client, node=node, upid=upid, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_acme_accounts(endpoint: str | None = None) -> str:
    """(read-only). List ACME accounts"""
    return await acme.list_acme_accounts(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_get_acme_account(name: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get ACME account details"""
    return await acme.get_acme_account(client, name=name, endpoint=endpoint)


@mcp.tool()
async def proxmox_create_acme_account(
    name: str = "", contact: str = "", directory: str | None = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Create an ACME account"""
    return await acme.create_acme_account(
        client,
        name=name,
        contact=contact,
        directory=directory,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_delete_acme_account(name: str = "", confirm: bool = False, endpoint: str | None = None) -> str:
    """(elevated, confirm required). Delete an ACME account"""
    return await acme.delete_acme_account(client, name=name, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_update_acme_account(
    name: str = "",
    contact: str | None = None,
    confirm: bool = False,
    kwargs: str | None = None,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Update an ACME account"""
    return await acme.update_acme_account(
        client, name=name, contact=contact, confirm=confirm, **_parse(kwargs), endpoint=endpoint
    )


@mcp.tool()
async def proxmox_list_acme_directories(endpoint: str | None = None) -> str:
    """(read-only). List ACME directories"""
    return await acme.list_acme_directories(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_acme_plugins(endpoint: str | None = None) -> str:
    """(read-only). List ACME plugins"""
    return await acme.list_acme_plugins(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_create_acme_plugin(
    id: str = "", type: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Create an ACME plugin"""
    return await acme.create_acme_plugin(client, id=id, type=type, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_delete_acme_plugin(id: str = "", confirm: bool = False, endpoint: str | None = None) -> str:
    """(elevated, confirm required). Delete an ACME plugin"""
    return await acme.delete_acme_plugin(client, id=id, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_update_acme_plugin(
    id: str = "", confirm: bool = False, kwargs: str | None = None, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Update an ACME plugin"""
    return await acme.update_acme_plugin(client, id=id, confirm=confirm, **_parse(kwargs), endpoint=endpoint)


@mcp.tool()
async def proxmox_get_acme_plugin(id: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get ACME plugin configuration"""
    return await acme.get_acme_plugin(client, id=id, endpoint=endpoint)


@mcp.tool()
async def proxmox_acme_meta(endpoint: str | None = None) -> str:
    """(read-only). Get ACME directory meta information"""
    return await acme.acme_meta(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_cluster_config(endpoint: str | None = None) -> str:
    """(read-only). Get cluster corosync config"""
    return await cluster.cluster_config(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_cluster_config_nodes(endpoint: str | None = None) -> str:
    """(read-only). Get cluster config nodes"""
    return await cluster.cluster_config_nodes(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_cluster_config_join(endpoint: str | None = None) -> str:
    """(read-only). Get cluster join info"""
    return await cluster.cluster_config_join(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_get_backup_job(id: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get backup job configuration"""
    return await cluster.get_backup_job(client, id=id, endpoint=endpoint)


@mcp.tool()
async def proxmox_update_backup_job(
    id: str = "", confirm: bool = False, kwargs: str | None = None, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Update a backup job"""
    return await cluster.update_backup_job(client, id=id, confirm=confirm, **_parse(kwargs), endpoint=endpoint)


@mcp.tool()
async def proxmox_backup_info_not_backed_up(endpoint: str | None = None) -> str:
    """(read-only). List guests not covered by any backup job"""
    return await cluster.backup_info_not_backed_up(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_api_version(endpoint: str | None = None) -> str:
    """(read-only). Get Proxmox API version"""
    return await cluster.api_version(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_cluster_config_totem(endpoint: str | None = None) -> str:
    """(read-only). Get cluster corosync totem config"""
    return await cluster.cluster_config_totem(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_cluster_config_qdevice(endpoint: str | None = None) -> str:
    """(read-only). Get cluster QDevice status"""
    return await cluster.cluster_config_qdevice(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_backup_info_index(endpoint: str | None = None) -> str:
    """(read-only). Get backup info index"""
    return await cluster.backup_info_index(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_backup_job_included_volumes(id: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get backup job included volumes"""
    return await cluster.backup_job_included_volumes(client, id=id, endpoint=endpoint)


@mcp.tool()
async def proxmox_update_dns(
    node: str | None = None,
    dns1: str | None = None,
    dns2: str | None = None,
    search: str | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Update DNS settings for a node"""
    return await nodes.update_dns(
        client, node=node, dns1=dns1, dns2=dns2, search=search, confirm=confirm, endpoint=endpoint
    )


@mcp.tool()
async def proxmox_update_hosts(
    node: str | None = None, data: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Update hosts file for a node"""
    return await nodes.update_hosts(client, node=node, data=data, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_update_time(
    node: str | None = None, timezone: str | None = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Update timezone for a node"""
    return await nodes.update_time(client, node=node, timezone=timezone, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_vzdump_defaults(
    node: str | None = None, storage: str | None = None, endpoint: str | None = None
) -> str:
    """(read-only). Get VZDump backup defaults for a node"""
    return await nodes.vzdump_defaults(client, node=node, storage=storage, endpoint=endpoint)


@mcp.tool()
async def proxmox_extract_backup_config(node: str | None = None, archive: str = "", endpoint: str | None = None) -> str:
    """(read-only). Extract config from a backup archive"""
    return await nodes.extract_backup_config(client, node=node, archive=archive, endpoint=endpoint)


@mcp.tool()
async def proxmox_get_volume_info(
    node: str | None = None, storage: str = "local", volume: str = "", endpoint: str | None = None
) -> str:
    """(read-only). Get detailed volume info"""
    return await storage_mod.get_volume_info(client, node=node, storage=storage, volume=volume, endpoint=endpoint)


@mcp.tool()
async def proxmox_node_storage_list(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). List all storage on a node"""
    return await storage_mod.node_storage_list(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_scan_nfs(node: str | None = None, server: str = "", endpoint: str | None = None) -> str:
    """(read-only). Scan for NFS exports on a remote server."""
    return await nodes.scan_nfs(client, node=node, server=server, endpoint=endpoint)


@mcp.tool()
async def proxmox_scan_iscsi(node: str | None = None, server: str = "", endpoint: str | None = None) -> str:
    """(read-only). Scan for iSCSI targets on a remote server."""
    return await nodes.scan_iscsi(client, node=node, server=server, endpoint=endpoint)


@mcp.tool()
async def proxmox_scan_lvm(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). List LVM volume groups on a node."""
    return await nodes.scan_lvm(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_scan_lvmthin(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). List LVM thin pools on a node."""
    return await nodes.scan_lvmthin(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_scan_cifs(node: str | None = None, server: str = "", endpoint: str | None = None) -> str:
    """(read-only). Scan for CIFS shares on a remote server."""
    return await nodes.scan_cifs(client, node=node, server=server, endpoint=endpoint)


@mcp.tool()
async def proxmox_scan_zfs(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). List ZFS pools on a node."""
    return await nodes.scan_zfs(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_scan_pbs(
    node: str | None = None,
    server: str = "",
    username: str | None = None,
    password: str | None = None,
    endpoint: str | None = None,
) -> str:
    """(read-only). Scan for Proxmox Backup Server datastores."""
    return await nodes.scan_pbs(
        client, node=node, server=server, username=username, password=password, endpoint=endpoint
    )


@mcp.tool()
async def proxmox_get_subscription(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). Get node subscription info"""
    return await nodes.get_subscription(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_update_subscription(
    node: str | None = None, key: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Set subscription key on a node"""
    return await nodes.update_subscription(client, node=node, key=key, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_node_report(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). Get system report for a node"""
    return await nodes.node_report(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_node_execute(
    node: str | None = None, commands: str | None = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required, DANGEROUS). Execute commands on a node"""
    return await nodes.node_execute(client, node=node, commands=commands, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_get_network_interface(node: str | None = None, iface: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get details of a single network interface on a node"""
    return await nodes.get_network_interface(client, node=node, iface=iface, endpoint=endpoint)


@mcp.tool()
async def proxmox_bulk_migrate_guests(
    vmids: str = "", target: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Bulk migrate guests to another node"""
    return await cluster.bulk_migrate_guests(client, vmids=vmids, target=target, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_bulk_shutdown_guests(vmids: str = "", confirm: bool = False, endpoint: str | None = None) -> str:
    """(elevated, confirm required). Bulk shutdown guests across the cluster"""
    return await cluster.bulk_shutdown_guests(client, vmids=vmids, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_node_ceph_fs(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). List Ceph filesystems on a node"""
    return await ceph.node_ceph_fs(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_create_ceph_fs(
    node: str | None = None, name: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Create a Ceph filesystem"""
    return await ceph.create_ceph_fs(client, node=node, name=name, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_ceph_osd(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). List Ceph OSDs on a node"""
    return await ceph.list_ceph_osd(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_ceph_mon(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). List Ceph monitors on a node"""
    return await ceph.list_ceph_mon(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_ceph_mgr(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). List Ceph managers on a node"""
    return await ceph.list_ceph_mgr(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_ceph_config(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). Get raw Ceph configuration on a node"""
    return await ceph.ceph_config(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_ceph_flags(endpoint: str | None = None) -> str:
    """(read-only). Get Ceph cluster flags"""
    return await ceph.ceph_flags(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_set_ceph_flags(flags: str = "", confirm: bool = False, endpoint: str | None = None) -> str:
    """(elevated, confirm required). Set Ceph cluster flags"""
    return await ceph.set_ceph_flags(client, flags=flags, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_get_ceph_flag(flag: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get a specific Ceph cluster flag"""
    return await ceph.get_ceph_flag(client, flag=flag, endpoint=endpoint)


@mcp.tool()
async def proxmox_set_ceph_flag(
    flag: str = "", value: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Set a specific Ceph cluster flag"""
    return await ceph.set_ceph_flag(client, flag=flag, value=value, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_ceph_osd_detail(node: str | None = None, osdid: int = 0, endpoint: str | None = None) -> str:
    """(read-only). Get Ceph OSD detail"""
    return await ceph.list_ceph_osd_detail(client, node=node, osdid=osdid, endpoint=endpoint)


@mcp.tool()
async def proxmox_create_ceph_osd(
    node: str | None = None, dev: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Create a Ceph OSD"""
    return await ceph.create_ceph_osd(client, node=node, dev=dev, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_destroy_ceph_osd(
    node: str | None = None, osdid: int = 0, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Destroy a Ceph OSD"""
    return await ceph.destroy_ceph_osd(client, node=node, osdid=osdid, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_ceph_osd_in(
    node: str | None = None, osdid: int = 0, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Mark Ceph OSD in"""
    return await ceph.ceph_osd_in(client, node=node, osdid=osdid, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_ceph_osd_out(
    node: str | None = None, osdid: int = 0, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Mark Ceph OSD out"""
    return await ceph.ceph_osd_out(client, node=node, osdid=osdid, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_ceph_osd_scrub(
    node: str | None = None, osdid: int = 0, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Scrub a Ceph OSD"""
    return await ceph.ceph_osd_scrub(client, node=node, osdid=osdid, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_ceph_osd_metadata(node: str | None = None, osdid: int = 0, endpoint: str | None = None) -> str:
    """(read-only). Get Ceph OSD metadata"""
    return await ceph.ceph_osd_metadata(client, node=node, osdid=osdid, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_ceph_pools(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). List Ceph pools on a node"""
    return await ceph.list_ceph_pools(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_create_ceph_pool(
    node: str | None = None,
    name: str = "",
    confirm: bool = False,
    pg_num: int | None = None,
    size: int | None = None,
    min_size: int | None = None,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Create a Ceph pool"""
    return await ceph.create_ceph_pool(
        client,
        node=node,
        name=name,
        confirm=confirm,
        pg_num=pg_num,
        size=size,
        min_size=min_size,
    )


@mcp.tool()
async def proxmox_get_ceph_pool(node: str | None = None, name: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get Ceph pool details"""
    return await ceph.get_ceph_pool(client, node=node, name=name, endpoint=endpoint)


@mcp.tool()
async def proxmox_update_ceph_pool(
    node: str | None = None,
    name: str = "",
    confirm: bool = False,
    kwargs: str | None = None,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Update a Ceph pool"""
    return await ceph.update_ceph_pool(
        client, node=node, name=name, confirm=confirm, **_parse(kwargs), endpoint=endpoint
    )


@mcp.tool()
async def proxmox_destroy_ceph_pool(
    node: str | None = None, name: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Destroy a Ceph pool"""
    return await ceph.destroy_ceph_pool(client, node=node, name=name, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_ceph_pool_status(node: str | None = None, name: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get Ceph pool status"""
    return await ceph.ceph_pool_status(client, node=node, name=name, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_ceph_mds_detail(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). List Ceph MDS detail on a node"""
    return await ceph.list_ceph_mds_detail(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_create_ceph_mds(
    node: str | None = None, name: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Create Ceph MDS"""
    return await ceph.create_ceph_mds(client, node=node, name=name, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_destroy_ceph_mds(
    node: str | None = None, name: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Destroy Ceph MDS"""
    return await ceph.destroy_ceph_mds(client, node=node, name=name, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_create_ceph_mgr(
    node: str | None = None, id: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Create Ceph MGR"""
    return await ceph.create_ceph_mgr(client, node=node, id=id, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_destroy_ceph_mgr(
    node: str | None = None, id: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Destroy Ceph MGR"""
    return await ceph.destroy_ceph_mgr(client, node=node, id=id, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_create_ceph_mon(
    node: str | None = None, monid: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Create Ceph MON"""
    return await ceph.create_ceph_mon(client, node=node, monid=monid, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_destroy_ceph_mon(
    node: str | None = None, monid: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Destroy Ceph MON"""
    return await ceph.destroy_ceph_mon(client, node=node, monid=monid, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_start_ceph(node: str | None = None, confirm: bool = False, endpoint: str | None = None) -> str:
    """(elevated, confirm required). Start Ceph services on a node"""
    return await ceph.start_ceph(client, node=node, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_stop_ceph(node: str | None = None, confirm: bool = False, endpoint: str | None = None) -> str:
    """(elevated, confirm required). Stop Ceph services on a node"""
    return await ceph.stop_ceph(client, node=node, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_restart_ceph(node: str | None = None, confirm: bool = False, endpoint: str | None = None) -> str:
    """(elevated, confirm required). Restart Ceph services on a node"""
    return await ceph.restart_ceph(client, node=node, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_ceph_cfg_db(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). Get Ceph config database on a node"""
    return await ceph.ceph_cfg_db(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_ceph_cfg_value(
    node: str | None = None, name: str | None = None, section: str | None = None, endpoint: str | None = None
) -> str:
    """(read-only). Get Ceph config values on a node"""
    params = {}
    if name is not None:
        params["name"] = name
    if section is not None:
        params["section"] = section
    return await ceph.ceph_cfg_value(client, node=node, **params, endpoint=endpoint)


@mcp.tool()
async def proxmox_ceph_crush(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). Get Ceph CRUSH map on a node"""
    return await ceph.ceph_crush(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_ceph_log(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). Get Ceph log on a node"""
    return await ceph.ceph_log(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_init_ceph(node: str | None = None, confirm: bool = False, endpoint: str | None = None) -> str:
    """(elevated, confirm required). Initialize Ceph on a node"""
    return await ceph.init_ceph(client, node=node, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_apt_updates(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). List available APT updates on a node"""
    return await apt.list_updates(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_refresh_apt_updates(
    node: str | None = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Refresh APT package index"""
    return await apt.refresh_updates(client, node=node, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_apt_repositories(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). List APT repositories on a node"""
    return await apt.list_repositories(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_apt_versions(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). List APT package versions on a node"""
    return await apt.list_versions(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_add_apt_repo(
    node: str | None = None,
    path: str | None = None,
    index: int | None = None,
    enabled: bool | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Add an APT repository"""
    return await apt.add_apt_repo(
        client, node=node, path=path, index=index, enabled=enabled, confirm=confirm, endpoint=endpoint
    )


@mcp.tool()
async def proxmox_update_apt_repo(
    node: str | None = None,
    path: str | None = None,
    index: int | None = None,
    enabled: bool | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Update an APT repository"""
    return await apt.update_apt_repo(
        client, node=node, path=path, index=index, enabled=enabled, confirm=confirm, endpoint=endpoint
    )


@mcp.tool()
async def proxmox_list_apt_changelog(
    node: str | None = None, name: str | None = None, version: str | None = None, endpoint: str | None = None
) -> str:
    """(read-only). List APT changelog for a package"""
    return await apt.list_apt_changelog(client, node=node, name=name, version=version, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_cpu_models(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). List QEMU CPU models on a node"""
    return await capabilities.list_cpu_models(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_cpu_flags(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). List QEMU CPU flags on a node"""
    return await capabilities.list_cpu_flags(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_machine_types(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). List QEMU machine types on a node"""
    return await capabilities.list_machine_types(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_capabilities(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). List node capabilities index"""
    return await capabilities.list_capabilities(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_capabilities_qemu(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). List QEMU capabilities on a node"""
    return await capabilities.list_capabilities_qemu(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_get_capability_qemu_migration(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). Get QEMU migration capabilities on a node"""
    return await capabilities.get_capability_qemu_migrations(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_certificates(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). List certificate info on a node"""
    return await certificates.list_certificates(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_order_acme_certificate(
    node: str | None = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Order ACME certificate"""
    return await certificates.order_acme_certificate(client, node=node, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_renew_acme_certificate(
    node: str | None = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Renew ACME certificate"""
    return await certificates.renew_acme_certificate(client, node=node, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_revoke_certificate(
    node: str | None = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Revoke certificate from ACME CA"""
    return await certificates.revoke_certificate(client, node=node, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_upload_custom_certificate(
    node: str | None = None,
    certificates: str | None = None,
    key: str | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Upload custom certificate and key"""
    import proxmox_mcp.certificates as certs_mod

    return await certs_mod.upload_custom_certificate(
        client,
        node=node,
        certificates=certificates,
        key=key,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_delete_custom_certificate(
    node: str | None = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Delete custom certificate"""
    return await certificates.delete_custom_certificate(client, node=node, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_acme_certs(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). List ACME certificate entries on a node"""
    return await certificates.list_acme_certs(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_sdn_zones(endpoint: str | None = None) -> str:
    """(read-only). List SDN zones in the cluster"""
    return await sdn.list_sdn_zones(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_get_sdn_zone(zone: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get SDN zone configuration"""
    return await sdn.get_sdn_zone(client, zone=zone, endpoint=endpoint)


@mcp.tool()
async def proxmox_create_sdn_zone(
    zone: str = "",
    type: str = "",
    comment: str | None = None,
    nodes: str | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Create an SDN zone"""
    return await sdn.create_sdn_zone(
        client,
        zone=zone,
        type=type,
        comment=comment,
        nodes=nodes,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_update_sdn_zone(
    zone: str = "",
    comment: str | None = None,
    nodes: str | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Update an SDN zone"""
    return await sdn.update_sdn_zone(
        client, zone=zone, comment=comment, nodes=nodes, confirm=confirm, endpoint=endpoint
    )


@mcp.tool()
async def proxmox_delete_sdn_zone(zone: str = "", confirm: bool = False, endpoint: str | None = None) -> str:
    """(elevated, confirm required). Delete an SDN zone"""
    return await sdn.delete_sdn_zone(client, zone=zone, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_sdn_vnets(endpoint: str | None = None) -> str:
    """(read-only). List SDN VNets in the cluster"""
    return await sdn.list_sdn_vnets(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_get_sdn_vnet(vnet: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get SDN VNet configuration"""
    return await sdn.get_sdn_vnet(client, vnet=vnet, endpoint=endpoint)


@mcp.tool()
async def proxmox_create_sdn_vnet(
    vnet: str = "", zone: str = "", comment: str | None = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Create an SDN VNet"""
    return await sdn.create_sdn_vnet(
        client,
        vnet=vnet,
        zone=zone,
        comment=comment,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_update_sdn_vnet(
    vnet: str = "", comment: str | None = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Update an SDN VNet"""
    return await sdn.update_sdn_vnet(client, vnet=vnet, comment=comment, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_delete_sdn_vnet(vnet: str = "", confirm: bool = False, endpoint: str | None = None) -> str:
    """(elevated, confirm required). Delete an SDN VNet"""
    return await sdn.delete_sdn_vnet(client, vnet=vnet, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_sdn_subnets(vnet: str = "", endpoint: str | None = None) -> str:
    """(read-only). List SDN subnets in a VNet"""
    return await sdn.list_sdn_subnets(client, vnet=vnet, endpoint=endpoint)


@mcp.tool()
async def proxmox_create_sdn_subnet(
    vnet: str = "", subnet: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Create an SDN subnet"""
    return await sdn.create_sdn_subnet(client, vnet=vnet, subnet=subnet, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_delete_sdn_subnet(
    vnet: str = "", subnet: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Delete an SDN subnet"""
    return await sdn.delete_sdn_subnet(client, vnet=vnet, subnet=subnet, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_sdn_controllers(endpoint: str | None = None) -> str:
    """(read-only). List SDN controllers in the cluster"""
    return await sdn.list_sdn_controllers(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_create_sdn_controller(
    controller: str = "", type: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Create an SDN controller"""
    return await sdn.create_sdn_controller(client, controller=controller, type=type, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_delete_sdn_controller(
    controller: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Delete an SDN controller"""
    return await sdn.delete_sdn_controller(client, controller=controller, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_sdn_dns(endpoint: str | None = None) -> str:
    """(read-only). List SDN DNS entries in the cluster"""
    return await sdn.list_sdn_dns(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_create_sdn_dns(
    dns: str = "", type: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Create an SDN DNS entry"""
    return await sdn.create_sdn_dns(client, dns=dns, type=type, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_delete_sdn_dns(dns: str = "", confirm: bool = False, endpoint: str | None = None) -> str:
    """(elevated, confirm required). Delete an SDN DNS entry"""
    return await sdn.delete_sdn_dns(client, dns=dns, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_sdn_ipams(endpoint: str | None = None) -> str:
    """(read-only). List SDN IPAMs in the cluster"""
    return await sdn.list_sdn_ipams(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_create_sdn_ipam(
    ipam: str = "", type: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Create an SDN IPAM"""
    return await sdn.create_sdn_ipam(client, ipam=ipam, type=type, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_delete_sdn_ipam(ipam: str = "", confirm: bool = False, endpoint: str | None = None) -> str:
    """(elevated, confirm required). Delete an SDN IPAM"""
    return await sdn.delete_sdn_ipam(client, ipam=ipam, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_apply_sdn(confirm: bool = False, endpoint: str | None = None) -> str:
    """(elevated, confirm required). Apply pending SDN changes"""
    return await sdn.apply_sdn(client, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_node_sdn_zones(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). List SDN zone status on a node"""
    return await sdn.list_node_sdn_zones(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_get_node_sdn_zone_status(node: str | None = None, zone: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get SDN zone status on a node"""
    return await sdn.get_node_sdn_zone_status(client, node=node, zone=zone, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_notification_targets(endpoint: str | None = None) -> str:
    """(read-only). List notification targets"""
    return await notifications.list_notification_targets(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_notification_matchers(endpoint: str | None = None) -> str:
    """(read-only). List notification matchers"""
    return await notifications.list_notification_matchers(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_get_notification_matcher(name: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get notification matcher configuration"""
    return await notifications.get_notification_matcher(client, name=name, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_sendmail_endpoints(endpoint: str | None = None) -> str:
    """(read-only). List sendmail notification endpoints"""
    return await notifications.list_sendmail_endpoints(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_create_sendmail_endpoint(
    name: str = "",
    mailto: str | None = None,
    comment: str | None = None,
    confirm: bool = False,
) -> str:
    """(elevated, confirm required). Create a sendmail notification endpoint"""
    return await notifications.create_sendmail_endpoint(
        client,
        name=name,
        mailto=mailto,
        comment=comment,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_delete_sendmail_endpoint(
    name: str = "",
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Delete a sendmail notification endpoint"""
    return await notifications.delete_sendmail_endpoint(client, name=name, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_smtp_endpoints(endpoint: str | None = None) -> str:
    """(read-only). List SMTP notification endpoints"""
    return await notifications.list_smtp_endpoints(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_create_smtp_endpoint(
    name: str = "",
    server: str | None = None,
    comment: str | None = None,
    confirm: bool = False,
) -> str:
    """(elevated, confirm required). Create an SMTP notification endpoint"""
    return await notifications.create_smtp_endpoint(
        client,
        name=name,
        server=server,
        comment=comment,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_delete_smtp_endpoint(
    name: str = "",
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Delete an SMTP notification endpoint"""
    return await notifications.delete_smtp_endpoint(client, name=name, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_gotify_endpoints(endpoint: str | None = None) -> str:
    """(read-only). List Gotify notification endpoints"""
    return await notifications.list_gotify_endpoints(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_create_gotify_endpoint(
    name: str = "",
    server: str | None = None,
    token: str | None = None,
    comment: str | None = None,
    confirm: bool = False,
) -> str:
    """(elevated, confirm required). Create a Gotify notification endpoint"""
    return await notifications.create_gotify_endpoint(
        client,
        name=name,
        server=server,
        token=token,
        comment=comment,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_delete_gotify_endpoint(
    name: str = "",
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Delete a Gotify notification endpoint"""
    return await notifications.delete_gotify_endpoint(client, name=name, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_webhook_endpoints(endpoint: str | None = None) -> str:
    """(read-only). List webhook notification endpoints"""
    return await notifications.list_webhook_endpoints(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_create_webhook_endpoint(
    name: str = "",
    url: str | None = None,
    comment: str | None = None,
    confirm: bool = False,
) -> str:
    """(elevated, confirm required). Create a webhook notification endpoint"""
    return await notifications.create_webhook_endpoint(
        client,
        name=name,
        url=url,
        comment=comment,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_delete_webhook_endpoint(
    name: str = "",
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Delete a webhook notification endpoint"""
    return await notifications.delete_webhook_endpoint(client, name=name, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_notification_index(endpoint: str | None = None) -> str:
    """(read-only). Get notification system index"""
    return await notifications.notification_index(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_notification_endpoints_index(endpoint: str | None = None) -> str:
    """(read-only). Get notification endpoints index"""
    return await notifications.notification_endpoints_index(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_get_notification_target(name: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get notification target details"""
    return await notifications.get_notification_target(client, name=name, endpoint=endpoint)


@mcp.tool()
async def proxmox_test_notification_target(name: str = "", confirm: bool = False, endpoint: str | None = None) -> str:
    """(elevated, confirm required). Send a test notification to a target"""
    return await notifications.test_notification_target(client, name=name, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_notification_matcher_fields(endpoint: str | None = None) -> str:
    """(read-only). List notification matcher fields"""
    return await notifications.notification_matcher_fields(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_notification_matcher_field_values(endpoint: str | None = None) -> str:
    """(read-only). List notification matcher field values"""
    return await notifications.notification_matcher_field_values(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_create_notification_matcher(
    name: str = "",
    comment: str | None = None,
    confirm: bool = False,
    kwargs: str | None = None,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Create a notification matcher"""
    return await notifications.create_notification_matcher(
        client, name=name, comment=comment, confirm=confirm, **_parse(kwargs)
    )


@mcp.tool()
async def proxmox_update_notification_matcher(
    name: str = "",
    comment: str | None = None,
    confirm: bool = False,
    kwargs: str | None = None,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Update a notification matcher"""
    return await notifications.update_notification_matcher(
        client, name=name, comment=comment, confirm=confirm, **_parse(kwargs)
    )


@mcp.tool()
async def proxmox_delete_notification_matcher(
    name: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Delete a notification matcher"""
    return await notifications.delete_notification_matcher(client, name=name, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_get_sendmail_endpoint(name: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get sendmail endpoint details"""
    return await notifications.get_sendmail_endpoint(client, name=name, endpoint=endpoint)


@mcp.tool()
async def proxmox_update_sendmail_endpoint(
    name: str = "",
    comment: str | None = None,
    confirm: bool = False,
    kwargs: str | None = None,
) -> str:
    """(elevated, confirm required). Update a sendmail endpoint"""
    return await notifications.update_sendmail_endpoint(
        client, name=name, comment=comment, confirm=confirm, **_parse(kwargs)
    )


@mcp.tool()
async def proxmox_get_smtp_endpoint(name: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get SMTP endpoint details"""
    return await notifications.get_smtp_endpoint(client, name=name, endpoint=endpoint)


@mcp.tool()
async def proxmox_update_smtp_endpoint(
    name: str = "",
    comment: str | None = None,
    confirm: bool = False,
    kwargs: str | None = None,
) -> str:
    """(elevated, confirm required). Update an SMTP endpoint"""
    return await notifications.update_smtp_endpoint(
        client, name=name, comment=comment, confirm=confirm, **_parse(kwargs)
    )


@mcp.tool()
async def proxmox_get_gotify_endpoint(name: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get Gotify endpoint details"""
    return await notifications.get_gotify_endpoint(client, name=name, endpoint=endpoint)


@mcp.tool()
async def proxmox_update_gotify_endpoint(
    name: str = "",
    comment: str | None = None,
    confirm: bool = False,
    kwargs: str | None = None,
) -> str:
    """(elevated, confirm required). Update a Gotify endpoint"""
    return await notifications.update_gotify_endpoint(
        client, name=name, comment=comment, confirm=confirm, **_parse(kwargs)
    )


@mcp.tool()
async def proxmox_get_webhook_endpoint(name: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get webhook endpoint details"""
    return await notifications.get_webhook_endpoint(client, name=name, endpoint=endpoint)


@mcp.tool()
async def proxmox_update_webhook_endpoint(
    name: str = "",
    comment: str | None = None,
    confirm: bool = False,
    kwargs: str | None = None,
) -> str:
    """(elevated, confirm required). Update a webhook endpoint"""
    return await notifications.update_webhook_endpoint(
        client, name=name, comment=comment, confirm=confirm, **_parse(kwargs)
    )


@mcp.tool()
async def proxmox_list_pci_mappings(endpoint: str | None = None) -> str:
    """(read-only). List PCI hardware mappings"""
    return await mapping.list_pci_mappings(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_create_pci_mapping(
    id: str = "", description: str | None = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Create a PCI hardware mapping"""
    return await mapping.create_pci_mapping(client, id=id, description=description, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_get_pci_mapping(id: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get PCI hardware mapping configuration"""
    return await mapping.get_pci_mapping(client, id=id, endpoint=endpoint)


@mcp.tool()
async def proxmox_update_pci_mapping(
    id: str = "", description: str | None = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Update a PCI hardware mapping"""
    return await mapping.update_pci_mapping(client, id=id, description=description, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_delete_pci_mapping(id: str = "", confirm: bool = False, endpoint: str | None = None) -> str:
    """(elevated, confirm required). Delete a PCI hardware mapping"""
    return await mapping.delete_pci_mapping(client, id=id, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_usb_mappings(endpoint: str | None = None) -> str:
    """(read-only). List USB hardware mappings"""
    return await mapping.list_usb_mappings(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_create_usb_mapping(
    id: str = "", description: str | None = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Create a USB hardware mapping"""
    return await mapping.create_usb_mapping(client, id=id, description=description, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_get_usb_mapping(id: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get USB hardware mapping configuration"""
    return await mapping.get_usb_mapping(client, id=id, endpoint=endpoint)


@mcp.tool()
async def proxmox_update_usb_mapping(
    id: str = "", description: str | None = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Update a USB hardware mapping"""
    return await mapping.update_usb_mapping(client, id=id, description=description, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_delete_usb_mapping(id: str = "", confirm: bool = False, endpoint: str | None = None) -> str:
    """(elevated, confirm required). Delete a USB hardware mapping"""
    return await mapping.delete_usb_mapping(client, id=id, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_mapping_index(endpoint: str | None = None) -> str:
    """(read-only). Get mapping resource types index"""
    return await mapping.mapping_index(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_dir_mappings(endpoint: str | None = None) -> str:
    """(read-only). List directory mappings"""
    return await mapping.list_dir_mappings(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_get_dir_mapping(id: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get directory mapping configuration"""
    return await mapping.get_dir_mapping(client, id=id, endpoint=endpoint)


@mcp.tool()
async def proxmox_create_dir_mapping(
    id: str = "", description: str | None = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Create a directory mapping"""
    return await mapping.create_dir_mapping(client, id=id, description=description, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_update_dir_mapping(
    id: str = "",
    description: str | None = None,
    confirm: bool = False,
    kwargs: str | None = None,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Update a directory mapping"""
    return await mapping.update_dir_mapping(
        client, id=id, description=description, confirm=confirm, **_parse(kwargs), endpoint=endpoint
    )


@mcp.tool()
async def proxmox_delete_dir_mapping(id: str = "", confirm: bool = False, endpoint: str | None = None) -> str:
    """(elevated, confirm required). Delete a directory mapping"""
    return await mapping.delete_dir_mapping(client, id=id, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_metric_servers(endpoint: str | None = None) -> str:
    """(read-only). List metric server configurations"""
    return await metrics.list_metric_servers(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_get_metric_server(id: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get metric server configuration"""
    return await metrics.get_metric_server(client, id=id, endpoint=endpoint)


@mcp.tool()
async def proxmox_create_metric_server(
    id: str = "",
    type: str = "graphite",
    server: str | None = None,
    port: int | None = None,
    comment: str | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Create a metric server configuration type: graphite, influxdb, opentelemetry."""
    return await metrics.create_metric_server(
        client,
        id=id,
        type=type,
        server=server,
        port=port,
        comment=comment,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_update_metric_server(
    id: str = "",
    server: str | None = None,
    port: int | None = None,
    comment: str | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Update a metric server configuration"""
    return await metrics.update_metric_server(
        client,
        id=id,
        server=server,
        port=port,
        comment=comment,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_delete_metric_server(id: str = "", confirm: bool = False, endpoint: str | None = None) -> str:
    """(elevated, confirm required). Delete a metric server configuration"""
    return await metrics.delete_metric_server(client, id=id, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_metrics_index(endpoint: str | None = None) -> str:
    """(read-only). Get metrics subsystem index"""
    return await metrics.metrics_index(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_export_metrics(endpoint: str | None = None) -> str:
    """(read-only). Export cluster metrics data"""
    return await metrics.export_metrics(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_node_netstat(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). Get network device interface counters for a node"""
    return await nodes.node_netstat(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_lxc_migrate_preconditions(
    node: str | None = None, vmid: int | None = None, endpoint: str | None = None
) -> str:
    """(read-only). Check LXC container migration preconditions"""
    return await lifecycle.lxc_migrate_preconditions(client, node=node, vmid=vmid, endpoint=endpoint)


@mcp.tool()
async def proxmox_vm_migrate_preconditions(
    node: str | None = None, vmid: int | None = None, endpoint: str | None = None
) -> str:
    """(read-only). Check VM migration preconditions"""
    return await lifecycle.vm_migrate_preconditions(client, node=node, vmid=vmid, endpoint=endpoint)


@mcp.tool()
async def proxmox_storage_metrics(
    node: str | None = None,
    storage: str = "local",
    timeframe: str = "hour",
    cf: str = "AVERAGE",
    endpoint: str | None = None,
) -> str:
    """(read-only). Get RRD metrics for a storage pool on a node"""
    return await storage_mod.storage_metrics(
        client, node=node, storage=storage, timeframe=timeframe, cf=cf, endpoint=endpoint
    )


@mcp.tool()
async def proxmox_storage_identity(node: str | None = None, storage: str = "local", endpoint: str | None = None) -> str:
    """(read-only). Get storage identity information"""
    return await storage_mod.storage_identity(client, node=node, storage=storage, endpoint=endpoint)


@mcp.tool()
async def proxmox_allocate_disk(
    node: str | None = None,
    storage: str = "local",
    vmid: int | None = None,
    filename: str | None = None,
    size: str = "1G",
    format: str | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Allocate a disk image on storage"""
    return await storage_mod.allocate_disk(
        client,
        node=node,
        storage=storage,
        vmid=vmid,
        filename=filename,
        size=size,
        format=format,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_list_node_lxc(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). List LXC containers on a specific node"""
    return await discovery.list_node_lxc(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_node_vms(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). List VMs on a specific node"""
    return await discovery.list_node_vms(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_node_tasks(node: str | None = None, limit: int = 50, endpoint: str | None = None) -> str:
    """(read-only). List tasks on a specific node"""
    return await discovery.list_node_tasks(client, node=node, limit=limit, endpoint=endpoint)


@mcp.tool()
async def proxmox_node_index(node: str | None = None, endpoint: str | None = None) -> str:
    """(read-only). Get node index information"""
    return await discovery.node_index(client, node=node, endpoint=endpoint)


@mcp.tool()
async def proxmox_regenerate_cloudinit(
    node: str | None = None, vmid: int | None = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Regenerate cloud-init drive for a VM"""
    return await cloudinit.regenerate_cloudinit(client, node=node, vmid=vmid, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_revert_network(node: str | None = None, confirm: bool = False, endpoint: str | None = None) -> str:
    """(elevated, confirm required). Revert pending network changes on a node"""
    return await networking.revert_network(client, node=node, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_get_acme_challenge_schema(endpoint: str | None = None) -> str:
    """(read-only). Get ACME challenge schema"""
    return await acme.get_acme_challenge_schema(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_acme_tos(endpoint: str | None = None) -> str:
    """(read-only). List ACME Terms of Service (read-only, deprecated)."""
    return await acme.list_acme_tos(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_get_sdn_ipam_status(ipam: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get SDN IPAM status"""
    return await sdn.get_sdn_ipam_status(client, ipam=ipam, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_sdn_fabrics(endpoint: str | None = None) -> str:
    """(read-only). List SDN fabrics"""
    return await sdn.list_sdn_fabrics(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_sdn_fabric_detail(fabric: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get SDN fabric detail"""
    return await sdn.list_sdn_fabric_detail(client, fabric=fabric, endpoint=endpoint)


@mcp.tool()
async def proxmox_create_sdn_fabric(
    fabric: str = "", type: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Create an SDN fabric"""
    return await sdn.create_sdn_fabric(client, fabric=fabric, type=type, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_delete_sdn_fabric(id: str = "", confirm: bool = False, endpoint: str | None = None) -> str:
    """(elevated, confirm required). Delete an SDN fabric"""
    return await sdn.delete_sdn_fabric(client, id=id, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_update_sdn_fabric(
    id: str = "", confirm: bool = False, kwargs: str | None = None, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Update an SDN fabric"""
    return await sdn.update_sdn_fabric(client, id=id, confirm=confirm, **_parse(kwargs), endpoint=endpoint)


@mcp.tool()
async def proxmox_list_sdn_prefix_lists(endpoint: str | None = None) -> str:
    """(read-only). List SDN prefix lists"""
    return await sdn.list_sdn_prefix_lists(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_create_sdn_prefix_list(id: str = "", confirm: bool = False, endpoint: str | None = None) -> str:
    """(elevated, confirm required). Create an SDN prefix list"""
    return await sdn.create_sdn_prefix_list(client, id=id, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_delete_sdn_prefix_list(id: str = "", confirm: bool = False, endpoint: str | None = None) -> str:
    """(elevated, confirm required). Delete an SDN prefix list"""
    return await sdn.delete_sdn_prefix_list(client, id=id, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_sdn_route_maps(endpoint: str | None = None) -> str:
    """(read-only). List SDN route maps"""
    return await sdn.list_sdn_route_maps(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_sdn_rollback(confirm: bool = False, endpoint: str | None = None) -> str:
    """(elevated, confirm required). Rollback pending SDN changes"""
    return await sdn.sdn_rollback(client, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_get_sdn_ipam(ipam: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get SDN IPAM configuration"""
    return await sdn.get_sdn_ipam(client, ipam=ipam, endpoint=endpoint)


@mcp.tool()
async def proxmox_update_sdn_ipam(
    ipam: str = "", confirm: bool = False, kwargs: str | None = None, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Update an SDN IPAM"""
    return await sdn.update_sdn_ipam(client, ipam=ipam, confirm=confirm, **_parse(kwargs), endpoint=endpoint)


@mcp.tool()
async def proxmox_get_sdn_dns(dns: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get SDN DNS configuration"""
    return await sdn.get_sdn_dns(client, dns=dns, endpoint=endpoint)


@mcp.tool()
async def proxmox_update_sdn_dns(
    dns: str = "", confirm: bool = False, kwargs: str | None = None, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Update an SDN DNS entry"""
    return await sdn.update_sdn_dns(client, dns=dns, confirm=confirm, **_parse(kwargs), endpoint=endpoint)


@mcp.tool()
async def proxmox_get_sdn_controller(controller: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get SDN controller configuration"""
    return await sdn.get_sdn_controller(client, controller=controller, endpoint=endpoint)


@mcp.tool()
async def proxmox_update_sdn_controller(
    controller: str = "", confirm: bool = False, kwargs: str | None = None, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Update an SDN controller"""
    return await sdn.update_sdn_controller(
        client, controller=controller, confirm=confirm, **_parse(kwargs), endpoint=endpoint
    )


@mcp.tool()
async def proxmox_list_sdn_fabric_nodes(fabric_id: str = "", endpoint: str | None = None) -> str:
    """(read-only). List SDN fabric nodes"""
    return await sdn.list_sdn_fabric_nodes(client, fabric_id=fabric_id, endpoint=endpoint)


@mcp.tool()
async def proxmox_add_sdn_fabric_node(
    fabric_id: str = "", node: str = "", confirm: bool = False, kwargs: str | None = None, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Add an SDN fabric node"""
    return await sdn.add_sdn_fabric_node(
        client, fabric_id=fabric_id, node=node, confirm=confirm, **_parse(kwargs), endpoint=endpoint
    )


@mcp.tool()
async def proxmox_get_sdn_fabric_node(fabric_id: str = "", node_id: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get SDN fabric node detail"""
    return await sdn.get_sdn_fabric_node(client, fabric_id=fabric_id, node_id=node_id, endpoint=endpoint)


@mcp.tool()
async def proxmox_update_sdn_fabric_node(
    fabric_id: str = "",
    node_id: str = "",
    confirm: bool = False,
    kwargs: str | None = None,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Update an SDN fabric node"""
    return await sdn.update_sdn_fabric_node(
        client, fabric_id=fabric_id, node_id=node_id, confirm=confirm, **_parse(kwargs)
    )


@mcp.tool()
async def proxmox_remove_sdn_fabric_node(
    fabric_id: str = "", node_id: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Remove an SDN fabric node"""
    return await sdn.remove_sdn_fabric_node(
        client, fabric_id=fabric_id, node_id=node_id, confirm=confirm, endpoint=endpoint
    )


@mcp.tool()
async def proxmox_create_sdn_vnet_ip(
    vnet: str = "", confirm: bool = False, kwargs: str | None = None, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Create an SDN VNet IP mapping"""
    return await sdn.create_sdn_vnet_ip(client, vnet=vnet, confirm=confirm, **_parse(kwargs), endpoint=endpoint)


@mcp.tool()
async def proxmox_update_sdn_vnet_ip(
    vnet: str = "", confirm: bool = False, kwargs: str | None = None, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Update an SDN VNet IP mapping"""
    return await sdn.update_sdn_vnet_ip(client, vnet=vnet, confirm=confirm, **_parse(kwargs), endpoint=endpoint)


@mcp.tool()
async def proxmox_delete_sdn_vnet_ip(
    vnet: str = "", confirm: bool = False, kwargs: str | None = None, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Delete an SDN VNet IP mapping"""
    return await sdn.delete_sdn_vnet_ip(client, vnet=vnet, confirm=confirm, **_parse(kwargs), endpoint=endpoint)


@mcp.tool()
async def proxmox_get_sdn_vnet_firewall_options(vnet: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get SDN VNet firewall options"""
    return await sdn.get_sdn_vnet_firewall_options(client, vnet=vnet, endpoint=endpoint)


@mcp.tool()
async def proxmox_set_sdn_vnet_firewall_options(
    vnet: str = "", confirm: bool = False, kwargs: str | None = None, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Set SDN VNet firewall options"""
    return await sdn.set_sdn_vnet_firewall_options(
        client, vnet=vnet, confirm=confirm, **_parse(kwargs), endpoint=endpoint
    )


@mcp.tool()
async def proxmox_list_sdn_vnet_firewall_rules(vnet: str = "", endpoint: str | None = None) -> str:
    """(read-only). List SDN VNet firewall rules"""
    return await sdn.list_sdn_vnet_firewall_rules(client, vnet=vnet, endpoint=endpoint)


@mcp.tool()
async def proxmox_create_sdn_vnet_firewall_rule(
    vnet: str = "", confirm: bool = False, kwargs: str | None = None, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Create an SDN VNet firewall rule"""
    return await sdn.create_sdn_vnet_firewall_rule(
        client, vnet=vnet, confirm=confirm, **_parse(kwargs), endpoint=endpoint
    )


@mcp.tool()
async def proxmox_delete_sdn_vnet_firewall_rule(
    vnet: str = "", pos: int = 0, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Delete an SDN VNet firewall rule"""
    return await sdn.delete_sdn_vnet_firewall_rule(client, vnet=vnet, pos=pos, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_get_sdn_vnet_firewall_rule(vnet: str = "", pos: int = 0, endpoint: str | None = None) -> str:
    """(read-only). Get an SDN VNet firewall rule"""
    return await sdn.get_sdn_vnet_firewall_rule(client, vnet=vnet, pos=pos, endpoint=endpoint)


@mcp.tool()
async def proxmox_update_sdn_vnet_firewall_rule(
    vnet: str = "", pos: int = 0, confirm: bool = False, kwargs: str | None = None, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Update an SDN VNet firewall rule"""
    return await sdn.update_sdn_vnet_firewall_rule(
        client, vnet=vnet, pos=pos, confirm=confirm, **_parse(kwargs), endpoint=endpoint
    )


@mcp.tool()
async def proxmox_list_prefix_list_entries(id: str = "", endpoint: str | None = None) -> str:
    """(read-only). List SDN prefix list entries"""
    return await sdn.list_prefix_list_entries(client, id=id, endpoint=endpoint)


@mcp.tool()
async def proxmox_create_prefix_list_entry(
    id: str = "", confirm: bool = False, kwargs: str | None = None, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Create an SDN prefix list entry"""
    return await sdn.create_prefix_list_entry(client, id=id, confirm=confirm, **_parse(kwargs), endpoint=endpoint)


@mcp.tool()
async def proxmox_delete_prefix_list_entry(
    id: str = "", url_seq: int = 0, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Delete an SDN prefix list entry"""
    return await sdn.delete_prefix_list_entry(client, id=id, url_seq=url_seq, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_get_prefix_list_entry(id: str = "", url_seq: int = 0, endpoint: str | None = None) -> str:
    """(read-only). Get an SDN prefix list entry"""
    return await sdn.get_prefix_list_entry(client, id=id, url_seq=url_seq, endpoint=endpoint)


@mcp.tool()
async def proxmox_update_prefix_list_entry(
    id: str = "", url_seq: int = 0, confirm: bool = False, kwargs: str | None = None, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Update an SDN prefix list entry"""
    return await sdn.update_prefix_list_entry(
        client, id=id, url_seq=url_seq, confirm=confirm, **_parse(kwargs), endpoint=endpoint
    )


@mcp.tool()
async def proxmox_list_route_map_entries(endpoint: str | None = None) -> str:
    """(read-only). List SDN route map entries"""
    return await sdn.list_route_map_entries(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_create_route_map_entry(
    route_map_id: str = "", confirm: bool = False, kwargs: str | None = None, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Create an SDN route map entry"""
    return await sdn.create_route_map_entry(
        client, route_map_id=route_map_id, confirm=confirm, **_parse(kwargs), endpoint=endpoint
    )


@mcp.tool()
async def proxmox_get_route_map_entry(route_map_id: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get SDN route map entry detail"""
    return await sdn.get_route_map_entry(client, route_map_id=route_map_id, endpoint=endpoint)


@mcp.tool()
async def proxmox_delete_route_map_entry(
    route_map_id: str = "", order: int = 0, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Delete an SDN route map entry"""
    return await sdn.delete_route_map_entry(
        client, route_map_id=route_map_id, order=order, confirm=confirm, endpoint=endpoint
    )


@mcp.tool()
async def proxmox_update_route_map_entry(
    route_map_id: str = "",
    order: int = 0,
    confirm: bool = False,
    kwargs: str | None = None,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Update an SDN route map entry"""
    return await sdn.update_route_map_entry(
        client, route_map_id=route_map_id, order=order, confirm=confirm, **_parse(kwargs)
    )


@mcp.tool()
async def proxmox_sdn_dry_run(endpoint: str | None = None) -> str:
    """(read-only). Preview pending SDN changes (read-only dry-run)."""
    return await sdn.sdn_dry_run(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_get_node_sdn_vnet(node: str | None = None, vnet: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get SDN VNet status on a node"""
    return await sdn.get_node_sdn_vnet(client, node=node, vnet=vnet, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_node_sdn_zone_bridges(
    node: str | None = None, zone: str = "", endpoint: str | None = None
) -> str:
    """(read-only). List SDN zone bridges on a node"""
    return await sdn.list_node_sdn_zone_bridges(client, node=node, zone=zone, endpoint=endpoint)


@mcp.tool()
async def proxmox_get_node_sdn_zone_content(
    node: str | None = None, zone: str = "", endpoint: str | None = None
) -> str:
    """(read-only). Get SDN zone content on a node"""
    return await sdn.get_node_sdn_zone_content(client, node=node, zone=zone, endpoint=endpoint)


@mcp.tool()
async def proxmox_get_node_sdn_zone_ip_vrf(node: str | None = None, zone: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get SDN zone IP-VRF on a node"""
    return await sdn.get_node_sdn_zone_ip_vrf(client, node=node, zone=zone, endpoint=endpoint)


@mcp.tool()
async def proxmox_send_vm_key(
    node: str | None = None, vmid: int | None = None, key: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Send a key press to a VM"""
    return await lifecycle.send_vm_key(client, node=node, vmid=vmid, key=key, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_vm_monitor_command(
    node: str | None = None,
    vmid: int | None = None,
    command: str = "",
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required, DANGEROUS). Send raw QEMU monitor command to VM.

    VERY DANGEROUS - can damage the VM.
    """
    return await lifecycle.vm_monitor_command(
        client, node=node, vmid=vmid, command=command, confirm=confirm, endpoint=endpoint
    )


@mcp.tool()
async def proxmox_unlink_vm_disk(
    node: str | None = None,
    vmid: int | None = None,
    idlist: str = "",
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Unlink disks from a VM idlist is comma-separated disk IDs."""
    return await lifecycle.unlink_vm_disk(
        client, node=node, vmid=vmid, idlist=idlist, confirm=confirm, endpoint=endpoint
    )


@mcp.tool()
async def proxmox_vm_dbus_vmstate(
    node: str | None = None, vmid: int | None = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Trigger DBus VMstate save on a VM"""
    return await lifecycle.vm_dbus_vmstate(client, node=node, vmid=vmid, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_bulk_start_guests(vmids: str = "", confirm: bool = False, endpoint: str | None = None) -> str:
    """(elevated, confirm required). Bulk start guests across the cluster"""
    return await cluster.bulk_start_guests(client, vmids=vmids, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_bulk_suspend_guests(vmids: str = "", confirm: bool = False, endpoint: str | None = None) -> str:
    """(elevated, confirm required). Bulk suspend guests across the cluster"""
    return await cluster.bulk_suspend_guests(client, vmids=vmids, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_vm_vnc_proxy(
    node: str | None = None, vmid: int | None = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Create VNC proxy for a VM"""
    return await console.vm_vnc_proxy(client, node=node, vmid=vmid, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_vm_spice_proxy(
    node: str | None = None, vmid: int | None = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Create SPICE proxy for a VM"""
    return await console.vm_spice_proxy(client, node=node, vmid=vmid, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_vm_termproxy(
    node: str | None = None, vmid: int | None = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Create terminal proxy for a VM"""
    return await console.vm_termproxy(client, node=node, vmid=vmid, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_lxc_vnc_proxy(
    node: str | None = None, vmid: int | None = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Create VNC proxy for an LXC container"""
    return await console.lxc_vnc_proxy(client, node=node, vmid=vmid, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_lxc_termproxy(
    node: str | None = None, vmid: int | None = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Create terminal proxy for an LXC container"""
    return await console.lxc_termproxy(client, node=node, vmid=vmid, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_lxc_spice_proxy(
    node: str | None = None, vmid: int | None = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Create SPICE proxy for an LXC container"""
    return await console.lxc_spice_proxy(client, node=node, vmid=vmid, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_lxc_vnc_websocket(
    node: str | None = None, vmid: int | None = None, endpoint: str | None = None
) -> str:
    """(read-only). Get VNC websocket info for an LXC container"""
    return await console.lxc_vnc_websocket(client, node=node, vmid=vmid, endpoint=endpoint)


@mcp.tool()
async def proxmox_node_vncshell(node: str | None = None, confirm: bool = False, endpoint: str | None = None) -> str:
    """(elevated, confirm required). Create VNC shell for a node"""
    return await console.node_vncshell(client, node=node, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_node_spiceshell(node: str | None = None, confirm: bool = False, endpoint: str | None = None) -> str:
    """(elevated, confirm required). Create SPICE shell for a node"""
    return await console.node_spiceshell(client, node=node, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_node_termproxy(node: str | None = None, confirm: bool = False, endpoint: str | None = None) -> str:
    """(elevated, confirm required). Create terminal proxy for a node"""
    return await console.node_termproxy(client, node=node, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_tfa(endpoint: str | None = None) -> str:
    """(read-only). List TFA configurations"""
    return await access.list_tfa(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_get_user_tfa(userid: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get TFA entries for a user"""
    return await access.get_user_tfa(client, userid=userid, endpoint=endpoint)


@mcp.tool()
async def proxmox_add_tfa_entry(
    userid: str = "",
    type: str = "",
    description: str | None = None,
    value: str | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Add a TFA entry for a user"""
    return await access.add_tfa_entry(
        client,
        userid=userid,
        type=type,
        description=description,
        value=value,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_delete_tfa_entry(
    userid: str = "", id: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Delete a TFA entry"""
    return await access.delete_tfa_entry(client, userid=userid, id=id, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_get_tfa_entry(userid: str = "", id: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get a specific TFA entry"""
    return await access.get_tfa_entry(client, userid=userid, id=id, endpoint=endpoint)


@mcp.tool()
async def proxmox_update_tfa_entry(
    userid: str = "",
    id: str = "",
    description: str | None = None,
    enable: bool | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Update a TFA entry"""
    return await access.update_tfa_entry(
        client,
        userid=userid,
        id=id,
        description=description,
        enable=enable,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_unlock_tfa(userid: str = "", confirm: bool = False, endpoint: str | None = None) -> str:
    """(elevated, confirm required). Unlock a user's TFA authentication"""
    return await access.unlock_tfa(client, userid=userid, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_domains(endpoint: str | None = None) -> str:
    """(read-only). List authentication domains"""
    return await access.list_domains(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_get_domain(realm: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get auth domain configuration"""
    return await access.get_domain(client, realm=realm, endpoint=endpoint)


@mcp.tool()
async def proxmox_sync_domain(realm: str = "", confirm: bool = False, endpoint: str | None = None) -> str:
    """(elevated, confirm required). Sync users/groups from auth domain"""
    return await access.sync_domain(client, realm=realm, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_change_password(
    userid: str = "", password: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Change user password"""
    return await access.change_password(client, userid=userid, password=password, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_create_domain(
    realm: str = "", type: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Create an auth domain"""
    return await access.create_domain(client, realm=realm, type=type, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_update_domain(
    realm: str = "", confirm: bool = False, kwargs: str | None = None, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Update an auth domain"""
    return await access.update_domain(client, realm=realm, confirm=confirm, **_parse(kwargs), endpoint=endpoint)


@mcp.tool()
async def proxmox_delete_domain(realm: str = "", confirm: bool = False, endpoint: str | None = None) -> str:
    """(elevated, confirm required). Delete an auth domain"""
    return await access.delete_domain(client, realm=realm, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_get_user_tfa_types(userid: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get TFA types for a user via /access/users endpoint"""
    return await access.get_user_tfa_types(client, userid=userid, endpoint=endpoint)


@mcp.tool()
async def proxmox_openid_auth_url(realm: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get OpenID auth URL"""
    return await access.openid_auth_url(client, realm=realm, endpoint=endpoint)


@mcp.tool()
async def proxmox_openid_login(realm: str = "", code: str = "", state: str = "", endpoint: str | None = None) -> str:
    """(read-only). Login via OpenID"""
    return await access.openid_login(client, realm=realm, code=code, state=state, endpoint=endpoint)


@mcp.tool()
async def proxmox_update_snapshot_config(
    node: str | None = None,
    vmid: int | None = None,
    snapname: str = "",
    vmtype: str = "qemu",
    description: str | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Update snapshot configuration"""
    return await snapshots.update_snapshot_config(
        client,
        node=node,
        vmid=vmid,
        snapname=snapname,
        vmtype=vmtype,
        description=description,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_delete_subscription(
    node: str | None = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Delete node subscription"""
    return await nodes.delete_subscription(client, node=node, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_acquire_sdn_lock(confirm: bool = False, endpoint: str | None = None) -> str:
    """(elevated, confirm required). Acquire SDN lock"""
    return await sdn.acquire_sdn_lock(client, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_release_sdn_lock(confirm: bool = False, endpoint: str | None = None) -> str:
    """(elevated, confirm required). Release SDN lock"""
    return await sdn.release_sdn_lock(client, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_query_url_metadata(node: str | None = None, url: str = "", endpoint: str | None = None) -> str:
    """(read-only). Query URL metadata (file size/name/mime) on a node"""
    return await nodes.query_url_metadata(client, node=node, url=url, endpoint=endpoint)


@mcp.tool()
async def proxmox_wake_on_lan(
    node: str | None = None, macaddr: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Send Wake-on-LAN packet"""
    return await nodes.wake_on_lan(client, node=node, macaddr=macaddr, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_get_storage_on_node(
    node: str | None = None, storage: str = "local", endpoint: str | None = None
) -> str:
    """(read-only). Get detailed storage info on a node"""
    return await storage_mod.get_storage_on_node(client, node=node, storage=storage, endpoint=endpoint)


@mcp.tool()
async def proxmox_copy_volume(
    node: str | None = None,
    storage: str = "local",
    volume: str = "",
    target: str = "",
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Copy a volume to another storage"""
    return await storage_mod.copy_volume(
        client,
        node=node,
        storage=storage,
        volume=volume,
        target=target,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_update_volume_attributes(
    node: str | None = None,
    storage: str = "local",
    volume: str = "",
    confirm: bool = False,
    kwargs: str | None = None,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Update volume attributes"""
    return await storage_mod.update_volume_attributes(
        client,
        node=node,
        storage=storage,
        volume=volume,
        confirm=confirm,
        **_parse(kwargs),
    )


@mcp.tool()
async def proxmox_file_restore_list(
    node: str | None = None, storage: str = "local", endpoint: str | None = None
) -> str:
    """(read-only). List PBS backup file restore entries"""
    return await storage_mod.file_restore_list(client, node=node, storage=storage, endpoint=endpoint)


@mcp.tool()
async def proxmox_file_restore_download(
    node: str | None = None, storage: str = "local", filepath: str = "", endpoint: str | None = None
) -> str:
    """(read-only). Download a file from PBS backup"""
    return await storage_mod.file_restore_download(
        client, node=node, storage=storage, filepath=filepath, endpoint=endpoint
    )


@mcp.tool()
async def proxmox_storage_import_metadata(
    node: str | None = None, storage: str = "local", volume: str = "", endpoint: str | None = None
) -> str:
    """(read-only). Get storage import metadata for a volume"""
    return await storage_mod.storage_import_metadata(
        client, node=node, storage=storage, volume=volume, endpoint=endpoint
    )


@mcp.tool()
async def proxmox_oci_registry_pull(
    node: str | None = None, storage: str = "local", image: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Pull an OCI container image to storage"""
    return await storage_mod.oci_registry_pull(
        client, node=node, storage=storage, image=image, confirm=confirm, endpoint=endpoint
    )


@mcp.tool()
async def proxmox_cluster_config_apiversion(endpoint: str | None = None) -> str:
    """(read-only). Get cluster API version info"""
    return await cluster.cluster_config_apiversion(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_cluster_jobs_index(endpoint: str | None = None) -> str:
    """(read-only). List cluster jobs index"""
    return await cluster.cluster_jobs_index(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_list_realm_sync_jobs(endpoint: str | None = None) -> str:
    """(read-only). List realm synchronization jobs"""
    return await cluster.list_realm_sync_jobs(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_get_realm_sync_job(id: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get a specific realm sync job"""
    return await cluster.get_realm_sync_job(client, id=id, endpoint=endpoint)


@mcp.tool()
async def proxmox_vm_rrd(
    node: str | None = None,
    vmid: int | None = None,
    timeframe: str = "hour",
    cf: str = "AVERAGE",
    ds: str | None = None,
    endpoint: str | None = None,
) -> str:
    """Get VM RRD data (read-only, may return PNG).

    timeframe: hour/day/week/month/year. cf: AVERAGE/MAX. ds: specific data source.
    """
    return await lifecycle.vm_rrd(client, node=node, vmid=vmid, timeframe=timeframe, cf=cf, ds=ds, endpoint=endpoint)


@mcp.tool()
async def proxmox_lxc_rrd(
    node: str | None = None,
    vmid: int | None = None,
    timeframe: str = "hour",
    cf: str = "AVERAGE",
    ds: str | None = None,
    endpoint: str | None = None,
) -> str:
    """Get LXC container RRD data (read-only, may return PNG).

    timeframe: hour/day/week/month/year. cf: AVERAGE/MAX. ds: specific data source.
    """
    return await lifecycle.lxc_rrd(client, node=node, vmid=vmid, timeframe=timeframe, cf=cf, ds=ds, endpoint=endpoint)


@mcp.tool()
async def proxmox_lxc_rrddata(
    node: str | None = None,
    vmid: int | None = None,
    timeframe: str = "hour",
    cf: str = "AVERAGE",
    endpoint: str | None = None,
) -> str:
    """(read-only). Get LXC container RRD data points timeframe: hour/day/week/month/year. cf: AVERAGE/MAX."""
    return await lifecycle.lxc_rrddata(client, node=node, vmid=vmid, timeframe=timeframe, cf=cf, endpoint=endpoint)


@mcp.tool()
async def proxmox_get_lxc_config(node: str | None = None, vmid: int | None = None, endpoint: str | None = None) -> str:
    """(read-only). Get LXC container configuration"""
    return await lifecycle.get_lxc_config(client, node=node, vmid=vmid, endpoint=endpoint)


@mcp.tool()
async def proxmox_get_lxc_status(node: str | None = None, vmid: int | None = None, endpoint: str | None = None) -> str:
    """(read-only). Get LXC container current status"""
    return await lifecycle.get_lxc_status(client, node=node, vmid=vmid, endpoint=endpoint)


@mcp.tool()
async def proxmox_remote_migrate_lxc(
    node: str | None = None,
    vmid: int | None = None,
    target: str | None = None,
    target_endpoint: str | None = None,
    confirm: bool = False,
    kwargs: str | None = None,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Remote migrate an LXC container to another cluster Requires confirm=true."""
    return await lifecycle.remote_migrate_lxc(
        client,
        node=node,
        vmid=vmid,
        target=target,
        target_endpoint=target_endpoint,
        confirm=confirm,
        **_parse(kwargs),
    )


@mcp.tool()
async def proxmox_move_lxc_volume(
    node: str | None = None,
    vmid: int | None = None,
    volume: str = "rootfs",
    storage: str | None = None,
    target_vmid: int | None = None,
    target_volume: str | None = None,
    confirm: bool = False,
    kwargs: str | None = None,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Move an LXC container volume to different storage."""
    return await lifecycle.move_lxc_volume(
        client,
        node=node,
        vmid=vmid,
        volume=volume,
        storage=storage,
        target_vmid=target_vmid,
        target_volume=target_volume,
        confirm=confirm,
        **_parse(kwargs),
    )


@mcp.tool()
async def proxmox_get_vm_config(
    node: str | None = None, vmid: int | None = None, current: bool = False, endpoint: str | None = None
) -> str:
    """(read-only). Get VM configuration Set current=True for current config instead of pending."""
    return await lifecycle.get_vm_config(client, node=node, vmid=vmid, current=current, endpoint=endpoint)


@mcp.tool()
async def proxmox_update_vm_config(
    node: str | None = None,
    vmid: int | None = None,
    confirm: bool = False,
    kwargs: str | None = None,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Update VM configuration (elevated, confirm required, asynchronous API)."""
    return await lifecycle.update_vm_config(
        client, node=node, vmid=vmid, confirm=confirm, **_parse(kwargs), endpoint=endpoint
    )


@mcp.tool()
async def proxmox_vm_rrddata(
    node: str | None = None,
    vmid: int | None = None,
    timeframe: str = "hour",
    cf: str = "AVERAGE",
    endpoint: str | None = None,
) -> str:
    """(read-only). Get VM RRD data points timeframe: hour/day/week/month/year. cf: AVERAGE/MAX."""
    return await lifecycle.vm_rrddata(client, node=node, vmid=vmid, timeframe=timeframe, cf=cf, endpoint=endpoint)


@mcp.tool()
async def proxmox_remote_migrate_vm(
    node: str | None = None,
    vmid: int | None = None,
    target_address: str | None = None,
    target_node: str | None = None,
    target_storage: str | None = None,
    confirm: bool = False,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Remote migrate a VM to another cluster. EXPERIMENTAL."""
    return await lifecycle.remote_migrate_vm(
        client,
        node=node,
        vmid=vmid,
        target_address=target_address,
        target_node=target_node,
        target_storage=target_storage,
        confirm=confirm,
    )


@mcp.tool()
async def proxmox_list_ha_rules(endpoint: str | None = None) -> str:
    """(read-only). List HA rules in the cluster"""
    return await ha.list_ha_rules(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_create_ha_rule(
    group: str = "", comment: str | None = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Create an HA rule"""
    return await ha.create_ha_rule(client, group=group, comment=comment, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_get_ha_rule(rule: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get HA rule configuration"""
    return await ha.get_ha_rule(client, rule=rule, endpoint=endpoint)


@mcp.tool()
async def proxmox_update_ha_rule(
    rule: str = "",
    comment: str | None = None,
    confirm: bool = False,
    kwargs: str | None = None,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Update an HA rule"""
    return await ha.update_ha_rule(
        client, rule=rule, comment=comment, confirm=confirm, **_parse(kwargs), endpoint=endpoint
    )


@mcp.tool()
async def proxmox_delete_ha_rule(rule: str = "", confirm: bool = False, endpoint: str | None = None) -> str:
    """(elevated, confirm required). Delete an HA rule"""
    return await ha.delete_ha_rule(client, rule=rule, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_get_ha_group(group: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get HA group configuration"""
    return await ha.get_ha_group(client, group=group, endpoint=endpoint)


@mcp.tool()
async def proxmox_update_ha_group(
    group: str = "",
    comment: str | None = None,
    nodes: str | None = None,
    confirm: bool = False,
    kwargs: str | None = None,
    endpoint: str | None = None,
) -> str:
    """(elevated, confirm required). Update an HA group"""
    return await ha.update_ha_group(
        client, group=group, comment=comment, nodes=nodes, confirm=confirm, **_parse(kwargs)
    )


@mcp.tool()
async def proxmox_delete_ha_group(group: str = "", confirm: bool = False, endpoint: str | None = None) -> str:
    """(elevated, confirm required). Delete an HA group"""
    return await ha.delete_ha_group(client, group=group, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_arm_ha(confirm: bool = False, endpoint: str | None = None) -> str:
    """(elevated, confirm required). Arm the HA manager"""
    return await ha.arm_ha(client, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_disarm_ha(confirm: bool = False, endpoint: str | None = None) -> str:
    """(elevated, confirm required). Disarm the HA manager"""
    return await ha.disarm_ha(client, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_ha_manager_status(endpoint: str | None = None) -> str:
    """(read-only). Get HA manager status"""
    return await ha.ha_manager_status(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_create_ticket(username: str = "", password: str = "", endpoint: str | None = None) -> str:
    """(read-only). Create an authentication ticket (returns ticket+CSRF token)."""
    return await access.create_ticket(client, username=username, password=password, endpoint=endpoint)


@mcp.tool()
async def proxmox_create_vnc_ticket(
    port: int | None = None, vnc: str | None = None, endpoint: str | None = None
) -> str:
    """(read-only). Create a VNC ticket (VNC auth)."""
    return await access.create_vnc_ticket(client, port=port, vnc=vnc, endpoint=endpoint)


@mcp.tool()
async def proxmox_lxc_sendkey(
    node: str | None = None, vmid: int | None = None, key: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Send a key press to an LXC container"""
    return await lifecycle.lxc_sendkey(client, node=node, vmid=vmid, key=key, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_check_subscription(
    node: str | None = None, confirm: bool = False, endpoint: str | None = None
) -> str:
    """(read-only). Check for subscription updates from Proxmox servers"""
    return await nodes.check_subscription(client, node=node, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_get_directory_detail(node: str | None = None, name: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get directory storage details"""
    return await disks.get_directory_detail(client, node=node, name=name, endpoint=endpoint)


@mcp.tool()
async def proxmox_get_lvmthin_detail(node: str | None = None, name: str = "", endpoint: str | None = None) -> str:
    """(read-only). Get LVM thin pool details"""
    return await disks.get_lvmthin_detail(client, node=node, name=name, endpoint=endpoint)


@mcp.tool()
async def proxmox_reload_service(
    node: str | None = None, service: str = "", confirm: bool = False, endpoint: str | None = None
) -> str:
    """(elevated, confirm required). Reload a service on a node"""
    return await nodes.reload_service(client, node=node, service=service, confirm=confirm, endpoint=endpoint)


@mcp.tool()
async def proxmox_get_next_vmid(endpoint: str | None = None) -> str:
    """(read-only). Get the next available VMID"""
    return await discovery.get_next_vmid(client, endpoint=endpoint)


@mcp.tool()
async def proxmox_generate_cluster_config(
    node: str | None = None, confirm: bool = False, kwargs: str | None = None, endpoint: str | None = None
) -> str:
    """(elevated, confirm required, DANGEROUS). Generate cluster config for joining"""
    return await cluster.generate_cluster_config(
        client, node=node, confirm=confirm, **_parse(kwargs), endpoint=endpoint
    )


@mcp.tool()
async def proxmox_remove_cluster_node(node: str = "", confirm: bool = False, endpoint: str | None = None) -> str:
    """(elevated, confirm required). Remove a node from the cluster"""
    return await cluster.remove_cluster_node(client, node=node, confirm=confirm, endpoint=endpoint)


async def startup() -> None:
    global client
    await client.initialize()


def main() -> None:
    global client
    try:
        multi_config = MultiConfig.from_env()
    except ValueError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        sys.exit(1)

    client = MultiClient(multi_config)

    transport = os.environ.get("PROXMOX_MCP_TRANSPORT", "stdio")

    if transport == "sse":
        mcp.run(transport="sse")
    else:
        mcp.run()


if __name__ == "__main__":
    main()
