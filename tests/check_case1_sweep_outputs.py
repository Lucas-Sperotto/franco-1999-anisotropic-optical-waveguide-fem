#!/usr/bin/env python3
"""Smoke checks for the Case 1 homogeneous-channel sweep artifacts."""

from __future__ import annotations

import csv
import sys
from pathlib import Path


EXPECTED_FREQUENCIES = [1.2, 2.0, 4.0]


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        raise RuntimeError("usage: check_case1_sweep_outputs.py <sweep_root>")

    sweep_root = Path(argv[1]).resolve()
    consolidated_dir = sweep_root / "consolidated"
    plots_dir = sweep_root / "plots"

    expect((sweep_root / "study_manifest.csv").exists(), "missing study_manifest.csv")
    expect((sweep_root / "point_manifest.csv").exists(), "missing point_manifest.csv")
    expect((sweep_root / "sweep_parameters.txt").exists(), "missing sweep_parameters.txt")
    expect(
        (consolidated_dir / "consolidated_curve.csv").exists(),
        "missing consolidated_curve.csv",
    )
    expect(
        (consolidated_dir / "reference_dispersion.csv").exists(),
        "missing reference_dispersion.csv",
    )
    expect(
        (plots_dir / "fig1_like_reference.svg").exists(),
        "missing fig1_like_reference.svg",
    )

    rows = read_csv_rows(consolidated_dir / "reference_dispersion.csv")
    expect(len(rows) == len(EXPECTED_FREQUENCIES), "unexpected row count in reference dispersion")

    frequencies = [float(row["normalized_frequency"]) for row in rows]
    expect(frequencies == EXPECTED_FREQUENCIES, "unexpected smoke sweep frequencies")

    beta_values = []
    for row in rows:
        expect(row["status"] == "ok", "expected ok status in smoke sweep")
        expect(row["guided"] == "yes", "expected guided mode in smoke sweep")
        beta_value = float(row["normalized_beta"])
        expect(0.0 <= beta_value <= 1.0, "expected normalized beta in [0, 1]")
        beta_values.append(beta_value)

    expect(beta_values[0] < beta_values[1] < beta_values[2], "expected monotonic beta growth")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv))
    except Exception as exc:
        print(f"check_case1_sweep_outputs.py failure: {exc}", file=sys.stderr)
        raise
