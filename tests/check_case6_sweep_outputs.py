#!/usr/bin/env python3
"""Smoke checks for the Case 6 Ti:LiNbO3 W-sweep artifacts."""

from __future__ import annotations

import csv
import math
import sys
from pathlib import Path


EXPECTED_W_VALUES = [5.0, 7.0]


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        raise RuntimeError("usage: check_case6_sweep_outputs.py <sweep_root>")

    sweep_root = Path(argv[1]).resolve()
    consolidated_dir = sweep_root / "consolidated"
    plots_dir = sweep_root / "plots"

    mode_sizes_path = consolidated_dir / "neff_mode_sizes.csv"
    summary_path = consolidated_dir / "consolidation_summary.txt"
    svg_path = plots_dir / "fig7_like_reference.svg"

    expect(mode_sizes_path.exists(), "missing neff_mode_sizes.csv")
    expect(summary_path.exists(), "missing consolidation_summary.txt")
    expect(svg_path.exists(), "missing fig7_like_reference.svg")

    rows = read_csv_rows(mode_sizes_path)
    expect(len(rows) == len(EXPECTED_W_VALUES), "unexpected Case 6 smoke row count")

    w_values = [float(row["W_um"]) for row in rows]
    expect(w_values == EXPECTED_W_VALUES, "unexpected smoke sweep W values")

    neff_values = []
    for row in rows:
        neff = float(row["neff"])
        w_x = float(row["W_x_um"])
        w_y = float(row["W_y_um"])
        expect(math.isfinite(neff) and neff > 2.0, "expected finite positive neff")
        expect(math.isfinite(w_x) and w_x > 0.0, "expected finite positive W_x")
        expect(math.isfinite(w_y) and w_y > 0.0, "expected finite positive W_y")
        neff_values.append(neff)

    expect(neff_values[0] < neff_values[1], "expected monotonic Case 6 neff")

    summary_text = summary_path.read_text(encoding="utf-8")
    expect("delta_x/delta_z ENABLED" in summary_text, "missing gradient-enabled summary")
    expect("FWHM" in summary_text, "missing mode-size extraction summary")

    svg_text = svg_path.read_text(encoding="utf-8")
    expect("Fig. 7" in svg_text or "Ti" in svg_text, "unexpected Case 6 SVG content")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv))
    except Exception as exc:
        print(f"check_case6_sweep_outputs.py failure: {exc}", file=sys.stderr)
        raise
