#!/usr/bin/env python3
"""Run a reproducible sweep for the planar diffuse isotropic guide."""

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
    truncation_ymax: float
    dy: float
    reference_plot: bool


FULL_K0_B_VALUES = [5.0, 10.0, 15.0, 20.0, 30.0, 40.0, 50.0, 70.0, 90.0, 110.0, 150.0]
SMOKE_K0_B_VALUES = [10.0, 40.0, 150.0]

FULL_STUDIES = [
    StudyDefinition(
        "d10_reference",
        "meshes/planar_d10_a2b_reference.mesh",
        "reference",
        5.0,
        0.03125,
        True,
    ),
]

SMOKE_STUDIES = [
    StudyDefinition(
        "d10_smoke",
        "meshes/planar_d10_a2b_smoke.mesh",
        "smoke",
        5.0,
        0.125,
        True,
    ),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Execute a k0*b sweep for the planar diffuse isotropic case."
    )
    parser.add_argument(
        "--case-template",
        default="cases/planar_diffuse_isotropic_case.yaml",
        help="Base YAML case used as the source of common parameters",
    )
    parser.add_argument(
        "--output-root",
        default=None,
        help="Sweep output root. Defaults to out/planar_diffuse_sweep/<timestamp>",
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


def compute_k0(wavelength_um: float) -> float:
    if wavelength_um <= 0.0:
        raise ValueError("The sweep requires a positive solver.wavelength_um")
    return 2.0 * 3.14159265358979323846 / wavelength_um


def compute_wavelength_um(k0: float) -> float:
    if k0 <= 0.0:
        raise ValueError("The sweep requires a positive k0")
    return 2.0 * 3.14159265358979323846 / k0


def write_case_file(
    destination: Path,
    template_entries: dict[str, str],
    study: StudyDefinition,
    diffusion_depth: float,
    wavelength_um: float,
    k0_b: float,
    repo_root: Path,
) -> None:
    case_id = (
        f"case02_planar_diffuse_{study.study_id}_k0b_{format_value_label(k0_b)}"
    )
    mesh_path = (repo_root / study.mesh_file).resolve()
    content = f"""schema_version: 1

case:
  id: {case_id}
  description: "Planar diffuse isotropic sweep point {study.study_id} with assumed d={diffusion_depth:.2f} and k0*d={k0_b:.2f}"

mesh:
  file: {mesh_path}

material:
  model: {template_entries['material.model']}
  background_index: {template_entries['material.background_index']}
  cover_index: {template_entries.get('material.cover_index', template_entries['material.background_index'])}
  delta_index: {template_entries['material.delta_index']}
  diffusion_depth: {diffusion_depth:.6f}
  linearized_permittivity: {template_entries.get('material.linearized_permittivity', 'false')}

boundary:
  condition: {template_entries.get('boundary.condition', 'dirichlet_zero_on_boundary')}

solver:
  requested_modes: {template_entries['solver.requested_modes']}
  wavelength_um: {wavelength_um:.12f}
  planar_x_invariant_reduction: {template_entries.get('solver.planar_x_invariant_reduction', 'false')}

output:
  tag: planar_diffuse_sweep
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
        sweep_root = repo_root / "out" / "planar_diffuse_sweep" / timestamp
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
    assumed_b = float(template_entries["material.diffusion_depth"])
    if assumed_b <= 0.0:
        raise ValueError("The planar sweep requires a positive material.diffusion_depth")
    k0_b_values = SMOKE_K0_B_VALUES if args.smoke else FULL_K0_B_VALUES
    studies = SMOKE_STUDIES if args.smoke else FULL_STUDIES

    study_manifest_path = sweep_root / "study_manifest.csv"
    point_manifest_path = sweep_root / "point_manifest.csv"

    with study_manifest_path.open("w", encoding="utf-8", newline="") as study_stream:
        writer = csv.writer(study_stream)
        writer.writerow(
            [
                "study_id",
                "mesh_file",
                "mesh_label",
                "truncation_ymax",
                "dy",
                "reference_plot",
            ]
        )
        for study in studies:
            writer.writerow(
                [
                    study.study_id,
                    study.mesh_file,
                    study.mesh_label,
                    f"{study.truncation_ymax:.6f}",
                    f"{study.dy:.6f}",
                    "yes" if study.reference_plot else "no",
                ]
            )

    with point_manifest_path.open("w", encoding="utf-8", newline="") as point_stream:
        writer = csv.writer(point_stream)
        writer.writerow(
            [
                "study_id",
                "mesh_label",
                "truncation_ymax",
                "dy",
                "b",
                "diffusion_depth",
                "cover_index",
                "background_index",
                "delta_index",
                "linearized_permittivity",
                "wavelength_um",
                "k0",
                "k0_b",
                "planar_x_invariant_reduction",
                "case_file",
                "output_dir",
                "run_label",
            ]
        )

        for study in studies:
            for k0_b in k0_b_values:
                diffusion_depth = assumed_b
                k0 = k0_b / diffusion_depth
                wavelength_um = compute_wavelength_um(k0)
                sweep_label = format_value_label(k0_b)
                point_output_dir = points_dir / study.study_id / f"k0b_{sweep_label}"
                point_output_dir.mkdir(parents=True, exist_ok=True)
                case_file = (
                    solver_cases_dir / f"{study.study_id}_k0b_{sweep_label}.yaml"
                )
                archived_case_file = (
                    generated_cases_dir / f"{study.study_id}_k0b_{sweep_label}.yaml"
                )
                run_label = f"{study.study_id}_k0b_{sweep_label}"
                write_case_file(
                    case_file,
                    template_entries,
                    study,
                    diffusion_depth,
                    wavelength_um,
                    k0_b,
                    repo_root,
                )
                shutil.copyfile(case_file, archived_case_file)
                run_solver(solver_path, case_file, point_output_dir, run_label)
                writer.writerow(
                    [
                        study.study_id,
                        study.mesh_label,
                        f"{study.truncation_ymax:.6f}",
                        f"{study.dy:.6f}",
                        f"{diffusion_depth:.6f}",
                        f"{diffusion_depth:.6f}",
                        template_entries.get("material.cover_index", ""),
                        template_entries["material.background_index"],
                        template_entries["material.delta_index"],
                        template_entries.get("material.linearized_permittivity", "false"),
                        f"{wavelength_um:.6f}",
                        f"{k0:.6f}",
                        f"{k0_b:.6f}",
                        template_entries.get("solver.planar_x_invariant_reduction", "false"),
                        case_file,
                        point_output_dir,
                        run_label,
                    ]
                )

    parameters_path = sweep_root / "sweep_parameters.txt"
    parameters_path.write_text(
        "\n".join(
            [
                f"case_template: {case_template}",
                f"solver: {solver_path}",
                f"smoke_mode: {'yes' if args.smoke else 'no'}",
                "parameter: k0_b",
                f"assumed_diffusion_depth_b: {assumed_b:.6f}",
                "derived_parameter: k0 = (k0_b / b_assumed) and wavelength = 2*pi / k0",
                "k0_b_values: " + ", ".join(f"{value:.2f}" for value in k0_b_values),
                f"study_count: {len(studies)}",
                f"reference_plot_study: {next(study.study_id for study in studies if study.reference_plot)}",
                f"cover_index: {template_entries.get('material.cover_index', '')}",
                f"background_index: {template_entries['material.background_index']}",
                f"delta_index: {template_entries['material.delta_index']}",
                "linearized_permittivity: "
                + template_entries.get("material.linearized_permittivity", "false"),
                "planar_x_invariant_reduction: "
                + template_entries.get("solver.planar_x_invariant_reduction", "false"),
                f"domain_width_x: {10.0:.6f}",
                f"domain_width_y: {10.0:.6f}",
                "source_case_note: the source PDFs indicate a planar one-sided diffused profile, so x acts only as a numerical buffer and not as a physical guide width parameter",
                "refinement_note: mesh refinement is concentrated near the surface y = 0 and along the diffusion depth scale d = 1",
                "comparison_status: preliminary_case_2_reproduction_with_b_assumed_constant",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"Sweep concluído em: {sweep_root}")
    print(f"Manifests: {study_manifest_path} e {point_manifest_path}")


if __name__ == "__main__":
    main()
