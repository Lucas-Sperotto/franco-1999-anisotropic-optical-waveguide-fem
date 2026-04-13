#!/usr/bin/env python3
"""Generate SVG plots for the planar diffuse isotropic sweep."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path


MODE_COLORS = {
    "TE0": "#1b6ef3",
    "TE1": "#e36f00",
    "TE2": "#1c8c5e",
}

FIG2_X_MIN = 0.0
FIG2_X_MAX = 160.0
FIG2_Y_MIN = 2.200
FIG2_Y_MAX = 2.208


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate SVG plots from a consolidated planar sweep."
    )
    parser.add_argument(
        "--sweep-root",
        required=True,
        help="Sweep root produced by scripts/run_planar_diffuse_sweep.py",
    )
    return parser.parse_args()


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def build_polyline(points: list[tuple[float, float]]) -> str:
    return " ".join(f"{x:.2f},{y:.2f}" for x, y in points)


def map_value(
    value: float,
    value_min: float,
    value_max: float,
    pixel_min: float,
    pixel_max: float,
) -> float:
    if abs(value_max - value_min) <= 1.0e-12:
        return 0.5 * (pixel_min + pixel_max)
    alpha = (value - value_min) / (value_max - value_min)
    return pixel_min + alpha * (pixel_max - pixel_min)


def write_svg(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def append_plot_frame(
    svg_parts: list[str],
    *,
    width: int,
    height: int,
    left: int,
    right: int,
    top: int,
    bottom: int,
    title: str,
    subtitle: str,
    x_label: str,
    y_label: str,
) -> tuple[float, float, float, float]:
    plot_left = left
    plot_right = width - right
    plot_top = top
    plot_bottom = height - bottom

    svg_parts.extend(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
            f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff"/>',
            f'<text x="{width / 2:.1f}" y="28" text-anchor="middle" font-size="21" font-family="Arial">{title}</text>',
            f'<text x="{width / 2:.1f}" y="50" text-anchor="middle" font-size="13" fill="#555" font-family="Arial">{subtitle}</text>',
            f'<line x1="{plot_left}" y1="{plot_bottom}" x2="{plot_right}" y2="{plot_bottom}" stroke="#333" stroke-width="1.5"/>',
            f'<line x1="{plot_left}" y1="{plot_bottom}" x2="{plot_left}" y2="{plot_top}" stroke="#333" stroke-width="1.5"/>',
            f'<text x="{width / 2:.1f}" y="{height - 20}" text-anchor="middle" font-size="16" font-family="Arial">{x_label}</text>',
            f'<text x="28" y="{height / 2:.1f}" transform="rotate(-90 28 {height / 2:.1f})" text-anchor="middle" font-size="16" font-family="Arial">{y_label}</text>',
        ]
    )

    return plot_left, plot_right, plot_top, plot_bottom


def append_grid_and_ticks(
    svg_parts: list[str],
    *,
    plot_left: float,
    plot_right: float,
    plot_top: float,
    plot_bottom: float,
    x_values: list[float],
    y_values: list[float],
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
) -> None:
    for x_value in x_values:
        x_pixel = map_value(x_value, x_min, x_max, plot_left, plot_right)
        svg_parts.append(
            f'<line x1="{x_pixel:.2f}" y1="{plot_top}" x2="{x_pixel:.2f}" y2="{plot_bottom}" stroke="#e6e6e6" stroke-width="1"/>'
        )
        svg_parts.append(
            f'<line x1="{x_pixel:.2f}" y1="{plot_bottom}" x2="{x_pixel:.2f}" y2="{plot_bottom + 6}" stroke="#333" stroke-width="1"/>'
        )
        svg_parts.append(
            f'<text x="{x_pixel:.2f}" y="{plot_bottom + 24}" text-anchor="middle" font-size="12" font-family="Arial">{x_value:.0f}</text>'
        )

    for y_value in y_values:
        y_pixel = map_value(y_value, y_min, y_max, plot_bottom, plot_top)
        svg_parts.append(
            f'<line x1="{plot_left}" y1="{y_pixel:.2f}" x2="{plot_right}" y2="{y_pixel:.2f}" stroke="#e6e6e6" stroke-width="1"/>'
        )
        svg_parts.append(
            f'<line x1="{plot_left - 6}" y1="{y_pixel:.2f}" x2="{plot_left}" y2="{y_pixel:.2f}" stroke="#333" stroke-width="1"/>'
        )
        svg_parts.append(
            f'<text x="{plot_left - 10}" y="{y_pixel + 4:.2f}" text-anchor="end" font-size="12" font-family="Arial">{y_value:.3f}</text>'
        )


def generate_reference_dispersion_svg(
    reference_rows: list[dict[str, str]], output_path: Path
) -> None:
    width = 920
    height = 600
    left = 90
    right = 50
    top = 78
    bottom = 78

    grouped: defaultdict[str, list[tuple[float, float]]] = defaultdict(list)
    for row in reference_rows:
        if row["status"] != "ok":
            continue
        grouped[row["mode_label"]].append((float(row["k0_b"]), float(row["neff"])))

    for points in grouped.values():
        points.sort()

    svg_parts: list[str] = []
    plot_left, plot_right, plot_top, plot_bottom = append_plot_frame(
        svg_parts,
        width=width,
        height=height,
        left=left,
        right=right,
        top=top,
        bottom=bottom,
        title="Caso 2 - Curva de dispersão comparável à Fig. 2",
        subtitle="Comparação preliminar: eixos e grandezas alinhados à Fig. 2; ainda não é validação final.",
        x_label="k0 b",
        y_label="n_eff",
    )

    append_grid_and_ticks(
        svg_parts,
        plot_left=plot_left,
        plot_right=plot_right,
        plot_top=plot_top,
        plot_bottom=plot_bottom,
        x_values=[0.0, 40.0, 80.0, 120.0, 160.0],
        y_values=[2.200, 2.202, 2.204, 2.206, 2.208],
        x_min=FIG2_X_MIN,
        x_max=FIG2_X_MAX,
        y_min=FIG2_Y_MIN,
        y_max=FIG2_Y_MAX,
    )

    legend_y = plot_top + 20
    for mode_label in ("TE0", "TE1", "TE2"):
        points = grouped.get(mode_label, [])
        if not points:
            continue
        color = MODE_COLORS.get(mode_label, "#444444")
        polyline_points = []
        for x_value, y_value in points:
            x_pixel = map_value(x_value, FIG2_X_MIN, FIG2_X_MAX, plot_left, plot_right)
            y_pixel = map_value(y_value, FIG2_Y_MIN, FIG2_Y_MAX, plot_bottom, plot_top)
            polyline_points.append((x_pixel, y_pixel))
            svg_parts.append(
                f'<circle cx="{x_pixel:.2f}" cy="{y_pixel:.2f}" r="3.2" fill="{color}"/>'
            )
        svg_parts.append(
            f'<polyline fill="none" stroke="{color}" stroke-width="2.4" points="{build_polyline(polyline_points)}"/>'
        )
        svg_parts.append(
            f'<line x1="{plot_right - 120}" y1="{legend_y}" x2="{plot_right - 88}" y2="{legend_y}" stroke="{color}" stroke-width="2.4"/>'
        )
        svg_parts.append(
            f'<text x="{plot_right - 76}" y="{legend_y + 4}" font-size="13" font-family="Arial">{mode_label}</text>'
        )
        legend_y += 24

    svg_parts.append(
        f'<text x="{plot_left}" y="{height - 46}" font-size="12" fill="#666" font-family="Arial">Saída consolidada em k0 b e n_eff para comparação preliminar com a Fig. 2.</text>'
    )
    svg_parts.append("</svg>")
    write_svg(output_path, "\n".join(svg_parts))


def generate_mode1_sensitivity_svg(
    consolidated_rows: list[dict[str, str]], output_path: Path
) -> None:
    width = 920
    height = 600
    left = 90
    right = 50
    top = 78
    bottom = 78

    grouped: defaultdict[str, list[tuple[float, float]]] = defaultdict(list)
    labels: dict[str, str] = {}
    for row in consolidated_rows:
        if row["status"] != "ok" or row["mode_label"] != "TE0":
            continue
        study_id = row["study_id"]
        labels[study_id] = (
            f"{row['study_id']} ({row['mesh_label']}, ymax={float(row['truncation_ymax']):.0f})"
        )
        grouped[study_id].append((float(row["k0_b"]), float(row["neff"])))

    for points in grouped.values():
        points.sort()

    svg_parts: list[str] = []
    plot_left, plot_right, plot_top, plot_bottom = append_plot_frame(
        svg_parts,
        width=width,
        height=height,
        left=left,
        right=right,
        top=top,
        bottom=bottom,
        title="Sensibilidade numérica preliminar - TE0",
        subtitle="Mesmo eixo k0 b da Fig. 2 para facilitar comparação entre malhas e truncamentos.",
        x_label="k0 b",
        y_label="n_eff",
    )

    all_y = [point[1] for points in grouped.values() for point in points]
    y_min = min(all_y) if all_y else FIG2_Y_MIN
    y_max = max(all_y) if all_y else FIG2_Y_MAX
    y_padding = 0.1 * max(1.0e-4, y_max - y_min)
    y_min -= y_padding
    y_max += y_padding

    append_grid_and_ticks(
        svg_parts,
        plot_left=plot_left,
        plot_right=plot_right,
        plot_top=plot_top,
        plot_bottom=plot_bottom,
        x_values=[0.0, 40.0, 80.0, 120.0, 160.0],
        y_values=[
            y_min,
            y_min + 0.25 * (y_max - y_min),
            y_min + 0.50 * (y_max - y_min),
            y_min + 0.75 * (y_max - y_min),
            y_max,
        ],
        x_min=FIG2_X_MIN,
        x_max=FIG2_X_MAX,
        y_min=y_min,
        y_max=y_max,
    )

    palette = ["#1b6ef3", "#e36f00", "#1c8c5e", "#9a3ec8"]
    legend_y = plot_top + 20
    for color_index, study_id in enumerate(sorted(grouped)):
        color = palette[color_index % len(palette)]
        polyline_points = []
        for x_value, y_value in grouped[study_id]:
            x_pixel = map_value(x_value, FIG2_X_MIN, FIG2_X_MAX, plot_left, plot_right)
            y_pixel = map_value(y_value, y_min, y_max, plot_bottom, plot_top)
            polyline_points.append((x_pixel, y_pixel))
        svg_parts.append(
            f'<polyline fill="none" stroke="{color}" stroke-width="2.2" points="{build_polyline(polyline_points)}"/>'
        )
        svg_parts.append(
            f'<line x1="{plot_right - 260}" y1="{legend_y}" x2="{plot_right - 228}" y2="{legend_y}" stroke="{color}" stroke-width="2.2"/>'
        )
        svg_parts.append(
            f'<text x="{plot_right - 216}" y="{legend_y + 4}" font-size="12" font-family="Arial">{labels[study_id]}</text>'
        )
        legend_y += 22

    svg_parts.append("</svg>")
    write_svg(output_path, "\n".join(svg_parts))


def main() -> None:
    args = parse_args()
    sweep_root = Path(args.sweep_root).resolve()
    consolidated_dir = sweep_root / "consolidated"
    plots_dir = sweep_root / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    consolidated_rows = read_csv_rows(consolidated_dir / "consolidated_modes.csv")
    reference_rows = read_csv_rows(consolidated_dir / "reference_dispersion.csv")

    generate_reference_dispersion_svg(
        reference_rows, plots_dir / "fig2_like_reference.svg"
    )
    generate_mode1_sensitivity_svg(
        consolidated_rows, plots_dir / "mode1_sensitivity.svg"
    )

    print(f"Gráficos gerados em: {plots_dir}")


if __name__ == "__main__":
    main()
