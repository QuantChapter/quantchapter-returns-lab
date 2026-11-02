# Mathematical conventions

Returns Lab describes a single ordered path of finite, strictly positive prices
or wealth values. All returns are decimal fractions: `0.05` means 5%. The core
has no market data, calendars, dividends, transaction costs, taxes, or cash-flow
model. A price return is a total investment return only when the supplied series
and its assumptions justify that interpretation.

The [tutorials](../notebooks/) build these ideas from small worked cases. This
page is a precise reference for comparing implementations and results.

## Adjacent returns

For prices $P_0,\ldots,P_n$, the simple return from observation $t-1$ to $t$ is

$$r_t=\frac{P_t-P_{t-1}}{P_{t-1}}=\frac{P_t}{P_{t-1}}-1.$$

There are $n$ returns for $n+1$ prices. `simple_returns` does not prepend an
invented zero or copy the first return. `total_return` compares only endpoints:

$$R=\frac{P_n}{P_0}-1.$$

For $(100,110,99,118.8)$, the simple returns are $(0.10,-0.10,0.20)$ and the
total return is $0.188$. Adding the simple returns gives $0.20$, a different
quantity that does not describe this compounded gain.

The natural-log return is

$$\ell_t=\log(P_t/P_{t-1})=\log(1+r_t).$$

For positive inputs, the mathematical log-additivity identity is

$$\sum_{t=1}^{n}\ell_t=\log(P_n/P_0),\qquad
R=\exp\!\left(\sum_{t=1}^{n}\ell_t\right)-1.$$

Use logarithmic returns for this additive representation, and convert back when
reporting a simple percentage gain. A log return and a simple return are not
interchangeable percentages.

## Compounded growth

Given positive initial wealth $W_0$, `cumulative_growth` includes that initial
value and then applies

$$W_t=W_{t-1}(1+r_t).$$

Its output has one more element than its return input. Empty returns produce
only $(W_0)$. Finite simple returns must be strictly greater than $-1$; this
package intentionally excludes a total loss or negative-wealth path.

Multiplying all price ratios cancels the intermediate prices, so the resulting
growth is mathematically equal to $W_0P_t/P_0$. Floating-point results can differ
slightly between these two calculations because their arithmetic order differs.

## Volatility and annualization

With $n$ supplied simple returns and arithmetic mean $\bar r$, the variance is

$$s^2=\frac{\sum_{t=1}^{n}(r_t-\bar r)^2}{n-d},$$

where `ddof=d` is either 1 (the sample convention, the default) or 0 (the
population convention). The calculation requires $n>d$. Estimating a mean from
a sample constrains the deviations to sum to zero; dividing by $n-1$ gives the
usual unbiased sample variance under random sampling. The square root itself
is not thereby an unbiased estimator of the population standard deviation.

`annualized_volatility` reports

$$\sigma_{\mathrm{annual}}=s\sqrt m,$$

where `periods_per_year=m` is an explicitly supplied positive integer. Its
default of 252 is a conventional setting, not a conclusion inferred from dates.
Use `periods_per_year=1` to obtain the unscaled standard deviation.

Square-root scaling comes from summing variances of uncorrelated increments
with a common finite variance. Independence is sufficient to remove covariance,
but is stronger than needed. When applied to simple returns, the result is a
scaling convention; it is not the exact standard deviation of compounded annual
simple returns. Serial correlation, changing variance, irregular sampling and
small or unrepresentative samples limit interpretation. The function does not
estimate those effects or forecast future risk.

For $(0.01,-0.01,0.02)$, the sample variance is $7/30000$ and the sample standard
deviation is approximately $0.0152752523$. Multiplication by $\sqrt{252}$ gives
approximately $0.2424871131$, or 24.2487% annually. The example contains only
three invented returns and is for checking arithmetic.

## Drawdown

For positive ordered values, define the running peak and signed drawdown as

$$H_t=\max(P_0,\ldots,P_t),\qquad D_t=P_t/H_t-1.$$

The first drawdown is zero. Subsequent values lie mathematically in $(-1,0]$;
zero means the path is at a peak. `maximum_drawdown` returns $\min_tD_t$, so the
largest loss has a negative sign. This sign convention must be retained when
comparing another library that reports loss magnitudes as positive values.
For extreme positive price ratios, binary floating-point rounding can produce
exactly $-1$ even though the supplied value is positive. This is a numerical
limit, not an inferred bankruptcy or a missing price.

For $(100,120,90,108,126)$, drawdowns are $(0,0,-0.25,-0.10,0)$, and maximum
drawdown is $-0.25$. The path's total return is still $0.26$. An endpoint gain
does not erase an intermediate loss. Drawdown describes the observations
provided; a closing-price series cannot reveal losses between closes.

## Dates, missingness and ordering

The CSV reader requires strictly increasing, unique ISO dates. It never sorts,
deduplicates, interpolates or forward-fills an input. A date gap is permitted;
the reader cannot infer whether it means a weekend, a holiday, missing data or
an irregular sampling design. The caller must verify that the selected
annualization factor fits the actual observation frequency. The bundled file
uses synthetic weekday observations, not an exchange trading calendar.

## Numerical scope

The public API uses Python binary floating-point numbers, not exact decimal
accounting. Finite `int` and `float` values are supported; booleans, strings,
nonfinite values and values outside the function's domain are rejected.
Results that cannot be represented within the package's floating-point domain
must fail rather than become silently infinite or fabricate a valid path.

Use an explicit tolerance when checking results. Ordinary examples here use
absolute tolerances around $10^{-14}$ to $10^{-13}$; those tolerances are not
universal error bounds for arbitrarily long or ill-conditioned paths. This
project is an educational implementation, not a decimal ledger, market data
validation service, trading system or comprehensive risk engine.

## External references

- [Python `statistics`](https://docs.python.org/3.11/library/statistics.html)
  documents the sample and population standard-deviation conventions.
- [Python floating-point arithmetic](https://docs.python.org/3.11/tutorial/floatingpoint.html)
  explains representation error and comparisons.
- [Python `math`](https://docs.python.org/3.11/library/math.html)
  documents natural logarithms, exponentials and accurate summation.
