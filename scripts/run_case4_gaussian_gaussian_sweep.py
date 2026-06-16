#!/usr/bin/env python3
"""Run a reproducible V-sweep for Case 4: channel diffused isotropic guide (Gaussian-Gaussian profile).

Normalization follows Franco et al. (1999), Fig. 5:
  V = (k0 * b / pi) * sqrt(n3m^2 - n2^2)
  with n2 = sqrt(2.1), n3m = 1.05*n2, b = 1.0 um

Converting V to wavelength:
  lambda_um = 2 * b * sqrt(n3m^2 - n2^2) / V
  With b=1.0, n2=sqrt(2.1), n3m=1.05*sqrt(2.1):
    n3m^2 - n2^2 = (1.05^2 - 1) * 2.1 = 0.1025 * 2.1 = 0.21525
    delta_n = sqrt(0.21525) ~= 0.46395
    lambda_um = 0.92790 / V
"""

from __future__ import annotations

import argparse
import math
import shutil
import subprocess
import tempfile
from pathlib import Path


# Physical constants for Case 4 normalization (Franco 1999 Fig. 5)
N2 = math.sqrt(2.1)          # background (substrate) index
N3M = 1.05 * math.sqrt(2.1)  # peak index
B_CORE = 1.0                  # core height (um)

_DELTA_N_SQ_NORM = N3M**2 - N2**2   # = 0.1025 * 2.1 = 0.21525
_DELTA_N_NORM = math.sqrt(_DELTA_N_SQ_NORM)   # ~= 0.46395

FULL_V_VALUES = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0,
                 1.25, 1.75, 2.25, 2.75, 3.25, 3.75, 4.25, 4.75]
SMOKE_V_VALUES = [2.0, 4.0]

DEFAULT_REQUESTED_MODES = 4


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Execute the normalised-frequency (V) sweep for Case 4: "
            "channel diffused isotropic guide with Gaussian-Gaussian index profile."
        )
    )
    parser.add_argument(
        "--case-template",
        default="cases/case4_gaussian_gaussian_channel.yaml",
        help="Base YAML case used as source of common parameters.",
    )
    parser.add_argument(
        "--output-root",
        default="out/case4_gaussian_gaussian/default_run",
        help="Sweep output root directory.",
    )
    parser.add_argument(
        "--solver",
        default="build/waveguide_solver",
        help="Path to the waveguide_solver executable.",
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Do not call scripts/build.sh before running the sweep.",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Run a reduced sweep (V=2.0 and V=4.0 only) for quick checks.",
    )
    parser.add_argument(
        "--requested-modes",
        type=int,
        default=DEFAULT_REQUESTED_MODES,
        help="Number of eigenpairs requested from the solver per sweep point.",
    )
    parser.add_argument(
        "--v-values",
        default=None,
        help="Comma-separated V values to sweep. Overrides the built-in grid.",
    )
    return parser.parse_args()


def v_to_wavelength_um(v: float) -> float:
    if v <= 0.0:
        raise ValueError(f"V must be positive, got {v}")
    return 2.0 * B_CORE * _DELTA_N_NORM / v


def resolve_v_values(args: argparse.Namespace) -> list[float]:
    if args.v_values is not None:
        values = [float(x.strip()) for x in args.v_values.split(",") if x.strip()]
        if not values:
            raise ValueError("--v-values produced an empty list.")
    elif args.smoke:
        values = list(SMOKE_V_VALUES)
    else:
        values = list(FULL_V_VALUES)
    values = sorted(set(values))
    if any(v <= 0.0 for v in values):
        raise ValueError("All V values must be positive.")
    return values


def strip_inline_comment(line: str) -> str:
    idx = line.find("#")
    return line if idx == -1 else line[:idx]


def load_yaml_entries(path: Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    current_section = ""
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = strip_inline_comment(raw_line)
        trimmed = line.strip()
        if not trimmed:
            continue
        indent = len(line) - len(line.lstrip(" "))
        if trimmed.endswith(":") and ":" not in trimmed[:-1]:
            current_section = trimmed[:-1].strip()
            continue
        if ":" not in trimmed:
            raise ValueError(f"Unrecognised line in {path}: {trimmed!r}")
        key, value = trimmed.split(":", 1)
        key = key.strip()
        value = value.strip().strip("'\"")
        full_key = f"{current_section}.{key}" if indent > 0 and current_section else key
        entries[full_key] = value
    return entries


def write_case_yaml(
    destination: Path,
    template_entries: dict[str, str],
    v: float,
    wavelength_um: float,
    requested_modes: int,
    mesh_path: Path,
) -> None:
    case_id = f"case04_gaussian_gaussian_v_{v:.3f}".replace(".", "p")
    content = f"""schema_version: 1

case:
  id: {case_id}
  description: "Case 4 Gaussian-Gaussian sweep point V={v:.3f}"

mesh:
  file: {mesh_path}

material:
  model: {template_entries['material.model']}
  cover_index: {template_entries['material.cover_index']}
  background_index: {template_entries['material.background_index']}
  peak_index: {template_entries['material.peak_index']}
  core_width: {template_entries['material.core_width']}
  core_height: {template_entries['material.core_height']}
  core_center_x: {template_entries['material.core_center_x']}
  surface_y: {template_entries['material.surface_y']}

boundary:
  condition: {template_entries.get('boundary.condition', 'dirichlet_zero_on_boundary_nodes')}

solver:
  requested_modes: {requested_modes}
  wavelength_um: {wavelength_um:.12f}
  planar_x_invariant_reduction: false

output:
  tag: case4_gaussian_gaussian
"""
    destination.write_text(content, encoding="utf-8")


def run_solver(solver_path: Path, case_file: Path, output_dir: Path, run_label: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [str(solver_path), "--case", str(case_file), "--output", str(output_dir),
         "--run-label", run_label],
        check=True,
    )


def v_label(v: float) -> str:
    return f"{v:.3f}"


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

    sweep_root = Path(args.output_root)
    if not sweep_root.is_absolute():
        sweep_root = repo_root / sweep_root
    sweep_root = sweep_root.resolve()

    if not solver_path.exists():
        raise FileNotFoundError(f"Solver not found: {solver_path}")

    if not args.skip_build:
        build_script = repo_root / "scripts" / "build.sh"
        if build_script.exists():
            subprocess.run([str(build_script)], check=True)

    sweep_root.mkdir(parents=True, exist_ok=True)
    template_entries = load_yaml_entries(case_template)

    raw_mesh = template_entries.get("mesh.file", "")
    mesh_path = (case_template.parent / raw_mesh).resolve()
    if not mesh_path.exists():
        mesh_path = (repo_root / raw_mesh.lstrip("../")).resolve()
    if not mesh_path.exists():
        raise FileNotFoundError(f"Mesh not found: {raw_mesh!r}")

    v_values = resolve_v_values(args)

    print(
        f"Case 4 sweep: {len(v_values)} point(s), "
        f"V in [{v_values[0]:.3f}, {v_values[-1]:.3f}], "
        f"output -> {sweep_root}"
    )
    print(f"  n2={N2:.9f}, n3m={N3M:.9f}, b={B_CORE}")
    print(f"  delta_n_norm={_DELTA_N_NORM:.6f}  (2*b*delta_n = {2*B_CORE*_DELTA_N_NORM:.5f} um)")
    print("  delta_x/delta_z: ENABLED (general_nonsym_refined route)")

    for v in v_values:
        point_dir = sweep_root / f"V_{v_label(v)}"
        neff_csv = point_dir / "results" / "neff.csv"

        if neff_csv.exists():
            print(f"  V={v:.3f}: skipping (neff.csv already present)")
            continue

        wavelength_um = v_to_wavelength_um(v)
        print(f"  V={v:.3f}: lambda={wavelength_um:.6f} um ...", end=" ", flush=True)

        point_dir.mkdir(parents=True, exist_ok=True)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, dir=point_dir, prefix="case_"
        ) as tmp_f:
            tmp_case = Path(tmp_f.name)

        write_case_yaml(tmp_case, template_entries, v, wavelength_um, args.requested_modes, mesh_path)
        shutil.copyfile(tmp_case, point_dir / "case.yaml")

        run_label = f"case4_v_{v_label(v)}"
        run_solver(solver_path, tmp_case, point_dir, run_label)
        tmp_case.unlink(missing_ok=True)
        print("done")

    print(f"\nSweep complete. Results in: {sweep_root}")
    print(
        "Next steps:\n"
        f"  python3 scripts/consolidate_case4_gaussian_gaussian_sweep.py --sweep-root {sweep_root}\n"
        f"  python3 scripts/plot_case4_gaussian_gaussian_sweep.py --sweep-root {sweep_root}"
    )


if __name__ == "__main__":
    main()
