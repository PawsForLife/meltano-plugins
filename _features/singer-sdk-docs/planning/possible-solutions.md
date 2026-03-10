# Possible solutions — Singer SDK docs structure

## Options considered

### 1. Single long guide (`docs/singer-sdk-guide.md`)

- **Pros:** One place for everything; simple navigation.
- **Cons:** Likely to exceed 500-line limit; harder to deep-link and maintain; mixes spec, taps, targets, and monorepo.

### 2. By role (e.g. contributor vs consumer)

- **Structure:** e.g. `docs/contributors/`, `docs/consumers/` with role-specific pages.
- **Pros:** Clear for "I only use plugins" vs "I build plugins."
- **Cons:** Spec and SDK concepts would be duplicated or split across roles; monorepo import is relevant to both.

### 3. By topic (spec, taps, targets, monorepo) — selected

- **Structure:** `docs/spec/`, `docs/taps/`, `docs/targets/`, `docs/monorepo/` with README (or index) in each; root `docs/README.md` as index.
- **Pros:** Matches how the feature file and SDK/Spec are organized; easy to link "taps" vs "targets" vs "spec"; keeps each file focused and under 500 lines; monorepo is a distinct topic.
- **Cons:** None significant.

### 4. Flat docs (all in `docs/` as single files)

- **Structure:** `docs/spec.md`, `docs/taps.md`, `docs/targets.md`, `docs/monorepo.md`, `docs/README.md`.
- **Pros:** No subdirs; simple.
- **Cons:** Slightly less clear grouping than subdirs; same content as option 3.

## Recommendation

**Option 3 (by topic with subdirs)** is chosen: it aligns with the requested path names (taps, targets, spec, monorepo), supports the 500-line rule, and makes it clear where to find spec vs implementation vs repo usage. Option 4 is acceptable if the implementer prefers no subdirs; the selected-solution doc uses subdirs for consistency with the feature file.
