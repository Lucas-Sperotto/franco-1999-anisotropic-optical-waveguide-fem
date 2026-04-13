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


FULL_DIFFUSION_DEPTHS = [0.25, 0.50, 0.75, 1.00, 1.25, 1.50, 2.00, 2.50, 3.00]
SMOKE_DIFFUSION_DEPTHS = [0.50, 1.00, 2.00]

STUDIES = [
    StudyDefinition("y4_coarse", "meshes/planar_strip_y4_coarse.mesh", "coarse", 4.0, 1.0, False),
    StudyDefinition("y4_fine", "meshes/planar_strip_y4_fine.mesh", "fine", 4.0, 0.5, False),
    StudyDefinition("y6_coarse", "meshes/planar_strip_y6_coarse.mesh", "coarse", 6.0, 1.0, False),
    StudyDefinition("y6_fine", "meshes/planar_strip_y6_fine.mesh", "fine", 6.0, 0.5, True),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Execute a diffusion-depth sweep for the planar diffuse isotropic case."
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


def format_depth_label(depth: float) -> str:
    return f"{depth:.2f}".replace(".", "p")


def write_case_file(
    destination: Path,
    template_entries: dict[str, str],
    study: StudyDefinition,
    diffusion_depth: float,
    repo_root: Path,
) -> None:
    case_id = f"case02_planar_diffuse_{study.study_id}_b_{format_depth_label(diffusion_depth)}"
    mesh_path = (repo_root / study.mesh_file).resolve()
    content = f"""schema_version: 1

case:
  id: {case_id}
  description: "Planar diffuse isotropic sweep point {study.study_id} with b={diffusion_depth:.2f}"

mesh:
  file: {mesh_path}

material:
  model: {template_entries['material.model']}
  background_index: {template_entries['material.background_index']}
  delta_index: {template_entries['material.delta_index']}
  diffusion_depth: {diffusion_depth:.6f}

boundary:
  condition: {template_entries.get('boundary.condition', 'dirichlet_zero_on_boundary')}

solver:
  requested_modes: {template_entries['solver.requested_modes']}
  wavelength_um: {template_entries['solver.wavelength_um']}

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
    points_dir = sweep_root / "points"
    generated_cases_dir.mkdir(parents=True, exist_ok=True)
    points_dir.mkdir(parents=True, exist_ok=True)

    template_entries = load_yaml_like_case(case_template)
    diffusion_depths = SMOKE_DIFFUSION_DEPTHS if args.smoke else FULL_DIFFUSION_DEPTHS

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
        for study in STUDIES:
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
                "diffusion_depth",
                "case_file",
                "output_dir",
                "run_label",
            ]
        )

        for study in STUDIES:
            for diffusion_depth in diffusion_depths:
                depth_label = format_depth_label(diffusion_depth)
                case_file = generated_cases_dir / f"{study.study_id}_b_{depth_label}.yaml"
                point_output_dir = points_dir / study.study_id / f"b_{depth_label}"
                run_label = f"{study.study_id}_b_{depth_label}"
                write_case_file(case_file, template_entries, study, diffusion_depth, repo_root)
                run_solver(solver_path, case_file, point_output_dir, run_label)
                writer.writerow(
                    [
                        study.study_id,
                        study.mesh_label,
                        f"{study.truncation_ymax:.6f}",
                        f"{study.dy:.6f}",
                        f"{diffusion_depth:.6f}",
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
                "parameter: diffusion_depth",
                "diffusion_depths: "
                + ", ".join(f"{value:.2f}" for value in diffusion_depths),
                f"study_count: {len(STUDIES)}",
                "reference_plot_study: y6_fine",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"Sweep concluído em: {sweep_root}")
    print(f"Manifests: {study_manifest_path} e {point_manifest_path}")


if __name__ == "__main__":
    main()
