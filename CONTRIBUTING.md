# Contributing

Small improvements to correctness, teaching, input validation, and reproducibility
are welcome. Start with an issue before proposing new metrics or changing public
behavior. Trading systems, market-data adapters, forecasting, and account services
are outside this release's scope.

## Set up a checkout

Install a supported Python version (3.11 through 3.14) and
[uv](https://docs.astral.sh/uv/getting-started/installation/), then run:

```bash
git clone https://github.com/QuantChapter/quantchapter-returns-lab.git
cd quantchapter-returns-lab
uv sync --locked --all-extras --dev
```

The tracked `uv.lock` captures the development dependency resolution. Ordinary
checks must not silently change it. Update it deliberately with `uv lock` when
changing dependencies and review both the manifest and lockfile.

## Check a change

```bash
uv run --frozen ruff check .
uv run --frozen ruff format --check .
uv run --frozen mypy
uv run --frozen pytest
uv run --frozen python tools/generate_data.py --check
uv run --frozen python tools/verify_notebooks.py
uv run --frozen pip-audit --skip-editable
uv build --no-build-isolation
uv run --frozen python -m twine check --strict dist/*
```

On Windows PowerShell, a native application may not expand `dist/*`. Pass the
wheel and source archive filenames explicitly to `twine check` if needed.
The CI build job also installs the wheel in an isolated environment and exercises
the API and command line from outside the checkout.

Tests should check independently derived results, important numerical properties,
and realistic failure behavior. A test that repeats the implementation does not
independently establish correctness. Add a regression for a confirmed defect and
state the expected numerical tolerance. Preserve the dependency-free core.

## Submit a pull request

1. Create a focused branch, make the change, and run the relevant checks.
2. Explain the concrete problem and resulting behavior. Include a small example
   when it helps, the checks actually run, and any remaining limitation.
3. Update the API documentation, worked examples, and changelog for public changes.
4. Keep notebooks executable in order, clear of local paths and private data, and
   retain intentional outputs. A learner exercise needs a complete worked comparison.
5. Wait for review and required CI before merging. Do not dismiss failing checks
   or lower the coverage threshold merely to make a change pass.

Contributions must be your own work or have a compatible license and clear
attribution. By submitting a contribution, you make it available under this
repository's MIT license. Keep discussion specific, respectful, and focused on
the work. Report security concerns through [SECURITY.md](SECURITY.md).

## Compatibility

The `0.x` API may evolve. Explain a behavior change, add a changelog entry, and
use an appropriate new version. Never silently reinterpret the units, sign,
baseline, missing-data policy, or estimation convention of an existing metric.
See [the release process](docs/release-process.md) for the publication gate.
