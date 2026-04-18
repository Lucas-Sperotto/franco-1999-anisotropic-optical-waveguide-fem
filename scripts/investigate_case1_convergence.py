#!/usr/bin/env python3
"""Investigate Case 1 sensitivity to boundary condition and domain truncation."""

from __future__ import annotations

import argparse
import csv
import math
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


FULL_NORMALIZED_FREQUENCIES = [
    0.8,
    1.0,
    1.2,
    1.4,
    1.6,
    1.8,
    2.0,
    2.2,
    2.4,
    2.6,
    2.8,
    3.0,
    3.2,
    3.4,
    3.6,
    3.8,
    4.0,
]

LARGE_DOMAIN_X_VALUES = [
    -30.0,
    -24.0,
    -18.0,
    -12.0,
    -9.0,
    -7.0,
    -5.0,
    -4.0,
    -3.0,
    -2.5,
    -2.0,
    -1.5,
    -1.0,
    -0.5,
    0.0,
    0.5,
    1.0,
    1.5,
    2.0,
    2.5,
    3.0,
    4.0,
    5.0,
    7.0,
    9.0,
    12.0,
    18.0,
    24.0,
    30.0,
]

LARGE_DOMAIN_Y_VALUES = [
    -20.0,
    -16.0,
    -12.0,
    -9.0,
    -7.0,
    -5.0,
    -4.0,
    -3.0,
    -2.5,
    -2.0,
    -1.5,
    -1.0,
    -0.75,
    -0.5,
    -0.25,
    0.0,
    0.125,
    0.25,
    0.5,
    0.75,
    1.0,
    1.25,
    1.5,
    2.0,
    3.0,
    4.0,
    6.0,
    8.0,
    12.0,
    16.0,
    24.0,
    32.0,
    40.0,
]


@dataclass(frozen=True)
class GeneratedMeshDefinition:
    mesh_id: str
    x_values: list[float]
    y_values: list[float]


@dataclass(frozen=True)
class StudyDefinition:
    study_id: str
    mesh_file: str | None
    generated_mesh_id: str | None
    boundary_condition: str
    note: str


@dataclass(frozen=True)
class ModeCandidate:
    mode_index: int
    mode_label: str
    status: str
    neff: float | None
    beta: float | None
    guided_by_index: bool
    core_energy_fraction: float | None


GENERATED_MESHES = [
    GeneratedMeshDefinition(
        mesh_id="large_domain_x30_y40",
        x_values=LARGE_DOMAIN_X_VALUES,
        y_values=LARGE_DOMAIN_Y_VALUES,
    ),
]

FULL_STUDIES = [
    StudyDefinition(
        study_id="farfield_dirichlet",
        mesh_file="meshes/channel_a2b_b1_farfield.mesh",
        generated_mesh_id=None,
        boundary_condition="dirichlet_zero_on_boundary_nodes",
        note="Current Case 1 baseline in the repository.",
    ),
    StudyDefinition(
        study_id="farfield_natural",
        mesh_file="meshes/channel_a2b_b1_farfield.mesh",
        generated_mesh_id=None,
        boundary_condition="natural_zero_flux_on_boundary",
        note="Open-boundary surrogate on the current farfield mesh.",
    ),
    StudyDefinition(
        study_id="large_domain_dirichlet",
        mesh_file=None,
        generated_mesh_id="large_domain_x30_y40",
        boundary_condition="dirichlet_zero_on_boundary_nodes",
        note="Larger truncation box with Dirichlet boundary.",
    ),
    StudyDefinition(
        study_id="large_domain_natural",
        mesh_file=None,
        generated_mesh_id="large_domain_x30_y40",
        boundary_condition="natural_zero_flux_on_boundary",
        note="Larger truncation box with open-boundary surrogate.",
    ),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Investigate Case 1 convergence and boundary sensitivity."
    )
    parser.add_argument(
        "--case-template",
        default="cases/homogeneous_channel_isotropic_case.yaml",
        help="Base YAML case used as the source of common parameters",
    )
    parser.add_argument(
        "--reference-points",
        default="cases/homogeneous_channel_fig1_reference_points.csv",
        help="CSV with approximate points from Fig. 1 for preliminary comparison",
    )
    parser.add_argument(
        "--output-root",
        default=None,
        help="Output root. Defaults to out/case1_homogeneous_channel/investigation_<timestamp>",
    )
    parser.add_argument(
        "--solver",
        default="build/waveguide_solver",
        help="Path to the waveguide_solver executable",
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Do not call scripts/build.sh before running the investigation",
    )
    parser.add_argument(
        "--frequencies",
        default=",".join(f"{value:.1f}" for value in FULL_NORMALIZED_FREQUENCIES),
        help="Comma-separated normalized frequencies to evaluate",
    )
    parser.add_argument(
        "--requested-modes",
        type=int,
        default=16,
        help="Number of eigenpairs requested per point for modal tracking",
    )
    return parser.parse_args()


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


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def parse_frequencies(raw_values: str) -> list[float]:
    values = [float(token.strip()) for token in raw_values.split(",") if token.strip()]
    if not values:
        raise ValueError("At least one normalized frequency must be provided")
    for value in values:
        if value <= 0.0:
            raise ValueError("Normalized frequencies must be positive")
    return values


def compute_k0(normalized_frequency: float, core_height: float, n2: float, n3: float) -> float:
    if core_height <= 0.0:
        raise ValueError("The sweep requires a positive core height")
    delta_index_squared = n3 * n3 - n2 * n2
    if delta_index_squared <= 0.0:
        raise ValueError("The sweep requires n3 > n2")
    return normalized_frequency * math.pi / (core_height * delta_index_squared ** 0.5)


def compute_wavelength_um(k0: float) -> float:
    if k0 <= 0.0:
        raise ValueError("The sweep requires a positive k0")
    return 2.0 * math.pi / k0


def parse_optional_float(raw_value: str) -> float | None:
    value = raw_value.strip()
    if not value:
        return None
    return float(value)


def compute_normalized_beta(neff: float, n2: float, n3: float) -> float:
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
                mode_label=metrics_row.get("mode_label", f"mode_{mode_index}"),
                status=row["status"],
                neff=neff,
                beta=beta,
                guided_by_index=guided_by_index,
                core_energy_fraction=parse_optional_float(
                    metrics_row.get("core_energy_fraction", "")
                ),
            )
        )

    return candidates


def choose_tracked_mode(
    candidates: list[ModeCandidate],
    previous_guided_neff: float | None,
) -> tuple[ModeCandidate | None, str]:
    valid_modes = [
        candidate
        for candidate in candidates
        if candidate.status == "ok" and candidate.neff is not None
    ]
    if not valid_modes:
        return None, "no_valid_mode"

    guided_modes = [candidate for candidate in valid_modes if candidate.guided_by_index]

    def core_fraction(candidate: ModeCandidate) -> float:
        return (
            candidate.core_energy_fraction
            if candidate.core_energy_fraction is not None
            else -1.0
        )

    if guided_modes:
        if previous_guided_neff is None:
            selected = max(
                guided_modes,
                key=lambda candidate: (
                    core_fraction(candidate),
                    candidate.neff if candidate.neff is not None else -1.0,
                    -candidate.mode_index,
                ),
            )
            return selected, "guided_entry_max_core_fraction"

        selected = min(
            guided_modes,
            key=lambda candidate: (
                abs((candidate.neff or 0.0) - previous_guided_neff),
                -core_fraction(candidate),
                -(candidate.neff if candidate.neff is not None else -1.0),
                candidate.mode_index,
            ),
        )
        return selected, "guided_continuity"

    selected = max(
        valid_modes,
        key=lambda candidate: (
            candidate.neff if candidate.neff is not None else -1.0,
            core_fraction(candidate),
            -candidate.mode_index,
        ),
    )
    return selected, "fallback_highest_neff"


def format_value_label(value: float) -> str:
    return f"{value:.2f}".replace(".", "p")


def build_mesh_file(
    *,
    repo_root: Path,
    output_dir: Path,
    definition: GeneratedMeshDefinition,
) -> Path:
    mesh_dir = output_dir / "generated_meshes"
    mesh_dir.mkdir(parents=True, exist_ok=True)
    mesh_path = mesh_dir / f"{definition.mesh_id}.mesh"
    x_values = ",".join(f"{value:.6f}" for value in definition.x_values)
    y_values = ",".join(f"{value:.6f}" for value in definition.y_values)
    subprocess.run(
        [
            "python3",
            str((repo_root / "scripts" / "generate_planar_strip_mesh.py").resolve()),
            "--output",
            str(mesh_path),
            f"--x-values={x_values}",
            f"--y-values={y_values}",
        ],
        check=True,
    )
    return mesh_path.resolve()


def write_case_file(
    destination: Path,
    template_entries: dict[str, str],
    *,
    case_id: str,
    description: str,
    mesh_path: Path,
    boundary_condition: str,
    wavelength_um: float,
    requested_modes: int,
) -> None:
    content = f"""schema_version: 1

case:
  id: {case_id}
  description: "{description}"

mesh:
  file: {mesh_path}

material:
  model: {template_entries['material.model']}
  cover_index: {template_entries['material.cover_index']}
  substrate_index: {template_entries['material.substrate_index']}
  core_index: {template_entries['material.core_index']}
  core_width: {template_entries['material.core_width']}
  core_height: {template_entries['material.core_height']}
  core_center_x: {template_entries['material.core_center_x']}
  surface_y: {template_entries['material.surface_y']}

boundary:
  condition: {boundary_condition}

solver:
  requested_modes: {requested_modes}
  wavelength_um: {wavelength_um:.12f}
  planar_x_invariant_reduction: false

output:
  tag: case1_boundary_investigation
"""
    destination.write_text(content, encoding="utf-8")


def run_solver(
    solver_path: Path,
    case_file: Path,
    output_dir: Path,
    run_label: str,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            str(solver_path),
            "--case",
            str(case_file),
            "--output",
            str(output_dir),
            "--run-label",
            run_label,
        ],
        check=True,
    )


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]

    case_template = Path(args.case_template)
    if not case_template.is_absolute():
        case_template = repo_root / case_template
    case_template = case_template.resolve()

    reference_points_path = Path(args.reference_points)
    if not reference_points_path.is_absolute():
        reference_points_path = repo_root / reference_points_path
    reference_points_path = reference_points_path.resolve()

    solver_path = Path(args.solver)
    if not solver_path.is_absolute():
        solver_path = repo_root / solver_path
    solver_path = solver_path.resolve()

    frequencies = parse_frequencies(args.frequencies)
    if args.requested_modes <= 0:
        raise ValueError("--requested-modes must be a positive integer")
    requested_modes = args.requested_modes

    if args.output_root is None:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        investigation_root = (
            repo_root
            / "out"
            / "case1_homogeneous_channel"
            / f"investigation_{timestamp}"
        )
    else:
        investigation_root = Path(args.output_root)
        if not investigation_root.is_absolute():
            investigation_root = repo_root / investigation_root
        investigation_root = investigation_root.resolve()

    if not args.skip_build:
        subprocess.run([str((repo_root / "scripts" / "build.sh").resolve())], check=True)

    if investigation_root.exists():
        shutil.rmtree(investigation_root)
    investigation_root.mkdir(parents=True, exist_ok=True)

    generated_cases_dir = investigation_root / "generated_cases"
    points_dir = investigation_root / "points"
    generated_cases_dir.mkdir(parents=True, exist_ok=True)
    points_dir.mkdir(parents=True, exist_ok=True)

    template_entries = load_yaml_like_case(case_template)
    core_height = float(template_entries["material.core_height"])
    n2 = float(template_entries["material.substrate_index"])
    n3 = float(template_entries["material.core_index"])

    generated_mesh_by_id: dict[str, Path] = {}
    for definition in GENERATED_MESHES:
        generated_mesh_by_id[definition.mesh_id] = build_mesh_file(
            repo_root=repo_root,
            output_dir=investigation_root,
            definition=definition,
        )

    with (investigation_root / "study_manifest.csv").open(
        "w", encoding="utf-8", newline=""
    ) as stream:
        writer = csv.writer(stream)
        writer.writerow(
            [
                "study_id",
                "mesh_source",
                "boundary_condition",
                "requested_modes",
                "note",
            ]
        )
        for study in FULL_STUDIES:
            mesh_source = (
                study.mesh_file if study.mesh_file is not None else study.generated_mesh_id
            )
            writer.writerow(
                [
                    study.study_id,
                    mesh_source,
                    study.boundary_condition,
                    requested_modes,
                    study.note,
                ]
            )

    point_rows: list[dict[str, str]] = []
    for study in FULL_STUDIES:
        if study.mesh_file is not None:
            mesh_path = (repo_root / study.mesh_file).resolve()
        else:
            mesh_path = generated_mesh_by_id[study.generated_mesh_id or ""]

        previous_guided_neff: float | None = None
        for frequency in frequencies:
            k0 = compute_k0(frequency, core_height, n2, n3)
            wavelength_um = compute_wavelength_um(k0)
            value_label = format_value_label(frequency)
            run_label = f"{study.study_id}_v_{value_label}"

            case_file = generated_cases_dir / f"{run_label}.yaml"
            output_dir = points_dir / study.study_id / f"v_{value_label}"
            write_case_file(
                case_file,
                template_entries,
                case_id=f"case01_{study.study_id}_v_{value_label}",
                description=(
                    "Case 1 boundary/truncation investigation point "
                    f"with V={frequency:.2f}"
                ),
                mesh_path=mesh_path,
                boundary_condition=study.boundary_condition,
                wavelength_um=wavelength_um,
                requested_modes=requested_modes,
            )

            run_solver(solver_path, case_file, output_dir, run_label)
            candidates = load_mode_candidates(output_dir / "results", n2, n3)
            tracked_mode, selection_reason = choose_tracked_mode(
                candidates, previous_guided_neff
            )

            first_mode = candidates[0] if candidates else None
            neff_value = tracked_mode.neff if tracked_mode is not None else None
            beta_value = tracked_mode.beta if tracked_mode is not None else None
            normalized_beta = (
                compute_normalized_beta(neff_value, n2, n3) if neff_value is not None else None
            )
            guided = tracked_mode.guided_by_index if tracked_mode is not None else False
            if guided and neff_value is not None:
                previous_guided_neff = neff_value
            else:
                previous_guided_neff = None

            point_rows.append(
                {
                    "study_id": study.study_id,
                    "mesh_file": str(mesh_path),
                    "boundary_condition": study.boundary_condition,
                    "normalized_frequency": f"{frequency:.6f}",
                    "k0": f"{k0:.12f}",
                    "wavelength_um": f"{wavelength_um:.12f}",
                    "requested_modes": str(requested_modes),
                    "candidate_mode_count": str(len(candidates)),
                    "mode_status": tracked_mode.status if tracked_mode is not None else "not_applicable",
                    "selected_mode_index": (
                        str(tracked_mode.mode_index) if tracked_mode is not None else ""
                    ),
                    "selected_mode_label": (
                        tracked_mode.mode_label if tracked_mode is not None else ""
                    ),
                    "selection_reason": selection_reason,
                    "neff": f"{neff_value:.6f}" if neff_value is not None else "",
                    "beta": f"{beta_value:.6f}" if beta_value is not None else "",
                    "normalized_beta": (
                        f"{normalized_beta:.6f}" if normalized_beta is not None else ""
                    ),
                    "core_energy_fraction": (
                        f"{tracked_mode.core_energy_fraction:.6f}"
                        if tracked_mode is not None
                        and tracked_mode.core_energy_fraction is not None
                        else ""
                    ),
                    "guided": "yes" if guided else "no",
                    "first_mode_index": (
                        str(first_mode.mode_index) if first_mode is not None else ""
                    ),
                    "first_mode_neff": (
                        f"{first_mode.neff:.6f}"
                        if first_mode is not None and first_mode.neff is not None
                        else ""
                    ),
                    "first_mode_guided": (
                        "yes"
                        if first_mode is not None and first_mode.guided_by_index
                        else "no"
                    ),
                    "output_dir": str(output_dir),
                }
            )

    point_rows.sort(key=lambda row: (row["study_id"], float(row["normalized_frequency"])))

    with (investigation_root / "point_manifest.csv").open(
        "w", encoding="utf-8", newline=""
    ) as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "study_id",
                "mesh_file",
                "boundary_condition",
                "normalized_frequency",
                "k0",
                "wavelength_um",
                "requested_modes",
                "candidate_mode_count",
                "mode_status",
                "selected_mode_index",
                "selected_mode_label",
                "selection_reason",
                "neff",
                "beta",
                "normalized_beta",
                "core_energy_fraction",
                "guided",
                "first_mode_index",
                "first_mode_neff",
                "first_mode_guided",
                "output_dir",
            ],
        )
        writer.writeheader()
        writer.writerows(point_rows)

    consolidated_dir = investigation_root / "consolidated"
    consolidated_dir.mkdir(parents=True, exist_ok=True)

    with (consolidated_dir / "consolidated_curve.csv").open(
        "w", encoding="utf-8", newline=""
    ) as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "study_id",
                "normalized_frequency",
                "normalized_beta",
                "neff",
                "beta",
                "guided",
                "mode_status",
                "selected_mode_index",
                "selected_mode_label",
                "selection_reason",
                "core_energy_fraction",
                "requested_modes",
                "candidate_mode_count",
                "first_mode_index",
                "first_mode_neff",
                "first_mode_guided",
                "mesh_file",
                "boundary_condition",
            ],
        )
        writer.writeheader()
        for row in point_rows:
            writer.writerow(
                {
                    "study_id": row["study_id"],
                    "normalized_frequency": row["normalized_frequency"],
                    "normalized_beta": row["normalized_beta"],
                    "neff": row["neff"],
                    "beta": row["beta"],
                    "guided": row["guided"],
                    "mode_status": row["mode_status"],
                    "selected_mode_index": row["selected_mode_index"],
                    "selected_mode_label": row["selected_mode_label"],
                    "selection_reason": row["selection_reason"],
                    "core_energy_fraction": row["core_energy_fraction"],
                    "requested_modes": row["requested_modes"],
                    "candidate_mode_count": row["candidate_mode_count"],
                    "first_mode_index": row["first_mode_index"],
                    "first_mode_neff": row["first_mode_neff"],
                    "first_mode_guided": row["first_mode_guided"],
                    "mesh_file": row["mesh_file"],
                    "boundary_condition": row["boundary_condition"],
                }
            )

    reference_lookup: dict[str, float] = {}
    if reference_points_path.exists():
        for reference_row in read_csv_rows(reference_points_path):
            frequency = f"{float(reference_row['normalized_frequency']):.6f}"
            reference_lookup[frequency] = float(reference_row["normalized_beta"])

    comparison_rows: list[dict[str, str]] = []
    for row in point_rows:
        frequency = row["normalized_frequency"]
        if not row["normalized_beta"] or frequency not in reference_lookup:
            continue
        calculated_beta = float(row["normalized_beta"])
        reference_beta = reference_lookup[frequency]
        signed_relative_percent = (
            100.0 * (reference_beta - calculated_beta) / reference_beta
        )
        absolute_relative_percent = (
            100.0 * abs(reference_beta - calculated_beta) / abs(reference_beta)
        )
        comparison_rows.append(
            {
                "study_id": row["study_id"],
                "normalized_frequency": frequency,
                "reference_beta": f"{reference_beta:.6f}",
                "calculated_beta": f"{calculated_beta:.6f}",
                "absolute_delta_beta": f"{abs(reference_beta - calculated_beta):.6f}",
                "relative_error_percent": f"{signed_relative_percent:.6f}",
                "absolute_relative_error_percent": f"{absolute_relative_percent:.6f}",
                "mode_status": row["mode_status"],
                "guided": row["guided"],
                "selected_mode_index": row["selected_mode_index"],
                "selection_reason": row["selection_reason"],
            }
        )

    comparison_rows.sort(
        key=lambda row: (row["study_id"], float(row["normalized_frequency"]))
    )

    with (consolidated_dir / "reference_comparison.csv").open(
        "w", encoding="utf-8", newline=""
    ) as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "study_id",
                "normalized_frequency",
                "reference_beta",
                "calculated_beta",
                "absolute_delta_beta",
                "relative_error_percent",
                "absolute_relative_error_percent",
                "mode_status",
                "guided",
                "selected_mode_index",
                "selection_reason",
            ],
        )
        writer.writeheader()
        writer.writerows(comparison_rows)

    errors_by_study: dict[str, list[tuple[float, float]]] = {}
    for row in comparison_rows:
        errors_by_study.setdefault(row["study_id"], []).append(
            (
                float(row["normalized_frequency"]),
                float(row["absolute_relative_error_percent"]),
            )
        )

    study_summary_rows: list[dict[str, str]] = []
    for study in FULL_STUDIES:
        values = errors_by_study.get(study.study_id, [])
        all_errors = [item[1] for item in values]
        low_frequency_errors = [item[1] for item in values if item[0] <= 2.0]
        rows_for_study = [row for row in point_rows if row["study_id"] == study.study_id]
        tracked_guided_count = sum(1 for row in rows_for_study if row["guided"] == "yes")
        tracked_status_ok_count = sum(
            1 for row in rows_for_study if row["mode_status"] == "ok"
        )
        first_mode_guided_count = sum(
            1 for row in rows_for_study if row["first_mode_guided"] == "yes"
        )
        guided_frequencies = sorted(
            float(row["normalized_frequency"])
            for row in rows_for_study
            if row["guided"] == "yes"
        )
        low_frequency_betas = [
            float(row["normalized_beta"])
            for row in point_rows
            if row["study_id"] == study.study_id
            and row["normalized_beta"]
            and float(row["normalized_frequency"]) <= 2.0
        ]
        study_summary_rows.append(
            {
                "study_id": study.study_id,
                "boundary_condition": study.boundary_condition,
                "point_count": str(len(all_errors)),
                "tracked_status_ok_count": str(tracked_status_ok_count),
                "tracked_guided_count": str(tracked_guided_count),
                "first_mode_guided_count": str(first_mode_guided_count),
                "first_guided_frequency": (
                    f"{guided_frequencies[0]:.6f}" if guided_frequencies else ""
                ),
                "mean_absolute_relative_error_percent": (
                    f"{(sum(all_errors) / len(all_errors)):.6f}" if all_errors else ""
                ),
                "max_absolute_relative_error_percent": (
                    f"{max(all_errors):.6f}" if all_errors else ""
                ),
                "mean_abs_error_low_frequency_percent": (
                    f"{(sum(low_frequency_errors) / len(low_frequency_errors)):.6f}"
                    if low_frequency_errors
                    else ""
                ),
                "min_normalized_beta_low_frequency": (
                    f"{min(low_frequency_betas):.6f}" if low_frequency_betas else ""
                ),
            }
        )

    with (consolidated_dir / "study_summary.csv").open(
        "w", encoding="utf-8", newline=""
    ) as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "study_id",
                "boundary_condition",
                "point_count",
                "tracked_status_ok_count",
                "tracked_guided_count",
                "first_mode_guided_count",
                "first_guided_frequency",
                "mean_absolute_relative_error_percent",
                "max_absolute_relative_error_percent",
                "mean_abs_error_low_frequency_percent",
                "min_normalized_beta_low_frequency",
            ],
        )
        writer.writeheader()
        writer.writerows(study_summary_rows)

    best_study = None
    best_score = None
    for row in study_summary_rows:
        value = row["mean_abs_error_low_frequency_percent"]
        if not value:
            continue
        score = float(value)
        if best_score is None or score < best_score:
            best_score = score
            best_study = row["study_id"]

    investigation_summary = [
        "case: Case 1 boundary/truncation investigation",
        "goal: quantify low-frequency sensitivity near the cutoff region",
        "normalization_frequency: V = (k0 * b / pi) * sqrt(n3^2 - n2^2)",
        "normalization_beta: B = (n_eff^2 - n2^2) / (n3^2 - n2^2)",
        f"requested_modes_per_point: {requested_modes}",
        "mode_tracking_policy: guided index window (n2 < n_eff < n3), "
        "core-energy preference, and n_eff continuity across V",
        "studies: " + ", ".join(study.study_id for study in FULL_STUDIES),
        "reference_points_file: " + str(reference_points_path),
        "best_study_low_frequency_by_mean_abs_error: "
        + (best_study if best_study is not None else "n/a"),
        "observation: this investigation is preliminary while the Fig. 1 points remain approximate reads.",
    ]
    (consolidated_dir / "investigation_summary.txt").write_text(
        "\n".join(investigation_summary) + "\n",
        encoding="utf-8",
    )

    print(f"Investigação concluída em: {investigation_root}")
    print(f"Consolidado: {consolidated_dir}")


if __name__ == "__main__":
    main()
