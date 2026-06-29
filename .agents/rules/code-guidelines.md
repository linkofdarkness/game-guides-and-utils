---
name: code-guidelines
description: >-
  Language-agnostic conventions for writing and reviewing code. Read before
  creating, editing, or reviewing code in any language.
---

# Code Guidelines

Language-agnostic conventions for writing and reviewing code. For stack-specific guidance, read the relevant skill in `.agents/skills/` (for example, `dotnet` for C#/.NET).

## Repository Structure

- Keep source code in a `src` directory at the repository root unless the project already uses a different established layout.
- Keep human-facing documentation (`README.md`, `REQUIREMENTS.md`) at the repository root, not inside project subdirectories.
- Match the existing folder structure and naming in the repository before introducing new patterns.

## Meaningful Names

- Use descriptive and unambiguous names.
- Avoid abbreviations unless they are widely understood.
- Use pronounceable names and maintain consistent naming conventions.

## Small Functions

- Ensure functions are small and perform a single task.
- Avoid flag arguments and side effects.
- Each function should operate at a single level of abstraction.

## Single Responsibility Principle

- Each class or function should have only one reason to change.
- Separate concerns and encapsulate responsibilities appropriately.

## Clean Formatting

- Use consistent indentation and spacing.
- Separate code blocks with new lines where needed for readability.
- Follow the formatter and linter configuration already present in the repository.

## Comments

- Write self-explanatory code that does not require comments.
- Use comments only to explain non-obvious business logic, constraints, or public APIs.

## Error Handling

- Prefer explicit error signaling over silent failure.
- Avoid catching overly broad errors unless rethrowing or translating at a boundary.
- Fail fast and handle errors at an appropriate level.

## Avoid Duplication

- Extract common logic into functions or classes.
- DRY — Don't Repeat Yourself.

## Code Smells to Flag

- Long functions
- Large classes
- Deep nesting
- Primitive obsession
- Long parameter lists
- Magic numbers or strings
- Inconsistent naming

## Review Style

- Maintain a strict but constructive tone.
- Use bullet points to list issues.
- Provide alternatives and improved code suggestions.
