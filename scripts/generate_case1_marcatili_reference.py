#!/usr/bin/env python3
"""Generate an adapted Marcatili reference for the Case 1 channel guide.

This script treats the Marcatili single-guide model as an auxiliary reference
for the current FEM Case 1 setup:

- core index   -> Marcatili n1
- cover index  -> Marcatili n2 (lower face)
- substrate    -> Marcatili n3 = n4 = n5

That mapping mirrors the current repository geometry by a vertical flip, while
preserving the same normalized axes used by the article-like Case 1 plot:

- normalized_frequency == b / A4
- normalized_beta      == (kz^2 - k4^2) / (k1^2 - k4^2)
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
from pathlib import Path


DEFAULT_MODES = [
    "E_y:1:1",
    "E_x:1:1",
    "E_y:2:1",
    "E_x:2:1",
    "E_y:1:2",
    "E_x:1:2",
    "E_y:2:2",
    "E_x:2:2",
    "E_y:3:1",
    "E_x:3:1",
    "E_y:1:3",
    "E_x:1:3",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate an adapted Marcatili Figure 6 reference for Case 1."
    )
    parser.add_argument(
        "--case-template",
        default="cases/homogeneous_channel_isotropic_case.yaml",
        help="Base YAML case used to recover the current Case 1 indices and geometry.",
    )
    parser.add_argument(
        "--marcatili-repo",
        default="/home/sperotto/marcatili-1969-rectangular-waveguide",
        help="Path to the Marcatili repository used as the auxiliary reference.",
    )
    parser.add_argument(
        "--output-root",
        default="out/case1_homogeneous_channel/marcatili_case1_reference",
        help="Output directory for the adapted Marcatili reference run.",
    )
    parser.add_argument(
        "--sweep-root",
        default=None,
        help=(
            "Optional Case 1 sweep root. When provided, the script copies the "
            "filtered Marcatili CSV into <sweep-root>/consolidated and produces "
            "FEM-vs-Marcatili comparison CSVs using that sweep."
        ),
    )
    parser.add_argument(
        "--point-count",
        type=int,
        default=161,
        help="Number of sweep points in normalized frequency.",
    )
    parser.add_argument(
        "--normalized-frequency-min",
        type=float,
        default=0.8,
        help="Lower bound of the Marcatili sweep.",
    )
    parser.add_argument(
        "--normalized-frequency-max",
        type=float,
        default=4.0,
        help="Upper bound of the Marcatili sweep.",
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


def write_csv_rows(
    path: Path,
    fieldnames: list[str],
    rows: list[dict[str, str]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def require_file(path: Path, description: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Missing {description}: {path}")


def interpolate(points: list[tuple[float, float]], x_value: float) -> float | None:
    if not points:
        return None
    if x_value < points[0][0] or x_value > points[-1][0]:
        return None
    for index, (x_current, y_current) in enumerate(points):
        if abs(x_value - x_current) <= 1.0e-12:
            return y_current
        if x_value < x_current:
            x_previous, y_previous = points[index - 1]
            alpha = (x_value - x_previous) / (x_current - x_previous)
            return y_previous + alpha * (y_current - y_previous)
    return points[-1][1]


def extract_curve_points(
    rows: list[dict[str, str]],
    *,
    solver_model: str,
    mode_family: str,
    p_value: int,
    q_value: int,
) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for row in rows:
        if row["solver_model"] != solver_model:
            continue
        if row["mode_family"] != mode_family:
            continue
        if int(row["p"]) != p_value or int(row["q"]) != q_value:
            continue
        beta_value = float(row["kz_normalized_against_n4"])
        if beta_value < 0.0:
            continue
        points.append((float(row["b_over_A4"]), beta_value))
    points.sort()
    return points


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]

    case_template = Path(args.case_template)
    if not case_template.is_absolute():
        case_template = repo_root / case_template
    case_template = case_template.resolve()

    marcatili_repo = Path(args.marcatili_repo).resolve()
    marcatili_binary = marcatili_repo / "build" / "bin" / "reproduce_fig6"
    marcatili_plotter = marcatili_repo / "scripts" / "plot_fig6.py"

    require_file(case_template, "Case 1 template")
    require_file(marcatili_binary, "Marcatili Figure 6 executable")
    require_file(marcatili_plotter, "Marcatili Figure 6 plotting script")

    template_entries = load_yaml_like_case(case_template)
    if template_entries.get("material.model") != "rectangular_channel_step_index":
        raise ValueError(
            "The Marcatili Case 1 adapter expects material.model = rectangular_channel_step_index"
        )

    output_root = Path(args.output_root)
    if not output_root.is_absolute():
        output_root = repo_root / output_root
    output_root = output_root.resolve()

    if output_root.exists():
        shutil.rmtree(output_root)

    inputs_dir = output_root / "inputs"
    results_dir = output_root / "results"
    consolidated_dir = output_root / "consolidated"
    plots_dir = output_root / "plots"
    inputs_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)
    consolidated_dir.mkdir(parents=True, exist_ok=True)
    plots_dir.mkdir(parents=True, exist_ok=True)

    cover_index = float(template_entries["material.cover_index"])
    substrate_index = float(template_entries["material.substrate_index"])
    core_index = float(template_entries["material.core_index"])
    core_width = float(template_entries["material.core_width"])
    core_height = float(template_entries["material.core_height"])

    adapted_input = {
        "case_id": "case1_marcatili_adapted",
        "article_target": (
            "Adapted Marcatili auxiliary reference for the FEM Case 1 "
            "homogeneous rectangular channel. The Case 1 geometry is mirrored "
            "vertically so that the lower face keeps the cover index and the "
            "remaining outer faces keep the substrate index."
        ),
        "panel_id": "CASE1-ADAPTED",
        "solver_models": ["closed_form", "exact"],
        "wavelength": 1.0e-6,
        "a_over_b": core_width / core_height,
        "n1": core_index,
        "n2": cover_index,
        "n3": substrate_index,
        "n4": substrate_index,
        "n5": substrate_index,
        "b_over_A4_min": args.normalized_frequency_min,
        "b_over_A4_max": args.normalized_frequency_max,
        "point_count": args.point_count,
        "modes": DEFAULT_MODES,
        "csv_file": str((results_dir / "case1_marcatili_adapted.csv").resolve()),
    }

    input_json_path = inputs_dir / "case1_marcatili_adapted.json"
    output_json_path = results_dir / "case1_marcatili_adapted.json"
    input_json_path.write_text(
        json.dumps(adapted_input, indent=2) + "\n",
        encoding="utf-8",
    )

    subprocess.run(
        [str(marcatili_binary), str(input_json_path), str(output_json_path)],
        check=True,
    )

    raw_csv_path = results_dir / "case1_marcatili_adapted.csv"
    require_file(raw_csv_path, "adapted Marcatili CSV report")

    subprocess.run(
        [
            "python3",
            str(marcatili_plotter),
            str(raw_csv_path),
            "--output",
            str((plots_dir / "case1_marcatili_adapted.png").resolve()),
            "--panel-title",
            "Case 1 adapted Marcatili reference",
        ],
        check=True,
    )

    raw_rows = read_csv_rows(raw_csv_path)

    normalized_rows: list[dict[str, str]] = []
    for row in raw_rows:
        beta_value = float(row["kz_normalized_against_n4"])
        if beta_value < 0.0:
            continue
        normalized_rows.append(
            {
                "panel_id": row["panel_id"],
                "variant_id": row["variant_id"],
                "curve_id": row["curve_id"],
                "solver_model": row["solver_model"],
                "mode_family": row["mode_family"],
                "p": row["p"],
                "q": row["q"],
                "normalized_frequency": f"{float(row['b_over_A4']):.6f}",
                "normalized_beta": f"{beta_value:.6f}",
                "guided": row["guided"],
                "domain_valid": row["domain_valid"],
            }
        )

    write_csv_rows(
        consolidated_dir / "marcatili_full_reference.csv",
        [
            "panel_id",
            "variant_id",
            "curve_id",
            "solver_model",
            "mode_family",
            "p",
            "q",
            "normalized_frequency",
            "normalized_beta",
            "guided",
            "domain_valid",
        ],
        normalized_rows,
    )

    ex11_rows = [
        row
        for row in normalized_rows
        if row["mode_family"] == "E_x" and row["p"] == "1" and row["q"] == "1"
    ]
    ex11_rows.sort(
        key=lambda row: (row["solver_model"], float(row["normalized_frequency"]))
    )
    write_csv_rows(
        consolidated_dir / "marcatili_ex11_reference.csv",
        [
            "panel_id",
            "variant_id",
            "curve_id",
            "solver_model",
            "mode_family",
            "p",
            "q",
            "normalized_frequency",
            "normalized_beta",
            "guided",
            "domain_valid",
        ],
        ex11_rows,
    )

    ey11_rows = [
        row
        for row in normalized_rows
        if row["mode_family"] == "E_y" and row["p"] == "1" and row["q"] == "1"
    ]
    ey11_rows.sort(
        key=lambda row: (row["solver_model"], float(row["normalized_frequency"]))
    )
    write_csv_rows(
        consolidated_dir / "marcatili_ey11_reference.csv",
        [
            "panel_id",
            "variant_id",
            "curve_id",
            "solver_model",
            "mode_family",
            "p",
            "q",
            "normalized_frequency",
            "normalized_beta",
            "guided",
            "domain_valid",
        ],
        ey11_rows,
    )

    summary_lines = [
        "status: ok",
        "reference_role: auxiliary Marcatili reference for Case 1",
        f"case_template: {case_template}",
        f"marcatili_repo: {marcatili_repo}",
        "geometry_mapping: core -> n1, lower face -> n2, left/top/right faces -> n3/n4/n5",
        (
            "normalization_note: normalized_frequency = b/A4 and "
            "normalized_beta = (kz^2-k4^2)/(k1^2-k4^2)"
        ),
        (
            f"adapted_indices: n1={core_index:.6f}, n2={cover_index:.6f}, "
            f"n3=n4=n5={substrate_index:.6f}"
        ),
        f"a_over_b: {core_width / core_height:.6f}",
        f"normalized_frequency_min: {args.normalized_frequency_min:.6f}",
        f"normalized_frequency_max: {args.normalized_frequency_max:.6f}",
        f"point_count: {args.point_count}",
        "primary_overlay_mode: E_x_11",
    ]
    (consolidated_dir / "summary.txt").write_text(
        "\n".join(summary_lines) + "\n",
        encoding="utf-8",
    )

    if args.sweep_root is None:
        return

    sweep_root = Path(args.sweep_root)
    if not sweep_root.is_absolute():
        sweep_root = repo_root / sweep_root
    sweep_root = sweep_root.resolve()

    sweep_consolidated_dir = sweep_root / "consolidated"
    sweep_consolidated_dir.mkdir(parents=True, exist_ok=True)

    shutil.copyfile(
        consolidated_dir / "marcatili_ex11_reference.csv",
        sweep_consolidated_dir / "marcatili_ex11_reference.csv",
    )
    shutil.copyfile(
        consolidated_dir / "marcatili_ey11_reference.csv",
        sweep_consolidated_dir / "marcatili_ey11_reference.csv",
    )
    shutil.copyfile(
        consolidated_dir / "marcatili_full_reference.csv",
        sweep_consolidated_dir / "marcatili_full_reference.csv",
    )

    fem_reference_path = sweep_consolidated_dir / "reference_dispersion.csv"
    if not fem_reference_path.exists():
        return

    fem_rows = read_csv_rows(fem_reference_path)
    ex11_exact_points = extract_curve_points(
        raw_rows,
        solver_model="exact",
        mode_family="E_x",
        p_value=1,
        q_value=1,
    )
    ex11_closed_form_points = extract_curve_points(
        raw_rows,
        solver_model="closed_form",
        mode_family="E_x",
        p_value=1,
        q_value=1,
    )

    comparison_rows: list[dict[str, str]] = []
    for fem_row in fem_rows:
        if fem_row["status"] != "ok" or not fem_row["normalized_beta"]:
            continue
        frequency = float(fem_row["normalized_frequency"])
        fem_beta = float(fem_row["normalized_beta"])
        exact_beta = interpolate(ex11_exact_points, frequency)
        closed_form_beta = interpolate(ex11_closed_form_points, frequency)
        if exact_beta is None or closed_form_beta is None:
            continue
        comparison_rows.append(
            {
                "normalized_frequency": f"{frequency:.6f}",
                "fem_mode_index": fem_row.get("mode_index", ""),
                "fem_raw_mode_label": fem_row.get("raw_mode_label", ""),
                "fem_guided": fem_row.get("guided", ""),
                "fem_selection_reason": fem_row.get("selection_reason", ""),
                "fem_candidate_mode_count": fem_row.get("candidate_mode_count", ""),
                "fem_beta": f"{fem_beta:.6f}",
                "marcatili_exact_beta": f"{exact_beta:.6f}",
                "marcatili_closed_form_beta": f"{closed_form_beta:.6f}",
                "delta_fem_minus_exact": f"{(fem_beta - exact_beta):.6f}",
                "delta_fem_minus_closed_form": f"{(fem_beta - closed_form_beta):.6f}",
                "abs_error_vs_exact_percent": (
                    f"{100.0 * abs(fem_beta - exact_beta) / abs(exact_beta):.6f}"
                ),
                "abs_error_vs_closed_form_percent": (
                    f"{100.0 * abs(fem_beta - closed_form_beta) / abs(closed_form_beta):.6f}"
                ),
            }
        )

    write_csv_rows(
        sweep_consolidated_dir / "fem_vs_marcatili_ex11.csv",
        [
            "normalized_frequency",
            "fem_mode_index",
            "fem_raw_mode_label",
            "fem_guided",
            "fem_selection_reason",
            "fem_candidate_mode_count",
            "fem_beta",
            "marcatili_exact_beta",
            "marcatili_closed_form_beta",
            "delta_fem_minus_exact",
            "delta_fem_minus_closed_form",
            "abs_error_vs_exact_percent",
            "abs_error_vs_closed_form_percent",
        ],
        comparison_rows,
    )


if __name__ == "__main__":
    main()
