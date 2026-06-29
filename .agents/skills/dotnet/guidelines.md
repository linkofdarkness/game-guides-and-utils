# C# / .NET Programming Guidelines

Lod Softworks conventions for C# and .NET projects. Loaded via the `dotnet` skill in `.agents/skills/dotnet/`.

## Fundamentals

Follow [code-guidelines.md](../../rules/code-guidelines.md) as the base for language-agnostic code quality, naming, structure, and review style. Apply those conventions by default; where this skill specifies .NET-specific guidance, the skill takes precedence.

## Repository Structure

- All source files including dotnet solution files should be in a `src` directory at the repository root.
- README files should be maintained at the repository root and not within project directories.

## Framework and Language Versions

- Use the latest C# features. `<LangVersion>latest</LangVersion>`
    - Prefer primary constructors without member fields/properties
    - Use file scoped namespaces
    - Add global `using` directives for frequently used namespaces via the .csproj `<Using Include=.. />` item.
    - Declare variable types instead of using `var`, prefer `new()` instead of `new Type()`.
    - Declare data models, database entities, and other POCOs as records (`record class`).
- Use the latest stable LTS version of dotnet.
- Use EntityFrameworkCore for database operations.
    - Use annotations (i.e. [Table("MyTable")]) rather than the model builder pattern (`OnModelCreating(ModelBuilder modelBuilder)`).
    - Use singular names for tables and columns (i.e. `dbo.Order` rather than `dbo.Orders`).

## Project Defaults

- Project namespaces should all be prefixed with `Lod.`
- Product, Copyright, Company (Lod Softworks LLC) and Description properties should be defined in .csproj files.

