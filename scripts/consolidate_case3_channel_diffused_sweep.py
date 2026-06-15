#!/usr/bin/env python3
"""Consolidate Case 3 sweep outputs into a dispersion-curve CSV.

Reads all V_*/results/neff.csv files found under --sweep-root and computes:

  B = (neff^2 - n2^2) / (n3av^2 - n2^2)

using the normalization from Franco et al. (1999) Fig. 4:
  n2   = 1.44  (background index)
  n3av = 1.47  (average peak index, used only for normalization)
  b    = 1.0 um

Saves consolidated/dispersion_curve.csv with columns:
  V, lambda_um, neff, B
"""

from __future__ import annotations

import argparse
import csv
import math
import re
from pathlib import Path


N2 = 1.44
N3AV = 1.47
B_CORE = 1.0

_DELTA_N_SQ_NORM = N3AV**2 - N2**2  # denominator for B
_DELTA_N_NORM = math.sqrt(_DELTA_N_SQ_NORM)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Consolidate Case 3 channel-diffused-isotropic sweep results "
            "into a single dispersion-curve CSV."
        )
    )
    parser.add_argument(
        "--sweep-root",
        required=True,
        help="Directory produced by run_case3_channel_diffused_sweep.py.",
    )
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
    """Normalised propagation constant B = (neff^2 - n2^2) / (n3av^2 - n2^2)."""
    return (neff**2 - N2**2) / _DELTA_N_SQ_NORM


def wavelength_to_V(lambda_um: float) -> float:
    """Recover V from wavelength: V = 2*b*delta_n / lambda."""
    return 2.0 * B_CORE * _DELTA_N_NORM / lambda_um


def choose_best_mode(rows: list[dict[str, str]]) -> dict[str, str] | None:
    """Pick the guided fundamental mode from neff.csv rows.

    Selection priority:
    1. Rows with status == 'ok' and n2 < neff < n3av (guided by index).
    2. Among those, the one with the highest neff (fundamental mode).
    3. If none are guided, fall back to the highest neff overall.
    """
    valid = [r for r in rows if r.get("status", "").strip() == "ok"]
    if not valid:
        return None

    candidates_with_neff: list[tuple[float, dict[str, str]]] = []
    for row in valid:
        neff = parse_optional_float(row.get("neff", ""))
        if neff is not None:
            candidates_with_neff.append((neff, row))

    if not candidates_with_neff:
        return None

    guided = [(neff, row) for neff, row in candidates_with_neff if N2 < neff < N3AV * 1.01]
    pool = guided if guided else candidates_with_neff
    best_neff, best_row = max(pool, key=lambda t: t[0])
    return best_row


def main() -> None:
    args = parse_args()
    sweep_root = Path(args.sweep_root).resolve()

    if not sweep_root.exists():
        raise FileNotFoundError(f"Sweep root not found: {sweep_root}")

    consolidated_dir = sweep_root / "consolidated"
    consolidated_dir.mkdir(parents=True, exist_ok=True)

    # Discover all V_* subdirectories
    v_dir_pattern = re.compile(r"^V_(\d+\.\d+)$")
    point_dirs = sorted(
        d for d in sweep_root.iterdir()
        if d.is_dir() and v_dir_pattern.match(d.name)
    )

    if not point_dirs:
        print(f"No V_* directories found under {sweep_root}")
        return

    output_rows: list[dict[str, str]] = []
    missing = []
    skipped = []

    for point_dir in point_dirs:
        match = v_dir_pattern.match(point_dir.name)
        v_str = match.group(1)
        v_value = float(v_str)

        neff_csv = point_dir / "results" / "neff.csv"
        if not neff_csv.exists():
            missing.append(point_dir.name)
            continue

        rows = read_csv_rows(neff_csv)
        if not rows:
            skipped.append((point_dir.name, "empty neff.csv"))
            continue

        best = choose_best_mode(rows)
        if best is None:
            skipped.append((point_dir.name, "no valid mode found"))
            continue

        neff = parse_optional_float(best.get("neff", ""))
        if neff is None:
            skipped.append((point_dir.name, "neff not parseable"))
            continue

        lambda_um = 2.0 * B_CORE * _DELTA_N_NORM / v_value
        B_value = compute_B(neff)
        guided = "yes" if N2 < neff < N3AV * 1.01 else "no"

        output_rows.append(
            {
                "V": f"{v_value:.6f}",
                "lambda_um": f"{lambda_um:.9f}",
                "neff": f"{neff:.9f}",
                "B": f"{B_value:.9f}",
                "guided": guided,
                "mode_index": best.get("mode_index", ""),
                "status": best.get("status", ""),
                "point_dir": str(point_dir),
            }
        )

    output_rows.sort(key=lambda r: float(r["V"]))

    out_path = consolidated_dir / "dispersion_curve.csv"
    fieldnames = ["V", "lambda_um", "neff", "B", "guided", "mode_index", "status", "point_dir"]
    with out_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    # Write a brief summary
    summary_lines = [
        "case: Case 3 channel diffused isotropic (circular profile)",
        "normalization: V = (k0 * b / pi) * sqrt(n3av^2 - n2^2)",
        "normalization_B: B = (neff^2 - n2^2) / (n3av^2 - n2^2)",
        f"n2: {N2}",
        f"n3av: {N3AV}",
        f"b: {B_CORE}",
        f"delta_n_norm: {_DELTA_N_NORM:.6f}",
        f"points_found: {len(output_rows)}",
        f"points_missing_neff_csv: {len(missing)}",
        f"points_skipped: {len(skipped)}",
        "note: delta_x/delta_z disabled (T-005); profile treated as isotropic piecewise-varying.",
    ]
    (consolidated_dir / "consolidation_summary.txt").write_text(
        "\n".join(summary_lines) + "\n", encoding="utf-8"
    )

    print(f"Consolidated {len(output_rows)} points -> {out_path}")
    if missing:
        print(f"  Missing neff.csv: {missing}")
    if skipped:
        print(f"  Skipped: {skipped}")

    print("\nDispersion curve points:")
    print(f"  {'V':>8}  {'lambda_um':>12}  {'neff':>12}  {'B':>10}  guided")
    for row in output_rows:
        print(
            f"  {float(row['V']):8.3f}  {float(row['lambda_um']):12.6f}  "
            f"{float(row['neff']):12.8f}  {float(row['B']):10.6f}  {row['guided']}"
        )


if __name__ == "__main__":
    main()
