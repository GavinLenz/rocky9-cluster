## HOSTS.md

This guide describes what each host role does today. The controller is feature-rich
because it owns PXE, validation, and repo state; compute nodes are intentionally
minimal so they can be wiped and rebuilt quickly.

> **WIP**: Compute nodes only get the automation user + Python today. Scheduler, storage,
> and workload roles will be layered later as requirements solidify.

---

## 1. Controller Role

### Responsibilities

1. **PXE authority** – dnsmasq + Apache + TFTP netboot the fleet. All Kickstart
   media, iPXE binaries, and repo mirrors live under `/var/www/html` and `/srv/tftp`.
2. **Configuration hub** – dynamic inventory, playbooks, and Pavilion run here.
3. **Validation** – Pavilion installs under `/opt/pavilion2` and runs controller-
   local smoke tests (PXE services, HTTP, firewall, repo mirrors).

### Provisioning Flow

1. Clone the repo and populate `.env` with password hashes from
   `scripts/generate_hashes.py`.
2. `make inv` to generate `inventory/inventory.json`.
3. `make controller`, which enforces:
   - `controller_common`: users, SSH keys, sudoers drop-in, baseline packages.
   - `controller`: hostname, static IP, Python virtualenv for Ansible.
   - `pxe`: dnsmasq, Apache, firewall, PXE assets, ISO mounts.
4. Optional: `make validate` installs Pavilion and runs the raw scheduler suites.

### Operational Discipline

- Never edit `/etc/dnsmasq*`, `/etc/NetworkManager/system-connections/*`, or
  `/opt/pavilion2` manually—change the role templates and rerun Ansible.
- Keep `inventory/inventory.json` current (`make inv`) before any playbook runs.
- When applying firewall changes over SSH, confirm the source IP so the guard logic
  adds the correct temporary allow rule.

### Failure Modes

| Symptom                     | Likely Cause                     | Recovery                                               |
| --------------------------- | -------------------------------- | ------------------------------------------------------ |
| PXE clients hang on DHCP    | dnsmasq down / wrong subnet      | `systemctl status dnsmasq`; rerun `make controller`.   |
| Kickstart downloads fail    | Apache not serving `/var/www`    | `curl http://10.0.0.1/os/...`; check SELinux + rerun.  |
| Pavilion run fails          | Missing configs or services      | Ensure PXE role succeeded, rerun `make validate`.      |
| Firewall locks out SSH      | Wrong source IP in guard logic   | Access via console, revert `firewalld`, rerun playbook |

---

## 2. Compute Role

### Responsibilities

1. Boot via PXE/iPXE/Kickstart and register the `ansible` automation user.
2. Keep only the minimal baseline needed for remote management (Python + SSH).
3. Stay disposable—if a node drifts, reimage it.

### Provisioning Flow

1. Set BIOS/UEFI to PXE first, NVMe second. Ensure NIC MACs are recorded in
   `config/nodes.yml`.
2. After Kickstart completes, run `make compute`. The `compute_common` role:
   - Creates the `cluster` group (system) and `ansible` user.
   - Installs the controller’s public key and passwordless sudo drop-in.
   - Installs `python3` so Ansible modules can execute.

> Future scheduler or application roles will be layered on top once the control
> plane hardens. For now, compute nodes are barebones by design.

### Troubleshooting

| Symptom                | Probable Cause                  | Fix                                             |
| ---------------------- | ------------------------------- | ----------------------------------------------- |
| Node stuck looping PXE | Boot order reset / wrong MAC    | Reorder devices, verify MAC in `config/nodes`.  |
| Ansible SSH failures   | User/key mismatch               | Re-run `make compute`, confirm `ansible` user.  |
| Python missing         | Kickstart image changed         | Install `python3`, rerun `compute_common`.      |

### Runtime Expectations

- Nodes remain stateless; no firewalld or scheduler config is applied yet.
- Reapply `make compute` after firmware updates or reimages to keep credentials in sync.
