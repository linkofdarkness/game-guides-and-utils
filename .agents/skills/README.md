# Skills

Optional, stack-specific guidance. Each skill is a directory with a `SKILL.md` file (YAML frontmatter required).

## Adding a skill

1. Create `.agents/skills/<name>/SKILL.md`.
2. Set `name` and `description` in frontmatter — the description should say **what** the skill covers and **when** to use it (same convention as rules in `.agents/rules/`).
3. Put detailed reference material in sibling files (for example `guidelines.md`) and link from `SKILL.md`.
4. Register the skill in `AGENTS.md` and `.agents/README.md`.

## Included skills

| Skill | Purpose |
|-------|---------|
| [dotnet](dotnet/) | C# / .NET and Lod Softworks conventions |

Use the `dotnet` skill as a reference for structure and depth.
