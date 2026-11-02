# Initial release verification

This record describes checks actually completed locally on 2 November 2026.
Remote workflow runs and release attestations supply separate evidence for the
published commit. These checks do not establish learner effectiveness,
investment suitability, production adoption, or external certification.

## Correctness and contracts

The initial suite passed 177 tests on Windows with Python 3.11, 3.12 and 3.14.
Measured statement/branch coverage was 97.57%, above the enforced 95% gate.
Two OS-specific tests were skipped locally: creating a symlink requires a
Windows privilege unavailable to the test process, and named pipes are POSIX
only. The Linux matrix is intended to exercise these paths; its outcome must
be read from the actual remote run.

An independent reviewer authored exact Fraction/Decimal comparisons and
property checks. They cover return reconstruction, scale invariance, log
additivity, drawdown bounds, sample/population conventions, neighboring-float
precision, and invalid/unrepresentable inputs. A second review identified and
closed bounded-file and nonregular-input gaps. Fault-injection checks verify
that a failed output flush preserves an existing report.

## Reproduction and packaging

- Ruff lint and format checks passed; strict mypy passed for the public package.
- Both notebooks executed in fresh kernels, with saved text/numeric output
  compared against a fresh execution and a portable source digest.
- Rendered notebook mathematics, tables, and figures were inspected. Images
  have explanatory alternative text and adjacent numeric/text accounts.
- The synthetic CSV and provenance manifest reproduce byte-for-byte.
- The source archive and wheel built and passed strict Twine metadata checks.
- The wheel was installed without dependencies in a fresh environment. Its API
  and console command ran successfully from outside the source checkout.
- The development/optional dependency environment passed pip-audit with no
  known vulnerabilities reported by the advisory service at check time.
- Actionlint validated the workflow definitions. Third-party Actions references
  were resolved against their official upstream repositories and pinned by SHA.

Python 3.11–3.14 is the declared support range. Patched optional/development
dependency floors are deliberate: a clean base installation still has no
third-party runtime dependencies. Security findings and dependency support can
change; the weekly update and audit workflows are part of continued maintenance.

The commands and publication gate are recorded in
[CONTRIBUTING.md](../CONTRIBUTING.md) and [release-process.md](release-process.md).
