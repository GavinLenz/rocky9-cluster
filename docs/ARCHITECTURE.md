# ARCHITECTURE.md

The cluster is intentionally small, repeatable, and deterministic. Every hardware
choice and software path exists to keep the operating envelope legible. This file is
the top-level contract for how the system is stitched together.

---

## 1. Physical And Logical Topology

| Role       | Hostname | CPU / RAM                  | Notes                                |
| ---------- | -------- | -------------------------- | ------------------------------------ |
| Controller | head     | Ryzen 7 PRO 4750U  / 16 GB | Runs PXE, Slurmctld, Apache, DNSMasq |
| Compute    | node01   | Ryzen 6800H / 24 GB        | Slurmd + Pavilion workers            |
| Compute    | node02   | Ryzen 6800H / 24 GB        | Slurmd + Pavilion workers            |
| Compute    | node03   | Ryzen 6800H / 24 GB        | Slurmd + Pavilion workers            |

* Interfaces are hard-wired to a single flat `/24` (10.0.0.0/24) switch. No routing,
  no DHCP from upstream. The controller’s `enp5s0` is authoritative for DHCP, PXE,
  and HTTP.
* Shared file services are deferred for the MVP; compute nodes run from local disks for
  now.

## 2. Control Flow

1. **PXE/iPXE**: Controller’s dnsmasq advertises DHCP + TFTP. Clients netboot into an
   iPXE script that points at `http://10.0.0.1/os` for kernel/initrd and downloads
   `ks.cfg` from the same host.
2. **Kickstart**: Installs Rocky 9 Minimal, configures networking via DHCP, creates
   the `ansible` user, and hands off to the installed OS.
3. **Dynamic Inventory**: `inventory/generator.py` reads `config/*.yml` + `.env`
   secrets to emit `inventory/inventory.json`. That file is the single source of truth
   for hostvars, PXE metadata, and credentials.
4. **Ansible Roles**: `make controller|compute` ties together the role stack:
   `common` → `pxe` → `controller/scheduler`. Tags are minimal; roles assume a clean
   environment and enforce idempotence themselves.
5. **Validation**: Pavilion installs on the controller and fans Slurm-based smoke
   tests across the cluster.


### Role Stack Per Host

- **Controller**: `common → pxe → controller → scheduler`
- **Compute**: `common → scheduler`

## 3. Network Contracts

- `10.0.0.1` – Controller interface. DHCP scope 10.0.0.10–10.0.0.15 for PXE installs.
- DNS points at the controller. External DNS is proxied through `8.8.8.8` only to
  simplify Kickstart repos.
- All hosts enforce a baseline firewalld policy. Controller opens HTTP/TFTP/DHCP.
  Compute nodes allow SSH plus internal traffic.

## 4. State Surfaces

- `/srv/tftp`, `/var/www/html/os`, `/var/www/html/repos` on the controller store PXE
  artifacts and mirrored RPM repositories.
- `.ansible_cache` and `inventory/inventory.json` live on the dev machine to speed up
  repeated runs.

This architecture intentionally avoids hidden state. If you need to change any
boundary (new subnet or more nodes), update `config/*.yml`, rerun `make inv`, and then
reapply the relevant playbooks. If you later add clustered file services, revisit the
inventory, roles, and firewall expectations.

