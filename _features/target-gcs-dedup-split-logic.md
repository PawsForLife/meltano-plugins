# Background

The target-gcs loader has grown organically. A code review is needed to find duplicated logic (to unify into shared functions) and branching/switch logic (to split into distinct functions per option) so the codebase stays maintainable and testable.

# This Task

- Review all target-gcs source under `loaders/target-gcs/target_gcs/` (and helpers) for:
  - **Duplication**: Same or near-identical logic in multiple places → extract into a single shared function.
  - **Switching**: Conditionals or branches that choose between different behaviours → split so each branch is a named function; call the appropriate one from a thin dispatcher.
- Produce a plan and implement: unify duplicated logic into shared functions; refactor switch/branch logic so each option is a separate function.
- Preserve behaviour; all existing tests must pass.

# Testing Needed

- Existing tests remain the regression gate; no behaviour change.
- New or updated tests only where new shared or split functions need direct unit coverage per TDD.
