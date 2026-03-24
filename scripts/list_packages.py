"""
Discover package directories (those containing pyproject.toml) under a root and print their
relative paths one per line, sorted lexicographically.

In this repository, package directories include Singer tap (extractor) and target (loader) plugin
directories (e.g. under taps/ and loaders/). Plugin names and paths are unchanged; this script
only lists directories that contain a pyproject.toml.

Usage: python scripts/list_packages.py [ROOT] [--json] [--git-before REF --git-after REF]
  ROOT: Optional directory to search; default is the current working directory. Resolved to
  absolute path before walking.
  --json: Output a single JSON object {"path": [...]} for use as a GitHub Actions matrix.
          Without --json, outputs one relative path per line.
  --git-before / --git-after: Optional pair; when both set, keep only packages whose
          project.version in pyproject.toml differs between the two git refs (via git show).
          An all-zero before ref skips filtering (GitHub branch-create push). Both must be passed
          together.

Output: One relative path per line (no header, no trailing blank line), or JSON when --json
(one line plus trailing newline for heredoc/GITHUB_OUTPUT compatibility). Paths sorted
lexicographically. Exits 0 on success; non-zero if ROOT is missing, not a directory, or invalid.

Excluded directory names (and their descendants are not walked): .git, .venv, _archive, node_modules.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path

# Directory names to skip when walking (do not descend into these or their children).
EXCLUDED_DIRS = {".git", ".venv", "_archive", "node_modules"}

# GitHub uses this SHA when `before` is unknown (e.g. branch creation); version diff is skipped.
_NULL_GIT_SHA = "0" * 40


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


def read_project_version_from_git(
    repo_root: Path, git_ref: str, package_rel: Path
) -> str | None:
    """
    Read `[project].version` from `package_rel/pyproject.toml` at `git_ref` in `repo_root`.

    Args:
        repo_root: Git working tree root (directory containing `.git`).
        git_ref: Commit or ref accepted by `git show`.
        package_rel: Package directory relative to repo root (e.g. taps/foo).

    Returns:
        Version string if the object exists and TOML parses with a string project.version;
        None if the blob is missing, git fails, or version is absent / invalid.
    """
    rel_toml = f"{package_rel.as_posix()}/pyproject.toml"
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_root), "show", f"{git_ref}:{rel_toml}"],
            capture_output=True,
            check=False,
            text=True,
        )
    except OSError:
        return None
    if proc.returncode != 0:
        return None
    try:
        data = tomllib.loads(proc.stdout)
    except tomllib.TOMLDecodeError:
        return None
    project = data.get("project")
    if not isinstance(project, dict):
        return None
    version = project.get("version")
    if not isinstance(version, str):
        return None
    return version


def packages_with_changed_versions(
    packages: list[Path],
    repo_root: Path,
    before_ref: str,
    after_ref: str,
) -> list[Path]:
    """
    Keep packages whose `project.version` differs between `before_ref` and `after_ref`.

    Args:
        packages: Relative package paths under repo_root.
        repo_root: Git repository root.
        before_ref: Older commit/ref.
        after_ref: Newer commit/ref (e.g. pushed HEAD).

    Returns:
        Sorted list of packages where versions differ, or only in one ref (new/removed metadata).
    """
    filtered: list[Path] = []
    for p in packages:
        v_before = read_project_version_from_git(repo_root, before_ref, p)
        v_after = read_project_version_from_git(repo_root, after_ref, p)
        if v_before is None and v_after is None:
            continue
        if v_before == v_after:
            continue
        filtered.append(p)
    filtered.sort()
    return filtered


def main(
    root: Path | None = None,
    json_output: bool = False,
    git_before: str | None = None,
    git_after: str | None = None,
) -> int:
    """
    Run discovery and print paths (one per line or JSON).

    Args:
        root: Directory to search; if None, uses current working directory.
        json_output: If True, print a single JSON object {"path": [...]}; else one path per line.
        git_before: When set with git_after, filter to packages with version changes (unless null SHA).
        git_after: See git_before.

    Returns:
        0 on success; non-zero if root does not exist or is not a directory.
    """
    if (git_before is None) ^ (git_after is None):
        print(
            "error: --git-before and --git-after must be passed together.",
            file=sys.stderr,
        )
        return 2

    if root is None:
        root = Path.cwd()
    root = root.resolve()
    if not root.exists():
        return 1
    if not root.is_dir():
        return 1

    packages = discover(root)
    if git_before is not None and git_after is not None:
        before_norm = git_before.strip().lower()
        if before_norm != _NULL_GIT_SHA:
            packages = packages_with_changed_versions(packages, root, git_before, git_after)
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
    parser.add_argument(
        "--git-before",
        dest="git_before",
        default=None,
        help="Git ref (e.g. github.event.before) for version diff filtering.",
    )
    parser.add_argument(
        "--git-after",
        dest="git_after",
        default=None,
        help="Git ref (e.g. github.sha) for version diff filtering.",
    )
    args = parser.parse_args()
    sys.exit(
        main(
            root=args.root,
            json_output=args.json_output,
            git_before=args.git_before,
            git_after=args.git_after,
        )
    )
