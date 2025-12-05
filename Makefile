.DEFAULT_GOAL := help
SHELL := /bin/bash

PYTHON ?= $(if $(VIRTUAL_ENV),$(VIRTUAL_ENV)/bin/python3,$(if $(wildcard .venv/bin/python3),./.venv/bin/python3,python3))
PIP := $(PYTHON) -m pip
ANSIBLE_CMD ?= ANSIBLE_NOCOWS=1 ansible-playbook
ANSIBLE_ARGS ?= -vv
ANSIBLE_PLAYBOOK := $(ANSIBLE_CMD) $(ANSIBLE_ARGS)
CACHE_DIR := .ansible_cache

RUFF := $(PYTHON) -m ruff
BLACK := $(PYTHON) -m black
YAMLLINT := $(PYTHON) -m yamllint
ANSIBLE_LINT := $(PYTHON) -m ansiblelint

INV_SCRIPT := inventory/generator.py
INV_JSON   := inventory/inventory.json
CONFIG_YAML := $(wildcard config/*.yml)

PLAYBOOK_DIR := playbooks
PLAYBOOK_CONTROLLER := $(PLAYBOOK_DIR)/controller.yml
PLAYBOOK_COMPUTE := $(PLAYBOOK_DIR)/compute.yml
PLAYBOOK_PXE := $(PLAYBOOK_DIR)/pxe.yml
PLAYBOOK_VALIDATION := $(PLAYBOOK_DIR)/validation.yml

.PHONY: help hashes inv inv-show inv-clean dev-venv venv-check lint format clean controller compute pxe scheduler validate site

help: ## Show available targets grouped by phase
	@echo "== Development =="
	@awk -F':.*## ' '/^[a-zA-Z0-9_.-]+:.*##/ && /venv|lint|format|check|test|clean/ { printf "  %-22s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ""
	@echo "== Inventory & Introspection =="
	@awk -F':.*## ' '/^[a-zA-Z0-9_.-]+:.*##/ && /hashes|inv|inv-show|inv-clean/ { printf "  %-22s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ""
	@echo "== Ansible =="
	@awk -F':.*## ' '/^[a-zA-Z0-9_.-]+:.*##/ && /controller|compute|pxe|scheduler|validate|slurm/ { printf "  %-22s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

hashes: ## Generate hashes for .env
	chmod +x ./scripts/generate_hashes.py
	@$(PYTHON) ./scripts/generate_hashes.py

inv: $(INV_JSON) ## Generate and cache dynamic inventory
	@echo "[OK] Inventory cached at $(INV_JSON)"

$(INV_JSON): $(INV_SCRIPT) $(CONFIG_YAML)
	@mkdir -p $(CACHE_DIR)
	@mkdir -p $(dir $(INV_JSON))
	@echo "[BUILD] Generating inventory..."
	@$(PYTHON) $(INV_SCRIPT) --list > $(INV_JSON)
	@echo "[DONE] Inventory generation complete."

inv-show: ## Print generated inventory JSON to stdout
	@$(PYTHON) $(INV_SCRIPT) --list | jq .

inv-clean: ## Remove cached inventory and Ansible fact cache
	@rm -rf $(INV_JSON) $(CACHE_DIR)
	@echo "[CLEAN] Inventory cache removed."

dev-venv: ## Create and initialize Python virtual environment
	@chmod +x scripts/dev_venv.sh
	@sudo scripts/dev_venv.sh
	@echo "[OK] Virtual environment ready."

venv-check: ## Verify Python 3.9+ and Ansible availability
	@command -v $(PYTHON) >/dev/null 2>&1 || { echo "Python 3 not found"; exit 1; }
	@$(PYTHON) -m ansible --version >/dev/null 2>&1 || { echo "Ansible not available"; exit 1; }
	@echo "[OK] Python and Ansible detected."

lint: ## Run all linters (Python, YAML, Ansible)
	@$(BLACK) --check .
	@$(RUFF) check .
	@$(YAMLLINT) .
	@$(ANSIBLE_LINT)
	@echo "[OK] Lint checks complete."

format: ## Auto-format Python and YAML
	@$(BLACK) .
	@$(RUFF) check --fix .
	@echo "[OK] Formatting complete."

clean: ## Remove caches, venv, and temporary files
	chmod +x ./scripts/clean.py
	./scripts/clean.py

# Playbook runners (auto-generate inventory first)
controller: inv ## Run controller playbook (PXE + controller + scheduler)
	@$(ANSIBLE_PLAYBOOK) -i $(INV_JSON) $(PLAYBOOK_CONTROLLER)

compute: inv ## Run compute playbook (common + scheduler)
	@$(ANSIBLE_PLAYBOOK) -i $(INV_JSON) $(PLAYBOOK_COMPUTE)

pxe: inv ## Run PXE-only playbook
	@$(ANSIBLE_PLAYBOOK) -i $(INV_JSON) $(PLAYBOOK_PXE)

validate: inv ## Run validation playbook on controller
	@$(ANSIBLE_PLAYBOOK) -i $(INV_JSON) $(PLAYBOOK_VALIDATION)
