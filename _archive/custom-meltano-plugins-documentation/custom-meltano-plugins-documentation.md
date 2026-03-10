# Archive: custom-meltano-plugins-documentation

## The request

The Meltano plugins in this repo (restful-api-tap, target-gcs) are custom: forked and modified, not published to the Meltano Hub or PyPI. They are intended to use variant name **petcircle**. External users install them by adding a plugin definition to their `meltano.yml` with `pip_url` pointing at this repo, not by adding from the Hub.

**Goal:** Ensure user-facing docs (README, docs/, install guides) clearly explain that these plugins are custom; that users must add them via `meltano.yml` with `pip_url` (and optionally `variant: petcircle`); and the exact `pip_url` form for external use (repo URL plus `#subdirectory=` per plugin). Use variant **petcircle** consistently in all user-facing examples. Reference Meltano plugin management (custom fork / custom plugins) and Meltano SDK where relevant. If any plugin metadata must be adjusted so plugins work when installed as custom via `pip_url`, make those adjustments.

**Scope:** No change to tap/target behaviour or stream logic; only install/setup and documentation.

**Testing:** No new automated tests. Manual verification: follow the documented steps from a fresh Meltano project (add plugin via `pip_url` + subdirectory, `meltano install`, run a pipeline) to confirm the instructions work. If plugin definition or executable changes are made, existing plugin tests must still pass.

---

## Planned approach

**Selected solution (Option D):** In-repo docs only—no Hub submission, no change to in-repo plugin definition files. Document that plugins are custom (not on Meltano Hub or PyPI), use **variant: petcircle** everywhere user-facing, and document the exact `pip_url` form: repo `https://github.com/PawsForLife/meltano-plugins` with `#subdirectory=taps/restful-api-tap` or `#subdirectory=loaders/target-gcs`. Keep links to Meltano plugin management and plugin definition syntax. In-repo `meltano.yml` files (tap and loader) were left unchanged; installed packages already expose the correct executables.

**Architecture:** Documentation-only. No new files or directories. Single source of truth for “add to your meltano.yml” is README.md and docs/monorepo/README.md; other docs repeat the same form or point to those. Canonical contracts (interfaces): variant `petcircle`; extractor `pip_url: "restful-api-tap @ git+https://github.com/PawsForLife/meltano-plugins.git#subdirectory=taps/restful-api-tap"`; loader `pip_url: "target-gcs @ git+.../#subdirectory=loaders/target-gcs"`; version pinning via ref before `#` (e.g. `@v1.0.0#subdirectory=...`).

**Task breakdown (7 tasks):**  
1. Root README.md — custom wording, variant petcircle, canonical pip_url in examples.  
2. docs/monorepo/README.md — purpose/mechanism “custom (not in Hub)”, variant petcircle, canonical pip_url.  
3. docs/README.md — “custom plugins from this repo”, point to monorepo for install.  
4. AI_CONTEXT_QUICK_REFERENCE.md — project summary, running via Meltano, troubleshooting (#subdirectory=, variant).  
5. AI_CONTEXT_REPOSITORY.md — high-level overview and any install example with petcircle.  
6. AI_CONTEXT_restful-api-tap.md and AI_CONTEXT_target-gcs.md — only if they mention install/variant; align with petcircle and canonical pip_url or pointer to repo/docs.  
7. taps/restful-api-tap/README.md — add “Install from this monorepo” example or pointer to repo/docs.

Tasks 01–02 could be done in parallel; 03–07 depend on canonical variant and pip_url from 01–02.

---

## What was implemented

All seven tasks were completed. No in-repo plugin definition files (taps/restful-api-tap/meltano.yml, loaders/target-gcs/meltano.yml) were changed.

- **README.md (root):** Installation states that plugins are **custom** (not on Meltano Hub or PyPI) and must be added via `meltano.yml` with `pip_url` and optionally `variant: petcircle`. All YAML examples use `variant: petcircle` and the canonical pip_url form with `#subdirectory=`; version-pinning example (ref before `#`) retained. Links to Meltano plugin management and plugin definition syntax kept.

- **docs/monorepo/README.md:** Purpose and mechanism state that plugins are custom (not on the Meltano Hub), added via `meltano.yml` with `pip_url` and `#subdirectory=`. Both extractor and loader YAML blocks use `variant: petcircle` and the canonical pip_url strings. Version-pinning note and references preserved.

- **docs/README.md:** Intro and contents describe “custom plugins from this repo” and direct readers to the monorepo doc for install (add via `meltano.yml` and `pip_url`).

- **docs/AI_CONTEXT/AI_CONTEXT_QUICK_REFERENCE.md:** Project summary states plugins are custom (not on Meltano Hub or PyPI) and install is via `meltano.yml` with `pip_url` (Git URL + `#subdirectory=`) and optionally `variant: petcircle`. Running-via-Meltano and troubleshooting align with that; troubleshooting references `#subdirectory=` and variant. Metadata (e.g. Last Updated) adjusted as needed.

- **docs/AI_CONTEXT/AI_CONTEXT_REPOSITORY.md:** High-level overview states plugins are custom (not on Meltano Hub or PyPI) and are added by editing `meltano.yml` with `pip_url` (and optionally `variant: petcircle`). Install wording uses canonical subdirectory form and variant petcircle.

- **docs/AI_CONTEXT component files (task 06):** Updates applied only where install/variant content existed. AI_CONTEXT_target-gcs.md uses “custom” only in a non-install sense (e.g. custom sink class); no install/variant changes required there. AI_CONTEXT_restful-api-tap.md was checked and aligned with petcircle and custom install where relevant.

- **taps/restful-api-tap/README.md:** “Install from this monorepo” subsection added with one YAML example: `name: restful-api-tap`, `variant: petcircle`, canonical `pip_url` with `#subdirectory=taps/restful-api-tap`, plus a sentence to add to `meltano.yml` and run `meltano install`. Link to repo root README and docs/monorepo for full guide and loader. Existing “Generic Meltano setup” (PyPI-style) example left intact.

Manual verification (add plugin with documented pip_url + subdirectory and variant petcircle, `meltano install`, run pipeline) is left to the user; no new automated tests were added.
