#!/usr/bin/env python3
"""Smoke checks for the Case 5 APE LiNbO3 sweep artifacts."""

from __future__ import annotations

import csv
import math
import sys
from pathlib import Path


EXPECTED_T_VALUES = [1.0, 4.0]


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        raise RuntimeError("usage: check_case5_sweep_outputs.py <sweep_root>")

    sweep_root = Path(argv[1]).resolve()
    consolidated_dir = sweep_root / "consolidated"
    plots_dir = sweep_root / "plots"

    dispersion_path = consolidated_dir / "dispersion_curve.csv"
    summary_path = consolidated_dir / "consolidation_summary.txt"
    svg_path = plots_dir / "fig6_like_reference.svg"

    expect(dispersion_path.exists(), "missing dispersion_curve.csv")
    expect(summary_path.exists(), "missing consolidation_summary.txt")
    expect(svg_path.exists(), "missing fig6_like_reference.svg")

    rows = read_csv_rows(dispersion_path)
    expect(rows, "empty Case 5 dispersion curve")

    t_values = sorted({float(row["t_h"]) for row in rows})
    expect(t_values == EXPECTED_T_VALUES, "unexpected smoke sweep anneal times")

    mode1_rows = sorted(
        (row for row in rows if row["mode_index"] == "1"),
        key=lambda row: float(row["t_h"]),
    )
    expect(len(mode1_rows) == len(EXPECTED_T_VALUES), "missing Case 5 mode-1 rows")

    beta_values = []
    for row in mode1_rows:
        v_value = float(row["V"])
        neff = float(row["neff"])
        normalized_beta = float(row["B"])
        expect(math.isfinite(v_value) and v_value > 0.0, "expected finite positive V")
        expect(math.isfinite(neff) and neff > 2.20, "expected guided APE neff")
        expect(0.0 <= normalized_beta <= 1.1, "expected normalized B near [0, 1]")
        beta_values.append(normalized_beta)

    expect(beta_values[0] < beta_values[1], "expected monotonic Case 5 mode-1 B")

    summary_text = summary_path.read_text(encoding="utf-8")
    expect("ape_diffusion_preprocessor.py" in summary_text, "missing APE preprocessor note")
    expect("delta_x/delta_z ENABLED" in summary_text, "missing gradient-enabled summary")

    svg_text = svg_path.read_text(encoding="utf-8")
    expect("Fig. 6" in svg_text or "APE" in svg_text, "unexpected Case 5 SVG content")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv))
    except Exception as exc:
        print(f"check_case5_sweep_outputs.py failure: {exc}", file=sys.stderr)
        raise
