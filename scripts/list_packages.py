"""
Discover package directories (those containing pyproject.toml) under a root and print their
relative paths one per line, sorted lexicographically.

In this repository, package directories include Singer tap (extractor) and target (loader) plugin
directories (e.g. under taps/ and loaders/). Plugin names and paths are unchanged; this script
only lists directories that contain a pyproject.toml.

Usage: python scripts/list_packages.py [ROOT] [--json]
  ROOT: Optional directory to search; default is the current working directory. Resolved to
  absolute path before walking.
  --json: Output a single JSON object {"path": [...]} for use as a GitHub Actions matrix.
          Without --json, outputs one relative path per line.

Output: One relative path per line (no header, no trailing blank line), or JSON when --json
(one line plus trailing newline for heredoc/GITHUB_OUTPUT compatibility). Paths sorted
lexicographically. Exits 0 on success; non-zero if ROOT is missing, not a directory, or invalid.

Excluded directory names (and their descendants are not walked): .git, .venv, _archive, node_modules.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Directory names to skip when walking (do not descend into these or their children).
EXCLUDED_DIRS = {".git", ".venv", "_archive", "node_modules"}


def discover(root: Path) -> list[Path]:
    """
    Discover package dirs (e.g. tap/target plugin dirs with pyproject.toml) under root.

    Args:
        root: Directory to search (must exist and be a directory).

    Returns:
        Sorted list of paths relative to root.
    """
    packages: list[Path] = []
    for dirpath, dirnames, _ in os.walk(root, topdown=True):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
        p = Path(dirpath)
        if (p / "pyproject.toml").exists():
            packages.append(p.relative_to(root))
    packages.sort()
    return packages


def main(root: Path | None = None, json_output: bool = False) -> int:
    """
    Run discovery and print paths (one per line or JSON).

    Args:
        root: Directory to search; if None, uses current working directory.
        json_output: If True, print a single JSON object {"path": [...]}; else one path per line.

    Returns:
        0 on success; non-zero if root does not exist or is not a directory.
    """
    if root is None:
        root = Path.cwd()
    root = root.resolve()
    if not root.exists():
        return 1
    if not root.is_dir():
        return 1

    packages = discover(root)
    if json_output:
        print(json.dumps({"path": [p.as_posix() for p in packages]}))
    else:
        for rel in packages:
            print(rel.as_posix())
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="List package directories (with pyproject.toml)."
    )
    parser.add_argument(
        "root",
        nargs="?",
        default=None,
        type=Path,
        help="Root directory to search; default is current working directory.",
    )
    parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help='Output JSON object {"path": [...]} for GitHub Actions matrix.',
    )
    args = parser.parse_args()
    sys.exit(main(root=args.root, json_output=args.json_output))
