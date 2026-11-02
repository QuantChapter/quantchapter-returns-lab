"""Execute the shipped tutorials in fresh kernels and validate portable output.

By default, execution is read-only with respect to tracked notebooks. Use
``--write`` to replace them with the freshly executed, sanitized notebooks.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]


def source_digest(notebook: nbformat.NotebookNode) -> str:
    """Bind saved output to portable notebook and package source content."""
    digest = hashlib.sha256()
    digest.update(json.dumps([cell.source for cell in notebook.cells]).encode("utf-8"))
    for path in sorted((ROOT / "src" / "quantchapter_returns").glob("*.py")):
        digest.update(path.name.encode("utf-8"))
        digest.update(path.read_text(encoding="utf-8").replace("\r\n", "\n").encode("utf-8"))
    return digest.hexdigest()


def textual_outputs(notebook: nbformat.NotebookNode) -> list[list[str]]:
    return [
        [
            output.get("text", output.get("data", {}).get("text/plain", ""))
            for output in cell.get("outputs", [])
        ]
        for cell in notebook.cells
        if cell.cell_type == "code"
    ]


def verify(path: Path, *, write: bool) -> None:
    """Run a notebook from an empty kernel, checking outputs and schema."""
    notebook = nbformat.read(path, as_version=4)
    nbformat.validate(notebook)
    original_text = textual_outputs(notebook)
    expected_digest = source_digest(notebook)
    if not write and notebook.metadata.get("quantchapter_source_sha256") != expected_digest:
        raise ValueError(f"Stale saved source/output binding in {path.name}; rerun with --write")
    if not write and not any(
        "image/png" in output.get("data", {})
        for cell in notebook.cells
        for output in cell.get("outputs", [])
    ):
        raise ValueError(f"Missing saved figure in {path.name}; rerun with --write")
    for cell in notebook.cells:
        if cell.cell_type == "code":
            cell.outputs = []
            cell.execution_count = None
        cell.metadata.pop("execution", None)
    client = NotebookClient(
        notebook,
        timeout=120,
        kernel_name="python3",
        allow_errors=False,
        record_timing=False,
        resources={"metadata": {"path": str(ROOT)}},
    )
    client.execute()
    has_figure = False
    for cell in notebook.cells:
        cell.metadata.pop("execution", None)
        if cell.cell_type != "code":
            continue
        if cell.execution_count is None:
            raise ValueError(f"Unexecuted code cell in {path.name}")
        for output in cell.outputs:
            if output.output_type == "error":
                raise ValueError(f"Error output in {path.name}")
            if "image/png" in output.get("data", {}):
                has_figure = True
                output.metadata["image/png"] = {
                    "alt": (
                        "Explanatory synthetic-data figure. Exact input values and the "
                        "calculated results are provided in the adjacent cells and text."
                    )
                }
            # Text and metadata should not disclose the executing machine.
            serialized = json.dumps(output, ensure_ascii=False)
            for private_prefix in ("C:\\\\Users\\\\", "C:/Users/", "/Users/", "/home/"):
                if private_prefix in serialized:
                    raise ValueError(f"Machine-local path in output of {path.name}")
    if not has_figure:
        raise ValueError(f"No rendered explanatory figure in {path.name}")
    notebook.metadata["language_info"] = {"name": "python"}
    notebook.metadata["quantchapter_source_sha256"] = expected_digest
    nbformat.validate(notebook)
    if write:
        nbformat.write(notebook, path)
    elif textual_outputs(notebook) != original_text:
        raise ValueError(f"Saved numerical/text outputs differ in {path.name}; rerun with --write")
    print(f"Executed and validated notebooks/{path.name}")


def main() -> None:
    """Execute the complete shipped notebook set without network data."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Save fresh executed output")
    args = parser.parse_args()
    paths = sorted((ROOT / "notebooks").glob("*.ipynb"))
    if len(paths) != 2:
        raise ValueError("Expected the two documented tutorial notebooks")
    for path in paths:
        verify(path, write=args.write)


if __name__ == "__main__":
    main()
