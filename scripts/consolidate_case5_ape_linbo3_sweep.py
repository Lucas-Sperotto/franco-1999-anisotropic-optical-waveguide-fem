#!/usr/bin/env python3
"""Consolidate Case 5 (APE LiNbO3) sweep outputs into a dispersion-curve CSV.

Reads T_*/results/neff.csv files produced by run_case5_ape_linbo3_sweep.py and computes:
  V = (2 * dy / lambda) * NA
  B = (neff^2 - ne_s^2) / (ne_max^2 - ne_s^2)
"""

from __future__ import annotations

import argparse
import csv
import math
import re
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ape_diffusion_preprocessor import (
    ApePhysicalParameters,
    compute_ape_gaussian_approximation,
)


DA_X = 0.92
DA_Z = 0.77
LAMBDA_UM = 0.6328
NE_S = 2.20
DELTA_NE = 0.12
NO_S = 2.20

_NE_MAX = NE_S + DELTA_NE * (1.0 - math.exp(-11.0))
_NA_SQ = _NE_MAX**2 - NE_S**2
_NA = math.sqrt(_NA_SQ)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Consolidate Case 5 APE LiNbO3 sweep into dispersion CSV."
    )
    parser.add_argument("--sweep-root", required=True)
    return parser.parse_args()


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def parse_optional_float(raw: str) -> float | None:
    v = raw.strip()
    if not v:
        return None
    try:
        return float(v)
    except ValueError:
        return None


def compute_V(t_h: float) -> float:
    dy = 2.0 * math.sqrt(DA_Z * t_h)
    return (2.0 * dy / LAMBDA_UM) * _NA


def compute_B(neff: float) -> float:
    return (neff**2 - NE_S**2) / _NA_SQ


def main() -> None:
    args = parse_args()
    sweep_root = Path(args.sweep_root).resolve()
    if not sweep_root.exists():
        raise FileNotFoundError(f"Sweep root not found: {sweep_root}")

    consolidated_dir = sweep_root / "consolidated"
    consolidated_dir.mkdir(parents=True, exist_ok=True)

    t_dir_pattern = re.compile(r"^T_(\d+\.\d+)h$")
    point_dirs = sorted(
        d for d in sweep_root.iterdir()
        if d.is_dir() and t_dir_pattern.match(d.name)
    )

    if not point_dirs:
        print(f"No T_*h directories found under {sweep_root}")
        return

    output_rows: list[dict[str, str]] = []
    missing = []
    skipped = []

    for point_dir in point_dirs:
        match = t_dir_pattern.match(point_dir.name)
        t_h = float(match.group(1))
        v = compute_V(t_h)

        params = ApePhysicalParameters(Da_x_um2_per_h=DA_X, Da_z_um2_per_h=DA_Z,
                                       t_anneal_h=t_h, peak_concentration=1.0)
        approx = compute_ape_gaussian_approximation(params)

        neff_csv = point_dir / "results" / "neff.csv"
        if not neff_csv.exists():
            missing.append(point_dir.name)
            continue

        rows = read_csv_rows(neff_csv)
        if not rows:
            skipped.append((point_dir.name, "empty neff.csv"))
            continue

        for row in rows:
            if row.get("status", "").strip() != "ok":
                continue
            neff = parse_optional_float(row.get("neff", ""))
            if neff is None or neff <= NE_S:
                continue
            mode_idx = row.get("mode_index", "")
            output_rows.append({
                "t_h": f"{t_h:.4f}",
                "V": f"{v:.6f}",
                "dx": f"{approx.diffusion_width_x:.6f}",
                "dy": f"{approx.diffusion_depth_y:.6f}",
                "neff": f"{neff:.9f}",
                "B": f"{compute_B(neff):.9f}",
                "mode_index": mode_idx,
                "point_dir": str(point_dir),
            })

    output_rows.sort(key=lambda r: (int(r["mode_index"]), float(r["V"])))

    out_path = consolidated_dir / "dispersion_curve.csv"
    fieldnames = ["t_h", "V", "dx", "dy", "neff", "B", "mode_index", "point_dir"]
    with out_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    summary_lines = [
        "case: Case 5 APE LiNbO3 anisotropic",
        f"Da_x: {DA_X} um^2/h",
        f"Da_z: {DA_Z} um^2/h",
        f"lambda: {LAMBDA_UM} um",
        f"ne_s: {NE_S}, delta_ne: {DELTA_NE}, ne_max: {_NE_MAX:.6f}",
        f"NA: {_NA:.6f}",
        "normalization_V: V = (2 * dy / lambda) * NA",
        "normalization_B: B = (neff^2 - ne_s^2) / (ne_max^2 - ne_s^2)",
        f"mode_rows_total: {len(output_rows)}",
        f"missing: {len(missing)}",
        f"skipped: {len(skipped)}",
        "preprocessor: ape_diffusion_preprocessor.py (C_peak=1.0, dx=2*sqrt(Da_x*t), dy=2*sqrt(Da_z*t))",
        "note: delta_x/delta_z ENABLED (T-008 audit passed)",
    ]
    (consolidated_dir / "consolidation_summary.txt").write_text(
        "\n".join(summary_lines) + "\n", encoding="utf-8"
    )

    print(f"Consolidated {len(output_rows)} mode-rows -> {out_path}")
    if missing:
        print(f"  Missing: {missing}")
    if skipped:
        print(f"  Skipped: {skipped}")

    v_range = sorted(set(float(r["V"]) for r in output_rows))
    if v_range:
        print(f"  V range: [{v_range[0]:.2f}, {v_range[-1]:.2f}]")


if __name__ == "__main__":
    main()
