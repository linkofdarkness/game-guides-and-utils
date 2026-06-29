---
name: adopting-this-template
description: >-
  Bootstraps a new repository from this template or tailors agent guidance to a
  specific project. Read when setting up a repo or adding project-specific rules
  and skills.
---

# Adopting This Template

Use this rule when bootstrapping a new repository from this template or tailoring agent guidance to a specific project.

## First Steps

1. Replace `README.md` with a project-specific overview.
2. Fill in `REQUIREMENTS.md` with product context, constraints, and implementation notes.
3. Remove or archive guidance that does not apply to the project's stack.
4. Add project-specific rules to `.agents/rules/` (with `name` and `description` frontmatter) and skills to `.agents/skills/`.

## Rules vs Skills

| Use **rules** for | Use **skills** for |
|-------------------|-------------------|
| Process and guardrails that apply broadly (scope, git, PRs) | Stack-specific or workflow-specific guidance loaded on demand |
| Repository conventions every agent should follow | Optional expertise (languages, frameworks, deployment) |
| Short, always-relevant constraints | Deeper reference material and examples |

## Adding Language or Stack Support

1. Create a directory under `.agents/skills/<stack>/` with a `SKILL.md` file.
2. Write a specific `description` in the skill frontmatter so agents know when to load it.
3. Link the skill from `.agents/README.md` and `AGENTS.md`.
4. Add optional `.gitignore` snippets under `templates/gitignore/` if the stack generates artifacts.

## Optional Git Ignore Snippets

The root `.gitignore` covers common cross-language artifacts. For stack-specific build output, append the matching file from `templates/gitignore/` to `.gitignore` (or copy its contents).

## Project-Specific Overrides

When project conventions conflict with template defaults:

- Document overrides in `REQUIREMENTS.md` or a dedicated rule in `.agents/rules/`.
- Prefer explicit user instructions over template defaults.
- Keep overrides minimal and easy to review.
