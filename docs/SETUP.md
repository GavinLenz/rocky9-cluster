# Development and Controller Setup Guide

This document explains how to prepare a development machine and how to bootstrap
the controller node that drives the provisioning workflow.

The cluster itself is always provisioned through Ansible. No development tools
should be installed directly on the controller unless explicitly noted.

---

## 1. Development Environment

The development environment is the workstation used to edit the repository,
run Ansible, and execute validation tooling.

### 1.1 Required packages
> This is what I use for my Rocky 9.6 WSL 
```bash
sudo dnf -y install python3 python3-devel make curl wget tar gzip unzip vim tmux jq rsync findutils tree
```
> Some optional packages that are nice to have
```bash
sudo dnf -y install findutils tree
```

### 1.2 Required software
- Python 3.9 or later
- Git
- A supported terminal (WSL2, native Linux, or macOS)
- SSH client

### 1.3 Install Python dependencies
Development dependencies are isolated in `requirements/dev.txt`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements/dev.txt
```

### 1.4 Install required Ansible Galaxy collections

```bash
ansible-galaxy collection install -r requirements/requirements.yml
```

### 1.5 Pre-commit hooks (optional but recommended)

If pre-commit is installed:

```bash
pre-commit install
```

This enforces formatting and linting before each commit.

---

## 2. Controller Node Setup

The controller node is the head of the cluster.
It must remain minimal and should **not** install development tooling.

### 2.1 Required software

The controller requires:

* Python 3.9 (system `python3` on Rocky 9)
* Minimal runtime libraries for the dynamic inventory and PXE subsystem

### 2.2 Install Python runtime dependencies

On the controller:

```bash
python3 -m venv ~/.venv
source ~/.venv/bin/activate
pip install --upgrade pip
pip install -r requirements/controller.txt
```

### 2.3 Install Ansible collections

Same as the development machine:

```bash
ansible-galaxy collection install -r requirements/requirements.yml
```

### 2.4 Repository secrets

Credentials used by Kickstart and PXE provisioning are loaded from `.env`.
Generate the password hashes with the helper script:

```bash
./scripts/generate_hashes.py
```

Copy the output into `.env`.
The file should contain:

```
CONTROLLER_BECOME_PASSWORD="<sudo password for controller user>"
PXE_ROOT_PASSWORD_HASH="<kickstart root hash>"
PXE_LOCAL_USER_PASSWORD_HASH="<kickstart local user hash (optional, defaults to root hash)>"
```

---

## 3. Running Ansible

Playbooks are wrapped in the Makefile so day-to-day runs stay reproducible:

```bash
make inv          # regenerate inventory/inventory.json from config/*.yml
make controller   # apply controller_common → controller → pxe on the controller
make compute      # seed compute nodes with compute_common (SSH + Python)
make validate     # install Pavilion locally and run controller smoke tests
```
To avoid storing the sudo password in `.env`, append `ASK_BECOME_PASS=1`
to any target (for example `ASK_BECOME_PASS=1 make controller`) and Ansible
will prompt for the password interactively on the first run.

All targets call `inventory/generator.py` directly; no static YAML inventory exists.

---

## 4. Deployment Pipeline

1. **Stage 0 – Config Authoring**
   - Edit `config/*.yml` to describe nodes, network, PXE images, and role stacks.
   - Populate `.env` with PXE password hashes.
   - Run `make inv` to compile `inventory/inventory.json` and refresh the fact cache.
2. **Stage 1 – PXE Bootstrap (part of `make controller`)**
   - Controller enables dnsmasq, Apache, and TFTP.
   - iPXE pulls kernel/initrd + `ks.cfg` from `http://10.0.0.1/os`.
3. **Stage 2 – Controller Configuration**
   - `make controller` enforces `controller_common → controller → pxe`.
   - Ensures Python tooling, PXE assets, firewall rules, and validation hooks are in place.
4. **Stage 3 – Compute Bootstrap**
   - PXE-installed nodes reboot, then `make compute` runs `compute_common` to create the `ansible` user, install Python, and authorize controller SSH.
5. **Stage 4 – Validation**
   - `make validate` installs Pavilion under `/opt/pavilion2`, copies raw-scheduler suites, and runs controller-local smoke tests for PXE, HTTP, and firewall.
6. **Stage 5 – Workloads (manual)**
   - Once validation passes, layer schedulers or benchmarking stacks as needed. Today this step is manual and intentionally outside Ansible.

---

## 5. Directory Summary

```
requirements/
  controller.txt      # runtime only (controller node)
  dev.txt             # development tooling (workstation)
  requirements.yml    # galaxy collections (shared)

scripts/
  dev_venv.sh         # privileged helper for creating the dev venv
  generate_hashes.py  # password hashing helper

docs/
  ARCHITECTURE.md     # wiring contract and topology
  DEV.md              # developer workflow tips
  HOSTS.md            # role responsibilities
  RESOURCES.md        # external reference links
  SETUP.md            # this document
```

This structure keeps concerns separated and avoids polluting runtime nodes
with development tools.

## Dependency Model

This repository uses a strict separation of dependency surfaces. The cluster
controller, compute nodes, and development workstation operate in different
execution contexts and therefore require different dependency sets.

### 1. Development Dependencies

The workstation (WSL2, Linux, or macOS) installs:

```
requirements/dev.txt
```

This includes formatting, linting, testing, and Ansible CLI tooling.
These dependencies must **never** be installed on controller or compute nodes.

### 2. Controller Runtime Dependencies

The controller node uses:

```
requirements/controller.txt
```

This contains only the libraries required to run the dynamic inventory,
PXE generation code, and provisioning logic.
The controller runs a minimal Python footprint and should not carry any
development tooling.

### 3. Ansible Collections

Both the development machine and controller install:

```
requirements/requirements.yml
```

This file defines Galaxy collections required for Ansible execution, such as:

* `ansible.posix`
* `community.general`

Collections are installed with:

```bash
ansible-galaxy collection install -r requirements/requirements.yml
```

### 4. Why this model exists

* Development machines carry analysis, linting, testing, and orchestration (of repo and controller configuration).
* Controller nodes carry the smallest possible runtime footprint.
* Compute nodes remain free of all off-path tooling.

This principle reduces security exposure, prevents configuration drift, and
keeps operational nodes deterministic.
