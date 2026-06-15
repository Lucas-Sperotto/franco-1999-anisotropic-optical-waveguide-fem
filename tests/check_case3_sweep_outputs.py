#!/usr/bin/env python3
"""Smoke checks for the Case 3 channel-diffused sweep artifacts."""

from __future__ import annotations

import csv
import math
import sys
from pathlib import Path


EXPECTED_V_VALUES = [2.0, 4.0]


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        raise RuntimeError("usage: check_case3_sweep_outputs.py <sweep_root>")

    sweep_root = Path(argv[1]).resolve()
    consolidated_dir = sweep_root / "consolidated"
    plots_dir = sweep_root / "plots"

    expect(
        (consolidated_dir / "dispersion_curve.csv").exists(),
        "missing dispersion_curve.csv",
    )
    expect(
        (consolidated_dir / "consolidation_summary.txt").exists(),
        "missing consolidation_summary.txt",
    )
    expect(
        (plots_dir / "fig4_like_reference.svg").exists(),
        "missing fig4_like_reference.svg",
    )

    rows = read_csv_rows(consolidated_dir / "dispersion_curve.csv")
    expect(len(rows) == len(EXPECTED_V_VALUES), "unexpected row count in dispersion curve")

    v_values = [float(row["V"]) for row in rows]
    expect(v_values == EXPECTED_V_VALUES, "unexpected smoke sweep V values")

    for row in rows:
        expect(row["status"] == "ok", "expected ok status in Case 3 smoke sweep")
        expect(row["guided"] == "yes", "expected guided marker in Case 3 smoke sweep")
        neff = float(row["neff"])
        normalized_beta = float(row["B"])
        expect(math.isfinite(neff) and neff > 0.0, "expected finite positive neff")
        expect(math.isfinite(normalized_beta), "expected finite normalized B")

    summary_text = (consolidated_dir / "consolidation_summary.txt").read_text(
        encoding="utf-8"
    )
    expect("delta_x/delta_z disabled" in summary_text, "missing T-005 limitation summary")

    svg_text = (plots_dir / "fig4_like_reference.svg").read_text(encoding="utf-8")
    expect("T-005" in svg_text, "missing T-005 limitation note in SVG")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv))
    except Exception as exc:
        print(f"check_case3_sweep_outputs.py failure: {exc}", file=sys.stderr)
        raise
