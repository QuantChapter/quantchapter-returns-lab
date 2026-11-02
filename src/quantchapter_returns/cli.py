"""Offline command line report with an explicit, versioned JSON contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path

from . import __version__, annualized_volatility, maximum_drawdown, simple_returns, total_return
from .csvio import _parse_prices, _read_snapshot


def _write_report(destination: Path, content: str, *, force: bool) -> None:
    """Stage output in the same filesystem; never follow an existing symlink.

    The default hard-link publication is atomic and refuses overwrite, including
    races. Explicit --force uses atomic replacement. Failure retains old output.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_symlink():
        raise ValueError("output must not be a symbolic link")
    staged: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n", dir=destination.parent, delete=False
        ) as stream:
            staged = Path(stream.name)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if force:
            os.replace(staged, destination)
        else:
            os.link(staged, destination)
    finally:
        if staged is not None:
            staged.unlink(missing_ok=True)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI. Return 0 on success and 2 for input or output errors."""
    parser = argparse.ArgumentParser(
        prog="quantchapter-returns",
        description=(
            "Offline educational price-return statistics. No forecasting or live market data."
        ),
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)
    report = commands.add_parser("report", help="validate dated prices and produce JSON")
    report.add_argument("input", type=Path, help="UTF-8 CSV with exact date,price columns")
    report.add_argument("--periods-per-year", type=int, default=252)
    report.add_argument("--ddof", type=int, choices=(0, 1), default=1)
    report.add_argument("--output", type=Path, help="write JSON atomically; default is stdout")
    report.add_argument(
        "--force", action="store_true", help="replace an existing output atomically"
    )
    args = parser.parse_args(argv)
    try:
        if args.force and args.output is None:
            raise ValueError("--force requires --output")
        if args.output is not None and args.input.resolve() == args.output.resolve():
            raise ValueError("output must differ from input")
        # The digest and the calculation consume exactly the same bounded bytes.
        snapshot = _read_snapshot(args.input)
        series = _parse_prices(snapshot)
        returns = simple_returns(series.prices)
        result = {
            "schema_version": 1,
            "package_version": __version__,
            "input_sha256": hashlib.sha256(snapshot).hexdigest(),
            "observations": len(series.prices),
            "return_observations": len(returns),
            "first_date": series.dates[0].isoformat(),
            "last_date": series.dates[-1].isoformat(),
            "periods_per_year": args.periods_per_year,
            "ddof": args.ddof,
            "total_return": total_return(series.prices),
            "annualized_volatility": annualized_volatility(
                returns, periods_per_year=args.periods_per_year, ddof=args.ddof
            ),
            "maximum_drawdown": maximum_drawdown(series.prices),
            "conventions": {
                "units": "decimal fractions",
                "return_type": "price-only simple returns",
                "drawdown_sign": "nonpositive",
                "frequency": "caller-supplied; calendar regularity is not inferred",
                "excludes": ["dividends", "fees", "taxes", "cash flows", "currency conversion"],
                "purpose": "educational descriptive analysis; not a forecast or investment advice",
            },
        }
        content = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
        if args.output is None:
            sys.stdout.write(content)
        else:
            _write_report(args.output, content, force=args.force)
    except (OSError, ValueError) as exc:
        print(f"quantchapter-returns: {exc}", file=sys.stderr)
        return 2
    return 0
