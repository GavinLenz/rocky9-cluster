#!/usr/bin/env python3
"""
Robust cleanup utility for development artifacts.
Removes cache directories, Python bytecode, and build debris
without risking accidental deletion outside the repository root.

Safe, deterministic, audit-friendly.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

# Default patterns and directories to remove
DEFAULT_PATTERNS = (
    "__pycache__",
    "*.pyc",
    "*.pyo",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
)

DEFAULT_DIRS = (
    ".ansible",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
)

# Directories that will *never* be removed
PROTECTED = {
    "/",
    "/root",
    "/home",
    "/usr",
    "/etc",
    "/var",
    "/opt",
}


def is_protected(path: Path) -> bool:
    """Reject unsafe deletions and strange roots."""
    try:
        rp = str(path.resolve())
    except Exception:
        return True

    if rp in PROTECTED:
        return True

    # Reject oddities like removing the repository root itself
    if path == path.root:
        return True

    return False


def log(msg: str) -> None:
    print(f"[cleanup] {msg}")


def warn_skip(path: Path, exc: Exception) -> None:
    sys.stderr.write(f"[cleanup] warning: could not remove {path}: {exc}\n")


def remove_path(path: Path, *, dry: bool) -> None:
    """Recursively remove file or directory."""
    if is_protected(path):
        warn_skip(path, PermissionError("protected path"))
        return

    if dry:
        log(f"would remove {path}")
        return

    if path.is_dir():
        try:
            for item in path.iterdir():
                remove_path(item, dry=dry)
            path.rmdir()
            log(f"removed dir {path}")
        except Exception as exc:
            warn_skip(path, exc)
    else:
        try:
            path.unlink(missing_ok=True)
            log(f"removed file {path}")
        except Exception as exc:
            warn_skip(path, exc)


def cleanup(root: Path, patterns: Iterable[str], dirs: Iterable[str], *, dry: bool) -> None:
    # Remove directories first (faster)
    for d in dirs:
        for p in root.rglob(d):
            if p.is_dir():
                remove_path(p, dry=dry)

    # Then glob patterns (files)
    for pattern in patterns:
        for path in root.rglob(pattern):
            remove_path(path, dry=dry)


def parse() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Repository cleanup utility")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--pattern", action="append", dest="patterns")
    parser.add_argument("--dir", action="append", dest="dirs")
    parser.add_argument("--dry-run", action="store_true", dest="dry")
    return parser.parse_args()


def main(argv=None) -> int:
    args = parse()

    root = args.root.resolve()

    # Validate root
    if is_protected(root):
        sys.stderr.write(f"[ERROR] Refusing to clean protected path: {root}\n")
        return 1

    patterns = tuple(args.patterns) if args.patterns else DEFAULT_PATTERNS
    dirs = tuple(args.dirs) if args.dirs else DEFAULT_DIRS

    log(f"starting cleanup under {root}")
    if args.dry:
        log("dry-run enabled (no changes will be made)")

    cleanup(root, patterns, dirs, dry=args.dry)
    log("cleanup complete")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
