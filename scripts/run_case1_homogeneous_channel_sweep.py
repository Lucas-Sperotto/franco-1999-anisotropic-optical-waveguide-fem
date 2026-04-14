#!/usr/bin/env python3
"""Run a reproducible sweep for Case 1: homogeneous isotropic channel guide."""

from __future__ import annotations

import argparse
import csv
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class StudyDefinition:
    study_id: str
    mesh_file: str
    mesh_label: str
    reference_plot: bool


FULL_NORMALIZED_FREQUENCIES = [
    0.8,
    0.9,
    1.0,
    1.1,
    1.2,
    1.3,
    1.4,
    1.6,
    1.8,
    2.0,
    2.2,
    2.4,
    2.6,
    2.8,
    3.2,
    3.6,
    4.0,
]
SMOKE_NORMALIZED_FREQUENCIES = [1.2, 2.0, 4.0]

FULL_STUDIES = [
    StudyDefinition(
        "channel_reference",
        "meshes/channel_a2b_b1_farfield.mesh",
        "reference",
        True,
    ),
]

SMOKE_STUDIES = [
    StudyDefinition(
        "channel_smoke",
        "meshes/channel_a2b_b1_smoke.mesh",
        "smoke",
        True,
    ),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Execute the normalized-frequency sweep for Case 1."
    )
    parser.add_argument(
        "--case-template",
        default="cases/homogeneous_channel_isotropic_case.yaml",
        help="Base YAML case used as the source of common parameters",
    )
    parser.add_argument(
        "--output-root",
        default=None,
        help="Sweep output root. Defaults to out/case1_homogeneous_channel/<timestamp>",
    )
    parser.add_argument(
        "--solver",
        default="build/waveguide_solver",
        help="Path to the waveguide_solver executable",
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Do not call scripts/build.sh before running the sweep",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Run a reduced sweep for automated checks",
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


def format_value_label(value: float) -> str:
    return f"{value:.2f}".replace(".", "p")


def compute_k0(normalized_frequency: float, core_height: float, n2: float, n3: float) -> float:
    if normalized_frequency <= 0.0:
        raise ValueError("The sweep requires positive normalized frequencies")
    if core_height <= 0.0:
        raise ValueError("The sweep requires a positive core height")
    delta_index_squared = n3 * n3 - n2 * n2
    if delta_index_squared <= 0.0:
        raise ValueError("The sweep requires n3 > n2")
    return normalized_frequency * 3.14159265358979323846 / (
        core_height * delta_index_squared ** 0.5
    )


def compute_wavelength_um(k0: float) -> float:
    if k0 <= 0.0:
        raise ValueError("The sweep requires a positive k0")
    return 2.0 * 3.14159265358979323846 / k0


def write_case_file(
    destination: Path,
    template_entries: dict[str, str],
    study: StudyDefinition,
    normalized_frequency: float,
    wavelength_um: float,
    repo_root: Path,
) -> None:
    case_id = f"case01_{study.study_id}_v_{format_value_label(normalized_frequency)}"
    mesh_path = (repo_root / study.mesh_file).resolve()
    content = f"""schema_version: 1

case:
  id: {case_id}
  description: "Case 1 homogeneous isotropic channel sweep point with V={normalized_frequency:.2f}"

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
  condition: {template_entries.get('boundary.condition', 'dirichlet_zero_on_boundary_nodes')}

solver:
  requested_modes: {template_entries['solver.requested_modes']}
  wavelength_um: {wavelength_um:.12f}
  planar_x_invariant_reduction: {template_entries.get('solver.planar_x_invariant_reduction', 'false')}

output:
  tag: case1_homogeneous_channel
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

    solver_path = Path(args.solver)
    if not solver_path.is_absolute():
        solver_path = repo_root / solver_path
    solver_path = solver_path.resolve()

    if args.output_root is None:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        sweep_root = repo_root / "out" / "case1_homogeneous_channel" / timestamp
    else:
        sweep_root = Path(args.output_root)
        if not sweep_root.is_absolute():
            sweep_root = repo_root / sweep_root
        sweep_root = sweep_root.resolve()

    if not args.skip_build:
        subprocess.run([str((repo_root / "scripts" / "build.sh").resolve())], check=True)

    if sweep_root.exists():
        shutil.rmtree(sweep_root)
    sweep_root.mkdir(parents=True, exist_ok=True)

    generated_cases_dir = sweep_root / "generated_cases"
    solver_cases_dir = repo_root / "build" / "generated_cases" / sweep_root.name
    points_dir = sweep_root / "points"
    if solver_cases_dir.exists():
        shutil.rmtree(solver_cases_dir)
    generated_cases_dir.mkdir(parents=True, exist_ok=True)
    solver_cases_dir.mkdir(parents=True, exist_ok=True)
    points_dir.mkdir(parents=True, exist_ok=True)

    template_entries = load_yaml_like_case(case_template)
    frequencies = (
        SMOKE_NORMALIZED_FREQUENCIES if args.smoke else FULL_NORMALIZED_FREQUENCIES
    )
    studies = SMOKE_STUDIES if args.smoke else FULL_STUDIES
    core_height = float(template_entries["material.core_height"])
    substrate_index = float(template_entries["material.substrate_index"])
    core_index = float(template_entries["material.core_index"])

    with (sweep_root / "study_manifest.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["study_id", "mesh_file", "mesh_label", "reference_plot"])
        for study in studies:
            writer.writerow(
                [
                    study.study_id,
                    study.mesh_file,
                    study.mesh_label,
                    "yes" if study.reference_plot else "no",
                ]
            )

    with (sweep_root / "point_manifest.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            [
                "study_id",
                "mesh_label",
                "normalized_frequency",
                "k0",
                "wavelength_um",
                "core_height",
                "substrate_index",
                "core_index",
                "case_file",
                "output_dir",
                "run_label",
            ]
        )

        for study in studies:
            for normalized_frequency in frequencies:
                k0 = compute_k0(
                    normalized_frequency, core_height, substrate_index, core_index
                )
                wavelength_um = compute_wavelength_um(k0)
                label = format_value_label(normalized_frequency)
                point_output_dir = points_dir / study.study_id / f"v_{label}"
                point_output_dir.mkdir(parents=True, exist_ok=True)
                case_file = solver_cases_dir / f"{study.study_id}_v_{label}.yaml"
                archived_case_file = generated_cases_dir / f"{study.study_id}_v_{label}.yaml"
                run_label = f"{study.study_id}_v_{label}"
                write_case_file(
                    case_file,
                    template_entries,
                    study,
                    normalized_frequency,
                    wavelength_um,
                    repo_root,
                )
                shutil.copyfile(case_file, archived_case_file)
                run_solver(solver_path, case_file, point_output_dir, run_label)
                writer.writerow(
                    [
                        study.study_id,
                        study.mesh_label,
                        f"{normalized_frequency:.6f}",
                        f"{k0:.12f}",
                        f"{wavelength_um:.12f}",
                        f"{core_height:.6f}",
                        f"{substrate_index:.6f}",
                        f"{core_index:.6f}",
                        str(archived_case_file),
                        str(point_output_dir),
                        run_label,
                    ]
                )

    (sweep_root / "sweep_parameters.txt").write_text(
        "\n".join(
            [
                "case: Case 1 homogeneous isotropic channel guide",
                "status: preliminary FEM sweep for the fundamental Ex-like mode",
                "assumption_geometry: a = 2b with b = 1.0 and a = 2.0",
                "reference_domain: x in [-10, 10], y in [-6, 14]",
                "smoke_domain: x in [-5, 5], y in [-3, 7]",
                "normalization_frequency: V = (k0 * b / pi) * sqrt(n3^2 - n2^2)",
                "normalization_beta: B = (n_eff^2 - n2^2) / (n3^2 - n2^2)",
                f"point_count: {len(frequencies)}",
                "reference_note: the figure overlay is pending until reference values are supplied or extracted.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
