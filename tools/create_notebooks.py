"""Rebuild the tutorial sources with deterministic cell IDs (outputs cleared).

Run this only when intentionally editing the tutorial source. Execute and save
the rebuilt notebooks with ``python tools/verify_notebooks.py --write``.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import nbformat

ROOT = Path(__file__).resolve().parents[1]


def write_notebook(name: str, cells: list[tuple[str, str]]) -> None:
    """Write a valid notebook without machine paths or variable cell identities."""
    notebook = nbformat.v4.new_notebook()
    notebook.metadata = {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {"name": "python"},
    }
    for index, (kind, source) in enumerate(cells):
        source = source.strip()
        cell = (
            nbformat.v4.new_markdown_cell(source)
            if kind == "markdown"
            else nbformat.v4.new_code_cell(source)
        )
        cell.id = hashlib.sha256(f"{name}:{index}".encode()).hexdigest()[:12]
        notebook.cells.append(cell)
    nbformat.validate(notebook)
    destination = ROOT / "notebooks" / name
    destination.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(notebook, destination)
    print(f"Wrote notebooks/{name}")


def main() -> None:
    """Build both connected tutorials from their reviewable teaching source."""
    write_notebook("01_prices_returns_growth.ipynb", RETURNS)
    write_notebook("02_drawdown_and_volatility.ipynb", RISK)


RETURNS = [
    (
        "markdown",
        r"""
# From prices to returns and growth

A price rises from 100 to 110, falls to 99, then finishes at 118.8. Did the
successive percentage changes produce the same answer as comparing the first
and last prices? This notebook connects those two calculations.

You will calculate a return, reconstruct a price path by compounding, and decide
when logarithmic returns can be added. You need basic Python lists, division,
and percentages. A decimal of `0.10` means 10%, not 0.10%. No calculus is needed.

All prices here are invented teaching inputs. They are not an investment,
historical market performance, or a prediction. These examples describe price
changes and omit dividends, fees, taxes, and external cash flows.

## Setup

From the repository root, run `uv sync --extra notebooks`, then open this file
with a Jupyter-capable editor using the repository's `.venv`.
The command `uv run --extra notebooks python tools/verify_notebooks.py` runs
both notebooks without needing an editor. In an installed environment, select
that environment's Python kernel. Run the cells in order.
""",
    ),
    (
        "code",
        """
import math

import matplotlib.pyplot as plt

from quantchapter_returns import (
    cumulative_growth,
    log_returns,
    simple_returns,
    total_return,
)

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 11,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.dpi": 110,
    }
)
prices = (100.0, 110.0, 99.0, 118.8)
print("Synthetic prices:", prices)
""",
    ),
    (
        "markdown",
        r"""
## Measure a change relative to its starting price

The first gain is 10 price units. To compare it with a gain on a differently
priced series, divide by the amount at the start: $10/100=0.10$, or 10%.

Write $P_t$ for the price at observation $t$, and $P_{t-1}$ for the immediately
previous price. The subscript identifies an observation, not a power. A **simple
return** is the change divided by its own starting price:

$$r_t=\frac{P_t-P_{t-1}}{P_{t-1}}=\frac{P_t}{P_{t-1}}-1.$$

For the second change, the starting price is now 110. The loss is 11, so its
return is $-11/110=-0.10$. The final change is $19.8/99=0.20$. There are three
returns from four prices: the first price has no earlier observation here.

The function performs these adjacent comparisons. It requires finite, strictly
positive prices; it neither fills missing observations nor sorts them for you.
""",
    ),
    (
        "code",
        """
returns = simple_returns(prices)
for start, end, result in zip(prices[:-1], prices[1:], returns, strict=True):
    print(f"{start:6.1f} -> {end:6.1f}: {result:+.2%}")
assert all(
    math.isclose(a, b, abs_tol=1e-14) for a, b in zip(returns, (0.10, -0.10, 0.20), strict=True)
)
""",
    ),
    (
        "markdown",
        r"""
**Check the denominator.** A separate price falls from 200 to 180. Choose the
return: (A) $-10\%$, (B) $-11.11\%$, or (C) $+10\%$.

**Worked comparison:** A is correct. The change is $180-200=-20$ and the starting
price is 200, so $-20/200=-0.10$. B divides by the ending price; C loses the sign.

## Rebuild the path one change at a time

A 10% gain turns each starting unit into 1.10 units. A subsequent 10% loss
multiplies the new amount by 0.90. Starting with one unit therefore gives

$$1\times1.10\times0.90=0.99.$$

Equal positive and negative percentages do not cancel because they apply to
different amounts. Adding the two percentages would hide the 1% loss.

**Compounding** means carrying the result of one period into the next. With
initial wealth $W_0$, the rule is $W_t=W_{t-1}(1+r_t)$. `cumulative_growth`
returns the initial value as well as every later value, so four prices and three
returns produce four growth values.
""",
    ),
    (
        "code",
        """
growth = cumulative_growth(returns)
print("Growth of one unit:", tuple(round(value, 6) for value in growth))
print(f"Compounded total return: {growth[-1] / growth[0] - 1:.2%}")
print(f"First-to-last price return: {total_return(prices):.2%}")
assert math.isclose(growth[-1], 1.188, abs_tol=1e-14)
assert math.isclose(growth[-1] - 1, total_return(prices), abs_tol=1e-14)
""",
    ),
    (
        "markdown",
        r"""
The growth path is $1, 1.10, 0.99, 1.188$: the final gain is 18.8%.
The shortcut works because consecutive price ratios cancel their intermediate
prices:

$$\frac{110}{100}\times\frac{99}{110}\times\frac{118.8}{99}
=\frac{118.8}{100}.$$

The sum $10\%-10\%+20\%=20\%$ does not reproduce the result. The multiplication
does. This agreement provides an independent way to check a calculation.

The next figure places the four exact growth values at their observation
numbers. Lines connect consecutive observations; they do not reveal what
happened between them. The baseline is one starting unit.
""",
    ),
    (
        "code",
        """
fig, ax = plt.subplots(figsize=(8, 3.8), layout="constrained")
observations = tuple(range(len(growth)))
ax.plot(observations, growth, color="#215b8f", marker="o", linewidth=2)
ax.axhline(1.0, color="#555555", linestyle="--", linewidth=1, label="One starting unit")
for position, value in zip(observations, growth, strict=True):
    ax.annotate(
        f"{value:.3f}", (position, value), xytext=(0, 9), textcoords="offset points", ha="center"
    )
ax.set(
    xticks=observations,
    xlabel="Observation number",
    ylabel="Wealth / initial wealth",
    ylim=(0.95, 1.24),
    title="Synthetic example: growth of one starting unit",
)
ax.legend(loc="upper left", frameon=False)
ax.grid(axis="y", color="#dedede", linewidth=0.7)
plt.show()
""",
    ),
    (
        "markdown",
        r"""
The path ends above its start, but observation 2 is below the starting amount.
An endpoint comparison and the route between endpoints answer different
questions. We will use that distinction in the next notebook.

## Use logarithms to turn multiplication into addition

A logarithm is a transformation with the rule $\log(ab)=\log(a)+\log(b)$
for positive $a$ and $b$. Here `log` means the natural logarithm, which Python
computes with `math.log`. You do not need its calculus to use this rule.

For a price ratio, define a **logarithmic return** by

$$\ell_t=\log\!\left(\frac{P_t}{P_{t-1}}\right)=\log(1+r_t).$$

Logarithmic returns can be added across consecutive observations because they
are logarithms of the same ratios that compounding multiplies. To recover the
total simple return, undo the logarithm with the exponential:

$$\text{total simple return}=\exp\!\left(\sum_t\ell_t\right)-1.$$

The summation symbol means add the individual logarithmic returns. A log return
of about 0.09531 corresponds to a simple gain of 10%; they are different measures.
""",
    ),
    (
        "code",
        """
log_changes = log_returns(prices)
print("Logarithmic returns:", tuple(round(value, 6) for value in log_changes))
recovered_total = math.expm1(math.fsum(log_changes))
print(f"Total simple return recovered from logs: {recovered_total:.2%}")
assert math.isclose(recovered_total, 0.188, abs_tol=1e-14)
assert math.isclose(math.fsum(log_changes), math.log(prices[-1] / prices[0]), abs_tol=1e-14)
""",
    ),
    (
        "markdown",
        r"""
**Independent attempt.** For prices $(50, 60, 48)$, choose the total simple return:
(A) $0\%$, (B) $-4\%$, or (C) $-20\%$. Then compare with the calculation below.

**Worked comparison:** the first return is $10/50=20\%$ and the second is
$-12/60=-20\%$. Multiplying $1.20\times0.80=0.96$ leaves a 4% loss, so B is
correct. The endpoint check is $48/50-1=-0.04$. Adding percentages gives A
incorrectly; C describes only the last change.

## Checks and next steps

The final cell verifies the fresh case with the public API. All checks use a
small floating-point tolerance because computers store most decimals only
approximately. These assertions check calculations, not learner mastery.
""",
    ),
    (
        "code",
        """
fresh_prices = (50.0, 60.0, 48.0)
fresh_returns = simple_returns(fresh_prices)
assert math.isclose(total_return(fresh_prices), -0.04, abs_tol=1e-14)
assert math.isclose(cumulative_growth(fresh_returns)[-1], 0.96, abs_tol=1e-14)
assert math.isclose(math.expm1(math.fsum(log_returns(fresh_prices))), -0.04, abs_tol=1e-14)
print("Fresh case: 20% gain, 20% loss, 4% total loss. Checks passed.")
""",
    ),
    (
        "markdown",
        """
Continue with [drawdown and volatility](02_drawdown_and_volatility.ipynb).
That notebook asks how a positive total return can coexist with a substantial
intermediate loss. The [mathematics reference](../docs/mathematics.md) records
the precise conventions and numerical limits used by the package.
""",
    ),
]

RISK = [
    (
        "markdown",
        r"""
# Two different questions about a changing price

An invented series moves through $100,120,90,108,126$. It finishes 26% above its
start. A person looking only at that gain would miss the fall from 120 to 90.
How can we describe that fall, and how is it different from the variation in
successive returns?

This notebook teaches **drawdown**, a loss relative to the highest value already
seen, and **volatility**, a measure of how returns vary around their mean. You
need the simple returns and compounding from notebook 1, plus arithmetic and
squares. We will explain the statistical notation locally.

All prices are synthetic. These descriptive calculations omit dividends, fees,
taxes, and cash flows. They do not estimate the probability of a future loss or
recommend an investment.

## Setup

Use the repository environment: `uv sync --extra notebooks`. Open this file
in a Jupyter-capable editor using `.venv`, or execute both notebooks with
`uv run --extra notebooks python tools/verify_notebooks.py`. Run cells in order.
""",
    ),
    (
        "code",
        """
import math

import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

from quantchapter_returns import (
    annualized_volatility,
    drawdowns,
    maximum_drawdown,
    simple_returns,
    total_return,
)

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 11,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.dpi": 110,
    }
)
prices = (100.0, 120.0, 90.0, 108.0, 126.0)
print(f"First-to-last price return: {total_return(prices):.2%}")
""",
    ),
    (
        "markdown",
        r"""
## Compare each value with the peak already reached

At observation 1, the highest price seen is 120. At observation 2, the price is
90, while that earlier peak remains 120. The loss relative to the peak is

$$\frac{90-120}{120}=\frac{-30}{120}=-0.25=-25\%.$$

At the next price, 108, the peak is still 120. The drawdown is
$108/120-1=-0.10$, or -10%. Reaching 126 creates a new peak and returns drawdown
to zero.

Write $H_t$ for the largest value observed up to and including observation $t$.
The running-peak rule and **drawdown** $D_t$ are

$$H_t=\max(P_0,\ldots,P_t),\qquad D_t=\frac{P_t}{H_t}-1.$$

The maximum symbol means choose the largest of the listed values. This package
reports drawdown as a signed number: zero at a peak and negative below it.
`maximum_drawdown` returns the most negative drawdown. Its name describes the
largest loss magnitude, not the numerically largest signed value.
""",
    ),
    (
        "code",
        """
underwater = drawdowns(prices)
print("Observation | Price | Drawdown")
for observation, (price, decline) in enumerate(zip(prices, underwater, strict=True)):
    print(f"{observation:11d} | {price:5.0f} | {decline:8.2%}")
print(f"Maximum drawdown (signed): {maximum_drawdown(prices):.2%}")
assert all(
    math.isclose(a, b, abs_tol=1e-14)
    for a, b in zip(underwater, (0.0, 0.0, -0.25, -0.10, 0.0), strict=True)
)
""",
    ),
    (
        "markdown",
        r"""
**Check the reference point.** At price 108, choose its drawdown: (A) $+8\%$,
(B) $-10\%$, or (C) $+20\%$.

**Worked comparison:** B uses the earlier peak, $108/120-1=-10\%$. A compares
with the initial price, $108/100-1=8\%$. C compares only with the preceding price,
$108/90-1=20\%$. All three calculations can be valid answers to different
questions; only B answers the drawdown question.

The chart shows the price and its running peak together, then drawdown below.
The table above supplies every value without depending on colour or the chart.
""",
    ),
    (
        "code",
        """
observations = tuple(range(len(prices)))
peaks = tuple(max(prices[: index + 1]) for index in observations)
fig, (price_ax, loss_ax) = plt.subplots(2, 1, figsize=(8, 6), sharex=True, layout="constrained")
price_ax.plot(
    observations, prices, color="#215b8f", marker="o", linewidth=2, label="Synthetic price"
)
price_ax.step(
    observations,
    peaks,
    where="post",
    color="#555555",
    linestyle="--",
    linewidth=1.5,
    label="Running peak",
)
price_ax.set(ylabel="Price units", title="Synthetic price and its running peak")
price_ax.legend(loc="lower right", frameon=False)
loss_ax.plot(observations, underwater, color="#215b8f", marker="o", linewidth=2)
loss_ax.fill_between(observations, underwater, 0, color="#215b8f", alpha=0.12)
loss_ax.axhline(0, color="#555555", linewidth=1)
loss_ax.yaxis.set_major_formatter(PercentFormatter(1.0))
loss_ax.set(
    xticks=observations,
    xlabel="Observation number",
    ylabel="Drawdown from prior peak",
    ylim=(-0.30, 0.03),
)
loss_ax.annotate("-25%", (2, -0.25), xytext=(12, -5), textcoords="offset points")
for axis in (price_ax, loss_ax):
    axis.grid(axis="y", color="#dedede", linewidth=0.7)
plt.show()
""",
    ),
    (
        "markdown",
        r"""
The final +26% return and the -25% maximum drawdown coexist. One compares
endpoints; the other searches the whole observed path. Drawdown only sees the
supplied observations, so a daily-close series cannot reveal an intraday fall.

## Measure variation around the mean

Now use a separate three-period example with returns $1\%,-1\%,2\%$. First take
the arithmetic mean: add the decimals and divide by three.

$$\bar r=\frac{0.01-0.01+0.02}{3}=0.006666\ldots.$$

The bar means average. Each return differs from that average. Squaring the
differences makes both positive and negative deviations contribute positively.
For a sample, add those squares and divide by $n-1$, where $n$ is the number of
returns. We use $n-1$ because the mean was estimated from these same values;
the deviations must sum to zero, leaving one fewer freely varying deviation.

$$s^2=\frac{\sum_{t=1}^n(r_t-\bar r)^2}{n-1}
=\frac{0.000466666\ldots}{2}=0.000233333\ldots.$$

This is the **sample variance**. Taking its square root gives the **sample
standard deviation**, about $0.015275$, or 1.5275% per observation. That standard
deviation is the volatility measure used here. Squaring then taking a square
root restores the original return units.
""",
    ),
    (
        "code",
        """
small_prices = (100.0, 101.0, 99.99, 101.9898)
small_returns = simple_returns(small_prices)
per_observation = annualized_volatility(small_returns, periods_per_year=1, ddof=1)
print("Synthetic simple returns:", tuple(round(value, 6) for value in small_returns))
print(f"Sample standard deviation per observation: {per_observation:.4%}")
assert math.isclose(per_observation, math.sqrt(7 / 30000), abs_tol=1e-14)
""",
    ),
    (
        "markdown",
        r"""
## Make the time convention explicit

To express a daily standard deviation on a conventional annual scale, this
package multiplies by the square root of the specified number of observations
per year, $m$:

$$\sigma_{\mathrm{annual}}=s\sqrt m.$$

The rule comes from adding variances of uncorrelated increments with a common
variance, then taking the square root. When applied to simple returns it is a
scaling convention, not the exact standard deviation of compounded annual
returns. Serial dependence or changing variance can make the convention
misleading. It is not a promise of future risk.

Here we explicitly choose 252 observations per year. This is a supplied
convention, not a fact inferred from timestamps or a guarantee that any series
has 252 trading days. Weekly, monthly, irregular, and mixed-frequency series
need their own justified treatment. Three synthetic returns are too few to
support a dependable market-risk estimate.
""",
    ),
    (
        "code",
        """
annual = annualized_volatility(small_returns, periods_per_year=252, ddof=1)
population_scaled = annualized_volatility(small_returns, periods_per_year=252, ddof=0)
print(f"Sample convention (ddof=1), annualized: {annual:.4%}")
print(f"Population convention (ddof=0), annualized: {population_scaled:.4%}")
assert math.isclose(annual, math.sqrt(7 / 30000) * math.sqrt(252), abs_tol=1e-13)
assert math.isclose(population_scaled / annual, math.sqrt(2 / 3), abs_tol=1e-13)
""",
    ),
    (
        "markdown",
        r"""
The sample convention gives about 24.2487% annually. `ddof` means degrees of
freedom removed: `1` divides the squared deviations by $n-1$; `0` divides by
$n$ and describes the supplied values as the whole population. State the choice
when comparing results. Neither choice fixes an unrepresentative input sample.

**Independent attempt.** A new path is $80,100,90,99$. Choose its final drawdown:
(A) $+23.75\%$, (B) $-1\%$, or (C) $-10\%$. Is that also its maximum drawdown?

**Worked comparison:** B is the final drawdown: the peak already reached is 100,
so $99/100-1=-1\%$. The maximum drawdown was -10% at 90. A is the first-to-last
return, $99/80-1=23.75\%$; C is the earlier worst drawdown. The distinction
requires retaining the path, not just the final value.

**A different boundary case:** for repeated prices $50,50,50$, choose volatility:
(A) zero, (B) undefined, or (C) 50%. A is correct: both returns are zero, their
deviations from the zero mean are zero, and two returns are enough for `ddof=1`.
With only one return, the sample denominator would be zero and the function
rejects the calculation instead of reporting a fabricated zero.
""",
    ),
    (
        "code",
        """
fresh_prices = (80.0, 100.0, 90.0, 99.0)
assert math.isclose(drawdowns(fresh_prices)[-1], -0.01, abs_tol=1e-14)
assert math.isclose(maximum_drawdown(fresh_prices), -0.10, abs_tol=1e-14)
flat_returns = simple_returns((50.0, 50.0, 50.0))
assert annualized_volatility(flat_returns, periods_per_year=252, ddof=1) == 0.0
try:
    annualized_volatility((0.01,), periods_per_year=252, ddof=1)
except ValueError as error:
    print("Insufficient sample rejected:", error)
else:
    raise AssertionError("One return cannot define a sample standard deviation")
print("Fresh path, flat path, and insufficient-sample checks passed.")
""",
    ),
    (
        "markdown",
        """
## Next steps

Use the [learning guide](../docs/learning-guide.md) to run the full synthetic-CSV
example. Use [mathematical conventions](../docs/mathematics.md) before supplying
your own series. Volatility and drawdown describe different features of a path;
neither by itself gives a complete account of investment risk. These notebooks
are authored tutorials with checked calculations, not learner-validated courses.
""",
    ),
]


if __name__ == "__main__":
    main()
