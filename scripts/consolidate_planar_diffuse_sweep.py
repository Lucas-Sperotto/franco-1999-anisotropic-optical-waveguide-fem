#!/usr/bin/env python3
"""Consolidate planar diffuse sweep points into CSV summaries."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Consolidate the outputs of run_planar_diffuse_sweep.py"
    )
    parser.add_argument(
        "--sweep-root",
        required=True,
        help="Sweep root produced by scripts/run_planar_diffuse_sweep.py",
    )
    return parser.parse_args()


def load_study_manifest(path: Path) -> dict[str, dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        return {row["study_id"]: row for row in reader}


def load_point_manifest(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def main() -> None:
    args = parse_args()
    sweep_root = Path(args.sweep_root).resolve()
    consolidated_dir = sweep_root / "consolidated"
    consolidated_dir.mkdir(parents=True, exist_ok=True)

    study_manifest = load_study_manifest(sweep_root / "study_manifest.csv")
    point_manifest = load_point_manifest(sweep_root / "point_manifest.csv")

    consolidated_rows: list[dict[str, str]] = []
    availability: defaultdict[tuple[str, str], set[int]] = defaultdict(set)

    for point in point_manifest:
        study = study_manifest[point["study_id"]]
        point_output_dir = Path(point["output_dir"])
        mode_rows = read_csv_rows(point_output_dir / "results" / "dispersion_curve_points.csv")
        for mode_row in mode_rows:
            consolidated_row = {
                "study_id": point["study_id"],
                "mesh_label": point["mesh_label"],
                "truncation_ymax": point["truncation_ymax"],
                "dy": point["dy"],
                "reference_plot": study["reference_plot"],
                "diffusion_depth": point["diffusion_depth"],
                "wavelength_um": mode_row["wavelength_um"],
                "mode_index": mode_row["mode_index"],
                "eigenvalue_n_eff_squared": mode_row["eigenvalue_n_eff_squared"],
                "neff": mode_row["neff"],
                "beta": mode_row["beta"],
                "status": mode_row["status"],
                "point_output_dir": point["output_dir"],
            }
            consolidated_rows.append(consolidated_row)

            if mode_row["status"] == "ok":
                availability[(point["study_id"], point["diffusion_depth"])].add(
                    int(mode_row["mode_index"])
                )

    consolidated_rows.sort(
        key=lambda row: (
            row["study_id"],
            float(row["diffusion_depth"]),
            int(row["mode_index"]),
        )
    )

    consolidated_modes_path = consolidated_dir / "consolidated_modes.csv"
    with consolidated_modes_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "study_id",
                "mesh_label",
                "truncation_ymax",
                "dy",
                "reference_plot",
                "diffusion_depth",
                "wavelength_um",
                "mode_index",
                "eigenvalue_n_eff_squared",
                "neff",
                "beta",
                "status",
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
                "diffusion_depth",
                "mode_index",
                "eigenvalue_n_eff_squared",
                "neff",
                "beta",
                "status",
            ],
        )
        writer.writeheader()
        for row in reference_rows:
            writer.writerow(
                {
                    "study_id": row["study_id"],
                    "diffusion_depth": row["diffusion_depth"],
                    "mode_index": row["mode_index"],
                    "eigenvalue_n_eff_squared": row["eigenvalue_n_eff_squared"],
                    "neff": row["neff"],
                    "beta": row["beta"],
                    "status": row["status"],
                }
            )

    reference_lookup: dict[tuple[str, int], float] = {}
    for row in reference_rows:
        if row["status"] == "ok":
            reference_lookup[(row["diffusion_depth"], int(row["mode_index"]))] = float(
                row["neff"]
            )

    sensitivity_path = consolidated_dir / "sensitivity_summary.csv"
    with sensitivity_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            [
                "study_id",
                "diffusion_depth",
                "mode_index",
                "neff",
                "reference_neff",
                "delta_neff_vs_reference",
                "status",
            ]
        )
        for row in consolidated_rows:
            mode_index = int(row["mode_index"])
            reference_value = reference_lookup.get((row["diffusion_depth"], mode_index))
            neff_value = float(row["neff"]) if row["neff"] else None
            delta_value = (
                neff_value - reference_value
                if neff_value is not None and reference_value is not None
                else None
            )
            writer.writerow(
                [
                    row["study_id"],
                    row["diffusion_depth"],
                    mode_index,
                    row["neff"],
                    f"{reference_value:.6f}" if reference_value is not None else "",
                    f"{delta_value:.6f}" if delta_value is not None else "",
                    row["status"],
                ]
            )

    availability_path = consolidated_dir / "availability_summary.csv"
    with availability_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            [
                "study_id",
                "diffusion_depth",
                "available_mode_count",
                "has_modes_1_2_3",
            ]
        )
        for point in point_manifest:
            key = (point["study_id"], point["diffusion_depth"])
            available_modes = availability[key]
            writer.writerow(
                [
                    point["study_id"],
                    point["diffusion_depth"],
                    len(available_modes),
                    "yes" if {1, 2, 3}.issubset(available_modes) else "no",
                ]
            )

    print(f"Consolidação concluída em: {consolidated_dir}")


if __name__ == "__main__":
    main()
