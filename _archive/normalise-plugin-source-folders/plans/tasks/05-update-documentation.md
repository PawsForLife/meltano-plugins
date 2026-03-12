# Task plan: 05-update-documentation

## Overview

This task updates all documentation that references the target-gcs package name, module path, or mypy/install commands from `gcs_target` to `target_gcs`, and records the source-package naming rule in AI context. It runs **after** tasks 01–04 (rename, plugin config, Python imports/tests, repository tooling) so code and tooling are final. No code or config changes; documentation and CHANGELOG entries only.

**Deliverables:**

- Plugin-local README and CHANGELOG use `target_gcs` and correct mypy command.
- AI context docs (quick reference, target-gcs component, patterns, repository) use `target_gcs` everywhere and state the rule: source package = plugin directory name with hyphens replaced by underscores.
- Root CHANGELOG has a migration note for users (namespace and verification commands).

---

## Files to Create/Modify

No new files. Modify the following in place.

### Plugin-local

| File | Changes |
|------|--------|
| `loaders/target-gcs/README.md` | Replace "Python package is `gcs_target`" with "Python package is `target_gcs`". Replace all `uv run mypy gcs_target` with `uv run mypy target_gcs` (occurrences in "Lint, format, and type check" and any other sections). |
| `loaders/target-gcs/CHANGELOG.md` | Add a new entry under `[Unreleased]` (e.g. under ### Changed): package/namespace renamed from `gcs_target` to `target_gcs` as part of normalise-plugin-source-folders. Historical mentions of `gcs_target` in older entries may remain. |

### Repository docs (AI context and root)

| File | Changes |
|------|--------|
| `docs/AI_CONTEXT/AI_CONTEXT_QUICK_REFERENCE.md` | **Commands table (target-gcs):** "Type check" row: `uv run mypy gcs_target` → `uv run mypy target_gcs`. **Runtime entry points table:** `gcs_target.target:GCSTarget.cli` → `target_gcs.target:GCSTarget.cli`. **Namespace:** ensure Meltano example uses `target_gcs`. **Frequently Used Imports (target-gcs):** `from gcs_target.target` / `from gcs_target.sinks` → `from target_gcs.target` / `from target_gcs.sinks`. **Quick Troubleshooting:** "Import errors … `gcs_target`" → "`target_gcs`". |
| `docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md` | **Module overview:** All paths `gcs_target/` → `target_gcs/`; "Source package: `gcs_target/`" → "Source package: `target_gcs/`". **Public interfaces:** Module paths `gcs_target.sinks`, `gcs_target.target` → `target_gcs.sinks`, `target_gcs.target`; CLI entry point string → `target_gcs.target:GCSTarget.cli`. **Tests section:** "patch(\"gcs_target.sinks.Client\")" → "patch(\"target_gcs.sinks.Client\")". Any other `gcs_target` references in examples or prose → `target_gcs`. |
| `docs/AI_CONTEXT/AI_CONTEXT_PATTERNS.md` | **Source package naming:** State the rule explicitly: source package = plugin directory name with hyphens replaced by underscores (e.g. `restful_api_tap`, `target_gcs`). **Code organization bullet:** Replace "e.g. `restful_api_tap/`, `gcs_target/`" with "e.g. `restful_api_tap/`, `target_gcs/`". **File reference table:** Target entry "`loaders/target-gcs/gcs_target/target.py`" → "`loaders/target-gcs/target_gcs/target.py`"; "`gcs_target/sinks.py`" → "`target_gcs/sinks.py`". **Q&A / How do I:** Any path or module example using `gcs_target` (e.g. "loaders/target-gcs/gcs_target/target.py", "gcs_target/sinks.py") → `target_gcs`. |
| `docs/AI_CONTEXT/AI_CONTEXT_REPOSITORY.md` | **Directory structure:** `gcs_target/` → `target_gcs/` under `loaders/target-gcs/`. **Component responsibilities (target-gcs):** Entry point "`gcs_target.target:GCSTarget.cli`" → "`target_gcs.target:GCSTarget.cli`". **Entry points table:** `gcs_target.target:GCSTarget.cli` → `target_gcs.target:GCSTarget.cli`. |
| `CHANGELOG.md` (repo root) | Add an entry under `[Unreleased]` (e.g. ### Changed): **normalise-plugin-source-folders (target-gcs)** — Package/namespace renamed from `gcs_target` to `target_gcs`. Users: update `meltano.yml` namespace to `target_gcs` and re-run `meltano install`; verification commands use `mypy target_gcs`. |

---

## Test Strategy

Per master testing plan: **no new test cases**. This task is documentation-only.

- **Validation:** Run a repo-wide grep for `gcs_target` and confirm the only remaining matches are in CHANGELOGs or explicit migration/historical text (no code, config, or active docs).
- **Line length:** After edits, ensure no modified doc file exceeds the project limit (see `.cursor/rules/content_length.mdc`: 500 lines). Current files are under that limit; changes are local replacements and should not push any file over.

---

## Implementation Order

1. **Plugin-local docs**  
   - Update `loaders/target-gcs/README.md` (package name and mypy command).  
   - Update `loaders/target-gcs/CHANGELOG.md` (add rename entry).

2. **AI context (order optional; can be done in one pass per file)**  
   - Update `docs/AI_CONTEXT/AI_CONTEXT_QUICK_REFERENCE.md`.  
   - Update `docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md`.  
   - Update `docs/AI_CONTEXT/AI_CONTEXT_PATTERNS.md` (rule + examples + file table + Q&A).  
   - Update `docs/AI_CONTEXT/AI_CONTEXT_REPOSITORY.md`.

3. **Root CHANGELOG**  
   - Add migration note to `CHANGELOG.md` at repo root.

4. **Validation**  
   - Grep for `gcs_target`; fix any stray references in active docs/code/config (except intended CHANGELOG/migration text).  
   - Optionally run `./install.sh` and plugin checks to confirm no doc-only change broke tooling (sanity check).

---

## Validation Steps

1. **Grep**  
   From repo root: `grep -r "gcs_target" --include="*.md" --include="*.py" --include="*.yml" --include="*.yaml" .` (or equivalent). Exclude `_archive`, `.git`, and known CHANGELOG/migration sections. Result: no matches in code, config, or active documentation; only CHANGELOG or explicit migration/historical mentions may retain `gcs_target`.

2. **Spot-check docs**  
   - README (plugin): package name and mypy command are `target_gcs`.  
   - AI_CONTEXT_QUICK_REFERENCE: commands, entry point, namespace, imports, troubleshooting use `target_gcs`.  
   - AI_CONTEXT_target-gcs: paths and module names use `target_gcs`.  
   - AI_CONTEXT_PATTERNS: rule stated; examples and file table use `target_gcs`.  
   - AI_CONTEXT_REPOSITORY: directory structure and entry point table use `target_gcs`.  
   - Root CHANGELOG: migration note present and mentions `meltano.yml` namespace and `mypy target_gcs`.

3. **Content length**  
   Confirm no modified file exceeds 500 lines (per `.cursor/rules/content_length.mdc`).

---

## Documentation Updates

This task **is** the documentation update for the normalise-plugin-source-folders feature. The "Documentation Updates" for this task are exactly the files listed in **Files to Create/Modify** above.

- **Plugin:** README and CHANGELOG so users and developers see the correct package name and mypy command.  
- **AI context:** Single source of truth for the naming rule and for target-gcs paths/imports/entry points so future work and agents use `target_gcs` consistently.  
- **Root CHANGELOG:** User-facing migration note so existing Meltano users know to update namespace and verification commands.

No separate "post-task" doc update is required; completion of this task fulfils the documentation scope of the master plan.
