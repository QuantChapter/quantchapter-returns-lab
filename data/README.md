# Synthetic price observations

`synthetic_prices.csv` contains 261 strictly ordered weekday observations in
arbitrary price units. It is an original teaching fixture, licensed under the
repository's MIT license. It contains no personal or third-party market data.

Run `python tools/generate_data.py --check` to reproduce both the CSV and its
SHA-256 provenance manifest. Omit `--check` to regenerate them. The generator
uses specified integer arithmetic, a fixed seed, six decimal places and three
engineered shocks. It does not depend on platform-specific random streams.

Weekends are excluded; exchange holidays are not modelled. A frequency of 252
returns per year is an illustrative convention supplied to the analysis, not
something verified by these dates. The shocks are deliberately chosen to make
drawdowns visible. This construction is neither a calibrated market model nor
evidence of trading performance. Dividends, fees, taxes, cash flows and currency
conversion are absent.
