# Fix: github-output-eof-delimiter

## The request

The plugin unit tests workflow (`discover` job) failed when writing the `packages` output to `GITHUB_OUTPUT` with: "Unable to process file command 'output' successfully" and "Invalid value. Matching delimiter not found 'EOF'". The step runs `list_packages.py --json` and wraps the result in a heredoc (`packages<<EOF` … `EOF`). Expected: multiline value written correctly and the test matrix job receives valid JSON. Actual: runner never sees a line that is exactly `EOF` because the value did not end with a newline.

## Planned approach

Root cause: GitHub Actions requires the delimiter to be on its own line. The script printed JSON with `print(..., end="")`, so the next write (`echo "EOF"`) was appended to the same line as the JSON’s `}`. Chosen fix: emit a trailing newline from `list_packages.py` when outputting JSON (remove `end=""`). Two tasks: (1) add a regression test that JSON stdout ends with `\n`; (2) change the script to use default `print()` so the newline is emitted; optionally document in the script that `--json` output is one line plus newline for heredoc compatibility.

## What was implemented

- **Task 01:** In `scripts/tests/test_list_packages.py`, added `test_json_output_ends_with_newline_for_heredoc_compatibility`: given a root with at least one package, run `list_packages.py --json`, assert exit 0, `stdout.endswith("\n")`, and `json.loads(stdout.strip())` is valid with key `"path"`. Ensures the contract is enforced and the test failed before the fix.
- **Task 02:** In `scripts/list_packages.py`, replaced `print(json.dumps(...), end="")` with `print(json.dumps(...))` and updated the module docstring to state that with `--json`, output is one JSON line plus trailing newline for heredoc/GITHUB_OUTPUT compatibility. All script tests pass; the discover step would now succeed in CI.
