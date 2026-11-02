"""Strict, bounded input: a single positive price series and explicit dates."""

from __future__ import annotations

import csv
import io
import os
import re
import stat
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .metrics import _positive

MAX_BYTES = 20 * 1024 * 1024
MAX_ROWS = 100_000


@dataclass(frozen=True)
class PriceSeries:
    """Validated immutable observations in strictly increasing date order."""

    dates: tuple[date, ...]
    prices: tuple[float, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.dates, tuple) or not isinstance(self.prices, tuple):
            raise ValueError("dates and prices must be tuples")
        if len(self.dates) != len(self.prices):
            raise ValueError("dates and prices must have matching lengths")
        _positive(self.prices, "prices", 3)
        if any(type(value) is not date for value in self.dates):
            raise ValueError("dates must contain date objects, excluding datetime")
        if any(left >= right for left, right in zip(self.dates, self.dates[1:], strict=False)):
            raise ValueError("dates must be strictly increasing and unique")


def _read_snapshot(path: str | Path) -> bytes:
    """Bound actual bytes, not just a racy size check; reject devices and pipes."""
    source = Path(path)
    if not source.is_file():
        raise ValueError("input must be a regular CSV file")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NONBLOCK", 0)
    descriptor = os.open(source, flags)
    with os.fdopen(descriptor, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError("input must be a regular CSV file")
        snapshot = stream.read(MAX_BYTES + 1)
    if len(snapshot) > MAX_BYTES:
        raise ValueError("CSV exceeds the 20 MiB input limit")
    return snapshot


def _parse_prices(snapshot: bytes) -> PriceSeries:
    dates: list[date] = []
    prices: list[float] = []
    try:
        with io.StringIO(snapshot.decode("utf-8-sig"), newline="") as stream:
            reader = csv.reader(stream, strict=True)
            if next(reader, None) != ["date", "price"]:
                raise ValueError("CSV header must be exactly date,price")
            for row in reader:
                line = reader.line_num
                if len(dates) >= MAX_ROWS:
                    raise ValueError("CSV exceeds the 100,000 observation limit")
                if len(row) != 2 or not row[1] or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", row[0]):
                    raise ValueError(f"CSV line {line}: expected YYYY-MM-DD and one price")
                try:
                    observed = date.fromisoformat(row[0])
                    price = float(row[1])
                except ValueError as exc:
                    raise ValueError(f"CSV line {line}: invalid date or numeric price") from exc
                _positive((price,), f"CSV line {line} price")
                if dates and observed <= dates[-1]:
                    raise ValueError(
                        f"CSV line {line}: dates must be strictly increasing and unique"
                    )
                dates.append(observed)
                prices.append(price)
    except (csv.Error, UnicodeError) as exc:
        raise ValueError("input must be a well-formed UTF-8 CSV") from exc
    return PriceSeries(tuple(dates), tuple(prices))


def read_prices(path: str | Path) -> PriceSeries:
    """Read UTF-8 CSV with exact date,price columns and at least three rows.

    ISO dates must use YYYY-MM-DD. Missing cells, duplicate/out-of-order dates,
    non-finite/non-positive prices, blank records and extra columns fail. No
    sorting or imputation is performed. Limit: 20 MiB and 100,000 observations.
    An optional UTF-8 BOM is accepted. Quoted fields follow strict CSV syntax.
    The complete bounded input snapshot is parsed, preserving its exact bytes.
    """
    return _parse_prices(_read_snapshot(path))
