# Commit

Review uncommitted files, ensure no unsafe files are included, and generate a Conventional Commits-formatted message. Follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) spec. Reference `@commits` for spec details.

## Prerequisites

- Git repository with uncommitted changes (staged or unstaged)
- `.gitignore` present at project root (covers base patterns: cache, logs, venv, etc.)

## Instructions

You MUST follow these phases in order. Do not generate a commit message until Phase 2 passes.

## Completion Checklist

**Phase 1: Gather Uncommitted State**
- [ ] Ran `git status` to list staged and unstaged files
- [ ] Ran `git diff --staged` and `git diff` to inspect changes
- [ ] Read `.gitignore` for project ignore patterns

**Phase 2: Safety Check**
- [ ] Sanity-checked staged files that will be committed and flagged anything that looks like it should normally be ignored (artifacts, caches, logs, env/secrets, etc.)
- [ ] Checked each uncommitted file against command blocklist
- [ ] Confirmed no unsafe files; or stopped and reported if any found

**Phase 3: Analyze Changes**
- [ ] Identified affected components and change types
- [ ] Inferred change goal (high-level, not file-specific)

**Phase 4: Generate Message**
- [ ] Produced Conventional Commits message with goal-focused body

---

## Phase 1: Gather Uncommitted State

### Step 1.1: Get Git State

1. Run `git status` to list all staged and unstaged files
2. Run `git diff --staged` to see staged changes
3. Run `git diff` to see unstaged changes (if any)
4. Read `.gitignore` at project root

### Step 1.2: Collect File List

Build a complete list of all uncommitted files (staged and unstaged). Include their paths and staging status.

---

## Phase 2: Safety Check (Identify Files That Should Not Be Committed)

**Purpose**: `.gitignore` handles base patterns; this step is a safety net for files staged despite being ignored, or matching risky patterns not in `.gitignore`.

### Step 2.1: Check Against Expected Ignore Patterns (no `.gitignore` commands)

Look at the list of staged files that will be included in the commit and sanity-check them. If any look like something that would normally be ignored (build artifacts, caches, logs, secrets, environment files, etc.), flag them as suspicious based on their path, name, or content. Do **not** run `git check-ignore`; `.gitignore` is already doing its job during staging.

### Step 2.2: Check Against Command Blocklist

Additional patterns the command enforces (secrets/credentials):

- `.env` or `.env.*` (e.g. `.env.local`, `.env.production`)
- `*.key`, `*.pem`
- `secrets.*` (e.g. `secrets.json`)

If any staged file matches these patterns, flag it.

### Step 2.3: Report and Stop if Needed

If any files are flagged:

1. Output a clear list of flagged files with their paths
2. Indicate why each was flagged (e.g. looks like an artifact/cache/log/env file, or matches the secrets/blocklist patterns)
3. Explicitly ask the user whether they intend to commit each flagged file or whether it should have been ignored (e.g. by `.gitignore`)
4. **Pause here until the user responds.** Do not proceed to Phase 3 or 4 until the user confirms how to handle the flagged files. If the user decides a file should not be committed, instruct them to unstage (`git restore --staged <path>`) or remove it before re-running this command.

---

## Phase 3: Analyze Changes for Message Generation

### Step 3.1: Identify Affected Components

Map changed files to **components** using project path conventions (e.g. document in README or `.cursor/rules` which paths correspond to which scope). Use project-defined component names where available.

### Step 3.2: Infer Change Type and Goal

- **Change type**: feat, fix, docs, refactor, test, chore (per Conventional Commits)
- **Change goal**: What does this commit accomplish at a high level? Focus on the outcome, not implementation details.

**Examples**:
- Good goal: "Implemented repo-wide logging"
- Bad goal: "Added logging.create and logging.report to start, end and update functions in main.py"

---

## Phase 4: Generate Commit Message

### Step 4.1: Format

```
<type>(<scope>): <brief description>

<optional body - dot points, each <100 chars, goal-focused>
```

**Type** (required): `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

**Scope** (optional): Use project-defined component names (e.g. parser, webview, extension, docs — or as defined by the project) based on affected paths.

**Description** (required): Brief, imperative mood (e.g. "add", "fix", "implement").

### Step 4.2: Body Rules

If a body is needed:

- Use dot points (bullet list)
- Each line **under 100 characters**
- **Goal-focused**: describe what the change achieves, not implementation details
- Relate to the change goal, not file-specific mechanics

**Example good body**:
```
- Implemented repo-wide logging
- Standardised log format across services
```

**Example bad body**:
```
- Added logging.create and logging.report to start, end and update functions in main.py
- Updated character_create in character.py to use new logging module
```

### Step 4.3: Output

Present the generated message to the user in a code block, ready to copy. Do **not** execute `git commit`; the user reviews and runs it manually.

---

## Notes

- The command outputs a suggested message only; it does not perform the commit
- `.gitignore` is the primary source for "should not commit"; the command blocklist is minimal (secrets only)
- When in doubt, prefer a shorter, more goal-focused message over a detailed one

## Git Compatibility

If the project's Git does not support certain flags (e.g. `--trailer`), use the project's wrapper script if provided (e.g. `scripts/git-commit.cmd` or `scripts/git-commit.sh`); the wrapper strips unsupported arguments before forwarding to `git commit`. Otherwise use `git commit` directly. The wrapper accepts all standard `git commit` arguments (e.g. `-m`, `-a`, `--amend`).
