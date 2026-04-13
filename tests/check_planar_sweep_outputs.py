#!/usr/bin/env python3
"""Check the expected artifacts of the planar diffuse sweep smoke run."""

from __future__ import annotations

import csv
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: check_planar_sweep_outputs.py <sweep_root>")

    sweep_root = Path(sys.argv[1]).resolve()
    required_files = [
        sweep_root / "sweep_parameters.txt",
        sweep_root / "study_manifest.csv",
        sweep_root / "point_manifest.csv",
        sweep_root / "consolidated" / "consolidated_modes.csv",
        sweep_root / "consolidated" / "reference_dispersion.csv",
        sweep_root / "consolidated" / "availability_summary.csv",
        sweep_root / "plots" / "fig2_like_reference.svg",
        sweep_root / "plots" / "mode1_sensitivity.svg",
    ]

    for required_file in required_files:
        if not required_file.exists():
            raise SystemExit(f"Missing expected sweep artifact: {required_file}")

    with (sweep_root / "consolidated" / "reference_dispersion.csv").open(
        "r", encoding="utf-8", newline=""
    ) as stream:
        rows = list(csv.DictReader(stream))

    available_modes = {
        int(row["mode_index"])
        for row in rows
        if row["status"] == "ok" and row["mode_index"]
    }
    if not {1, 2, 3}.issubset(available_modes):
        raise SystemExit(
            "The reference dispersion output does not contain modes 1, 2 and 3"
        )

    with (sweep_root / "consolidated" / "availability_summary.csv").open(
        "r", encoding="utf-8", newline=""
    ) as stream:
        availability_rows = list(csv.DictReader(stream))

    if not any(row["has_modes_1_2_3"] == "yes" for row in availability_rows):
        raise SystemExit(
            "No sweep point reported the simultaneous availability of modes 1, 2 and 3"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
