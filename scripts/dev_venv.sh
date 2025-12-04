#!/bin/bash
# run on dev machine (not a cluster node)

set -euo pipefail

log() { printf "[venv] %s\n" "$*" >&2; }

python_is_39() {
    local bin="$1"

    if ! command -v "$bin" >/dev/null 2>&1; then
        return 1
    fi

    # Extract major/minor reliably
    local major minor
    major="$("$bin" -c 'import sys; print(sys.version_info[0])')"
    minor="$("$bin" -c 'import sys; print(sys.version_info[1])')"

    (( major == 3 && minor == 9 ))
}

ensure_python39_installed() {
    if python_is_39 python3; then
        log "Python 3.9 already installed."
        return 0
    fi

    log "Installing Python 3.9..."
    dnf -y install python3 python3-devel openmpi openmpi-devel|| {
        log "Failed to install python3"
        exit 1
    }

    if ! python_is_39 python3; then
        log "Python 3 installation failed."
        exit 1
    fi

    log "Python 3 installation confirmed."
}

create_venv() {
    local repo_root="$1"
    local venv_path="${repo_root}/.venv"

    local owner user_home
    owner="$(stat -c '%U' "$repo_root")"

    log "Creating venv at: ${venv_path}"
    log "Creating as owner: ${owner}"

    runuser -u "${owner}" -- bash -lc "
        python3 -m venv '${venv_path}'
        '${venv_path}/bin/python' -m pip install --upgrade pip setuptools wheel
        '${venv_path}/bin/pip' install -r '${repo_root}/requirements/dev.txt'
        '${venv_path}/bin/ansible-galaxy' collection install ansible.posix community.general ansible.netcommon
        '${venv_path}/bin/pre-commit' install
        "
    log "venv created and packages installed."
}

# ENTRYPOINT
if [[ "$(id -u)" -ne 0 ]]; then
    log "Run with sudo/root."
    exit 1
fi

ensure_python39_installed

# Resolve repo root: script resides under repo/scripts/, so go up one level.
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
log "Repo root resolved as: ${REPO_ROOT}"

create_venv "${REPO_ROOT}"

log "===================================================================="
log "Virtualenv ready:"
log "  source ${REPO_ROOT}/.venv/bin/activate"
log "===================================================================="
