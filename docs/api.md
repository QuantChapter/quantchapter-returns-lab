# Python API

The installable project is `quantchapter-returns-lab`; its import name is
`quantchapter_returns`. The calculation core has no third-party runtime
dependencies. It accepts ordered iterables and returns immutable tuples or
scalar floats. The supplied input is not mutated.

```python
from quantchapter_returns import simple_returns, total_return

prices = (100.0, 110.0, 99.0)
returns = simple_returns(prices)  # approximately (0.10, -0.10)
result = total_return(prices)  # approximately -0.01
```

Return values are decimal fractions, so `-0.01` means -1%. See
[mathematics](mathematics.md) for conventions and numerical limits.

## Calculation functions

| Function | Input and output | Conditions and meaning |
| --- | --- | --- |
| `simple_returns(prices)` | Prices → tuple of adjacent simple returns | At least two finite positive prices. Output length is one less than input length. |
| `log_returns(prices)` | Prices → tuple of adjacent natural-log returns | At least two finite positive prices. Log returns add across consecutive observations. |
| `total_return(prices)` | Prices → scalar endpoint simple return | At least two finite positive prices. Compares the last price with the first. |
| `cumulative_growth(returns, *, initial=1.0)` | Simple returns → wealth tuple including the initial value | Finite returns strictly greater than -1; positive finite initial wealth. Empty input returns the initial value only. |
| `annualized_volatility(returns, *, periods_per_year=252, ddof=1)` | Simple returns → scalar scaled standard deviation | `periods_per_year` is a positive integer; `ddof` is integer 0 or 1; number of returns must exceed `ddof`. Use a factor of 1 for per-observation standard deviation. |
| `drawdowns(values)` | Positive prices or wealth → signed drawdown tuple | At least one value. Each result compares with the highest value already observed, including the current value. |
| `maximum_drawdown(values)` | Positive prices or wealth → scalar largest loss | At least one value. The result is signed and nonpositive, e.g. -0.25 for a 25% peak-to-trough loss. |

The API rejects strings, booleans, nonfinite numbers, domain violations and
unrepresentable results with `ValueError`. It does not treat an input string
such as `"0.10"` as a numeric return. Use explicit parsing at the input boundary.
Invalid observations are not dropped or filled.

## Read a dated CSV

```python
from quantchapter_returns.csvio import read_prices

series = read_prices("data/synthetic_prices.csv")
print(series.dates[0])
print(len(series.prices))
```

`read_prices(path)` returns a `PriceSeries` with `.dates` (a tuple of Python
`date` values) and `.prices` (a tuple of floats). Its file contract is:

- Exact `date,price` header, with one date and price per data row.
- ISO `YYYY-MM-DD` dates, strictly increasing and unique.
- At least three positive finite prices, sufficient for two sample returns.
- No blank data rows, extra columns, malformed CSV or silently repaired values.
- Bounded input: at most 100,000 observations and a 20 MiB file.

Date gaps are permitted. The reader does not infer trading calendars or the
correct annualization factor. Filesystem errors and malformed input are
reported rather than converted to empty data. The CLI presents recoverable
errors without dumping a traceback for ordinary invalid input.

## Command-line interface

The installed entry point is `quantchapter-returns`. Run
`quantchapter-returns --help` and `quantchapter-returns report --help` for the
authoritative options. The report JSON includes conventions alongside its
statistics so the annualization setting and drawdown sign remain inspectable.
The [README](../README.md) supplies the complete current invocation and output
example. Plotting is an optional extra and has no effect on core calculations.

## Compatibility

Version 0.1.0 establishes this initial public surface. Mathematical convention
changes and incompatible behavior changes must be identified in the changelog
and release notes. An educational release is not a financial-system service
level agreement or an assurance of suitability for a particular investment.
