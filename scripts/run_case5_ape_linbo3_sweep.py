#!/usr/bin/env python3
"""Run a reproducible anneal-time sweep for Case 5: APE LiNbO3 anisotropic guide (Fig. 6).

The sweep variable is the anneal time t_a (hours), which controls the diffusion widths:
  dx = 2 * sqrt(Da_x * t_a)   (lateral)
  dy = 2 * sqrt(Da_z * t_a)   (depth)

Normalization (V axis, Fig. 6):
  ne_max = ne_s + delta_ne * (1 - exp(-11))  ~= 2.32  (at C_peak = 1.0)
  NA     = sqrt(ne_max^2 - ne_s^2)
  V      = (k0 * dy / pi) * NA  = (2 * dy / lambda) * NA
  B      = (neff^2 - ne_s^2) / (ne_max^2 - ne_s^2)

Physical parameters (Franco 1999, Fig. 6, x-cut LiNbO3, 360 C anneal):
  Da_x = 0.92 um^2/h, Da_z = 0.77 um^2/h, lambda = 0.6328 um
"""

from __future__ import annotations

import argparse
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ape_diffusion_preprocessor import (
    ApePhysicalParameters,
    compute_ape_gaussian_approximation,
)


# Physical constants
DA_X = 0.92    # um^2/h lateral
DA_Z = 0.77    # um^2/h depth
LAMBDA_UM = 0.6328   # fixed wavelength
NE_S = 2.20          # extraordinary substrate index
DELTA_NE = 0.12      # max extraordinary index change
C_PEAK = 1.0         # normalized peak concentration

# Derived constants
_NE_MAX = NE_S + DELTA_NE * (1.0 - math.exp(-11.0))  # ~= 2.32
_NA_SQ = _NE_MAX**2 - NE_S**2
_NA = math.sqrt(_NA_SQ)

# Anneal time range (hours) → 15 points giving V ~ 3..12
FULL_T_VALUES_H = [0.3, 0.5, 0.75, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0, 6.0, 7.0, 8.0, 10.0]
SMOKE_T_VALUES_H = [1.0, 4.0]

DEFAULT_REQUESTED_MODES = 4


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Execute the APE diffusion sweep for Case 5: "
            "APE LiNbO3 anisotropic guide with Gaussian diffusion preprocessing."
        )
    )
    parser.add_argument(
        "--case-template",
        default="cases/case5_ape_linbo3.yaml",
        help="Base YAML case template.",
    )
    parser.add_argument(
        "--output-root",
        default="out/case5_ape_linbo3/default_run",
        help="Sweep output root directory.",
    )
    parser.add_argument("--solver", default="build/waveguide_solver")
    parser.add_argument("--skip-build", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument(
        "--requested-modes", type=int, default=DEFAULT_REQUESTED_MODES
    )
    parser.add_argument(
        "--t-values",
        default=None,
        help="Comma-separated anneal times in hours. Overrides the built-in grid.",
    )
    return parser.parse_args()


def t_to_V(t_h: float) -> float:
    dy = 2.0 * math.sqrt(DA_Z * t_h)
    return (2.0 * dy / LAMBDA_UM) * _NA


def t_to_diffusion_params(t_h: float) -> tuple[float, float]:
    """Returns (dx, dy) in um."""
    params = ApePhysicalParameters(Da_x_um2_per_h=DA_X, Da_z_um2_per_h=DA_Z,
                                   t_anneal_h=t_h, peak_concentration=C_PEAK)
    approx = compute_ape_gaussian_approximation(params)
    return approx.diffusion_width_x, approx.diffusion_depth_y


def resolve_t_values(args: argparse.Namespace) -> list[float]:
    if args.t_values is not None:
        values = [float(x.strip()) for x in args.t_values.split(",") if x.strip()]
    elif args.smoke:
        values = list(SMOKE_T_VALUES_H)
    else:
        values = list(FULL_T_VALUES_H)
    values = sorted(set(values))
    if any(t <= 0.0 for t in values):
        raise ValueError("All anneal times must be positive.")
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
            continue
        key, value = trimmed.split(":", 1)
        key = key.strip()
        value = value.strip().strip("'\"")
        full_key = f"{current_section}.{key}" if indent > 0 and current_section else key
        entries[full_key] = value
    return entries


def write_case_yaml(
    destination: Path,
    template_entries: dict[str, str],
    t_h: float,
    dx: float,
    dy: float,
    requested_modes: int,
    mesh_path: Path,
) -> None:
    v = t_to_V(t_h)
    case_id = f"case05_ape_linbo3_t_{t_h:.2f}h".replace(".", "p")
    content = f"""schema_version: 1

case:
  id: {case_id}
  description: "Case 5 APE LiNbO3 sweep t_anneal={t_h:.2f}h -> V={v:.3f}"

mesh:
  file: {mesh_path}

material:
  model: {template_entries['material.model']}
  cover_index: {template_entries['material.cover_index']}
  ordinary_index: {template_entries['material.ordinary_index']}
  extraordinary_substrate_index: {template_entries['material.extraordinary_substrate_index']}
  delta_extraordinary_index: {template_entries['material.delta_extraordinary_index']}
  peak_concentration: {C_PEAK:.6f}
  diffusion_width_x: {dx:.9f}
  diffusion_depth_y: {dy:.9f}
  core_center_x: {template_entries.get('material.core_center_x', '0.00')}
  surface_y: {template_entries.get('material.surface_y', '0.00')}

boundary:
  condition: {template_entries.get('boundary.condition', 'dirichlet_zero_on_boundary_nodes')}

solver:
  requested_modes: {requested_modes}
  wavelength_um: {LAMBDA_UM:.10f}
  planar_x_invariant_reduction: false

output:
  tag: case5_ape_linbo3
"""
    destination.write_text(content, encoding="utf-8")


def t_label(t_h: float) -> str:
    return f"{t_h:.2f}h"


def run_solver(solver_path: Path, case_file: Path, output_dir: Path, run_label: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [str(solver_path), "--case", str(case_file), "--output", str(output_dir),
         "--run-label", run_label],
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

    t_values = resolve_t_values(args)

    print(f"Case 5 APE sweep: {len(t_values)} anneal-time points")
    print(f"  Da_x={DA_X}, Da_z={DA_Z} um^2/h, lambda={LAMBDA_UM} um, C_peak={C_PEAK}")
    print(f"  ne_s={NE_S}, delta_ne={DELTA_NE}, ne_max~={_NE_MAX:.4f}, NA~={_NA:.4f}")
    print(f"  V range: [{t_to_V(t_values[0]):.2f}, {t_to_V(t_values[-1]):.2f}]")
    print(f"  delta_x/delta_z: ENABLED (general_nonsym_refined route)")

    for t_h in t_values:
        dx, dy = t_to_diffusion_params(t_h)
        v = t_to_V(t_h)
        point_dir = sweep_root / f"T_{t_label(t_h)}"
        neff_csv = point_dir / "results" / "neff.csv"

        if neff_csv.exists():
            print(f"  t={t_h:.2f}h (V={v:.2f}): skipping")
            continue

        print(f"  t={t_h:.2f}h (V={v:.2f}, dx={dx:.3f}, dy={dy:.3f}) ...", end=" ", flush=True)
        point_dir.mkdir(parents=True, exist_ok=True)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, dir=point_dir, prefix="case_"
        ) as tmp_f:
            tmp_case = Path(tmp_f.name)

        write_case_yaml(tmp_case, template_entries, t_h, dx, dy, args.requested_modes, mesh_path)
        shutil.copyfile(tmp_case, point_dir / "case.yaml")

        run_label = f"case5_t_{t_label(t_h)}"
        run_solver(solver_path, tmp_case, point_dir, run_label)
        tmp_case.unlink(missing_ok=True)
        print("done")

    print(f"\nSweep complete. Results in: {sweep_root}")
    print(
        "Next steps:\n"
        f"  python3 scripts/consolidate_case5_ape_linbo3_sweep.py --sweep-root {sweep_root}\n"
        f"  python3 scripts/plot_case5_ape_linbo3_sweep.py --sweep-root {sweep_root}"
    )


if __name__ == "__main__":
    main()
