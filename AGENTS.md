## AI Agents

Guidance for AI agents working in this repository is found within the `.agents` directory at the root of the repository.

## Documentation expectations

- `README.md` should be human-focused and high-level.
- `REQUIREMENTS.md` should be maintained as a living Product Requirements Document with detailed project context that agents can update as understanding evolves.
- Agents may maintain `.agents/FILES.md` to document important files and where they live so frequently needed files can be found quickly with fewer repeated searches.

## Rules

Files which define the repo-specific instructions, conventions, and guardrails you should follow.

- **Rules directory**: `.agents/rules/`
- **Rule files**: `*.md` and `*.mdc` files

If you’re looking for “how to behave in this repo”, start with the files in `.agents/rules/`.

### Rule index (what to read when)

- `scope-of-work.md`: Read at the start of any task to keep changes minimal, on-request, and reviewable.
- `dotnet-guidelines.md`: Read before creating or editing C#/.NET code, solution/project layout, naming, or review feedback about code quality.
- `git-committing.md`: Read before writing commit messages or creating commits.
- `pull-requests.md`: Read before preparing PR titles/descriptions or performing a PR/code review.

### When to use the rules

Use the rules as **constraints** and **process guidance** whenever you:

- **Change code**: follow repo conventions (style, structure, naming, frameworks).
- **Make Git changes**: follow commit/pull request expectations when applicable.
- **Review or propose changes**: match the requested review tone/format and scope boundaries.
- **Are uncertain**: prefer the rules over assumptions; treat them as the source of truth for repo-specific preferences.

### Rule format conventions

- **`md` and `.mdc`** files in `.agents/rules/` are authoritative instructions for agents.
- Prefer applying the **most relevant** rule(s) to the current task context.
- If multiple rules apply, resolve conflicts by:
  - Prioritizing **explicit user instructions** first.
  - Otherwise following **repo scope/guardrails** rules to keep changes minimal and reviewable.

## Skills

AI agent skills can be found within the `.agents/skills/` directory.

- **Skills directory**: `.agents/skills/`

### Skill index (what to read when)

- No repository-local skill files are currently defined in `.agents/skills/`.
- If skill files are added, read the relevant skill before performing specialized workflows it describes.
