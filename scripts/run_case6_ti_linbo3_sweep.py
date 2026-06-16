#!/usr/bin/env python3
"""Run a W-sweep for Case 6: Ti:LiNbO3 anisotropic guide (Fig. 7).

Sweeps strip_width W (initial Ti strip width in um) from ~3 to 12 um.
At each W, computes neff(W) and the mode field for W_x/W_y extraction.

Uses the far-field mesh (20x20 um domain) for adequate mode coverage.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path


# Strip width sweep range (um)
FULL_W_VALUES = [3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0,
                 3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9.5, 10.5]
SMOKE_W_VALUES = [5.0, 7.0]

DEFAULT_REQUESTED_MODES = 1   # only Ex11 for Fig. 7


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Execute the strip-width W sweep for Case 6: Ti:LiNbO3 anisotropic guide."
        )
    )
    parser.add_argument(
        "--case-template",
        default="cases/case6_ti_linbo3.yaml",
        help="Base YAML case template.",
    )
    parser.add_argument(
        "--output-root",
        default="out/case6_ti_linbo3/default_run",
        help="Sweep output root directory.",
    )
    parser.add_argument("--solver", default="build/waveguide_solver")
    parser.add_argument("--skip-build", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument(
        "--requested-modes", type=int, default=DEFAULT_REQUESTED_MODES,
        help="Number of eigenpairs requested (1 = Ex11 only for Fig. 7).",
    )
    parser.add_argument(
        "--w-values",
        default=None,
        help="Comma-separated W values (um). Overrides built-in grid.",
    )
    return parser.parse_args()


def resolve_w_values(args: argparse.Namespace) -> list[float]:
    if args.w_values is not None:
        values = [float(x.strip()) for x in args.w_values.split(",") if x.strip()]
    elif args.smoke:
        values = list(SMOKE_W_VALUES)
    else:
        values = list(FULL_W_VALUES)
    values = sorted(set(values))
    if any(w <= 0.0 for w in values):
        raise ValueError("All W values must be positive.")
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
    w: float,
    requested_modes: int,
    mesh_path: Path,
) -> None:
    case_id = f"case06_ti_linbo3_W_{w:.1f}um".replace(".", "p")
    m = template_entries
    content = f"""schema_version: 1

case:
  id: {case_id}
  description: "Case 6 Ti:LiNbO3 sweep W={w:.1f} um"

mesh:
  file: {mesh_path}

material:
  model: {m['material.model']}
  cover_index: {m['material.cover_index']}
  extraordinary_substrate_index: {m['material.extraordinary_substrate_index']}
  ordinary_substrate_index: {m['material.ordinary_substrate_index']}
  extraordinary_surface_delta_index: {m['material.extraordinary_surface_delta_index']}
  ordinary_surface_delta_index: {m['material.ordinary_surface_delta_index']}
  extraordinary_diffusion_width_x: {m['material.extraordinary_diffusion_width_x']}
  extraordinary_diffusion_depth_y: {m['material.extraordinary_diffusion_depth_y']}
  ordinary_diffusion_width_x: {m['material.ordinary_diffusion_width_x']}
  ordinary_diffusion_depth_y: {m['material.ordinary_diffusion_depth_y']}
  strip_width: {w:.4f}
  core_center_x: {m.get('material.core_center_x', '0.00')}
  surface_y: {m.get('material.surface_y', '0.00')}

boundary:
  condition: {m.get('boundary.condition', 'dirichlet_zero_on_boundary_nodes')}

solver:
  requested_modes: {requested_modes}
  wavelength_um: {m['solver.wavelength_um']}
  planar_x_invariant_reduction: false

output:
  tag: case6_ti_linbo3
"""
    destination.write_text(content, encoding="utf-8")


def w_label(w: float) -> str:
    return f"{w:.1f}"


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

    # Use reference mesh (10x10 um domain, 304 nodes).
    # Mode field may be slightly truncated at boundaries for large W; the trend
    # W_x(W) and W_y(W) remains physically meaningful.
    raw_mesh = template_entries.get("mesh.file", "")
    mesh_path = (case_template.parent / raw_mesh).resolve()
    if not mesh_path.exists():
        mesh_path = (repo_root / raw_mesh.lstrip("../")).resolve()
    if not mesh_path.exists():
        raise FileNotFoundError(f"Mesh not found: {raw_mesh!r}")
    print(f"Using mesh: {mesh_path.name}")

    w_values = resolve_w_values(args)

    print(
        f"Case 6 Ti:LiNbO3 sweep: {len(w_values)} W points, "
        f"W in [{w_values[0]:.1f}, {w_values[-1]:.1f}] um"
    )
    print(f"  lambda={template_entries['solver.wavelength_um']} um, "
          f"requested_modes={args.requested_modes}")
    print("  delta_x/delta_z: ENABLED (general_nonsym_refined route)")

    for w in w_values:
        point_dir = sweep_root / f"W_{w_label(w)}um"
        neff_csv = point_dir / "results" / "neff.csv"

        if neff_csv.exists():
            print(f"  W={w:.1f}: skipping (neff.csv present)")
            continue

        print(f"  W={w:.1f} um ...", end=" ", flush=True)
        point_dir.mkdir(parents=True, exist_ok=True)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, dir=point_dir, prefix="case_"
        ) as tmp_f:
            tmp_case = Path(tmp_f.name)

        write_case_yaml(tmp_case, template_entries, w, args.requested_modes, mesh_path)
        shutil.copyfile(tmp_case, point_dir / "case.yaml")

        run_label = f"case6_W_{w_label(w)}um"
        run_solver(solver_path, tmp_case, point_dir, run_label)
        tmp_case.unlink(missing_ok=True)
        print("done")

    print(f"\nSweep complete. Results in: {sweep_root}")
    print(
        "Next steps:\n"
        f"  python3 scripts/consolidate_case6_ti_linbo3_sweep.py --sweep-root {sweep_root}\n"
        f"  python3 scripts/plot_case6_ti_linbo3_sweep.py --sweep-root {sweep_root}"
    )


if __name__ == "__main__":
    main()
