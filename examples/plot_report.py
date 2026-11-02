"""Render a static, reproducible price/growth/drawdown teaching figure."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import PercentFormatter  # noqa: E402

from quantchapter_returns import (  # noqa: E402
    cumulative_growth,
    drawdowns,
    maximum_drawdown,
    simple_returns,
    total_return,
)
from quantchapter_returns.csvio import read_prices  # noqa: E402


def main() -> None:
    """Plot the same validated observations used by the report command."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, nargs="?", default=Path("data/synthetic_prices.csv"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/returns-report.png"))
    parser.add_argument("--force", action="store_true", help="Replace an existing figure")
    args = parser.parse_args()
    if args.output.exists() and not args.force:
        parser.error("output already exists; choose another path or pass --force")
    series = read_prices(args.input)
    growth = cumulative_growth(simple_returns(series.prices))
    declines = drawdowns(series.prices)
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 11,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )
    fig, (growth_ax, drawdown_ax) = plt.subplots(
        2, 1, figsize=(10, 6.4), sharex=True, layout="constrained"
    )
    fig.suptitle("QuantChapter Returns Lab | Supplied price path", fontsize=15, x=0.06, ha="left")
    growth_ax.plot(series.dates, growth, color="#215b8f", linewidth=1.8)
    growth_ax.axhline(1, color="#555555", linestyle="--", linewidth=1)
    growth_ax.set(ylabel="Wealth / initial wealth", title="Compounded growth of one starting unit")
    drawdown_ax.plot(series.dates, declines, color="#215b8f", linewidth=1.8)
    drawdown_ax.fill_between(series.dates, declines, 0, color="#215b8f", alpha=0.12)
    drawdown_ax.axhline(0, color="#555555", linewidth=1)
    drawdown_ax.set(ylabel="Drawdown from running peak", xlabel="Observation date")
    drawdown_ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    # The exact first and last dates remain visible regardless of auto-tick choice.
    import matplotlib.dates as mdates

    middle_ticks = [
        tick
        for tick in drawdown_ax.get_xticks()
        if mdates.date2num(series.dates[0]) < tick < mdates.date2num(series.dates[-1])
    ]
    ticks = [mdates.date2num(series.dates[0]), *middle_ticks, mdates.date2num(series.dates[-1])]
    drawdown_ax.set_xticks(ticks)
    drawdown_ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b %Y"))
    for axis in (growth_ax, drawdown_ax):
        axis.grid(axis="y", color="#dedede", linewidth=0.7)
    fig.supxlabel(
        "Supplied observations. Price returns exclude dividends, fees, taxes and cash flows.",
        fontsize=9,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=160, metadata={"Software": "QuantChapter Returns Lab"})
    plt.close(fig)
    print(f"Saved {args.output.name}")
    print(f"Observations: {len(series.prices)}; period: {series.dates[0]} to {series.dates[-1]}")
    print(f"Total price return: {total_return(series.prices):.6%}")
    print(f"Maximum drawdown (signed): {maximum_drawdown(series.prices):.6%}")


if __name__ == "__main__":
    main()
