#!/usr/bin/env python3
"""Consolidate planar diffuse sweep points into CSV summaries."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path


MODE_LABELS = {
    1: "TE0",
    2: "TE1",
    3: "TE2",
}


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


def mode_index_to_label(mode_index: int) -> str:
    return MODE_LABELS.get(mode_index, f"mode_{mode_index}")


def read_mode_float(mode_row: dict[str, str], key: str) -> float | None:
    value = mode_row.get(key, "")
    return float(value) if value else None


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
            mode_index = int(mode_row["mode_index"])
            b_value = read_mode_float(mode_row, "b")
            k0_value = read_mode_float(mode_row, "k0")
            k0_b_value = read_mode_float(mode_row, "k0_b")
            point_b = point.get("b", point["diffusion_depth"])
            point_k0 = point.get("k0", "")
            point_k0_b = point.get("k0_b", "")
            consolidated_row = {
                "study_id": point["study_id"],
                "mesh_label": point["mesh_label"],
                "truncation_ymax": point["truncation_ymax"],
                "dy": point["dy"],
                "reference_plot": study["reference_plot"],
                "b": f"{b_value:.6f}" if b_value is not None else point_b,
                "k0": f"{k0_value:.6f}" if k0_value is not None else point_k0,
                "k0_b": f"{k0_b_value:.6f}" if k0_b_value is not None else point_k0_b,
                "mode_index": str(mode_index),
                "mode_label": mode_row.get("mode_label", mode_index_to_label(mode_index)),
                "eigenvalue_n_eff_squared": mode_row["eigenvalue_n_eff_squared"],
                "neff": mode_row["neff"],
                "beta": mode_row["beta"],
                "status": mode_row["status"],
                "point_output_dir": point["output_dir"],
            }
            consolidated_rows.append(consolidated_row)

            if mode_row["status"] == "ok":
                availability[(point["study_id"], consolidated_row["b"])].add(mode_index)

    consolidated_rows.sort(
        key=lambda row: (
            row["study_id"],
            float(row["k0_b"]) if row["k0_b"] else float(row["b"]),
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
                "b",
                "k0",
                "k0_b",
                "mode_index",
                "mode_label",
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
                "b",
                "k0",
                "k0_b",
                "mode_index",
                "mode_label",
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
                    "b": row["b"],
                    "k0": row["k0"],
                    "k0_b": row["k0_b"],
                    "mode_index": row["mode_index"],
                    "mode_label": row["mode_label"],
                    "eigenvalue_n_eff_squared": row["eigenvalue_n_eff_squared"],
                    "neff": row["neff"],
                    "beta": row["beta"],
                    "status": row["status"],
                }
            )

    reference_lookup: dict[tuple[str, int], float] = {}
    for row in reference_rows:
        if row["status"] == "ok":
            reference_lookup[(row["b"], int(row["mode_index"]))] = float(
                row["neff"]
            )

    sensitivity_path = consolidated_dir / "sensitivity_summary.csv"
    with sensitivity_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            [
                "study_id",
                "b",
                "k0_b",
                "mode_index",
                "mode_label",
                "neff",
                "reference_neff",
                "delta_neff_vs_reference",
                "status",
            ]
        )
        for row in consolidated_rows:
            mode_index = int(row["mode_index"])
            reference_value = reference_lookup.get((row["b"], mode_index))
            neff_value = float(row["neff"]) if row["neff"] else None
            delta_value = (
                neff_value - reference_value
                if neff_value is not None and reference_value is not None
                else None
            )
            writer.writerow(
                [
                    row["study_id"],
                    row["b"],
                    row["k0_b"],
                    mode_index,
                    row["mode_label"],
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
                "b",
                "k0_b",
                "available_mode_count",
                "has_modes_1_2_3",
                "has_TE0_TE1_TE2",
            ]
        )
        for point in point_manifest:
            point_key_b = point.get("b", point["diffusion_depth"])
            key = (point["study_id"], point_key_b)
            matching_rows = [
                row
                for row in consolidated_rows
                if row["study_id"] == point["study_id"] and row["b"] == point_key_b
            ]
            k0_b_value = matching_rows[0]["k0_b"] if matching_rows else point.get("k0_b", "")
            available_modes = availability[key]
            writer.writerow(
                [
                    point["study_id"],
                    point_key_b,
                    k0_b_value,
                    len(available_modes),
                    "yes" if {1, 2, 3}.issubset(available_modes) else "no",
                    "yes" if {1, 2, 3}.issubset(available_modes) else "no",
                ]
            )

    print(f"Consolidação concluída em: {consolidated_dir}")


if __name__ == "__main__":
    main()
