"""Immutable series contracts and consequential filesystem failure behavior."""

from __future__ import annotations

import math
import os
import runpy
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pytest

from quantchapter_returns import annualized_volatility, simple_returns
from quantchapter_returns.cli import main
from quantchapter_returns.csvio import PriceSeries, read_prices


@pytest.mark.parametrize(
    ("dates", "prices"),
    [
        ([date(2024, 1, 1)] * 3, (1, 2, 3)),
        ((date(2024, 1, 1),), (1, 2, 3)),
        ((datetime(2024, 1, 1),) * 3, (1, 2, 3)),
        ((date(2024, 1, 1),) * 3, (1, 2, 3)),
        ((date(2024, 1, 1), date(2024, 1, 2), date(2024, 1, 3)), [1, 2, 3]),
    ],
)
def test_series_rejects_mutable_or_inconsistent_inputs(dates: Any, prices: Any) -> None:
    with pytest.raises(ValueError):
        PriceSeries(dates, prices)


@pytest.mark.parametrize("invalid", [None, "100,110", [1, 10**1000]])
def test_bad_container_and_unrepresentable_integer_are_rejected(invalid: Any) -> None:
    with pytest.raises(ValueError):
        simple_returns(invalid)


def test_volatility_cannot_silently_overflow() -> None:
    with pytest.raises(ValueError):
        annualized_volatility([0, 1e308], periods_per_year=252)


def test_module_version_entrypoint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.argv", ["quantchapter_returns", "--version"])
    with pytest.raises(SystemExit) as stopped:
        runpy.run_module("quantchapter_returns", run_name="__main__")
    assert stopped.value.code == 0


def test_failed_disk_flush_preserves_old_output_and_cleans_up(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "prices.csv"
    source.write_text("date,price\n2024-01-01,100\n2024-01-02,110\n2024-01-03,99\n")
    output = tmp_path / "report.json"
    output.write_text("previous successful report")

    def full_disk(descriptor: int) -> None:
        raise OSError("simulated disk flush failure")

    monkeypatch.setattr(os, "fsync", full_disk)
    assert main(["report", str(source), "--output", str(output), "--force"]) == 2
    assert output.read_text() == "previous successful report"
    assert sorted(path.name for path in tmp_path.iterdir()) == ["prices.csv", "report.json"]


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="POSIX named pipes only")
def test_named_pipe_is_rejected_without_waiting_for_writer(tmp_path: Path) -> None:
    source = tmp_path / "pipe.csv"
    os.mkfifo(source)
    with pytest.raises(ValueError, match="regular"):
        read_prices(source)
    assert main(["report", str(source)]) == 2


def test_drawdown_rounds_tiny_peak_ratio_explicitly() -> None:
    from quantchapter_returns import drawdowns

    assert drawdowns([1e300, 1e-300]) == (0, -1)
    assert all(math.isfinite(value) for value in drawdowns([1e300, 1e-300]))
