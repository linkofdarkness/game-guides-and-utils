# C#/DotNet Programming Guidelines

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

## Meaningful Names

- Use descriptive and unambiguous names.
- Avoid abbreviations unless they are widely understood.
- Use pronounceable names and maintain consistent naming conventions.
- Do not use the `Async` suffix for `async` methods.

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

## Avoid Comments

- Write self-explanatory code that doesn't require comments.
- Use comments only to explain complex logic or public APIs.

## Error Handling

- Use exceptions rather than return codes.
- Avoid catching generic exceptions.
- Fail fast and handle exceptions at a high level.

## Avoid Duplication

- Extract common logic into functions or classes.
- DRY – Don't Repeat Yourself.

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
