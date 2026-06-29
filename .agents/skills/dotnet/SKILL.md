---
name: dotnet
description: >-
  C# and .NET coding conventions, project layout, Entity Framework patterns,
  and Lod Softworks defaults. Use when creating or editing C#/.NET code,
  solution or project files, naming, or review feedback about .NET code quality.
---

# C# / .NET

Read [guidelines.md](guidelines.md) for full conventions before making C#/.NET changes.

## Quick Reference

- Source and solution files live under `src/` at the repository root.
- Use latest stable LTS .NET with `<LangVersion>latest</LangVersion>`.
- Prefer primary constructors, file-scoped namespaces, explicit types over `var`, `new()` over `new Type()`.
- Data models and POCOs: `record class`.
- Entity Framework Core with annotations (not fluent `OnModelCreating`); singular table/column names.
- Namespaces prefixed with `Lod.`; set Product, Copyright, Company, and Description in `.csproj`.
- Do not use the `Async` suffix on async methods.

For universal code quality rules (naming, SRP, review style), also read `.agents/rules/code-guidelines.md`.
