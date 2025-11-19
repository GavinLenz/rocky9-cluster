## PIPELINE.md

This is the battle plan from bare metal to validated cluster. No stage is optional.

### Stage 0 – Config Authoring

- Edit `config/*.yml` to describe nodes, network, PXE images, and roles.
- Populate `.env` with PXE password hashes.
- `make inv` compiles those inputs into `inventory/inventory.json` and caches facts
  under `.ansible_cache/` for reproducible runs.

### Stage 1 – PXE Bootstrap

1. Controller runs `make pxe` (part of `make controller`).
2. dnsmasq hands out addresses and chainloads iPXE.
3. iPXE script fetches kernel/initrd + Kickstart from Apache.
4. Kickstart:
   - Sets timezone, networking (DHCP), root + local user passwords.
   - Enables SSH, SELinux enforcing.
   - Downloads Rocky packages from mirrored repos.

### Stage 2 – Baseline OS + Common Role

- After Kickstart, newly installed nodes reboot.
- `make controller|compute` runs `common` first on every host:
  - Creates `ansible` user + SSH key.
  - Installs baseline packages (python3, git, tmux, diagnostics tools).
  - Applies sysctl + ulimit settings so subsequent roles inherit sane defaults.

### Stage 3 – Role-Specific Configuration

- **Controller**: `pxe`, `controller`, `scheduler`.
- **Compute**: `scheduler` (slurmd + munge).

Each role is idempotent: re-running the play is safe and expected after any firmware
or OS change.

### Stage 4 – Validation + Telemetry

- `make validate` installs Pavilion, copies suites, and runs Slurm-backed smoke tests.
- Future scope: feed job metrics into Prometheus and visualize via Grafana. Hooks are
  laid out under `roles/validation/` for easy extension.

### Stage 5 – Benchmark Orchestration (manual)

- After validation passes, schedule HPC workloads through Slurm.
- Document anomalies in `docs/THINKING.md` for future reference.
