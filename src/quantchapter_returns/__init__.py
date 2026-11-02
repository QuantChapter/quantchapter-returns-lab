"""Reproducible educational return and risk calculations from QuantChapter."""

from .metrics import (
    annualized_volatility,
    cumulative_growth,
    drawdowns,
    log_returns,
    maximum_drawdown,
    simple_returns,
    total_return,
)

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "annualized_volatility",
    "cumulative_growth",
    "drawdowns",
    "log_returns",
    "maximum_drawdown",
    "simple_returns",
    "total_return",
]
