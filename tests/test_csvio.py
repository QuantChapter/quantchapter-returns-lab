"""CSV contracts exercise schema, date order, number validity, and input bounds."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from quantchapter_returns.csvio import read_prices


def write_csv(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "prices.csv"
    path.write_text(text, encoding="utf-8", newline="")
    return path


def test_read_prices_returns_validated_dated_series(tmp_path: Path) -> None:
    path = write_csv(tmp_path, "date,price\n2024-01-02,100\n2024-01-03,110\n2024-01-05,99\n")
    series = read_prices(path)
    assert series.dates == (date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 5))
    assert series.prices == (100.0, 110.0, 99.0)
    assert isinstance(series.dates, tuple)
    assert isinstance(series.prices, tuple)


def test_utf8_bom_and_windows_newlines_are_supported(tmp_path: Path) -> None:
    path = write_csv(
        tmp_path,
        "\ufeffdate,price\r\n2024-02-28,100\r\n2024-02-29,101\r\n2024-03-01,102\r\n",
    )
    series = read_prices(path)
    assert series.dates[1] == date(2024, 2, 29)
    assert series.prices == (100.0, 101.0, 102.0)


def test_quoted_fields_and_scientific_numbers_are_valid(tmp_path: Path) -> None:
    path = write_csv(
        tmp_path,
        'date,price\n"2024-01-01","1e2"\n"2024-01-02","1.1e2"\n"2024-01-03","9.9e1"\n',
    )
    assert read_prices(path).prices == (100.0, 110.0, 99.0)


@pytest.mark.parametrize(
    "header", ["", "price,date", "date,close", "Date,price", "date,price,volume", "date,date"]
)
def test_exact_header_schema_is_required(tmp_path: Path, header: str) -> None:
    path = write_csv(tmp_path, header + "\n2024-01-01,100\n2024-01-02,110\n2024-01-03,99\n")
    with pytest.raises(ValueError):
        read_prices(path)


@pytest.mark.parametrize(
    "body",
    [
        "",
        "2024-01-01,100\n",
        "2024-01-01,100\n2024-01-02,110\n",
    ],
)
def test_at_least_three_prices_are_required(tmp_path: Path, body: str) -> None:
    path = write_csv(tmp_path, "date,price\n" + body)
    with pytest.raises(ValueError):
        read_prices(path)


@pytest.mark.parametrize(
    "bad_date",
    ["2024-1-02", "20240102", "2024-01-02T00:00:00", "2023-02-29", "2024-13-01", "", "2024-W01-2"],
)
def test_dates_must_be_real_iso_calendar_dates(tmp_path: Path, bad_date: str) -> None:
    path = write_csv(tmp_path, f"date,price\n2024-01-01,100\n{bad_date},110\n2024-01-03,99\n")
    with pytest.raises(ValueError):
        read_prices(path)


@pytest.mark.parametrize("middle", ["2024-01-01", "2023-12-31", "2024-01-04"])
def test_dates_must_be_unique_and_strictly_increasing(tmp_path: Path, middle: str) -> None:
    path = write_csv(tmp_path, f"date,price\n2024-01-01,100\n{middle},110\n2024-01-03,99\n")
    with pytest.raises(ValueError):
        read_prices(path)


@pytest.mark.parametrize(
    "price", ["0", "-1", "nan", "NaN", "inf", "-inf", "1e10000", "", "hello", "=1+1"]
)
def test_price_values_must_be_finite_and_positive(tmp_path: Path, price: str) -> None:
    path = write_csv(tmp_path, f"date,price\n2024-01-01,100\n2024-01-02,{price}\n2024-01-03,99\n")
    with pytest.raises(ValueError):
        read_prices(path)


@pytest.mark.parametrize("row", ["2024-01-02", "2024-01-02,110,extra", ",", "", '"2024-01-02,110'])
def test_malformed_and_blank_rows_are_rejected(tmp_path: Path, row: str) -> None:
    path = write_csv(tmp_path, f"date,price\n2024-01-01,100\n{row}\n2024-01-03,99\n")
    with pytest.raises(ValueError):
        read_prices(path)


def test_invalid_utf8_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "invalid.csv"
    path.write_bytes(b"date,price\n2024-01-01,100\n2024-01-02,\xff\n2024-01-03,99\n")
    with pytest.raises((ValueError, UnicodeError)):
        read_prices(path)


def test_missing_file_reports_a_file_error(tmp_path: Path) -> None:
    with pytest.raises((FileNotFoundError, ValueError)):
        read_prices(tmp_path / "missing.csv")


def test_oversized_file_is_rejected_before_parsing(tmp_path: Path) -> None:
    path = tmp_path / "large.csv"
    with path.open("wb") as handle:
        handle.write(b"date,price\n")
        handle.seek(20 * 1024 * 1024)
        handle.write(b"\n")
    with pytest.raises(ValueError):
        read_prices(path)


def test_excess_rows_are_rejected(tmp_path: Path) -> None:
    # A date range long enough to exceed the limit without duplicate-date failure.
    from datetime import timedelta

    path = tmp_path / "many.csv"
    start = date(1700, 1, 1)
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write("date,price\n")
        for index in range(100_001):
            handle.write(f"{start + timedelta(days=index)},100\n")
    with pytest.raises(ValueError):
        read_prices(path)
