"""
Discover package directories (those containing pyproject.toml) under a root and print their
relative paths one per line, sorted lexicographically.

In this repository, package directories include Singer tap (extractor) and target (loader) plugin
directories (e.g. under taps/ and loaders/). Plugin names and paths are unchanged; this script
only lists directories that contain a pyproject.toml.

Usage: python scripts/list_packages.py [ROOT]
  ROOT: Optional directory to search; default is the current working directory. Resolved to
  absolute path before walking.

Output: One relative path per line (no header, no trailing blank line). Paths are sorted
lexicographically. Exits 0 on success; non-zero if ROOT is missing, not a directory, or invalid.

Excluded directory names (and their descendants are not walked): .git, .venv, _archive, node_modules.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Directory names to skip when walking (do not descend into these or their children).
EXCLUDED_DIRS = {".git", ".venv", "_archive", "node_modules"}


def main(root: Path | None = None) -> int:
    """
    Discover package dirs (e.g. tap/target plugin dirs with pyproject.toml) under root and print
    their relative paths, one per line, sorted.

    Args:
        root: Directory to search; if None, uses current working directory.

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

    packages: list[Path] = []
    for dirpath, dirnames, _ in os.walk(root, topdown=True):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
        p = Path(dirpath)
        if (p / "pyproject.toml").exists():
            packages.append(p.relative_to(root))

    packages.sort()
    for rel in packages:
        print(rel.as_posix())
    return 0


if __name__ == "__main__":
    root_arg: Path | None = None
    if len(sys.argv) >= 2:
        root_arg = Path(sys.argv[1])
    sys.exit(main(root_arg))
