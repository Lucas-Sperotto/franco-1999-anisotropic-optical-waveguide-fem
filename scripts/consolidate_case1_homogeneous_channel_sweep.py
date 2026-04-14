#!/usr/bin/env python3
"""Consolidate Case 1 sweep points into normalized-dispersion CSV summaries."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Consolidate the outputs of run_case1_homogeneous_channel_sweep.py"
    )
    parser.add_argument(
        "--sweep-root",
        required=True,
        help="Sweep root produced by scripts/run_case1_homogeneous_channel_sweep.py",
    )
    parser.add_argument(
        "--reference-points",
        default="cases/homogeneous_channel_fig1_reference_points.csv",
        help="Optional CSV with approximate Fig. 1 points to compare against",
    )
    return parser.parse_args()


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def load_study_manifest(path: Path) -> dict[str, dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        return {row["study_id"]: row for row in reader}


def compute_normalized_beta(neff: float, n2: float, n3: float) -> float:
    return (neff * neff - n2 * n2) / (n3 * n3 - n2 * n2)


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    sweep_root = Path(args.sweep_root).resolve()
    consolidated_dir = sweep_root / "consolidated"
    consolidated_dir.mkdir(parents=True, exist_ok=True)

    reference_points_path = Path(args.reference_points)
    if not reference_points_path.is_absolute():
        reference_points_path = repo_root / reference_points_path
    reference_points_path = reference_points_path.resolve()

    study_manifest = load_study_manifest(sweep_root / "study_manifest.csv")
    point_manifest = read_csv_rows(sweep_root / "point_manifest.csv")

    consolidated_rows: list[dict[str, str]] = []

    for point in point_manifest:
        neff_rows = read_csv_rows(Path(point["output_dir"]) / "results" / "neff.csv")
        if not neff_rows:
            raise RuntimeError(f"Missing neff rows for point output {point['output_dir']}")

        mode_row = neff_rows[0]
        neff_value = float(mode_row["neff"]) if mode_row["neff"] else None
        normalized_beta = (
            compute_normalized_beta(
                neff_value,
                float(point["substrate_index"]),
                float(point["core_index"]),
            )
            if neff_value is not None
            else None
        )
        status = mode_row["status"]
        consolidated_rows.append(
            {
                "study_id": point["study_id"],
                "mesh_label": point["mesh_label"],
                "reference_plot": study_manifest[point["study_id"]]["reference_plot"],
                "normalized_frequency": point["normalized_frequency"],
                "normalized_beta": (
                    f"{normalized_beta:.6f}" if normalized_beta is not None else ""
                ),
                "mode_index": mode_row["mode_index"],
                "mode_label": "Ex_fundamental",
                "eigenvalue_n_eff_squared": mode_row["eigenvalue_n_eff_squared"],
                "neff": mode_row["neff"],
                "beta": mode_row["beta"],
                "k0": point["k0"],
                "wavelength_um": point["wavelength_um"],
                "status": status,
                "guided": (
                    "yes"
                    if neff_value is not None
                    and float(point["substrate_index"]) < neff_value < float(point["core_index"])
                    else "no"
                ),
                "point_output_dir": point["output_dir"],
            }
        )

    consolidated_rows.sort(
        key=lambda row: (row["study_id"], float(row["normalized_frequency"]))
    )

    consolidated_curve_path = consolidated_dir / "consolidated_curve.csv"
    with consolidated_curve_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "study_id",
                "mesh_label",
                "reference_plot",
                "normalized_frequency",
                "normalized_beta",
                "mode_index",
                "mode_label",
                "eigenvalue_n_eff_squared",
                "neff",
                "beta",
                "k0",
                "wavelength_um",
                "status",
                "guided",
                "point_output_dir",
            ],
        )
        writer.writeheader()
        writer.writerows(consolidated_rows)

    reference_study_id = next(
        study_id for study_id, row in study_manifest.items() if row["reference_plot"] == "yes"
    )
    reference_rows = [row for row in consolidated_rows if row["study_id"] == reference_study_id]

    reference_dispersion_path = consolidated_dir / "reference_dispersion.csv"
    with reference_dispersion_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "study_id",
                "normalized_frequency",
                "normalized_beta",
                "mode_label",
                "neff",
                "beta",
                "k0",
                "wavelength_um",
                "status",
                "guided",
            ],
        )
        writer.writeheader()
        for row in reference_rows:
            writer.writerow(
                {
                    "study_id": row["study_id"],
                    "normalized_frequency": row["normalized_frequency"],
                    "normalized_beta": row["normalized_beta"],
                    "mode_label": row["mode_label"],
                    "neff": row["neff"],
                    "beta": row["beta"],
                    "k0": row["k0"],
                    "wavelength_um": row["wavelength_um"],
                    "status": row["status"],
                    "guided": row["guided"],
                }
            )

    availability_path = consolidated_dir / "availability_summary.csv"
    with availability_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            [
                "study_id",
                "normalized_frequency",
                "has_mode",
                "guided",
                "status",
            ]
        )
        for row in consolidated_rows:
            writer.writerow(
                [
                    row["study_id"],
                    row["normalized_frequency"],
                    "yes" if row["status"] == "ok" else "no",
                    row["guided"],
                    row["status"],
                ]
            )

    if reference_points_path.exists():
        reference_rows_external = read_csv_rows(reference_points_path)
        normalized_reference_rows: list[dict[str, str]] = []
        lookup: dict[str, dict[str, str]] = {}
        for row in reference_rows_external:
            normalized_row = {
                "normalized_frequency": f"{float(row['normalized_frequency']):.6f}",
                "normalized_beta": f"{float(row['normalized_beta']):.6f}",
                "source": row.get("source", "external_reference"),
            }
            normalized_reference_rows.append(normalized_row)
            lookup[normalized_row["normalized_frequency"]] = normalized_row

        normalized_reference_rows.sort(key=lambda row: float(row["normalized_frequency"]))
        with (consolidated_dir / "fig1_reference_points.csv").open(
            "w", encoding="utf-8", newline=""
        ) as stream:
            writer = csv.DictWriter(
                stream,
                fieldnames=["normalized_frequency", "normalized_beta", "source"],
            )
            writer.writeheader()
            writer.writerows(normalized_reference_rows)

        comparison_rows: list[dict[str, str]] = []
        for row in reference_rows:
            reference_row = lookup.get(f"{float(row['normalized_frequency']):.6f}")
            if reference_row is None or not row["normalized_beta"]:
                continue
            reference_value = float(reference_row["normalized_beta"])
            calculated_value = float(row["normalized_beta"])
            comparison_rows.append(
                {
                    "normalized_frequency": row["normalized_frequency"],
                    "reference_beta": f"{reference_value:.6f}",
                    "calculated_beta": f"{calculated_value:.6f}",
                    "absolute_delta_beta": f"{abs(reference_value - calculated_value):.6f}",
                }
            )

        with (consolidated_dir / "reference_comparison.csv").open(
            "w", encoding="utf-8", newline=""
        ) as stream:
            writer = csv.DictWriter(
                stream,
                fieldnames=[
                    "normalized_frequency",
                    "reference_beta",
                    "calculated_beta",
                    "absolute_delta_beta",
                ],
            )
            writer.writeheader()
            writer.writerows(comparison_rows)

    (consolidated_dir / "consolidation_summary.txt").write_text(
        "\n".join(
            [
                "case: Case 1 homogeneous isotropic channel guide",
                "status: preliminary FEM consolidation",
                "normalization_frequency: V = (k0 * b / pi) * sqrt(n3^2 - n2^2)",
                "normalization_beta: B = (n_eff^2 - n2^2) / (n3^2 - n2^2)",
                "mode_note: the current sweep keeps only the leading Ex-like mode",
                (
                    "reference_overlay: enabled"
                    if reference_points_path.exists()
                    else "reference_overlay: pending"
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
