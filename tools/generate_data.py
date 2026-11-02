"""Generate the public teaching fixture using only deterministic integer arithmetic."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = 982451653


def generate() -> tuple[bytes, bytes]:
    """Return exact CSV and provenance bytes, independent of random/math libraries."""
    state = SEED
    price_microunits = 100_000_000
    observed = date(2024, 1, 2)
    rows = ["date,price"]
    for index in range(261):
        if index:
            state = (1664525 * state + 1013904223) % (2**32)
            basis_points = (state % 361) - 180 + 4
            basis_points = {80: -1100, 81: -600, 170: 800}.get(index, basis_points)
            price_microunits = price_microunits * (10_000 + basis_points) // 10_000
        whole, fraction = divmod(price_microunits, 1_000_000)
        rows.append(f"{observed.isoformat()},{whole}.{fraction:06d}")
        observed += timedelta(days=1)
        while observed.weekday() >= 5:
            observed += timedelta(days=1)
    csv_bytes = ("\n".join(rows) + "\n").encode("utf-8")
    provenance = {
        "schema_version": 1,
        "dataset": "synthetic_prices.csv",
        "sha256": hashlib.sha256(csv_bytes).hexdigest(),
        "observations": 261,
        "generator": "tools/generate_data.py",
        "algorithm": "32-bit LCG, integer basis-point moves, floor to six decimal places",
        "seed": SEED,
        "initial_price": "100.000000",
        "stress_moves_basis_points": {"80": -1100, "81": -600, "170": 800},
        "dates": "Weekdays from 2024-01-02; ignores exchange holidays",
        "currency": "arbitrary teaching units",
        "source": "Original synthetic teaching data authored for QuantChapter Returns Lab",
        "license": "MIT",
        "limitations": (
            "Not observed market prices or investment results. The engineered shocks and "
            "pseudo-random moves are a teaching construction, not a calibrated financial model."
        ),
    }
    return csv_bytes, (json.dumps(provenance, indent=2, sort_keys=True) + "\n").encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="verify checked-in bytes without writing"
    )
    args = parser.parse_args()
    csv_bytes, provenance_bytes = generate()
    for name, content in (
        ("synthetic_prices.csv", csv_bytes),
        ("provenance.json", provenance_bytes),
    ):
        path = ROOT / "data" / name
        if args.check:
            if not path.is_file() or path.read_bytes() != content:
                raise SystemExit(f"Reproducibility check failed: data/{name}")
        else:
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(content)
    print("Synthetic CSV and provenance reproduce exactly.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
