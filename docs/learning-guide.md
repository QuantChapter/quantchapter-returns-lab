# Learn with Returns Lab

Start here if you know basic Python arithmetic and lists, and want to connect
the code with the mathematics. The tutorials are small, authored educational
examples with checked calculations. They have not been piloted with learners.

## Prepare a working environment

Clone the repository and enter its directory. With a supported Python version
and [uv](https://docs.astral.sh/uv/) installed:

```console
uv sync --extra notebooks
uv run --extra notebooks python tools/verify_notebooks.py
```

The second command runs both notebooks from clean kernels. To read and edit
them, open the `notebooks` directory in a Jupyter-capable editor and select the
project's `.venv` interpreter. This repository includes the kernel dependencies;
it does not require a particular notebook editor. If you prefer a browser-based
Jupyter interface, install your chosen interface separately in that environment.

Without uv, create a virtual environment, activate it using your operating
system's normal command, and install from the checkout:

```console
python -m pip install ".[notebooks]"
python tools/verify_notebooks.py
```

Do not mix a system kernel with packages installed in another environment.
An `ImportError` usually means the selected kernel is not that environment.

## Follow the connected examples

1. [Prices, returns and growth](../notebooks/01_prices_returns_growth.ipynb)
   starts with four invented prices. It explains each denominator, reconstructs
   the path by compounding, and then uses logarithms to express the same growth
   additively. A fresh gain-and-loss case checks the distinction.
2. [Drawdown and volatility](../notebooks/02_drawdown_and_volatility.ipynb)
   separates endpoint performance, distance below a prior peak and variation
   around a mean. It derives the sample calculation and states what annualized
   scaling assumes. A new path and a flat path expose different boundary cases.

Read each worked comparison after making the requested choice. These local
checks have no grades, accounts or completion credit. Assertions check program
outputs; they do not establish learner understanding.

## Run the complete CSV example

The bundled `data/synthetic_prices.csv` contains an invented weekday price
series. Its provenance and regeneration rules are recorded beside the data.
From the repository root, use the report command documented in the
[README](../README.md). The command validates the file before calculating
statistics; it does not silently repair data.

To produce a static figure from the same validated observations:

```console
uv run --extra plot python examples/plot_report.py
```

This writes `artifacts/returns-report.png` and prints the observation count,
dates, total price return and signed maximum drawdown. Reruns preserve existing
output unless you choose another `--output` path or explicitly use `--force`.
The upper panel shows growth of one starting unit; the lower panel shows loss
relative to the running peak. Its displayed dates are observation dates, not a
verified exchange calendar.

## Bring your own series deliberately

Use an exact `date,price` header and one strictly positive finite price per
unique, ascending ISO date. Validate what each price actually means before
comparing results: currency, adjustments, dividends, sampling frequency and
cash flows all affect interpretation. The reader cannot establish those facts
from two columns. Never place account data or personal information in a public
issue or contributed fixture.

Consult the [mathematical conventions](mathematics.md) for return units,
drawdown signs, `ddof`, annualization and numerical limits. The
[API reference](api.md) explains individual functions.

## A final retrieval check

A synthetic path is $40,50,40,54$. Choose its total return and maximum drawdown:
(A) 35% and -20%, (B) 40% and -20%, or (C) 35% and 0%.

**Worked comparison:** A is correct. The endpoint return is $54/40-1=35\%$.
The running peaks are $40,50,50,54$, so drawdowns are $0,0,-20\%,0$.
The adjacent returns are $25\%,-20\%,35\%$; their sum is 40%, which produces B's
incorrect endpoint return. Compounding $1.25\times0.80\times1.35=1.35$ supplies
the valid calculation. C ignores the intermediate fall.
