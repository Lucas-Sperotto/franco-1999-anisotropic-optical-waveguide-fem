#!/usr/bin/env python3
"""Consolidate planar diffuse sweep points into CSV summaries."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

from planar_exact_reference import (
    PlanarExactReferenceConfig,
    solve_planar_exact_te_modes,
)

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
    parser.add_argument(
        "--reference-points",
        default="cases/planar_diffuse_isotropic_fig2_reference_points.csv",
        help="CSV with approximate Fig. 2 reference points to compare against",
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


def normalize_float_key(value: str) -> str:
    return f"{float(value):.6f}"


def mode_index_to_label(mode_index: int) -> str:
    return MODE_LABELS.get(mode_index, f"mode_{mode_index}")


def read_mode_float(mode_row: dict[str, str], key: str) -> float | None:
    value = mode_row.get(key, "")
    return float(value) if value else None


def trim_copy(value: str) -> str:
    return value.strip()


def strip_inline_comment(line: str) -> str:
    comment_index = line.find("#")
    if comment_index == -1:
        return line
    return line[:comment_index]


def load_yaml_like_case(case_path: Path) -> dict[str, str]:
    raw_entries: dict[str, str] = {}
    current_section = ""

    for raw_line in case_path.read_text(encoding="utf-8").splitlines():
        line_without_comment = strip_inline_comment(raw_line)
        trimmed = trim_copy(line_without_comment)
        if not trimmed:
            continue

        indent = len(line_without_comment) - len(line_without_comment.lstrip(" "))
        if trimmed.endswith(":"):
            current_section = trim_copy(trimmed[:-1])
            continue

        if ":" not in trimmed:
            raise ValueError(f"Invalid YAML-like line in {case_path}: {trimmed}")

        key, value = trimmed.split(":", 1)
        key = trim_copy(key)
        value = trim_copy(value).strip("'\"")
        full_key = f"{current_section}.{key}" if indent > 0 and current_section else key
        raw_entries[full_key] = value

    return raw_entries


def main() -> None:
    args = parse_args()
    sweep_root = Path(args.sweep_root).resolve()
    repo_root = Path(__file__).resolve().parents[1]
    reference_points_path = Path(args.reference_points)
    if not reference_points_path.is_absolute():
        reference_points_path = repo_root / reference_points_path
    reference_points_path = reference_points_path.resolve()
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
                availability[(point["study_id"], consolidated_row["k0_b"])].add(mode_index)

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
            reference_lookup[(row["k0_b"], int(row["mode_index"]))] = float(row["neff"])

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
            reference_value = reference_lookup.get((row["k0_b"], mode_index))
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
            point_key_k0_b = point.get("k0_b", "")
            key = (point["study_id"], point_key_k0_b)
            matching_rows = [
                row
                for row in consolidated_rows
                if row["study_id"] == point["study_id"] and row["k0_b"] == point_key_k0_b
            ]
            k0_b_value = matching_rows[0]["k0_b"] if matching_rows else point_key_k0_b
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

    reference_point_rows = read_csv_rows(reference_points_path)
    normalized_reference_rows: list[dict[str, str]] = []
    reference_lookup_by_mode: dict[tuple[str, str], dict[str, str]] = {}
    for row in reference_point_rows:
        normalized_row = {
            "mode_label": row["mode_label"],
            "k0_b": normalize_float_key(row["k0_b"]),
            "neff": f"{float(row['neff']):.6f}",
            "source": row.get("source", "external_reference"),
        }
        normalized_reference_rows.append(normalized_row)
        reference_lookup_by_mode[(normalized_row["mode_label"], normalized_row["k0_b"])] = (
            normalized_row
        )

    normalized_reference_rows.sort(
        key=lambda row: (row["mode_label"], float(row["k0_b"]))
    )

    with (consolidated_dir / "fig2_reference_points.csv").open(
        "w", encoding="utf-8", newline=""
    ) as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=["mode_label", "k0_b", "neff", "source"],
        )
        writer.writeheader()
        writer.writerows(normalized_reference_rows)

    case_entries = load_yaml_like_case(Path(point_manifest[0]["case_file"]))
    exact_config = PlanarExactReferenceConfig(
        diffusion_depth=float(case_entries["material.diffusion_depth"]),
        substrate_index=float(case_entries["material.background_index"]),
        cover_index=float(case_entries.get("material.cover_index", "1.0")),
        delta_index=float(case_entries["material.delta_index"]),
    )

    exact_reference_rows: list[dict[str, str]] = []
    unique_reference_points = sorted(
        {
            (float(row["k0_b"]), float(row["k0"]))
            for row in reference_rows
            if row["status"] == "ok"
        }
    )
    for k0_b_value, k0_value in unique_reference_points:
        exact_modes = solve_planar_exact_te_modes(
            k0_d=k0_b_value,
            config=exact_config,
            requested_modes=3,
        )
        for exact_mode in exact_modes:
            exact_reference_rows.append(
                {
                    "b": f"{exact_config.diffusion_depth:.6f}",
                    "k0": f"{k0_value:.6f}",
                    "k0_b": f"{k0_b_value:.6f}",
                    "mode_index": str(exact_mode["mode_index"]),
                    "mode_label": str(exact_mode["mode_label"]),
                    "neff": f"{float(exact_mode['n_eff']):.6f}",
                    "nu": f"{float(exact_mode['nu']):.6f}",
                    "residual": f"{float(exact_mode['residual']):.6e}",
                    "source": str(exact_mode["source"]),
                }
            )

    exact_reference_rows.sort(key=lambda row: (row["mode_label"], float(row["k0_b"])))

    with (consolidated_dir / "analytic_reference.csv").open(
        "w", encoding="utf-8", newline=""
    ) as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "b",
                "k0",
                "k0_b",
                "mode_index",
                "mode_label",
                "neff",
                "nu",
                "residual",
                "source",
            ],
        )
        writer.writeheader()
        writer.writerows(exact_reference_rows)

    exact_lookup_by_mode = {
        (row["mode_label"], normalize_float_key(row["k0_b"])): row
        for row in exact_reference_rows
    }

    reference_comparison_rows: list[dict[str, str]] = []
    for row in reference_rows:
        if row["status"] != "ok":
            continue
        key = (row["mode_label"], normalize_float_key(row["k0_b"]))
        reference_match = reference_lookup_by_mode.get(key)
        if reference_match is None:
            continue
        computed_neff = float(row["neff"])
        reference_neff = float(reference_match["neff"])
        signed_relative_percent = 100.0 * (computed_neff - reference_neff) / reference_neff
        absolute_relative_percent = 100.0 * abs(computed_neff - reference_neff) / reference_neff
        reference_comparison_rows.append(
            {
                "study_id": row["study_id"],
                "mode_label": row["mode_label"],
                "mode_index": row["mode_index"],
                "b": row["b"],
                "k0": row["k0"],
                "k0_b": normalize_float_key(row["k0_b"]),
                "computed_neff": f"{computed_neff:.6f}",
                "reference_neff": f"{reference_neff:.6f}",
                "delta_neff": f"{(computed_neff - reference_neff):.6f}",
                "relative_error_percent": f"{signed_relative_percent:.6f}",
                "absolute_relative_error_percent": f"{absolute_relative_percent:.6f}",
                "reference_source": reference_match["source"],
            }
        )

    reference_comparison_rows.sort(
        key=lambda row: (row["mode_label"], float(row["k0_b"]))
    )

    with (consolidated_dir / "reference_comparison.csv").open(
        "w", encoding="utf-8", newline=""
    ) as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "study_id",
                "mode_label",
                "mode_index",
                "b",
                "k0",
                "k0_b",
                "computed_neff",
                "reference_neff",
                "delta_neff",
                "relative_error_percent",
                "absolute_relative_error_percent",
                "reference_source",
            ],
        )
        writer.writeheader()
        writer.writerows(reference_comparison_rows)

    fem_vs_exact_rows: list[dict[str, str]] = []
    for row in reference_rows:
        if row["status"] != "ok":
            continue
        key = (row["mode_label"], normalize_float_key(row["k0_b"]))
        exact_match = exact_lookup_by_mode.get(key)
        if exact_match is None:
            continue
        fem_neff = float(row["neff"])
        exact_neff = float(exact_match["neff"])
        signed_relative_percent = 100.0 * (fem_neff - exact_neff) / exact_neff
        absolute_relative_percent = 100.0 * abs(fem_neff - exact_neff) / exact_neff
        fem_vs_exact_rows.append(
            {
                "study_id": row["study_id"],
                "mode_label": row["mode_label"],
                "mode_index": row["mode_index"],
                "b": row["b"],
                "k0": row["k0"],
                "k0_b": normalize_float_key(row["k0_b"]),
                "fem_neff": f"{fem_neff:.6f}",
                "exact_neff": f"{exact_neff:.6f}",
                "delta_neff": f"{(fem_neff - exact_neff):.6f}",
                "relative_error_percent": f"{signed_relative_percent:.6f}",
                "absolute_relative_error_percent": f"{absolute_relative_percent:.6f}",
                "exact_source": exact_match["source"],
            }
        )

    fem_vs_exact_rows.sort(key=lambda row: (row["mode_label"], float(row["k0_b"])))

    with (consolidated_dir / "fem_vs_exact_comparison.csv").open(
        "w", encoding="utf-8", newline=""
    ) as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "study_id",
                "mode_label",
                "mode_index",
                "b",
                "k0",
                "k0_b",
                "fem_neff",
                "exact_neff",
                "delta_neff",
                "relative_error_percent",
                "absolute_relative_error_percent",
                "exact_source",
            ],
        )
        writer.writeheader()
        writer.writerows(fem_vs_exact_rows)

    exact_vs_points_rows: list[dict[str, str]] = []
    for exact_row in exact_reference_rows:
        key = (exact_row["mode_label"], normalize_float_key(exact_row["k0_b"]))
        figure_match = reference_lookup_by_mode.get(key)
        if figure_match is None:
            continue
        exact_neff = float(exact_row["neff"])
        figure_neff = float(figure_match["neff"])
        signed_relative_percent = 100.0 * (exact_neff - figure_neff) / figure_neff
        absolute_relative_percent = 100.0 * abs(exact_neff - figure_neff) / figure_neff
        exact_vs_points_rows.append(
            {
                "mode_label": exact_row["mode_label"],
                "mode_index": exact_row["mode_index"],
                "b": exact_row["b"],
                "k0": exact_row["k0"],
                "k0_b": exact_row["k0_b"],
                "exact_neff": f"{exact_neff:.6f}",
                "reference_neff": f"{figure_neff:.6f}",
                "delta_neff": f"{(exact_neff - figure_neff):.6f}",
                "relative_error_percent": f"{signed_relative_percent:.6f}",
                "absolute_relative_error_percent": f"{absolute_relative_percent:.6f}",
                "reference_source": figure_match["source"],
                "exact_source": exact_row["source"],
            }
        )

    exact_vs_points_rows.sort(key=lambda row: (row["mode_label"], float(row["k0_b"])))

    with (consolidated_dir / "exact_vs_reference_points.csv").open(
        "w", encoding="utf-8", newline=""
    ) as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "mode_label",
                "mode_index",
                "b",
                "k0",
                "k0_b",
                "exact_neff",
                "reference_neff",
                "delta_neff",
                "relative_error_percent",
                "absolute_relative_error_percent",
                "reference_source",
                "exact_source",
            ],
        )
        writer.writeheader()
        writer.writerows(exact_vs_points_rows)

    summary_by_mode: dict[str, list[float]] = defaultdict(list)
    for row in reference_comparison_rows:
        summary_by_mode[row["mode_label"]].append(
            float(row["absolute_relative_error_percent"])
        )

    with (consolidated_dir / "reference_error_summary.csv").open(
        "w", encoding="utf-8", newline=""
    ) as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "mode_label",
                "point_count",
                "min_absolute_relative_error_percent",
                "max_absolute_relative_error_percent",
                "mean_absolute_relative_error_percent",
            ],
        )
        writer.writeheader()
        for mode_label in sorted(summary_by_mode):
            errors = summary_by_mode[mode_label]
            writer.writerow(
                {
                    "mode_label": mode_label,
                    "point_count": len(errors),
                    "min_absolute_relative_error_percent": f"{min(errors):.6f}",
                    "max_absolute_relative_error_percent": f"{max(errors):.6f}",
                    "mean_absolute_relative_error_percent": f"{(sum(errors) / len(errors)):.6f}",
                }
            )

    print(f"Consolidação concluída em: {consolidated_dir}")


if __name__ == "__main__":
    main()
