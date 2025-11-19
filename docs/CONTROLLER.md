## CONTROLLER.md

The controller is the only host that touches bare metal provisioning and the only
node exposed to the outside world.

### 1. Responsibilities

1. **PXE authority** – dnsmasq + Apache + TFTP chain together to netboot compute
   nodes. All Kickstart media, iPXE binaries, and repo mirrors live here.
2. **Configuration** – dynamic inventory, playbooks, and validation tooling run
   from this node.
3. **Scheduler** – Slurmctld, database paths (`/var/spool/slurmctld`), and
   controller-side Munge live here.
4. **Validation** – Pavilion installs under `/opt/pavilion2` and executes
   smoke tests that reach across the cluster.

> Slurm packages are mirrored on the controller only. Tune `config/slurm.yml`
> to set the upstream URL/version, mirror path, and (optional) GPG key. The
> controller playbook builds the mirror and publishes it via HTTP for offline
> compute nodes.

### 2. Bootstrapping Flow

1. Clone the repo under and populate `.env` with PXE password hashes generated via `scripts/generate_hashes.py`.
2. Run `make inv` from the dev workstation to generate `inventory/inventory.json`.
3. Execute `make controller`. That single command:
   - Ensures system Python 3.9 is present, creates `.venv`, and installs ansible-core + dependencies.
   - Configures dnsmasq, Apache, firewalld, and NetworkManager.
   - Seeds the Munge key, deploys Slurmctld, and ensures services are active.

> Repo note: the `controller_common` role auto-detects common Rocky/RHEL repo IDs
> but ultimately enables whatever is listed in `controller_core_repo_ids`. Override
> this variable when using custom repo names (subscription repos, internal mirrors,
> etc.) so automated package installs keep working.

### 3. Operational Discipline

- **No manual edits** under `/etc/dnsmasq*` and `/etc/slurm/`. Always
  modify the corresponding role/template and rerun Ansible.
- **Keep the repo clean**: `git status` should be empty between runs so inventory and
  secrets do not drift unnoticed.
- **Fact cache hygiene**: `make inv-clean` before major reconfiguration to avoid
  stale hostvars.
- **Firewall guardrails**: the controller runs the “SSH protector” logic, so running
  the playbook locally (without SSH) is safe. 
  > When connecting over SSH, confirm the source IP is accurate before allowing Ansible to reconfigure firewalld!

### 4. Failure Modes + Recovery

| Symptom                  | Likely Cause                              | Recovery                                                                                 |
| ------------------------ | ----------------------------------------- | ---------------------------------------------------------------------------------------- |
| PXE clients hang on DHCP | dnsmasq not running or wrong subnet       | `systemctl status dnsmasq`; rerun `make controller` to redeploy configs                  |
| Kickstart downloads fail | Apache not serving `/var/www/html/os`     | `curl http://10.0.0.1/os/images/pxeboot/vmlinuz`; check SELinux booleans, rerun PXE role |
| Slurmctld down           | Munge mismatch or `slurm.conf` corruption | `slurmctld -Dvvv` to inspect logs, reapply scheduler playbook                            |
| Pavilion cannot run      | Missing Pavilion configs or Slurm state   | ensure validation role succeeded, check `/opt/pavilion2` and Slurm services              |

### 5. Maintenance Windows

- Scheduled updates should follow: `dnf update`, `reboot`, `make controller`, `make compute`, `make validate`. 
  This sequence guarantees PXE assets and Slurm state are synchronized after the controller changes.
