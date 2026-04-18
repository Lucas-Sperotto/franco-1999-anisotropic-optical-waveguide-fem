#!/usr/bin/env python3
"""Consolidate Case 1 sweep points into normalized-dispersion CSV summaries."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ModeCandidate:
    mode_index: int
    raw_mode_label: str
    status: str
    eigenvalue_n_eff_squared: str
    neff: float | None
    beta: float | None
    guided_by_index: bool
    core_energy_fraction: float | None


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


def parse_optional_float(raw_value: str) -> float | None:
    value = raw_value.strip()
    if not value:
        return None
    return float(value)


def compute_normalized_beta(neff: float, n2: float, n3: float) -> float:
    if neff <= n2:
        return 0.0
    return (neff * neff - n2 * n2) / (n3 * n3 - n2 * n2)


def load_mode_candidates(results_dir: Path, n2: float, n3: float) -> list[ModeCandidate]:
    neff_rows = read_csv_rows(results_dir / "neff.csv")
    metrics_path = results_dir / "modal_metrics.csv"
    metrics_by_mode_index: dict[int, dict[str, str]] = {}
    if metrics_path.exists():
        for metrics_row in read_csv_rows(metrics_path):
            metrics_by_mode_index[int(metrics_row["mode_index"])] = metrics_row

    candidates: list[ModeCandidate] = []
    for row in neff_rows:
        mode_index = int(row["mode_index"])
        metrics_row = metrics_by_mode_index.get(mode_index, {})
        neff = parse_optional_float(row.get("neff", ""))
        beta = parse_optional_float(row.get("beta", ""))
        guided_from_index_window = neff is not None and n2 < neff < n3
        guided_token = metrics_row.get("guided_by_index", "").strip().lower()
        if guided_token in {"yes", "true", "1"}:
            guided_by_index = True
        elif guided_token in {"no", "false", "0"}:
            guided_by_index = False
        else:
            guided_by_index = guided_from_index_window

        candidates.append(
            ModeCandidate(
                mode_index=mode_index,
                raw_mode_label=metrics_row.get("mode_label", f"mode_{mode_index}"),
                status=row["status"],
                eigenvalue_n_eff_squared=row.get("eigenvalue_n_eff_squared", ""),
                neff=neff,
                beta=beta,
                guided_by_index=guided_by_index,
                core_energy_fraction=parse_optional_float(
                    metrics_row.get("core_energy_fraction", "")
                ),
            )
        )

    return candidates


def choose_case1_reference_mode(
    candidates: list[ModeCandidate],
) -> tuple[ModeCandidate | None, str]:
    valid_modes = [
        candidate
        for candidate in candidates
        if candidate.status == "ok" and candidate.neff is not None
    ]
    if not valid_modes:
        return None, "no_valid_mode"

    def core_fraction(candidate: ModeCandidate) -> float:
        return (
            candidate.core_energy_fraction
            if candidate.core_energy_fraction is not None
            else -1.0
        )

    guided_modes = [candidate for candidate in valid_modes if candidate.guided_by_index]
    if guided_modes:
        selected = max(
            guided_modes,
            key=lambda candidate: (
                candidate.neff if candidate.neff is not None else -1.0,
                core_fraction(candidate),
                -candidate.mode_index,
            ),
        )
        return selected, "guided_highest_neff"

    selected = max(
        valid_modes,
        key=lambda candidate: (
            candidate.neff if candidate.neff is not None else -1.0,
            core_fraction(candidate),
            -candidate.mode_index,
        ),
    )
    return selected, "fallback_highest_neff"


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
        point_output_dir = Path(point["output_dir"])
        candidates = load_mode_candidates(
            point_output_dir / "results",
            float(point["substrate_index"]),
            float(point["core_index"]),
        )
        if not candidates:
            raise RuntimeError(f"Missing neff rows for point output {point['output_dir']}")

        selected_mode, selection_reason = choose_case1_reference_mode(candidates)
        if selected_mode is None:
            continue

        neff_value = selected_mode.neff
        normalized_beta = (
            compute_normalized_beta(
                neff_value,
                float(point["substrate_index"]),
                float(point["core_index"]),
            )
            if neff_value is not None
            else None
        )

        consolidated_rows.append(
            {
                "study_id": point["study_id"],
                "mesh_label": point["mesh_label"],
                "reference_plot": study_manifest[point["study_id"]]["reference_plot"],
                "normalized_frequency": point["normalized_frequency"],
                "normalized_beta": (
                    f"{normalized_beta:.6f}" if normalized_beta is not None else ""
                ),
                "mode_index": str(selected_mode.mode_index),
                "mode_label": "Ex_fundamental",
                "raw_mode_label": selected_mode.raw_mode_label,
                "eigenvalue_n_eff_squared": selected_mode.eigenvalue_n_eff_squared,
                "neff": f"{selected_mode.neff:.6f}" if selected_mode.neff is not None else "",
                "beta": f"{selected_mode.beta:.6f}" if selected_mode.beta is not None else "",
                "k0": point["k0"],
                "wavelength_um": point["wavelength_um"],
                "status": selected_mode.status,
                "guided": "yes" if selected_mode.guided_by_index else "no",
                "selection_reason": selection_reason,
                "candidate_mode_count": str(len(candidates)),
                "core_energy_fraction": (
                    f"{selected_mode.core_energy_fraction:.6f}"
                    if selected_mode.core_energy_fraction is not None
                    else ""
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
                "raw_mode_label",
                "eigenvalue_n_eff_squared",
                "neff",
                "beta",
                "k0",
                "wavelength_um",
                "status",
                "guided",
                "selection_reason",
                "candidate_mode_count",
                "core_energy_fraction",
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
                "mode_index",
                "mode_label",
                "raw_mode_label",
                "neff",
                "beta",
                "k0",
                "wavelength_um",
                "status",
                "guided",
                "selection_reason",
                "candidate_mode_count",
                "core_energy_fraction",
            ],
        )
        writer.writeheader()
        for row in reference_rows:
            writer.writerow(
                {
                    "study_id": row["study_id"],
                    "normalized_frequency": row["normalized_frequency"],
                    "normalized_beta": row["normalized_beta"],
                    "mode_index": row["mode_index"],
                    "mode_label": row["mode_label"],
                    "raw_mode_label": row["raw_mode_label"],
                    "neff": row["neff"],
                    "beta": row["beta"],
                    "k0": row["k0"],
                    "wavelength_um": row["wavelength_um"],
                    "status": row["status"],
                    "guided": row["guided"],
                    "selection_reason": row["selection_reason"],
                    "candidate_mode_count": row["candidate_mode_count"],
                    "core_energy_fraction": row["core_energy_fraction"],
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
            signed_relative_percent = (
                100.0 * (reference_value - calculated_value) / reference_value
            )
            absolute_relative_percent = (
                100.0 * abs(reference_value - calculated_value) / abs(reference_value)
            )
            comparison_rows.append(
                {
                    "normalized_frequency": row["normalized_frequency"],
                    "reference_beta": f"{reference_value:.6f}",
                    "calculated_beta": f"{calculated_value:.6f}",
                    "absolute_delta_beta": f"{abs(reference_value - calculated_value):.6f}",
                    "relative_error_percent": f"{signed_relative_percent:.6f}",
                    "absolute_relative_error_percent": f"{absolute_relative_percent:.6f}",
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
                    "relative_error_percent",
                    "absolute_relative_error_percent",
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
                (
                    "mode_note: the current sweep selects the guided candidate with "
                    "the largest n_eff and falls back to the largest n_eff overall "
                    "when no guided mode is present."
                ),
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
