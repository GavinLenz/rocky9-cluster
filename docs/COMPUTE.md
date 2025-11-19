## COMPUTE.md

Compute nodes are disposable workhorses. They boot via PXE and run Slurmd. Their configuration is intentionally minimal so they can be reimaged in minutes, and for the current MVP they rely on local scratch only.

### 1. Responsibilities

1. Execute Slurm jobs via `slurmd`.
2. Run Pavilion tests when dispatched (validation role fans across compute hosts).
3. Stay stateless: local disks are scratch only.

### 2. Provisioning Path

1. BIOS/UEFI set to PXE first, NVMe second. MAC addresses recorded in `config/nodes.yml`.
2. PXE → iPXE → Kickstart installs Rocky 9 Minimal over DHCP.
3. `make compute` applies `common` and `scheduler` roles:
   - installs base packages and `ansible` user
   - ensures firewalld allows SSH + internal network
   - pulls the controller-generated Munge key and starts `slurmd`

### 3. Runtime Expectations

- Nodes reboot nightly via cron if idle, ensuring patches take effect after maintenance.
- `slurmd` auto-starts and re-registers with Slurmctld.
- If a node misbehaves, wipe it: netboot + `make compute` takes <10 minutes.

### 4. Troubleshooting Cheatsheet

| Symptom                   | Probable Cause                         | Fix                                                    |
| ------------------------- | -------------------------------------- | ------------------------------------------------------ |
| Node missing from `sinfo` | `slurmd` not running or Munge mismatch | `systemctl status slurmd`, reapply scheduler role      |
| PXE loop after reboot     | Boot order reset, wrong NIC            | Reorder boot devices, verify MAC in `config/nodes.yml` |
