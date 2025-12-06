#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

import yaml
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "config"
# Load secrets from .env (if present)
ENV = dotenv_values(ROOT / ".env")


CONFIG_FILES = {
    "images": CONFIG_DIR / "images.yml",
    "metadata": CONFIG_DIR / "metadata.yml",
    "net": CONFIG_DIR / "net.yml",
    "nodes": CONFIG_DIR / "nodes.yml",
    "pxe": CONFIG_DIR / "pxe.yml",
    "roles": CONFIG_DIR / "roles.yml",
}


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        return data if isinstance(data, dict) else {}


def build_inventory() -> tuple[dict[str, Any], dict[str, Any]]:
    """Build minimal static inventory from config/.

    Returns the inventory structure and a flattened hostvars mapping so we can
    still service `--host` lookups when invoked as a dynamic inventory script.
    """
    cfg = {name: load_yaml(path) for name, path in CONFIG_FILES.items()}

    # Names for inventory
    nodes = cfg.get("nodes", {}).get("nodes", {})
    roles = cfg.get("roles", {}).get("roles", {})
    net = cfg.get("net", {}).get("network", {})
    pxe = cfg.get("pxe", {}).get("pxe", {})
    metadata = cfg.get("metadata", {}).get("metadata", {})

    # Load secret credentials from .env
    controller_become_password = ENV.get("CONTROLLER_BECOME_PASSWORD")
    root_hash = ENV.get("PXE_ROOT_PASSWORD_HASH")
    local_hash = ENV.get("PXE_LOCAL_USER_PASSWORD_HASH")

    # Assignment
    controller_nodes = {n: c for n, c in nodes.items() if c.get("role") == "controller"}
    compute_nodes = {n: c for n, c in nodes.items() if c.get("role") == "compute"}

    if not controller_nodes and nodes:
        first = next(iter(nodes))
        controller_nodes[first] = nodes[first]
        compute_nodes.pop(first, None)

    hostvars: dict[str, Any] = {}

    # Controller vars
    for name, node in controller_nodes.items():
        conn = node.get("connection", {})
        hostvars[name] = {
            "ansible_host": conn.get("ansible_host", node.get("ip", name)),
            "ansible_connection": conn.get("ansible_connection", "local"),
            "ansible_python_interpreter": conn.get(
                "ansible_python_interpreter", "/usr/bin/python3"
            ),
            "cluster_role": "controller",
            "pxe_iface": net.get("pxe_iface", ""),
            "pxe_server_ip": net.get("server_ip", ""),
            "pxe_install_drive": pxe.get("install", {}).get("drive", ""),
            "pxe_default_target": pxe.get("ipxe", {}).get("default_target", ""),
            "pxe_ipxe_menu_items": pxe.get("ipxe", {}).get("menu", []),
        }
        # Allow arbitrary host-level vars from config/nodes.yml
        hostvars[name].update(node.get("variables", {}))
        if controller_become_password and "ansible_become_password" not in hostvars[name]:
            hostvars[name]["ansible_become_password"] = controller_become_password

    # Compute vars
    for name, node in compute_nodes.items():
        conn = node.get("connection", {})
        hostvars[name] = {
            "ansible_host": conn.get("ansible_host", node.get("ip", name)),
            "ansible_connection": conn.get("ansible_connection", "ssh"),
            "ansible_user": conn.get("ansible_user", "ansible"),
            "ansible_python_interpreter": conn.get(
                "ansible_python_interpreter", "/usr/bin/python3"
            ),
            "cluster_role": "compute",
            "nic_mac": node.get("mac", []),
        }
        hostvars[name].update(node.get("variables", {}))

    # Global vars
    all_vars = {
        "cluster_name": metadata.get("name", cfg.get("metadata", {}).get("name", "")),
        "cluster_description": metadata.get(
            "description", cfg.get("metadata", {}).get("description", "")
        ),
        "cluster_repo_root": str(ROOT),
        "cluster_config_root": str(CONFIG_DIR),
        "cluster_roles": roles,
        "network_config": net,
        "pxe_config": pxe,
        "images": cfg.get("images", {}).get("images", {}),
        "pxe_runtime_credentials": {
            "username": pxe.get("username", "ansible"),
            # Injected from .env
            "root_password_hash": root_hash,
            "local_user_password_hash": local_hash or root_hash,
        },
    }

    # Embed host-specific vars directly under each host entry so Ansible's YAML
    # inventory plugin sees them without relying on `_meta.hostvars`.
    controller_hosts = {name: hostvars[name] for name in controller_nodes}
    compute_hosts = {name: hostvars[name] for name in compute_nodes}

    inventory = {
        "all": {
            "cluster_metadata": metadata,
            "children": {
                "controller": {"hosts": controller_hosts},
                "compute": {"hosts": compute_hosts},
            },
            "vars": all_vars,
        }
    }

    return inventory, hostvars


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Cluster dynamic inventory")
    parser.add_argument("--host", type=str)
    parser.add_argument("--list", action="store_true")
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    inventory, hostvars = build_inventory()

    output_path = Path(__file__).resolve().parent / "inventory.json"

    if args.host:
        hv = hostvars.get(args.host, {})
        print(json.dumps(hv, indent=2))
    else:
        print(json.dumps(inventory, indent=2))

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(inventory, f, indent=2, ensure_ascii=False)
        f.write("\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
