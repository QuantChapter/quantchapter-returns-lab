"""Independent numerical examples, domain checks, and mathematical properties."""

from __future__ import annotations

import math
from decimal import Decimal, localcontext
from fractions import Fraction
from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from quantchapter_returns import (
    annualized_volatility,
    cumulative_growth,
    drawdowns,
    log_returns,
    maximum_drawdown,
    simple_returns,
    total_return,
)


def test_price_path_has_independently_calculated_returns() -> None:
    prices = [100.0, 120.0, 90.0, 108.0]
    expected = (Fraction(1, 5), Fraction(-1, 4), Fraction(1, 5))
    assert simple_returns(prices) == pytest.approx(tuple(map(float, expected)))
    assert total_return(prices) == pytest.approx(float(Fraction(2, 25)))
    assert cumulative_growth(simple_returns(prices)) == pytest.approx((1.0, 1.2, 0.9, 1.08))
    assert prices == [100.0, 120.0, 90.0, 108.0]


def test_log_returns_agree_with_high_precision_decimal_reference() -> None:
    with localcontext() as context:
        context.prec = 60
        prices = tuple(map(Decimal, ("100", "120", "90", "108")))
        expected = tuple(
            float((end / start).ln()) for start, end in zip(prices, prices[1:], strict=False)
        )
    actual = log_returns(map(float, prices))
    assert actual == pytest.approx(expected, rel=1e-12, abs=1e-14)
    assert math.fsum(actual) == pytest.approx(math.log(1.08), abs=1e-14)


def test_percentages_compound_rather_than_add() -> None:
    # A 50% gain followed by a 50% loss leaves three quarters of initial wealth.
    assert cumulative_growth([0.5, -0.5], initial=200.0) == pytest.approx((200.0, 300.0, 150.0))
    assert total_return([200.0, 300.0, 150.0]) == pytest.approx(-0.25)


def test_drawdown_uses_running_peak_and_includes_initial_observation() -> None:
    values = [100.0, 90.0, 100.0, 80.0, 120.0, 60.0]
    assert drawdowns(values) == pytest.approx((0.0, -0.1, 0.0, -0.2, 0.0, -0.5))
    assert maximum_drawdown(values) == pytest.approx(-0.5)
    assert values == [100.0, 90.0, 100.0, 80.0, 120.0, 60.0]


def test_recovery_is_measured_against_peak_not_trough() -> None:
    assert drawdowns([100.0, 120.0, 90.0, 108.0]) == pytest.approx((0.0, 0.0, -0.25, -0.1))
    assert maximum_drawdown([100.0, 120.0, 90.0, 108.0]) == pytest.approx(-0.25)


def test_constant_and_increasing_paths_have_zero_drawdown() -> None:
    assert simple_returns([7.0, 7.0, 7.0]) == (0.0, 0.0)
    assert log_returns([7.0, 7.0, 7.0]) == (0.0, 0.0)
    assert total_return([7.0, 7.0, 7.0]) == 0.0
    assert annualized_volatility([0.0, 0.0]) == 0.0
    assert drawdowns([7.0, 7.0, 7.0]) == (0.0, 0.0, 0.0)
    assert maximum_drawdown([1.0, 2.0, 3.0]) == 0.0


def test_volatility_distinguishes_sample_from_population() -> None:
    # Mean zero; sum of squared deviations = 1/50. Sample divisor = 2.
    returns = [0.1, -0.1, 0.0]
    assert annualized_volatility(returns, periods_per_year=1) == pytest.approx(0.1)
    assert annualized_volatility(returns, periods_per_year=1, ddof=0) == pytest.approx(
        math.sqrt(float(Fraction(1, 150)))
    )
    assert annualized_volatility(returns, periods_per_year=252) == pytest.approx(
        0.1 * math.sqrt(252)
    )


def test_volatility_is_centered_and_not_root_mean_square() -> None:
    # Each period has the same positive return, so its dispersion is zero.
    assert annualized_volatility([0.1, 0.1, 0.1]) == 0.0
    assert annualized_volatility([0.25], periods_per_year=12, ddof=0) == 0.0


def test_minimum_valid_lengths_and_iterator_support() -> None:
    assert simple_returns(iter([2.0, 3.0])) == (0.5,)
    assert log_returns(iter([2.0, 3.0])) == pytest.approx((math.log(1.5),))
    assert total_return(iter([2.0, 3.0])) == 0.5
    assert cumulative_growth(iter([]), initial=25.0) == (25.0,)
    assert drawdowns(iter([25.0])) == (0.0,)
    assert maximum_drawdown(iter([25.0])) == 0.0


@pytest.mark.parametrize("function", [simple_returns, log_returns, total_return])
@pytest.mark.parametrize("prices", [[], [1.0]])
def test_returns_require_two_prices(function: Any, prices: list[float]) -> None:
    with pytest.raises(ValueError):
        function(prices)


@pytest.mark.parametrize("function", [drawdowns, maximum_drawdown])
def test_drawdowns_require_an_observation(function: Any) -> None:
    with pytest.raises(ValueError):
        function([])


@pytest.mark.parametrize("invalid", [0.0, -1.0, math.inf, -math.inf, math.nan, True, "2", None])
@pytest.mark.parametrize(
    "function", [simple_returns, log_returns, total_return, drawdowns, maximum_drawdown]
)
def test_invalid_values_are_rejected_throughout_path(function: Any, invalid: Any) -> None:
    with pytest.raises(ValueError):
        function([1.0, invalid, 2.0])


@pytest.mark.parametrize("invalid", [-1.0, -1.01, math.inf, -math.inf, math.nan, True, "0.1", None])
@pytest.mark.parametrize("function", [cumulative_growth, annualized_volatility])
def test_return_domain_is_checked(function: Any, invalid: Any) -> None:
    with pytest.raises(ValueError):
        function([0.1, invalid, 0.2])


@pytest.mark.parametrize("initial", [0.0, -1.0, math.inf, math.nan, True, "1", None])
def test_initial_wealth_must_be_positive_finite_number(initial: Any) -> None:
    with pytest.raises(ValueError):
        cumulative_growth([0.1], initial=initial)


@pytest.mark.parametrize("periods", [0, -1, 1.5, True, "252", math.inf, None])
def test_annualization_requires_positive_integer(periods: Any) -> None:
    with pytest.raises(ValueError):
        annualized_volatility([0.1, 0.2], periods_per_year=periods)


@pytest.mark.parametrize("ddof", [-1, 2, 0.5, True, "1", None])
def test_only_documented_variance_conventions_are_accepted(ddof: Any) -> None:
    with pytest.raises(ValueError):
        annualized_volatility([0.1, 0.2], ddof=ddof)


@pytest.mark.parametrize("returns,ddof", [([], 0), ([], 1), ([0.1], 1)])
def test_volatility_requires_positive_degrees_of_freedom(returns: list[float], ddof: int) -> None:
    with pytest.raises(ValueError):
        annualized_volatility(returns, ddof=ddof)


def test_logarithms_handle_ratio_that_would_overflow() -> None:
    actual = log_returns([1e-300, 1e300])
    assert actual == pytest.approx((600 * math.log(10),), rel=1e-13)
    assert log_returns([1e300, 1e-300]) == pytest.approx((-600 * math.log(10),))


@pytest.mark.parametrize("start", [1e-200, 1.0, 1e200])
def test_small_price_change_is_not_lost_to_cancellation(start: float) -> None:
    end = math.nextafter(start, math.inf)
    with localcontext() as context:
        context.prec = 80
        ratio = Decimal.from_float(end) / Decimal.from_float(start)
        expected_simple = float(ratio - 1)
        expected_log = float(ratio.ln())
    assert simple_returns([start, end]) == pytest.approx((expected_simple,), rel=1e-12, abs=0.0)
    assert log_returns([start, end]) == pytest.approx((expected_log,), rel=1e-12, abs=0.0)


@pytest.mark.parametrize("function", [simple_returns, total_return])
@pytest.mark.parametrize("prices", [[1e-300, 1e300], [1e300, 1e-300]])
def test_unrepresentable_simple_returns_fail_explicitly(function: Any, prices: list[float]) -> None:
    with pytest.raises(ValueError):
        function(prices)


@pytest.mark.parametrize("returns,initial", [([1e308, 1.0], 1.0), ([-0.9] * 400, 1.0)])
def test_unrepresentable_growth_fails_explicitly(returns: list[float], initial: float) -> None:
    with pytest.raises(ValueError):
        cumulative_growth(returns, initial=initial)


def test_nonfinite_annualized_result_is_rejected() -> None:
    with pytest.raises(ValueError):
        annualized_volatility([0.0, 1e308], periods_per_year=252)


@settings(max_examples=100, deadline=None)
@given(
    prices=st.lists(st.integers(1, 1_000_000), min_size=3, max_size=30),
    scale=st.integers(1, 1000),
)
def test_positive_rescaling_preserves_relative_metrics(prices: list[int], scale: int) -> None:
    scaled = [price * scale for price in prices]
    assert simple_returns(scaled) == pytest.approx(simple_returns(prices), abs=1e-14)
    assert log_returns(scaled) == pytest.approx(log_returns(prices), abs=1e-13)
    assert total_return(scaled) == pytest.approx(total_return(prices), abs=1e-14)
    assert drawdowns(scaled) == pytest.approx(drawdowns(prices), abs=1e-14)


@settings(max_examples=100, deadline=None)
@given(prices=st.lists(st.integers(10, 10_000), min_size=2, max_size=30))
def test_compounding_reconstructs_normalized_original_prices(prices: list[int]) -> None:
    actual = cumulative_growth(simple_returns(prices))
    expected = [float(Fraction(price, prices[0])) for price in prices]
    assert actual == pytest.approx(expected, rel=1e-9, abs=1e-10)
    assert actual[-1] - 1.0 == pytest.approx(total_return(prices), rel=1e-9, abs=1e-10)


@settings(max_examples=100, deadline=None)
@given(prices=st.lists(st.integers(1, 1_000_000), min_size=2, max_size=30))
def test_log_returns_telescope(prices: list[int]) -> None:
    actual = math.fsum(log_returns(prices))
    expected = math.log(prices[-1] / prices[0])
    assert actual == pytest.approx(expected, rel=1e-10, abs=1e-12)


@settings(max_examples=100, deadline=None)
@given(prices=st.lists(st.integers(1, 1_000_000), min_size=1, max_size=30))
def test_drawdown_bounds_and_peak_definition(prices: list[int]) -> None:
    actual = drawdowns(prices)
    assert len(actual) == len(prices)
    assert actual[0] == 0.0
    assert all(-1.0 < value <= 0.0 for value in actual)
    assert maximum_drawdown(prices) == min(actual)
    for index, value in enumerate(actual):
        peak = max(prices[: index + 1])
        expected = float(Fraction(prices[index] - peak, peak))
        assert value == pytest.approx(expected, abs=1e-14)


@settings(max_examples=75, deadline=None)
@given(
    returns=st.lists(
        st.floats(min_value=-0.5, max_value=0.5, allow_nan=False, allow_infinity=False),
        min_size=2,
        max_size=30,
    ),
    periods=st.integers(1, 1000),
)
def test_volatility_scales_with_square_root_of_frequency(
    returns: list[float], periods: int
) -> None:
    one_period = annualized_volatility(returns, periods_per_year=1)
    annualized = annualized_volatility(returns, periods_per_year=periods)
    assert annualized == pytest.approx(one_period * math.sqrt(periods), abs=1e-14)
