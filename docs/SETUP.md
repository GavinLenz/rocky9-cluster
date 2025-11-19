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
A template is provided:

```
.env.example
```

To populate a real `.env`, use the provided script:

```bash
./scripts/generate_hashes.py
```

Copy the output into `.env`.

---

## 3. Running Ansible

From the development machine:

```bash
source .venv/bin/activate
ansible-playbook -i inventory/generator.py playbooks/site.yml
```

The generator builds the inventory dynamically from `config/`.

---

## 4. Directory Summary

```
requirements/
  controller.txt      # runtime only (controller node)
  dev.txt             # development tooling (workstation)
  requirements.yml    # galaxy collections (shared)

scripts/
  generate_hashes.py  # password hashing helper
  cleanup.py          # repository cache cleaning

docs/
  SETUP.md            # this document
```

This structure keeps concerns separated and avoids polluting runtime nodes
with development tools.

```

====================================================================
README excerpt: Dependency Model  
====================================================================
Insert below an existing “Architecture” or “Design Notes” section in your README.

```

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
