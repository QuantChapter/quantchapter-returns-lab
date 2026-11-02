"""Small, explicit calculations for positive price and wealth paths.

Returns and drawdowns are decimal fractions, never percentage points. These
functions describe the supplied observations; they do not estimate future risk.
"""

from __future__ import annotations

import math
import statistics
from collections.abc import Iterable
from numbers import Real


def _number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must contain real numbers, excluding booleans")
    try:
        result = float(value)
    except (OverflowError, ValueError) as exc:
        raise ValueError(f"{name} must be representable as finite floats") from exc
    if not math.isfinite(result):
        raise ValueError(f"{name} must contain only finite numbers")
    return result


def _values(values: Iterable[float], name: str, minimum: int = 1) -> tuple[float, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{name} must be an iterable of real numbers")
    try:
        result = tuple(_number(value, name) for value in values)
    except TypeError as exc:
        raise ValueError(f"{name} must be an iterable of real numbers") from exc
    if len(result) < minimum:
        raise ValueError(f"{name} requires at least {minimum} observations")
    return result


def _positive(values: Iterable[float], name: str, minimum: int = 1) -> tuple[float, ...]:
    result = _values(values, name, minimum)
    if any(value <= 0 for value in result):
        raise ValueError(f"{name} must be strictly positive")
    return result


def _returns(values: Iterable[float], minimum: int = 0) -> tuple[float, ...]:
    result = _values(values, "returns", minimum)
    if any(value <= -1 for value in result):
        raise ValueError("simple returns must be greater than -1")
    return result


def _simple_change(previous: float, current: float) -> float:
    change = (current - previous) / previous
    if not math.isfinite(change) or change <= -1:
        raise ValueError("price change is not representable as a finite simple return > -1")
    return change


def simple_returns(prices: Iterable[float]) -> tuple[float, ...]:
    """Return (current - previous) / previous for each adjacent price pair.

    At least two finite positive prices are required. One fewer return than
    prices is produced. No sorting, filling, adjustment, or mutation occurs.
    """
    values = _positive(prices, "prices", 2)
    return tuple(
        _simple_change(left, right) for left, right in zip(values, values[1:], strict=False)
    )


def log_returns(prices: Iterable[float]) -> tuple[float, ...]:
    """Return natural-log price changes, using log1p for small relative changes.

    Extreme positive price ratios are evaluated in log space, so they need not
    be representable as simple returns. Requires at least two positive prices.
    """
    values = _positive(prices, "prices", 2)
    result = []
    for previous, current in zip(values, values[1:], strict=False):
        relative = (current - previous) / previous
        change = (
            math.log1p(relative) if abs(relative) < 0.5 else math.log(current) - math.log(previous)
        )
        result.append(change)
    return tuple(result)


def cumulative_growth(returns: Iterable[float], *, initial: float = 1.0) -> tuple[float, ...]:
    """Compound simple returns and include the initial wealth as the first item.

    Empty returns produce only the initial wealth. Complete losses and short
    positions are outside this positive-wealth model. Underflow/overflow raises
    ValueError rather than silently returning zero or infinity.
    """
    values = _returns(returns)
    wealth = _number(initial, "initial")
    if wealth <= 0:
        raise ValueError("initial must be strictly positive")
    path = [wealth]
    for value in values:
        wealth *= 1 + value
        if not math.isfinite(wealth) or wealth <= 0:
            raise ValueError("compounded wealth is not representable as a finite positive float")
        path.append(wealth)
    return tuple(path)


def total_return(prices: Iterable[float]) -> float:
    """Return the last-to-first price change as a decimal fraction.

    At least two positive finite prices are required. This is a price return,
    excluding dividends, fees, taxes, external cash flows, and currency effects.
    """
    values = _positive(prices, "prices", 2)
    return _simple_change(values[0], values[-1])


def annualized_volatility(
    returns: Iterable[float], *, periods_per_year: int = 252, ddof: int = 1
) -> float:
    """Scale simple-return standard deviation by sqrt(periods_per_year).

    ddof=1 uses sample standard deviation; ddof=0 describes the supplied finite
    population. Need more observations than ddof. The scaling assumes equally
    spaced observations and uncorrelated returns with roughly stable variance;
    the caller must justify the frequency. Dates alone do not establish it.
    """
    if isinstance(periods_per_year, bool) or not isinstance(periods_per_year, int):
        raise ValueError("periods_per_year must be a positive integer")
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be a positive integer")
    if isinstance(ddof, bool) or not isinstance(ddof, int) or ddof not in (0, 1):
        raise ValueError("ddof must be 0 (population) or 1 (sample)")
    values = _returns(returns, ddof + 1)
    try:
        deviation = statistics.stdev(values) if ddof == 1 else statistics.pstdev(values)
        annualized = deviation * math.sqrt(periods_per_year)
    except (OverflowError, ValueError) as exc:
        raise ValueError("annualized volatility is not representable as a finite float") from exc
    if not math.isfinite(annualized):
        raise ValueError("annualized volatility is not representable as a finite float")
    return annualized


def drawdowns(values: Iterable[float]) -> tuple[float, ...]:
    """Return signed falls from each running peak, including the initial zero.

    Inputs are positive price or wealth LEVELS, not returns. No pre-sample peak
    is assumed. Results lie in [-1, 0]; tiny positive peak ratios may round to -1.
    """
    path = _positive(values, "values")
    peak = path[0]
    result = []
    for value in path:
        peak = max(peak, value)
        result.append((value - peak) / peak)
    return tuple(result)


def maximum_drawdown(values: Iterable[float]) -> float:
    """Return the most negative drawdown in the observed positive level path."""
    return min(drawdowns(values))
