# Rocky 9 Micro-Cluster Automation

A minimal reproducible workflow for bootstrapping a Rocky 9 controller and a small fleet
of PXE-booted compute nodes. The controller owns PXE (dnsmasq, Apache, TFTP) and local
validation via Pavilion; compute nodes stay intentionally bare so new schedulers or
application stacks can be layered later. Inventory, playbooks, and validation live in
this repo so deployments stay deterministic.

## Overview

- **Topology** – One controller (“head”) with static IP `10.0.0.1`, three compute nodes
  on the same `/24` LAN, Cat6e cabling into a 2.5 GbE switch.
- **Provisioning flow** – Kickstart via iPXE → Ansible roles:
  - `controller_common → controller → pxe` on the controller
  - `compute_common` on compute nodes (creates automation user + Python)
- **Validation** – Pavilion installs under `/opt/pavilion2` and runs raw-scheduler smoke
  tests on the controller (PXE services, HTTP, firewall, repo mirrors) before Slurm or
  other schedulers are introduced.

See `docs/ARCHITECTURE.md` for the full wiring contract and `docs/HOSTS.md` for per-role
responsibilities.

## Prerequisites

- Rocky 9.6 (bare metal or WSL) development machine with:
  - `python3`, `python3-devel`, `git`, `make`, `gcc`, `rsync`, `jq`, `tmux`, etc.
  - Virtualenv for repo tooling (`python3 -m venv .venv && pip install -r requirements/dev.txt`)
- `.env` populated with PXE password hashes (`scripts/generate_hashes.py` helps)
- Controller running Rocky 9 with system Python 3.9 and basic network connectivity
- Compute nodes configured to PXE-boot first; their MACs listed in `config/nodes.yml`

## Quick Start

1. Clone the repo and install dev deps:
   ```bash
   git clone <repo>
   cd rocky9-cluster
   python3 -m venv .venv && source .venv/bin/activate
   pip install --upgrade pip && pip install -r requirements/dev.txt
   ```
2. Populate `.env` with password hashes:
   ```bash
   ./scripts/generate_hashes.py   # copy the output into .env (root + local user)
   ```
3. Describe the cluster in `config/*.yml` (nodes, network, PXE image, role stack).
4. Generate inventory and apply roles via the Makefile:
   ```bash
   make inv          # config -> inventory/inventory.json
   make controller   # controller_common → controller → pxe on head node
   make compute      # compute_common on each compute host (once they netboot)
   make validate     # optional Pavilion install + controller smoke tests
   ```

Every target reruns the dynamic inventory; no static inventory file is committed.

## Repository Layout

```
config/         # Nodes, network, PXE, role stacks
docs/           # Architecture, host guides, setup flow, Pavilion notes
inventory/      # Dynamic generator + cached JSON
playbooks/      # controller.yml, compute.yml, pxe.yml, validation.yml
roles/          # controller_common, controller, compute_common, pxe, validation
scripts/        # hash generator, cleanup helpers
requirements/   # dev / controller pip requirements + galaxy requirements.yml
```

Key documentation:

- `docs/SETUP.md` – workstation + controller bootstrap flow (hardware/software prep)
- `docs/ARCHITECTURE.md` – topology, control/validation flow, state surfaces
- `docs/HOSTS.md` – controller vs compute responsibilities and troubleshooting
- `docs/_PAV.md` – Pavilion raw-scheduler plan and suggested tests

## Make Targets

| Target      | Description                                              |
| ----------- | -------------------------------------------------------- |
| `make inv`  | Regenerate `inventory/inventory.json` from `config/*.yml` |
| `make controller` | Apply controller roles (PXE, static IP, validation prep) |
| `make compute`    | Seed compute nodes with SSH user + Python          |
| `make validate`   | Install Pavilion and run controller smoke tests    |
| `make lint`       | Run Black, Ruff, Yamllint, ansible-lint            |
| `make clean`      | Remove caches, virtualenv, and temp files          |

Additional playbooks (`make pxe`, `scheduler`, `slurm`) are placeholders for future work.

## Validation

The validation role installs Pavilion from LANL’s GitHub repo into `/opt/pavilion2`,
copies host/suite definitions, and runs raw scheduler suites entirely on the controller.
The default suite (`controller_smoke`) checks:

- dnsmasq/httpd service health
- firewall allowances for PXE services
- HTTP reachability of PXE assets
- Presence of mirrored repos under `/var/www/html/repos`

Use `make validate` after significant PXE or controller changes to ensure local services
are healthy before onboarding compute nodes.

## Contributing & Support

- Keep changes idempotent and update `docs/` to match behavioral shifts.
- Use `make lint` before sending patches.
- Sensitive values (`.env`, inventory artifacts) stay out of git; `.gitignore` covers them.

Questions or feature ideas? Document them under `docs/THINKING.md` or raise an issue with
reproduction steps and inventory snippets (redacted as needed).
