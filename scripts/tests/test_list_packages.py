"""
Black-box tests for scripts/list_packages.py.

Run from repo root with a venv that has pytest: `pytest scripts/tests`

In this repo, packages are directories with pyproject.toml and include tap (extractor) and target
(loader) plugin directories. Path literals (e.g. taps/plugin) denote directory layout only.

Contract: script is invoked as `python scripts/list_packages.py [ROOT]` or with `--json`.
Stdout: one relative path per line (default), or JSON {"path": [...]} with --json. Sorted. No header.
Excluded trees: .git, .venv, _archive, node_modules. Exit 0 on success.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


# Repo root: parent of scripts/ (parent of tests/ is scripts/, parent of that is root).
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_SCRIPT = _REPO_ROOT / "scripts" / "list_packages.py"


def run_list_packages(root: Path) -> tuple[str, int]:
    """
    Run list_packages.py with the given root directory.

    Returns (stdout text, returncode). Uses repo root as cwd so script path resolves.
    """
    result = subprocess.run(
        [sys.executable, str(_SCRIPT), str(root.resolve())],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
    )
    return (result.stdout, result.returncode)


def run_list_packages_nonexistent(root: Path) -> tuple[str, int]:
    """Run list_packages.py with a non-existent path. Returns (stderr or stdout, returncode)."""
    result = subprocess.run(
        [sys.executable, str(_SCRIPT), str(root)],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
    )
    out = result.stdout or result.stderr or ""
    return (out, result.returncode)


def run_list_packages_json(root: Path) -> tuple[str, int]:
    """Run list_packages.py with --json and the given root. Returns (stdout, returncode)."""
    result = subprocess.run(
        [sys.executable, str(_SCRIPT), "--json", str(root.resolve())],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
    )
    return (result.stdout or "", result.returncode)


# --- Test cases (black box: assert only stdout and exit code) ---


def test_no_packages_empty_stdout_exit_zero(tmp_path: Path) -> None:
    """
    No packages: temp dir with no pyproject.toml. Expect empty stdout and exit 0.

    Ensures CI does not fail when the repo (or a subtree) has no packages.
    """
    stdout, returncode = run_list_packages(tmp_path)
    assert returncode == 0, f"Expected exit 0, got {returncode}. stderr/out: {stdout}"
    assert stdout.strip() == "", f"Expected empty stdout, got: {repr(stdout)}"


def test_one_package_single_line_exit_zero(tmp_path: Path) -> None:
    """
    One package: temp dir with foo/pyproject.toml. Expect one line 'foo' and exit 0.

    Ensures a single package is reported as one path relative to root.
    """
    (tmp_path / "foo").mkdir()
    (tmp_path / "foo" / "pyproject.toml").write_text("")
    stdout, returncode = run_list_packages(tmp_path)
    assert returncode == 0
    lines = [s for s in stdout.strip().splitlines() if s]
    assert lines == ["foo"], f"Expected ['foo'], got {lines}"


def test_multiple_packages_sorted_exit_zero(tmp_path: Path) -> None:
    """
    Multiple packages: a/pyproject.toml and b/pyproject.toml. Expect two lines, sorted (a, b), exit 0.

    Ensures stable, parseable output for CI matrix.
    """
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    (tmp_path / "a" / "pyproject.toml").write_text("")
    (tmp_path / "b" / "pyproject.toml").write_text("")
    stdout, returncode = run_list_packages(tmp_path)
    assert returncode == 0
    lines = [s for s in stdout.strip().splitlines() if s]
    assert lines == ["a", "b"], f"Expected sorted ['a','b'], got {lines}"


def test_excluded_dirs_archive_not_listed(tmp_path: Path) -> None:
    """
    Excluded dirs: _archive/x/pyproject.toml and ok/pyproject.toml. Expect only 'ok', exit 0.

    Ensures _archive (and other excluded trees) are not reported as packages.
    """
    (tmp_path / "_archive" / "x").mkdir(parents=True)
    (tmp_path / "ok").mkdir()
    (tmp_path / "_archive" / "x" / "pyproject.toml").write_text("")
    (tmp_path / "ok" / "pyproject.toml").write_text("")
    stdout, returncode = run_list_packages(tmp_path)
    assert returncode == 0
    lines = [s for s in stdout.strip().splitlines() if s]
    assert lines == ["ok"], f"Expected ['ok'] (exclude _archive), got {lines}"


def test_nested_package_relative_path_exit_zero(tmp_path: Path) -> None:
    """
    Nested package: taps/plugin/pyproject.toml. Expect one line 'taps/plugin' (relative to root), exit 0.

    Ensures nested package paths are reported as a single relative path.
    """
    (tmp_path / "taps" / "plugin").mkdir(parents=True)
    (tmp_path / "taps" / "plugin" / "pyproject.toml").write_text("")
    stdout, returncode = run_list_packages(tmp_path)
    assert returncode == 0
    lines = [s for s in stdout.strip().splitlines() if s]
    assert lines == ["taps/plugin"], f"Expected ['taps/plugin'], got {lines}"


def test_invalid_root_nonzero_exit(tmp_path: Path) -> None:
    """
    Invalid root: non-existent path. Expect non-zero exit.

    Documented behaviour: script must not exit 0 when root is invalid so CI can detect misconfiguration.
    """
    nonexistent = tmp_path / "does_not_exist_12345"
    assert not nonexistent.exists()
    _out, returncode = run_list_packages_nonexistent(nonexistent)
    assert returncode != 0, "Expected non-zero exit for non-existent root path"


def test_json_output_valid_matrix(tmp_path: Path) -> None:
    """
    --json: multiple packages. Expect valid JSON with "path" array, sorted, exit 0.

    Ensures CI can use script output directly with fromJson (no jq); matrix shape is {"path": [...]}.
    """
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    (tmp_path / "a" / "pyproject.toml").write_text("")
    (tmp_path / "b" / "pyproject.toml").write_text("")
    stdout, returncode = run_list_packages_json(tmp_path)
    assert returncode == 0, f"Expected exit 0, got {returncode}. stdout: {stdout!r}"
    data = json.loads(stdout)
    assert "path" in data, f"Expected 'path' key in JSON, got {list(data)}"
    assert data["path"] == ["a", "b"], f"Expected sorted ['a','b'], got {data['path']}"


def test_json_output_empty_path_array(tmp_path: Path) -> None:
    """
    --json: no packages. Expect JSON {"path": []}, exit 0.

    Ensures empty discovery produces valid matrix JSON for CI (fromJson does not fail).
    """
    stdout, returncode = run_list_packages_json(tmp_path)
    assert returncode == 0
    data = json.loads(stdout)
    assert data == {"path": []}, f'Expected {{"path": []}}, got {data}'


def test_json_output_ends_with_newline_for_heredoc_compatibility(
    tmp_path: Path,
) -> None:
    """
    --json: stdout must end with a newline so heredoc consumers (e.g. GITHUB_OUTPUT) get a valid delimiter line.

    GitHub Actions multiline output requires the delimiter on its own line; without a trailing newline the value and
    delimiter merge into one line and the runner reports "Matching delimiter not found".
    """
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "pyproject.toml").write_text("")
    stdout, returncode = run_list_packages_json(tmp_path)
    assert returncode == 0, f"Expected exit 0, got {returncode}. stdout: {stdout!r}"
    assert stdout.endswith("\n"), (
        f"JSON output must end with newline for GITHUB_OUTPUT heredoc; got {repr(stdout[-20:] if len(stdout) >= 20 else stdout)}"
    )
    data = json.loads(stdout.strip())
    assert "path" in data, f"Expected 'path' key in JSON, got {list(data)}"
