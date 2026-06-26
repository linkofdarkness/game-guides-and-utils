# Git Committing

### Frequency

- Prefer smaller commits which are easier to understand, review, and diff.
- Make `wip` commits as needed to show aid in code review.

## Style

- Commit messages should follow [conventional commits](https://www.conventionalcommits.org/en/v1.0.0/) format of `feat/fix/chore/docs(scope/module/category): commit description` with a detailed commit body detailing the change after an empty line.
  - Example:
    ```text
    feat(orders): added line item to checkout UI

    Added a new checkout line item summary row to improve visibility into per-item pricing before order submission. Updated src/Web/Pages/Checkout/CheckoutPage.razor to render each cart item with quantity, unit price, and extended total, and added supporting view models in src/Application/Orders/CheckoutLineItemViewModel.cs. Wired the data mapping in src/Application/Orders/Queries/GetCheckoutQueryHandler.cs so the UI now receives normalized line item details directly from the checkout query. Also adjusted src/Domain/Orders/OrderTotals.cs to expose subtotal calculations in a format usable by the presentation layer.

    Included styling and test coverage for the new UI. Added responsive row styling in src/Web/wwwroot/css/checkout.css and updated src/Web/Components/Orders/CheckoutSummary.razor to show the new line item block above tax and shipping totals. Added unit tests in tests/Application.UnitTests/Orders/GetCheckoutQueryHandlerTests.cs for line item mapping and updated snapshot coverage in tests/Web.Tests/CheckoutPageRenderTests.cs to verify the rendered output. No database changes were required.
    ```