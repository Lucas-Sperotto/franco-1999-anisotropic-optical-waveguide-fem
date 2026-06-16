#!/usr/bin/env python3
"""Consolidate and plot the implemented reproduction cases."""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CasePipeline:
    case_id: str
    description: str
    default_root: Path
    smoke_root: Path
    consolidate_script: str
    plot_script: str
    required_artifacts: tuple[Path, ...]


IMPLEMENTED_CASES = (
    CasePipeline(
        case_id="case1",
        description="Fig. 1 - homogeneous isotropic channel",
        default_root=Path("out/case1_homogeneous_channel/final_run"),
        smoke_root=Path("build/test_output/run_all_smoke/case1_homogeneous_channel"),
        consolidate_script="scripts/consolidate_case1_homogeneous_channel_sweep.py",
        plot_script="scripts/plot_case1_homogeneous_channel_sweep.py",
        required_artifacts=(
            Path("consolidated/reference_dispersion.csv"),
            Path("consolidated/consolidated_curve.csv"),
            Path("plots/fig1_like_reference.svg"),
        ),
    ),
    CasePipeline(
        case_id="case2",
        description="Fig. 2 - planar diffused isotropic guide",
        default_root=Path("out/planar_diffuse_sweep/final_run"),
        smoke_root=Path("build/test_output/run_all_smoke/planar_diffuse_sweep"),
        consolidate_script="scripts/consolidate_planar_diffuse_sweep.py",
        plot_script="scripts/plot_planar_diffuse_sweep.py",
        required_artifacts=(
            Path("consolidated/reference_dispersion.csv"),
            Path("consolidated/fem_vs_exact_comparison.csv"),
            Path("plots/fig2_like_reference.svg"),
        ),
    ),
    CasePipeline(
        case_id="case3",
        description="Fig. 4 - circular diffused isotropic channel",
        default_root=Path("out/case3_channel_diffused_isotropic/final_run"),
        smoke_root=Path("build/test_output/run_all_smoke/case3_channel_diffused_isotropic"),
        consolidate_script="scripts/consolidate_case3_channel_diffused_sweep.py",
        plot_script="scripts/plot_case3_channel_diffused_sweep.py",
        required_artifacts=(
            Path("consolidated/dispersion_curve.csv"),
            Path("consolidated/consolidation_summary.txt"),
            Path("plots/fig4_like_reference.svg"),
        ),
    ),
    CasePipeline(
        case_id="case4",
        description="Fig. 5 - Gaussian-Gaussian diffused channel",
        default_root=Path("out/case4_gaussian_gaussian/final_run"),
        smoke_root=Path("build/test_output/run_all_smoke/case4_gaussian_gaussian"),
        consolidate_script="scripts/consolidate_case4_gaussian_gaussian_sweep.py",
        plot_script="scripts/plot_case4_gaussian_gaussian_sweep.py",
        required_artifacts=(
            Path("consolidated/dispersion_curve.csv"),
            Path("consolidated/consolidation_summary.txt"),
            Path("plots/fig5_like_reference.svg"),
        ),
    ),
    CasePipeline(
        case_id="case5",
        description="Fig. 6 - APE LiNbO3 anisotropic guide",
        default_root=Path("out/case5_ape_linbo3/final_run"),
        smoke_root=Path("build/test_output/run_all_smoke/case5_ape_linbo3"),
        consolidate_script="scripts/consolidate_case5_ape_linbo3_sweep.py",
        plot_script="scripts/plot_case5_ape_linbo3_sweep.py",
        required_artifacts=(
            Path("consolidated/dispersion_curve.csv"),
            Path("consolidated/consolidation_summary.txt"),
            Path("plots/fig6_like_reference.svg"),
        ),
    ),
    CasePipeline(
        case_id="case6",
        description="Fig. 7 - Ti:LiNbO3 anisotropic guide",
        default_root=Path("out/case6_ti_linbo3/final_run"),
        smoke_root=Path("build/test_output/run_all_smoke/case6_ti_linbo3"),
        consolidate_script="scripts/consolidate_case6_ti_linbo3_sweep.py",
        plot_script="scripts/plot_case6_ti_linbo3_sweep.py",
        required_artifacts=(
            Path("consolidated/neff_mode_sizes.csv"),
            Path("consolidated/consolidation_summary.txt"),
            Path("plots/fig7_like_reference.svg"),
        ),
    ),
)

KNOWN_LIMITATIONS = (
    "case1/Fig. 1: quantitative reference remains visual/Marcatili-EIM, not digitized from the paper",
    "case3/Fig. 4: circular profile still keeps delta_x/delta_z disabled pending a separate gradient audit",
    "case4-case6: figures are generated, but paper overlays/digitized reference curves are not yet attached",
    "case5/Fig. 6: APE concentration uses a Gaussian proxy derived from diffusion constants, not a full 2D diffusion solve",
    "case6/Fig. 7: W_x/W_y are extracted from modal_fields.csv by FWHM binning and remain mesh-sensitive",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Consolidate and plot the currently implemented reproduction cases. "
            "Run scripts/run_all.sh first if the sweep folders do not exist."
        )
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Use the reduced roots produced by bash scripts/run_all.sh --smoke.",
    )
    parser.add_argument("--case1-root", default=None, help="Override Case 1 sweep root.")
    parser.add_argument("--case2-root", default=None, help="Override Case 2 sweep root.")
    parser.add_argument("--case3-root", default=None, help="Override Case 3 sweep root.")
    parser.add_argument("--case4-root", default=None, help="Override Case 4 sweep root.")
    parser.add_argument("--case5-root", default=None, help="Override Case 5 sweep root.")
    parser.add_argument("--case6-root", default=None, help="Override Case 6 sweep root.")
    parser.add_argument(
        "--manifest",
        default="out/reproduction_artifacts.csv",
        help="CSV manifest written with the checked final artifacts.",
    )
    return parser.parse_args()


def resolve_repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_case_root(
    repo_root: Path,
    args: argparse.Namespace,
    pipeline: CasePipeline,
) -> Path:
    override = getattr(args, f"{pipeline.case_id}_root")
    if override:
        root = Path(override)
    else:
        root = pipeline.smoke_root if args.smoke else pipeline.default_root
    if not root.is_absolute():
        root = repo_root / root
    return root.resolve()


def run_step(repo_root: Path, label: str, command: list[str]) -> None:
    print(f"{label}: {' '.join(command)}", flush=True)
    subprocess.run(command, cwd=repo_root, check=True)


def check_artifacts(root: Path, artifacts: tuple[Path, ...]) -> list[Path]:
    missing = [root / artifact for artifact in artifacts if not (root / artifact).exists()]
    if missing:
        missing_text = "\n".join(f"  - {path}" for path in missing)
        raise FileNotFoundError(f"Missing expected artifacts:\n{missing_text}")
    return [root / artifact for artifact in artifacts]


def write_manifest(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=["case_id", "description", "sweep_root", "artifact"],
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    args = parse_args()
    repo_root = resolve_repo_root()

    manifest_rows: list[dict[str, str]] = []
    for pipeline in IMPLEMENTED_CASES:
        root = resolve_case_root(repo_root, args, pipeline)
        if not root.exists():
            raise FileNotFoundError(
                f"Sweep root not found for {pipeline.case_id}: {root}\n"
                "Run bash scripts/run_all.sh first, or pass the matching --case*-root."
            )

        run_step(
            repo_root,
            f"{pipeline.case_id} consolidate",
            [sys.executable, pipeline.consolidate_script, "--sweep-root", str(root)],
        )
        run_step(
            repo_root,
            f"{pipeline.case_id} plot",
            [sys.executable, pipeline.plot_script, "--sweep-root", str(root)],
        )
        for artifact in check_artifacts(root, pipeline.required_artifacts):
            manifest_rows.append(
                {
                    "case_id": pipeline.case_id,
                    "description": pipeline.description,
                    "sweep_root": str(root),
                    "artifact": str(artifact),
                }
            )

    manifest_path = Path(args.manifest)
    if not manifest_path.is_absolute():
        manifest_path = repo_root / manifest_path
    write_manifest(manifest_path.resolve(), manifest_rows)

    print("\nImplemented artifacts verified:", flush=True)
    for row in manifest_rows:
        print(f"  {row['case_id']}: {row['artifact']}")

    print("\nKnown limitations:")
    for limitation in KNOWN_LIMITATIONS:
        print(f"  - {limitation}")

    print(f"\nArtifact manifest: {manifest_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
