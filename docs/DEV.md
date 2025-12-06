## DEV.md

The development environment is configured for repeatable Ansible work.

### 1. Baseline Environment

- **OS**: Bare-metal Rocky 9.6 or WSL2 on Windows with Rocky image.
- **Python**: System `python3` (Rocky 9 defaults to 3.9) with `python3-devel` for venv builds.
- **Packages**: `dnf install git make gcc python3 python3-devel openssl jq rsync
  tar gzip unzip tmux vim`.
- **Secrets**: `.env` stays outside git. Create `.env`, then run
  `scripts/generate_hashes.py`, paste hashes inside `.env`, and `chmod 600 .env`.

### 2. Workflow Loop

1. `git pull --rebase` to stay current.
2. `make dev-venv` (runs the hardening script with sudo) the first time on a
   new machine.
3. `source .venv/bin/activate` and run `pip install -r requirements/dev.txt` whenever dependencies change.
4. Edit configs, roles, or templates. Keep commits intentional and documented.
5. `make lint`  blocks merges if the style or Ansible best practices are not being met.
6. `make inv` + the relevant playbook target(s).
7. `make validate` whenever major surfaces move.

### 3. Quality Gates

- **Lint**: Black, Ruff, Yamllint, and ansible-lint must all pass.
- **Inventory**: `make inv-show | jq '.controller.hosts'` should always return the
  expected nodes. If not, fix `config/*.yml` before running playbooks.
- **Secrets**: Git should never show `.env` or password hashes. Verify `.gitignore`
  is doing its job.

### 4. Local Testing Tricks

- Use `ANSIBLE_STDOUT_CALLBACK=debug` when troubleshooting tasks.
- `ANSIBLE_NOCOWS=1` stays set in the Makefile to remove noise.
- `make inv-clean` to avoid stale caches.

### 5. Review Discipline

- Keep the relevant documentation (README, `docs/` guides, inventory comments) in
  sync with behavior changes so the operational context never lags behind the code.
- Favor small commits that map 1:1 with conceptual changes.
