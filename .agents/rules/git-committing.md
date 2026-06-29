---
name: git-committing
description: >-
  Commit frequency and conventional-commit message format. Read before creating
  commits or writing commit messages.
---

# Git Committing

## Frequency

- Prefer smaller commits which are easier to understand, review, and diff.
- Make `wip` commits as needed to show aid in code review.

## Style

- Commit messages should follow [conventional commits](https://www.conventionalcommits.org/en/v1.0.0/) format of `feat/fix/chore/docs(scope/module/category): commit description` with a detailed commit body detailing the change after an empty line.
  - Example:
    ```text
    feat(checkout): show per-item pricing on checkout page

    Added a line-item summary so users see quantity, unit price, and extended total before submitting an order. Updated the checkout page component and view models, wired mapping in the checkout query handler, and exposed subtotal helpers on the order totals type for the presentation layer.

    Added responsive styling for the new rows and unit tests for line-item mapping plus a render snapshot for the checkout summary. No database changes were required.
    ```
