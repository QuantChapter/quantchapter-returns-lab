"""Public CLI contract, reproducibility, input safety and failure recovery."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from quantchapter_returns.cli import main


@pytest.fixture
def prices(tmp_path: Path) -> Path:
    source = tmp_path / "prices.csv"
    source.write_text(
        "date,price\n2024-01-02,100\n2024-01-03,110\n2024-01-04,99\n", encoding="utf-8"
    )
    return source


def test_stdout_is_deterministic_checked_json(
    prices: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["report", str(prices)]) == 0
    first = capsys.readouterr()
    assert not first.err
    result = json.loads(first.out)
    assert result["schema_version"] == 1
    assert result["input_sha256"] == hashlib.sha256(prices.read_bytes()).hexdigest()
    assert result["observations"] == 3
    assert result["return_observations"] == 2
    assert result["total_return"] == pytest.approx(-0.01)
    assert result["maximum_drawdown"] == pytest.approx(-0.1)
    assert result["annualized_volatility"] == pytest.approx((0.02 * 252) ** 0.5)
    assert result["conventions"]["units"] == "decimal fractions"
    assert main(["report", str(prices)]) == 0
    assert capsys.readouterr().out == first.out


def test_atomic_output_and_explicit_replacement(prices: Path, tmp_path: Path) -> None:
    output = tmp_path / "new" / "report.json"
    assert main(["report", str(prices), "--output", str(output)]) == 0
    original = output.read_bytes()
    assert main(["report", str(prices), "--output", str(output)]) == 2
    assert output.read_bytes() == original
    assert main(["report", str(prices), "--output", str(output), "--force", "--ddof", "0"]) == 0
    assert json.loads(output.read_text())["ddof"] == 0
    assert list(output.parent.iterdir()) == [output]


def test_input_cannot_be_overwritten(prices: Path) -> None:
    original = prices.read_bytes()
    assert main(["report", str(prices), "--output", str(prices), "--force"]) == 2
    assert prices.read_bytes() == original


def test_force_requires_destination(prices: Path) -> None:
    assert main(["report", str(prices), "--force"]) == 2


@pytest.mark.parametrize("arguments", [["--periods-per-year", "0"], ["--periods-per-year", "-1"]])
def test_invalid_frequency_does_not_create_output(
    prices: Path, tmp_path: Path, arguments: list[str]
) -> None:
    output = tmp_path / "report.json"
    assert main(["report", str(prices), "--output", str(output), *arguments]) == 2
    assert not output.exists()


def test_input_errors_are_useful_without_tracebacks(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["report", str(tmp_path / "missing.csv")]) == 2
    captured = capsys.readouterr()
    assert not captured.out
    assert "quantchapter-returns:" in captured.err
    assert "Traceback" not in captured.err


def test_invalid_csv_does_not_replace_previous_output(prices: Path, tmp_path: Path) -> None:
    output = tmp_path / "report.json"
    output.write_text("keep me", encoding="utf-8")
    prices.write_text("invalid", encoding="utf-8")
    assert main(["report", str(prices), "--output", str(output), "--force"]) == 2
    assert output.read_text() == "keep me"


def test_module_entrypoint(prices: Path, tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, "-m", "quantchapter_returns", "report", str(prices)],
        capture_output=True,
        text=True,
        check=False,
        cwd=tmp_path,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["observations"] == 3


def test_version_and_help(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as stopped:
        main(["--version"])
    assert stopped.value.code == 0
    assert "0.1.0" in capsys.readouterr().out
    with pytest.raises(SystemExit) as stopped:
        main(["report", "--help"])
    assert stopped.value.code == 0
    assert "--output" in capsys.readouterr().out


def test_output_failure_cleans_staged_files(prices: Path, tmp_path: Path) -> None:
    output = tmp_path / "directory"
    output.mkdir()
    assert main(["report", str(prices), "--output", str(output)]) == 2
    assert sorted(path.name for path in tmp_path.iterdir()) == ["directory", "prices.csv"]


def test_symlink_destination_is_rejected_if_supported(prices: Path, tmp_path: Path) -> None:
    target = tmp_path / "target.json"
    target.write_text("untouched", encoding="utf-8")
    link = tmp_path / "link.json"
    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip("OS does not permit symlink creation for this account")
    assert main(["report", str(prices), "--output", str(link), "--force"]) == 2
    assert target.read_text() == "untouched"


def test_large_input_is_rejected_without_output(tmp_path: Path) -> None:
    from quantchapter_returns.csvio import MAX_BYTES

    source = tmp_path / "large.csv"
    with source.open("wb") as stream:
        stream.truncate(MAX_BYTES + 1)
    assert main(["report", str(source)]) == 2
