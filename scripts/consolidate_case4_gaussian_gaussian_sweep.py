#!/usr/bin/env python3
"""Consolidate Case 4 sweep outputs into a dispersion-curve CSV.

Reads V_*/results/neff.csv files and computes:

  B = (neff^2 - n2^2) / (n3m^2 - n2^2)

with n2 = sqrt(2.1), n3m = 1.05*sqrt(2.1), b = 1.0 um  (Franco 1999 Fig. 5).

Saves consolidated/dispersion_curve.csv with columns: V, lambda_um, neff, B, mode_index, ...
"""

from __future__ import annotations

import argparse
import csv
import math
import re
from pathlib import Path


N2 = math.sqrt(2.1)
N3M = 1.05 * math.sqrt(2.1)
B_CORE = 1.0

_DELTA_N_SQ_NORM = N3M**2 - N2**2
_DELTA_N_NORM = math.sqrt(_DELTA_N_SQ_NORM)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Consolidate Case 4 Gaussian-Gaussian sweep results into a dispersion CSV."
    )
    parser.add_argument("--sweep-root", required=True)
    return parser.parse_args()


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def parse_optional_float(raw: str) -> float | None:
    value = raw.strip()
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def compute_B(neff: float) -> float:
    return (neff**2 - N2**2) / _DELTA_N_SQ_NORM


def choose_modes(rows: list[dict[str, str]]) -> list[tuple[int, float]]:
    """Return list of (mode_index, neff) pairs for all valid guided modes."""
    result = []
    for row in rows:
        if row.get("status", "").strip() != "ok":
            continue
        neff = parse_optional_float(row.get("neff", ""))
        if neff is None:
            continue
        guided = N2 < neff < N3M * 1.01
        if guided:
            idx = int(row.get("mode_index", 0))
            result.append((idx, neff))
    result.sort(key=lambda t: -t[1])
    return result


def main() -> None:
    args = parse_args()
    sweep_root = Path(args.sweep_root).resolve()
    if not sweep_root.exists():
        raise FileNotFoundError(f"Sweep root not found: {sweep_root}")

    consolidated_dir = sweep_root / "consolidated"
    consolidated_dir.mkdir(parents=True, exist_ok=True)

    v_dir_pattern = re.compile(r"^V_(\d+\.\d+)$")
    point_dirs = sorted(
        d for d in sweep_root.iterdir()
        if d.is_dir() and v_dir_pattern.match(d.name)
    )

    if not point_dirs:
        print(f"No V_* directories found under {sweep_root}")
        return

    # Collect rows: one per (V, mode) pair
    output_rows: list[dict[str, str]] = []
    missing = []
    skipped = []

    for point_dir in point_dirs:
        match = v_dir_pattern.match(point_dir.name)
        v_value = float(match.group(1))

        neff_csv = point_dir / "results" / "neff.csv"
        if not neff_csv.exists():
            missing.append(point_dir.name)
            continue

        rows = read_csv_rows(neff_csv)
        if not rows:
            skipped.append((point_dir.name, "empty neff.csv"))
            continue

        modes = choose_modes(rows)
        if not modes:
            skipped.append((point_dir.name, "no guided modes"))
            continue

        lambda_um = 2.0 * B_CORE * _DELTA_N_NORM / v_value

        for mode_idx, neff in modes:
            output_rows.append({
                "V": f"{v_value:.6f}",
                "lambda_um": f"{lambda_um:.9f}",
                "neff": f"{neff:.9f}",
                "B": f"{compute_B(neff):.9f}",
                "mode_index": str(mode_idx),
                "point_dir": str(point_dir),
            })

    output_rows.sort(key=lambda r: (int(r["mode_index"]), float(r["V"])))

    out_path = consolidated_dir / "dispersion_curve.csv"
    fieldnames = ["V", "lambda_um", "neff", "B", "mode_index", "point_dir"]
    with out_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    summary_lines = [
        "case: Case 4 channel diffused isotropic Gaussian-Gaussian",
        "normalization_V: V = (k0 * b / pi) * sqrt(n3m^2 - n2^2)",
        "normalization_B: B = (neff^2 - n2^2) / (n3m^2 - n2^2)",
        f"n2: {N2:.12f}",
        f"n3m: {N3M:.12f}",
        f"b: {B_CORE}",
        f"delta_n_norm: {_DELTA_N_NORM:.9f}",
        f"points_found: {len(set(r['V'] for r in output_rows))}",
        f"mode_rows_total: {len(output_rows)}",
        f"points_missing_neff_csv: {len(missing)}",
        f"points_skipped: {len(skipped)}",
        "note: delta_x/delta_z ENABLED (T-008 audit passed).",
    ]
    (consolidated_dir / "consolidation_summary.txt").write_text(
        "\n".join(summary_lines) + "\n", encoding="utf-8"
    )

    print(f"Consolidated {len(output_rows)} mode-points -> {out_path}")
    if missing:
        print(f"  Missing neff.csv: {missing}")
    if skipped:
        print(f"  Skipped: {skipped}")

    print("\nDispersion curve (mode 1 only):")
    print(f"  {'V':>8}  {'lambda_um':>12}  {'neff':>12}  {'B':>10}")
    for row in sorted(output_rows, key=lambda r: float(r["V"])):
        if row["mode_index"] == "1":
            print(
                f"  {float(row['V']):8.3f}  {float(row['lambda_um']):12.6f}  "
                f"{float(row['neff']):12.8f}  {float(row['B']):10.6f}"
            )


if __name__ == "__main__":
    main()
