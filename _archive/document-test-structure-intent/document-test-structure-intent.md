# document-test-structure-intent — Archive Summary

## The request

Document test structure and scoping in .cursor so agents and contributors apply a consistent approach: one test file per source module, unit tests in-scope (single module, no integration mixing), integration tests thin (wire behaviour, trust callees, no re-validation of unit logic), and no duplication or mixing in test files or cases. No application or test code changes; rule and docs updates only.

## Planned approach

- **Solution:** Add a “Test structure and scoping” subsection to `.cursor/rules/development_practices.mdc` and align `docs/AI_CONTEXT/AI_CONTEXT_PATTERNS.md` “Testing & TDD” / test layout. Optional one-line pointer in `.cursor/CONVENTIONS.md`.
- **Tasks:** (1) Add subsection to development_practices.mdc with four bullets; (2) Update PATTERNS test layout and add/align unit/integration/no-duplication bullets; (3) Optionally add test layout line to CONVENTIONS. Verification by reading updated artifacts; no new automated tests.

## What was implemented

- **development_practices.mdc:** “Test structure and scoping” added after “Regression Gate” with four bullets: one test file per source module; unit tests in-scope; integration tests thin; avoid duplication and mixing.
- **AI_CONTEXT_PATTERNS.md:** “Test layout” updated to state one test file per source module; added “Unit tests in-scope”, “Integration tests thin”, and “No duplication or mixing” bullets consistent with the rule.
- **CONVENTIONS.md:** Under Usage, added “Test layout” bullet pointing to development_practices.mdc.
- **CHANGELOG:** Root 2026-03-13 entry added for document-test-structure-intent.
