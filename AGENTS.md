# QuantChapter Returns Lab

This is an independent public educational Python package. Keep the scope focused
on returns, growth, volatility, drawdown, strict dated CSV input, and reproducible
teaching examples. Do not add trading, forecasting, accounts, or network services.

- Support Python 3.11 through 3.14 and a dependency-free runtime core.
- State numerical conventions and reject invalid or unrepresentable inputs.
- Keep code in `src/quantchapter_returns/`, with a typed public API.
- Verify mathematics from independently calculated examples and properties.
- Preserve synthetic-data provenance; never imply observed investment results.
- Keep teaching concrete, reasoned, and checked. Every learner task needs a worked
  comparison. Do not claim learner validation or institutional certification.
- Run Ruff, strict mypy, pytest with branch coverage, packaging checks, a clean
  wheel installation, and executed notebooks before publishing a release.
- Never commit secrets, environments, caches, personal identities, or local paths.
- All GitHub Actions dependencies must be pinned to verified commit SHAs, with
  minimum permissions and no pull_request_target execution of contributor code.
- Check Git status and intended diff before every commit. Integrate through one
  owner and keep parallel work in explicitly assigned files.
- Never poll a running job or agent more often than every five minutes. Prefer
  completion events or blocking waits; do useful independent work meanwhile.
