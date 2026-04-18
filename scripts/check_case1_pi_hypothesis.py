#!/usr/bin/env python3
"""Check the Case 1 normalization hypothesis with and without pi."""

from __future__ import annotations

import argparse
import csv
import math
import subprocess
from dataclasses import dataclass
from pathlib import Path


DEFAULT_FREQUENCIES = [0.8, 1.0, 1.2, 2.0]


@dataclass(frozen=True)
class ModeCandidate:
    mode_index: int
    status: str
    neff: float | None
    beta: float | None
    guided_by_index: bool
    core_energy_fraction: float | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare Case 1 normalization with and without pi."
    )
    parser.add_argument(
        "--solver",
        default="build/waveguide_solver",
        help="Path to the waveguide_solver executable",
    )
    parser.add_argument(
        "--mesh",
        default="meshes/channel_a2b_b1_farfield.mesh",
        help="Mesh used for the quick hypothesis check",
    )
    parser.add_argument(
        "--output-root",
        default="out/case1_homogeneous_channel/pi_hypothesis_check",
        help="Output folder for generated cases and CSV summary",
    )
    parser.add_argument(
        "--frequencies",
        default=",".join(f"{value:.1f}" for value in DEFAULT_FREQUENCIES),
        help="Comma-separated normalized frequencies to test",
    )
    parser.add_argument(
        "--requested-modes",
        type=int,
        default=16,
        help="Number of eigenpairs requested per point",
    )
    return parser.parse_args()


def parse_frequencies(raw_values: str) -> list[float]:
    values = [float(token.strip()) for token in raw_values.split(",") if token.strip()]
    if not values:
        raise ValueError("At least one frequency must be provided")
    for value in values:
        if value <= 0.0:
            raise ValueError("Frequencies must be positive")
    return values


def compute_k0(*, normalized_frequency: float, with_pi: bool, b: float, n2: float, n3: float) -> float:
    delta = math.sqrt(n3 * n3 - n2 * n2)
    if with_pi:
        return normalized_frequency * math.pi / (b * delta)
    return normalized_frequency / (b * delta)


def compute_wavelength_um(k0: float) -> float:
    return 2.0 * math.pi / k0


def write_case(
    path: Path, *, mesh_path: Path, wavelength_um: float, requested_modes: int
) -> None:
    content = f"""schema_version: 1

case:
  id: case01_pi_hypothesis
  description: "Case 1 pi normalization hypothesis check"

mesh:
  file: {mesh_path}

material:
  model: rectangular_channel_step_index
  cover_index: 1.00
  substrate_index: 1.43
  core_index: 1.50
  core_width: 2.00
  core_height: 1.00
  core_center_x: 0.00
  surface_y: 0.00

boundary:
  condition: dirichlet_zero_on_boundary_nodes

solver:
  requested_modes: {requested_modes}
  wavelength_um: {wavelength_um:.12f}
  planar_x_invariant_reduction: false

output:
  tag: case1_pi_hypothesis
"""
    path.write_text(content, encoding="utf-8")


def parse_optional_float(raw_value: str) -> float | None:
    value = raw_value.strip()
    if not value:
        return None
    return float(value)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def load_mode_candidates(results_dir: Path, n2: float, n3: float) -> list[ModeCandidate]:
    neff_rows = read_csv_rows(results_dir / "neff.csv")
    metrics_path = results_dir / "modal_metrics.csv"
    metrics_by_index: dict[int, dict[str, str]] = {}
    if metrics_path.exists():
        for row in read_csv_rows(metrics_path):
            metrics_by_index[int(row["mode_index"])] = row

    candidates: list[ModeCandidate] = []
    for row in neff_rows:
        mode_index = int(row["mode_index"])
        metrics = metrics_by_index.get(mode_index, {})
        neff = parse_optional_float(row.get("neff", ""))
        beta = parse_optional_float(row.get("beta", ""))
        guided = neff is not None and n2 < neff < n3
        guided_token = metrics.get("guided_by_index", "").strip().lower()
        if guided_token in {"yes", "true", "1"}:
            guided = True
        elif guided_token in {"no", "false", "0"}:
            guided = False

        candidates.append(
            ModeCandidate(
                mode_index=mode_index,
                status=row["status"],
                neff=neff,
                beta=beta,
                guided_by_index=guided,
                core_energy_fraction=parse_optional_float(
                    metrics.get("core_energy_fraction", "")
                ),
            )
        )
    return candidates


def choose_mode(
    candidates: list[ModeCandidate], previous_guided_neff: float | None
) -> tuple[ModeCandidate | None, str]:
    valid = [
        candidate
        for candidate in candidates
        if candidate.status == "ok" and candidate.neff is not None
    ]
    if not valid:
        return None, "no_valid_mode"

    guided = [candidate for candidate in valid if candidate.guided_by_index]

    def core_fraction(candidate: ModeCandidate) -> float:
        return (
            candidate.core_energy_fraction
            if candidate.core_energy_fraction is not None
            else -1.0
        )

    if guided:
        if previous_guided_neff is None:
            selected = max(
                guided,
                key=lambda candidate: (
                    core_fraction(candidate),
                    candidate.neff if candidate.neff is not None else -1.0,
                    -candidate.mode_index,
                ),
            )
            return selected, "guided_entry_max_core_fraction"

        selected = min(
            guided,
            key=lambda candidate: (
                abs((candidate.neff or 0.0) - previous_guided_neff),
                -core_fraction(candidate),
                -(candidate.neff if candidate.neff is not None else -1.0),
                candidate.mode_index,
            ),
        )
        return selected, "guided_continuity"

    selected = max(
        valid,
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
    solver_path = Path(args.solver)
    if not solver_path.is_absolute():
        solver_path = repo_root / solver_path
    solver_path = solver_path.resolve()

    mesh_path = Path(args.mesh)
    if not mesh_path.is_absolute():
        mesh_path = repo_root / mesh_path
    mesh_path = mesh_path.resolve()

    output_root = Path(args.output_root)
    if not output_root.is_absolute():
        output_root = repo_root / output_root
    output_root = output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    frequencies = parse_frequencies(args.frequencies)
    if args.requested_modes <= 0:
        raise ValueError("--requested-modes must be a positive integer")
    n2 = 1.43
    n3 = 1.50
    b = 1.0

    rows: list[dict[str, str]] = []
    for with_pi in (True, False):
        formula_label = "with_pi" if with_pi else "without_pi"
        previous_guided_neff: float | None = None
        for frequency in frequencies:
            k0 = compute_k0(
                normalized_frequency=frequency,
                with_pi=with_pi,
                b=b,
                n2=n2,
                n3=n3,
            )
            wavelength_um = compute_wavelength_um(k0)

            point_id = f"{formula_label}_v_{frequency:.2f}".replace(".", "p")
            point_dir = output_root / "points" / point_id
            point_dir.mkdir(parents=True, exist_ok=True)
            case_file = point_dir / "case.yaml"
            write_case(
                case_file,
                mesh_path=mesh_path,
                wavelength_um=wavelength_um,
                requested_modes=args.requested_modes,
            )
            subprocess.run(
                [
                    str(solver_path),
                    "--case",
                    str(case_file),
                    "--output",
                    str(point_dir),
                    "--run-label",
                    point_id,
                ],
                check=True,
            )

            candidates = load_mode_candidates(point_dir / "results", n2, n3)
            selected_mode, selection_reason = choose_mode(
                candidates, previous_guided_neff
            )
            neff = selected_mode.neff if selected_mode is not None else float("nan")
            status = selected_mode.status if selected_mode is not None else "not_applicable"
            if (
                selected_mode is not None
                and selected_mode.neff is not None
                and selected_mode.guided_by_index
            ):
                previous_guided_neff = selected_mode.neff
            else:
                previous_guided_neff = None
            normalized_beta = (
                (neff * neff - n2 * n2) / (n3 * n3 - n2 * n2)
                if status == "ok" and selected_mode is not None and selected_mode.neff is not None
                else float("nan")
            )
            rows.append(
                {
                    "formula": formula_label,
                    "normalized_frequency": f"{frequency:.6f}",
                    "k0": f"{k0:.12f}",
                    "wavelength_um": f"{wavelength_um:.12f}",
                    "requested_modes": str(args.requested_modes),
                    "candidate_mode_count": str(len(candidates)),
                    "selected_mode_index": (
                        str(selected_mode.mode_index) if selected_mode is not None else ""
                    ),
                    "selection_reason": selection_reason,
                    "guided": (
                        "yes" if selected_mode is not None and selected_mode.guided_by_index else "no"
                    ),
                    "neff": f"{neff:.6f}" if status == "ok" else "",
                    "normalized_beta": (
                        f"{normalized_beta:.6f}" if status == "ok" else ""
                    ),
                    "status": status,
                }
            )

    rows.sort(key=lambda row: (row["formula"], float(row["normalized_frequency"])))
    summary_path = output_root / "normalization_hypothesis_check.csv"
    with summary_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "formula",
                "normalized_frequency",
                "k0",
                "wavelength_um",
                "requested_modes",
                "candidate_mode_count",
                "selected_mode_index",
                "selection_reason",
                "guided",
                "neff",
                "normalized_beta",
                "status",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Hypothesis check saved to: {summary_path}")


if __name__ == "__main__":
    main()
