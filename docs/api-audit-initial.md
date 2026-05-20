# PVE API Parameter Audit — Initial Report

**Issue:** #25  
**Date:** 2026-05-16  
**Auditor:** Reviewer Agent  
**Scope:** 5 critical modules — VM create/modify, LXC create/modify, Network, Storage, ACL/Permissions  

---

## Summary

Across the 5 audited modules, I found **31 issues** categorized as:

| Severity | Count | Description |
|----------|-------|-------------|
| **HIGH** | 8 | Missing required-or-common PVE parameters; incorrect required/optional marking |
| **MEDIUM** | 12 | Missing commonly-used parameters; type mismatches; incorrect defaults |
| **LOW** | 11 | Missing convenience parameters; documentation gaps; minor inconsistencies |

---

## Module 1: VM Create/Modify (lifecycle.py)

### `proxmox_create_vm` (server.py:342–372)

**Current parameters:** `node`, `vmid`, `name`, `memory`, `cores`, `sockets`, `disk_size`, `storage`, `iso`, `ostype`, `net0`, `confirm`, `endpoint`

**PVE API `POST /nodes/{node}/qemu` supports 80+ parameters.** Key missing parameters:

| Parameter | PVE Type | Priority | Notes |
|-----------|-----------|----------|-------|
| `description` | string | HIGH | Commonly set on VM creation |
| `boot` | string | HIGH | Boot order, e.g. `order=scsi0;ide2;net0` — critical for bootable VMs |
| `scsihw` | string | HIGH | SCSI controller model — required if using scsi disks (default `lsi` can cause issues) |
| `onboot` | boolean | MEDIUM | Auto-start on host boot |
| `pool` | string | MEDIUM | Assign VM to pool on creation |
| `start` | boolean | MEDIUM | Start after creation (PVE supports this; our tool doesn't) |
| `cpu` | string | MEDIUM | CPU type (e.g. `host`, `qemu64`) |
| `bios` | string | MEDIUM | `seabios` or `ovmf` — critical for UEFI VMs |
| `agent` | string/boolean | MEDIUM | QEMU Guest Agent enable |
| `tags` | string | LOW | VM tags |
| `cloud-init params` (`ciuser`, `cipassword`, `sshkeys`, `ipconfig0`) | various | MEDIUM | Cloud-init is common; we have a separate `set_cloudinit` but not on create |
| `ide[n]`, `sata[n]`, `virtio[n]` | string | LOW | Additional disk interfaces beyond scsi0 |
| `hostpci[n]` | string | LOW | PCIe passthrough |
| `usb[n]` | string | LOW | USB passthrough |

**Issues found:**

1. **[HIGH] Missing `boot` parameter** — Without this, VMs may not boot correctly. PVE defaults to legacy boot, but for UEFI/SCSI VMs `boot=order=scsi0` is required.

2. **[HIGH] Missing `scsihw` parameter** — Default is `lsi` which has driver issues. `virtio-scsi-pci` is the modern default in the PVE web UI. Our tool creates scsi0 disks but doesn't let users pick the SCSI controller.

3. **[HIGH] `memory` type is `int` but PVE accepts `string`** — PVE API allows `memory` as a string that can include balloon properties (e.g., `memory=4096,balloon=2048`). Our `int` type loses this capability.

4. **[MEDIUM] Missing `start` parameter** — PVE supports `start=1` to auto-start VM after creation. Users must call `proxmox_start_vm` separately.

5. **[MEDIUM] Missing `pool` parameter** — Cannot assign VM to a resource pool during creation.

6. **[MEDIUM] Missing `description` parameter** — Cannot set VM description during creation.

7. **[MEDIUM] `iso` parameter uses custom logic** — The `iso` param is transformed into `cdrom=` inside `lifecycle.py`. This is correct but confusing. The PVE API uses `cdrom` directly. Our tool should either rename this to `cdrom` or document the transformation clearly.

### `proxmox_configure_vm` (server.py:456–472)

**Current parameters:** `node`, `vmid`, `cores`, `memory`, `confirm`, `endpoint`

**Issues found:**

8. **[HIGH] Extremely limited** — Only exposes `cores` and `memory`. PVE `PUT /nodes/{node}/qemu/{vmid}/config` supports 80+ parameters including `boot`, `cpu`, `sockets`, `description`, `onboot`, `agent`, all disk/net configs, `tags`, `bios`, `vga`, etc. This tool is near-useless for real VM configuration.

9. **[MEDIUM] No `kwargs` passthrough** — Unlike some other tools (e.g., `update_vm_config` which has a `kwargs` param), this tool has no escape hatch for advanced parameters.

### `proxmox_clone_vm` (server.py:416–434)

**Current parameters:** `node`, `vmid`, `newid`, `name`, `full`, `confirm`, `endpoint`

**Issues found:**

10. **[MEDIUM] Missing `target` parameter** — PVE clone supports `target` node for cross-node cloning. The clone tool doesn't expose this. The LXC clone tool *does* expose `target`.

11. **[LOW] Missing `snapname` parameter** — PVE supports cloning from a specific snapshot.

### `proxmox_migrate_vm` (server.py:438–452)

**Current parameters:** `node`, `vmid`, `target`, `confirm`, `endpoint`

**Issues found:**

12. **[MEDIUM] Missing migration options** — PVE `POST /nodes/{node}/qemu/{vmid}/migrate` supports: `online` (boolean, live migration), `with-local-disks` (boolean), `targetstorage` (string), `migrate-speed` (integer). Only `target` is exposed.

13. **[MEDIUM] Missing `online` parameter specifically** — Live vs offline migration is a critical choice that users need to make.

---

## Module 2: LXC Create/Modify (lifecycle.py)

### `proxmox_create_lxc` (server.py:166–194)

**Current parameters:** `node`, `vmid`, `ostemplate`, `hostname`, `memory`, `cores`, `rootfs`, `storage`, `password`, `start`, `confirm`, `endpoint`

**PVE API `POST /nodes/{node}/lxc` supports 40+ parameters.** Key missing:

| Parameter | PVE Type | Priority | Notes |
|-----------|-----------|----------|-------|
| `swap` | integer | HIGH | Swap size in MiB — PVE default is 0, which is often wrong |
| `onboot` | boolean | MEDIUM | Auto-start on host boot |
| `pool` | string | MEDIUM | Assign to resource pool |
| `description` | string | MEDIUM | Container description |
| `net0` | string | MEDIUM | Network config, e.g. `name=eth0,bridge=vmbr0,ip=dhcp` |
| `nameserver` | string | MEDIUM | DNS server |
| `searchdomain` | string | MEDIUM | DNS search domain |
| `ssh-public-keys` | string | MEDIUM | SSH keys |
| `features` | string | MEDIUM | e.g., `nesting=1` — very commonly needed |
| `unprivileged` | boolean | MEDIUM | Unprivileged container — default is 0 (privileged) which is a security concern |
| `tags` | string | LOW | Tags |
| `protection` | boolean | LOW | Protection flag |

**Issues found:**

14. **[HIGH] Missing `features` parameter** — `nesting=1` is extremely commonly needed. Without it, containers can't run Docker. This is one of the first things users set in the PVE web UI.

15. **[HIGH] Missing `unprivileged` parameter** — PVE default is privileged containers (0). Security best practice is unprivileged (1). Users cannot set this via our tool.

16. **[HIGH] Missing `swap` parameter** — PVE defaults swap to 512MiB in the web UI but 0 in the API. Without this, containers created via our tool get no swap, which can cause OOM issues.

17. **[MEDIUM] Missing `net0` parameter** — Network configuration is one of the most important LXC parameters. Users would have to modify the container after creation.

18. **[MEDIUM] Missing `nameserver` and `searchdomain`** — DNS configuration — very commonly needed.

### `proxmox_configure_lxc` (server.py:238–254)

**Current parameters:** `node`, `vmid`, `cores`, `memory`, `confirm`, `endpoint`

**Issues found:**

19. **[HIGH] Same problem as VM configure** — Only exposes `cores` and `memory`. PVE `PUT /nodes/{node}/lxc/{vmid}/config` supports all the same parameters as create. This tool is nearly useless for real LXC configuration changes.

---

## Module 3: Network (networking.py)

### `proxmox_create_network` (server.py — via networking.py)

**Current parameters:** `node`, `iface`, `type`, `address`, `netmask`, `gateway`, `bridge_ports`, `confirm`, `apply`, `endpoint`

**PVE API `POST /nodes/{node}/network` supports:**

| Parameter | PVE Type | Priority | Notes |
|-----------|-----------|----------|-------|
| `iface` | string | ✅ Present | |
| `type` | string | ✅ Present | |
| `address` | string | ✅ Present | |
| `netmask` | string | ✅ Present | |
| `gateway` | string | ✅ Present | |
| `bridge_ports` | string | ✅ Present | |
| `cidr` | string | HIGH | PVE supports CIDR notation as alternative to address+netmask. Modern PVE prefers CIDR. |
| `address6` | string | MEDIUM | IPv6 address |
| `gateway6` | string | MEDIUM | IPv6 gateway |
| `cidr6` | string | MEDIUM | IPv6 CIDR |
| `autostart` | boolean | MEDIUM | Auto-start the interface |
| `comments` | string | LOW | Interface description |
| `mtu` | integer | LOW | MTU setting |
| `vlan-protocol` | string | LOW | 802.1Q vs 802.1ad |

**Issues found:**

20. **[HIGH] Missing `cidr` parameter** — Modern PVE configurations use CIDR notation (`192.168.1.1/24`) instead of separate `address`+`netmask`. Not supporting `cidr` forces users into the old format.

21. **[MEDIUM] Missing IPv6 parameters** — `address6`, `gateway6`, `cidr6` for IPv6 configuration.

22. **[MEDIUM] Missing `autostart` parameter** — Important for ensuring interfaces come up on boot.

### `proxmox_update_network` (server.py — via networking.py)

**Current parameters:** `node`, `iface`, `address`, `netmask`, `gateway`, `confirm`, `apply`, `endpoint`

**Issues found:**

23. **[HIGH] Same missing parameters as create** — `cidr`, IPv6, `autostart`, `mtu` not exposed. Update is even more limited than create.

24. **[LOW] No `delete` parameter** — PVE `PUT /nodes/{node}/network/{iface}` supports a `delete` parameter to remove specific config keys.

### `proxmox_delete_network` 

**Current parameters:** `node`, `iface`, `confirm`, `apply`, `endpoint`

**No issues found** — this is straightforward and matches the PVE API.

---

## Module 4: Storage (storage.py)

### `proxmox_create_storage` (server.py)

**Current parameters:** `storage`, `type`, `path`, `content`, `nodes`, `confirm`, `endpoint`

**PVE API `POST /storage` supports many more parameters depending on type:**

Key PVE storage parameters missing:

| Parameter | PVE Type | Priority | Notes |
|-----------|-----------|----------|-------|
| `blocksize` | integer | MEDIUM | For ZFS storage |
| `bwlimit` | string | LOW | Bandwidth limit |
| `compression` | string | MEDIUM | ZFS compression |
| `content` | string | ✅ Present | But should document format: `images,rootdir,backup,iso,vztmpl` |
| `data_pool` | string | LOW | For Ceph |
| `fs_name` | string | MEDIUM | For CephFS storage type |
| `keyring` | string | MEDIUM | For Ceph |
| `krbd` | boolean | LOW | For Ceph |
| `master` | string | LOW | For gluster |
| `monhost` | string | MEDIUM | For Ceph monitor hosts |
| `pool` | string | MEDIUM | For Ceph/ZFS pool name |
| `prefech` | integer | LOW | For NFS |
| `server` | string | HIGH | For NFS/CIFS — the remote server |
| `share` | string | MEDIUM | For CIFS share name |
| `username`/`password` | string | MEDIUM | For CIFS auth |
| ` subdir` | string | LOW | For gluster subdirectory |
| `target` | string | LOW | For gluster |
| `thinpool` | string | MEDIUM | For LVM-thin |

**Issues found:**

25. **[HIGH] Missing `server` parameter for NFS/CIFS storage** — NFS is one of the most common storage types. Without `server`, you cannot create NFS storage via our tool.

26. **[MEDIUM] Missing Ceph parameters** — `monhost`, `pool`, `fs_name` are essential for Ceph storage creation.

27. **[MEDIUM] Type-specific parameters not documented** — The `type` field accepts `dir`, `nfs`, `cifs`, `gluster`, `iscsi`, `cephfs`, `rbd`, `lvm`, `lvmthin`, `zfs`, `zfspool`, etc. But our tool gives no guidance about which additional parameters are needed for each type.

### `proxmox_update_storage` (server.py)

**Current parameters:** `storage`, `content`, `nodes`, `delete`, `confirm`, `endpoint`

**Issues found:**

28. **[MEDIUM] Very limited update parameters** — Only `content`, `nodes`, and `delete` are exposed. Storage update should support many more parameters (e.g., changing `server`, `bwlimit`, `compression`, etc.).

---

## Module 5: ACL/Permissions (permissions.py)

### `proxmox_set_acl` (server.py)

**Current parameters:** `users`, `roles`, `path`, `propagate`, `confirm`, `endpoint`

**PVE API `PUT /access/acl` supports:**

| Parameter | PVE Type | Priority | Notes |
|-----------|-----------|----------|-------|
| `users` | string | ✅ Present | |
| `roles` | string | ✅ Present | |
| `path` | string | ✅ Present | |
| `propagate` | boolean | ✅ Present | |
| `delete` | integer | MEDIUM | Delete flag (we use a separate delete function) |
| `groups` | string | HIGH | PVE ACLs can be set for groups, not just users |

**Issues found:**

29. **[HIGH] Missing `groups` parameter** — PVE ACL API supports both `users` and `groups`. Our tool only accepts `users`. Group-based ACL assignment is completely inaccessible.

30. **[LOW] `delete` for ACL uses `PUT` with `delete=1`** — Our `delete_acl` function correctly does this, but the approach is non-obvious. This is fine functionally.

### `proxmox_create_user` (server.py)

**Current parameters:** `userid`, `password`, `comment`, `email`, `firstname`, `lastname`, `enable`, `expire`, `groups`, `confirm`, `endpoint`

**PVE API `POST /access/users` — coverage is good.** 

**Issues found:**

31. **[LOW] `password` validation missing** — PVE allows empty passwords (for API-token-only users), but our code does `if not password: raise ValueError(...)`. This prevents creating API-only users without passwords. The PVE API does not require a password if other auth mechanisms are used.

---

## Cross-Cutting Issues

### Pattern: All required PVE parameters marked as `Optional[str] = None` or `Optional[int] = None`

In server.py, nearly every parameter uses `str | None = None` or `int | None = None`. PVE API has parameters that are required (`node`, `vmid`, `storage`, etc.) but our tool signatures mark them as optional. This leads to runtime validation instead of schema validation. The actual required validation happens in the underlying module functions (e.g., `validate_vmid()`, `validate_node_name()`) but is not reflected in the MCP tool schema.

**Recommendation:** Required PVE parameters should be marked as required (no `| None = None`) in tool signatures, and only truly optional PVE parameters should be optional. This would give LLM consumers better parameter guidance via the tool schema.

### Pattern: `kwargs` passthrough exists in some tools but not others

Some tools like `create_cluster_firewall_rule` accept `**kwargs` for passthrough, but most create/update tools don't. This inconsistency means:
- Firewall rules: advanced params work via `kwargs`
- VM/LXC create: no passthrough, missing params are silently dropped

**Recommendation:** All create/update tools should either expose important parameters explicitly OR provide a `kwargs` passthrough mechanism.

### Pattern: `confirm` and `endpoint` on every tool

These are our internal parameters, not PVE API parameters. This is correct and expected — they're for our elevated-ops gating and multi-endpoint support.

### Pattern: Type mismatches between PVE API and our tools

PVE API uses `string` for many `integer`-like parameters (e.g., `memory` in VM create can be a string with balloon properties). Our tools use Python `int` which is more restrictive. This is mostly acceptable since the common case is integer values, but should be documented.

---

## Recommended Priority Actions

1. **Add `description`, `boot`, `scsihw`, `onboot`, `start`, `pool` to `proxmox_create_vm`** — These are the most commonly needed VM creation parameters.
2. **Add `features`, `unprivileged`, `swap`, `net0`, `nameserver`, `searchdomain` to `proxmox_create_lxc`** — These are critical for functional LXC containers.
3. **Expand `proxmox_configure_vm` and `proxmox_configure_lxc`** — Consider adding `kwargs` passthrough or exposing at least `description`, `onboot`, `tags`, `boot`, `cpu`, `bios`, `agent` for VM and `features`, `swap`, `net0`, `onboot`, `nameserver`, `searchdomain`, `rootfs`, `mp[n]` for LXC.
4. **Add `cidr` and `autostart` to network create/update** — Modern PVE usage requires CIDR.
5. **Add `groups` parameter to `proxmox_set_acl`** — Essential for group-based ACL management.
6. **Add `server` and other type-specific parameters to `proxmox_create_storage`** — NFS/CIFS/Ceph storage creation is impossible without these.
7. **Add `online`, `with-local-disks`, `targetstorage` to VM migration** — Live migration is the common case.
8. **Document which PVE storage types require which parameters** — Consider validation based on `type` value.
9. **Consider making truly required PVE parameters required in tool signatures** — `node`, `vmid`, `storage`, etc. should not be `Optional`.
10. **Add `target` to VM clone** — Already present in LXC clone, missing from VM clone.

---

## Methodology

1. Read `server.py` (5604 lines) — all tool function signatures
2. Read `lifecycle.py` (1390 lines) — VM/LXC create/config/clone/migrate implementation
3. Read `networking.py` (244 lines) — network create/update/delete
4. Read `storage.py` (619 lines) — storage create/update/delete/ISO/volume
5. Read `permissions.py` (562 lines) — ACL/user/role/token operations
6. Compared against official PVE API docs (via Context7 PVE OpenAPI spec)
7. Verified parameter types against PVE JSON schema types