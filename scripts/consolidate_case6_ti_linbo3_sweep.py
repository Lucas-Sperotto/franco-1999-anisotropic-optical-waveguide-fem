#!/usr/bin/env python3
"""Consolidate Case 6 (Ti:LiNbO3) sweep: extract neff, W_x, W_y vs strip_width W.

Reads W_*um/results/neff.csv and modal_fields.csv for each W point.

Mode sizes W_x (lateral FWHM) and W_y (depth FWHM) of |E|^2 are computed
from the mode field by finding half-maximum crossings via linear interpolation.
"""

from __future__ import annotations

import argparse
import csv
import math
import re
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Consolidate Case 6 Ti:LiNbO3 W-sweep into neff/W_x/W_y CSV."
    )
    parser.add_argument("--sweep-root", required=True)
    return parser.parse_args()


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def parse_float(raw: str) -> float | None:
    v = raw.strip()
    if not v:
        return None
    try:
        return float(v)
    except ValueError:
        return None


def fwhm_1d(positions: list[float], intensities: list[float]) -> float | None:
    """Compute FWHM of intensity profile via linear interpolation.

    positions and intensities are sorted by position (ascending).
    Returns full width at half-maximum, or None if not computable.
    """
    if not positions or not intensities:
        return None

    max_val = max(intensities)
    if max_val <= 0.0:
        return None

    half = max_val / 2.0
    peak_idx = intensities.index(max_val)

    # Find left crossing (positions <= peak with intensity crossing half)
    x_left = None
    for i in range(peak_idx, 0, -1):
        if intensities[i - 1] <= half <= intensities[i]:
            # Linear interpolation
            dI = intensities[i] - intensities[i - 1]
            if abs(dI) < 1.0e-15:
                x_left = positions[i - 1]
            else:
                frac = (half - intensities[i - 1]) / dI
                x_left = positions[i - 1] + frac * (positions[i] - positions[i - 1])
            break
    if x_left is None:
        x_left = positions[0]

    # Find right crossing
    x_right = None
    for i in range(peak_idx, len(positions) - 1):
        if intensities[i] >= half >= intensities[i + 1]:
            dI = intensities[i] - intensities[i + 1]
            if abs(dI) < 1.0e-15:
                x_right = positions[i + 1]
            else:
                frac = (intensities[i] - half) / dI
                x_right = positions[i] + frac * (positions[i + 1] - positions[i])
            break
    if x_right is None:
        x_right = positions[-1]

    return x_right - x_left


def compute_mode_sizes(
    modal_fields_path: Path, surface_y: float = 0.0
) -> tuple[float | None, float | None]:
    """Compute W_x and W_y (FWHM of |E|^2) from modal_fields.csv.

    Returns (W_x_um, W_y_um).
    Uses binning along x and y axes to build 1D profiles, then interpolates.
    """
    rows = read_csv_rows(modal_fields_path)
    if not rows:
        return None, None

    # Detect mode column name (first column after x, y)
    fieldnames = list(rows[0].keys())
    mode_cols = [c for c in fieldnames if c not in ("node_id", "x", "y")]
    if not mode_cols:
        return None, None
    mode_col = mode_cols[0]

    # Extract (x, y, field^2) for nodes in substrate (y >= surface_y)
    data: list[tuple[float, float, float]] = []
    for row in rows:
        x = parse_float(row.get("x", ""))
        y = parse_float(row.get("y", ""))
        f = parse_float(row.get(mode_col, ""))
        if x is None or y is None or f is None:
            continue
        if y < surface_y - 0.5:   # allow slight cover penetration
            continue
        data.append((x, y, f * f))

    if not data:
        return None, None

    # --- X profile: bin by x, take max intensity in each bin ---
    n_bins = 120
    xs = [d[0] for d in data]
    ys = [d[1] for d in data]
    i2 = [d[2] for d in data]

    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)

    if x_max <= x_min or y_max <= y_min:
        return None, None

    # Build x-profile: max intensity per x-bin
    x_bins: dict[int, float] = {}
    for x, y, val in data:
        bi = min(int((x - x_min) / (x_max - x_min) * n_bins), n_bins - 1)
        x_bins[bi] = max(x_bins.get(bi, 0.0), val)

    x_centers = sorted(x_bins.keys())
    x_pos = [x_min + (k + 0.5) / n_bins * (x_max - x_min) for k in x_centers]
    x_int = [x_bins[k] for k in x_centers]

    # Smooth: simple 3-point moving average
    x_int_smooth = list(x_int)
    for i in range(1, len(x_int) - 1):
        x_int_smooth[i] = (x_int[i - 1] + x_int[i] + x_int[i + 1]) / 3.0

    w_x = fwhm_1d(x_pos, x_int_smooth)

    # Build y-profile: max intensity per y-bin
    y_bins: dict[int, float] = {}
    for x, y, val in data:
        bi = min(int((y - y_min) / (y_max - y_min) * n_bins), n_bins - 1)
        y_bins[bi] = max(y_bins.get(bi, 0.0), val)

    y_centers = sorted(y_bins.keys())
    y_pos = [y_min + (k + 0.5) / n_bins * (y_max - y_min) for k in y_centers]
    y_int = [y_bins[k] for k in y_centers]

    y_int_smooth = list(y_int)
    for i in range(1, len(y_int) - 1):
        y_int_smooth[i] = (y_int[i - 1] + y_int[i] + y_int[i + 1]) / 3.0

    w_y = fwhm_1d(y_pos, y_int_smooth)

    return w_x, w_y


def main() -> None:
    args = parse_args()
    sweep_root = Path(args.sweep_root).resolve()
    if not sweep_root.exists():
        raise FileNotFoundError(f"Sweep root not found: {sweep_root}")

    consolidated_dir = sweep_root / "consolidated"
    consolidated_dir.mkdir(parents=True, exist_ok=True)

    w_dir_pattern = re.compile(r"^W_(\d+\.\d+)um$")
    point_dirs = sorted(
        d for d in sweep_root.iterdir()
        if d.is_dir() and w_dir_pattern.match(d.name)
    )

    if not point_dirs:
        print(f"No W_*um directories found under {sweep_root}")
        return

    output_rows: list[dict[str, str]] = []
    missing = []
    skipped = []

    for point_dir in point_dirs:
        match = w_dir_pattern.match(point_dir.name)
        w_val = float(match.group(1))

        neff_csv = point_dir / "results" / "neff.csv"
        if not neff_csv.exists():
            missing.append(point_dir.name)
            continue

        neff_rows = read_csv_rows(neff_csv)
        if not neff_rows:
            skipped.append((point_dir.name, "empty neff.csv"))
            continue

        # Pick first valid mode
        neff = None
        for row in neff_rows:
            if row.get("status", "").strip() == "ok":
                neff = parse_float(row.get("neff", ""))
                if neff is not None:
                    break

        if neff is None:
            skipped.append((point_dir.name, "no valid neff"))
            continue

        # Compute mode sizes from modal_fields.csv
        fields_csv_candidates = list(point_dir.glob("results/modal_fields.csv"))
        w_x: float | None = None
        w_y: float | None = None
        if fields_csv_candidates:
            w_x, w_y = compute_mode_sizes(fields_csv_candidates[0])

        output_rows.append({
            "W_um": f"{w_val:.4f}",
            "neff": f"{neff:.9f}",
            "W_x_um": f"{w_x:.4f}" if w_x is not None else "",
            "W_y_um": f"{w_y:.4f}" if w_y is not None else "",
            "point_dir": str(point_dir),
        })

    output_rows.sort(key=lambda r: float(r["W_um"]))

    out_path = consolidated_dir / "neff_mode_sizes.csv"
    fieldnames = ["W_um", "neff", "W_x_um", "W_y_um", "point_dir"]
    with out_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    summary_lines = [
        "case: Case 6 Ti:LiNbO3 anisotropic",
        "sweep: strip_width W (um)",
        "extracted: neff, W_x (lateral FWHM of |E|^2), W_y (depth FWHM of |E|^2)",
        f"points_found: {len(output_rows)}",
        f"points_missing_neff_csv: {len(missing)}",
        f"points_skipped: {len(skipped)}",
        "note: delta_x/delta_z ENABLED (T-008 audit passed)",
        "note: W_x/W_y computed from modal_fields.csv via max-binning + FWHM interpolation",
    ]
    (consolidated_dir / "consolidation_summary.txt").write_text(
        "\n".join(summary_lines) + "\n", encoding="utf-8"
    )

    print(f"Consolidated {len(output_rows)} W-points -> {out_path}")
    if missing:
        print(f"  Missing: {missing}")
    if skipped:
        print(f"  Skipped: {skipped}")

    print("\nW-sweep results:")
    print(f"  {'W(um)':>8}  {'neff':>12}  {'W_x(um)':>10}  {'W_y(um)':>10}")
    for row in output_rows:
        print(
            f"  {float(row['W_um']):8.2f}  {float(row['neff']):12.8f}  "
            f"{row['W_x_um'] or 'N/A':>10}  {row['W_y_um'] or 'N/A':>10}"
        )


if __name__ == "__main__":
    main()
