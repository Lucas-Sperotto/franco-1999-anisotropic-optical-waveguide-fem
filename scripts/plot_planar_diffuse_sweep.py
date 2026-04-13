#!/usr/bin/env python3
"""Generate simple SVG plots for the planar diffuse isotropic sweep."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path


MODE_COLORS = {
    1: "#1b6ef3",
    2: "#e36f00",
    3: "#1c8c5e",
}


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


def map_value(value: float, value_min: float, value_max: float, pixel_min: float, pixel_max: float) -> float:
    if abs(value_max - value_min) <= 1.0e-12:
        return 0.5 * (pixel_min + pixel_max)
    alpha = (value - value_min) / (value_max - value_min)
    return pixel_min + alpha * (pixel_max - pixel_min)


def write_svg(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def generate_reference_dispersion_svg(reference_rows: list[dict[str, str]], output_path: Path) -> None:
    width = 900
    height = 560
    left = 90
    right = 40
    top = 40
    bottom = 70

    grouped: defaultdict[int, list[tuple[float, float]]] = defaultdict(list)
    for row in reference_rows:
        if row["status"] != "ok":
            continue
        grouped[int(row["mode_index"])].append(
            (float(row["diffusion_depth"]), float(row["neff"]))
        )

    for points in grouped.values():
        points.sort()

    all_x = [point[0] for points in grouped.values() for point in points]
    all_y = [point[1] for points in grouped.values() for point in points]

    x_min = min(all_x)
    x_max = max(all_x)
    y_min = min(all_y)
    y_max = max(all_y)
    y_padding = 0.02 * max(1.0, y_max - y_min)
    y_min -= y_padding
    y_max += y_padding

    plot_left = left
    plot_right = width - right
    plot_top = top
    plot_bottom = height - bottom

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff"/>',
        f'<text x="{width / 2:.1f}" y="24" text-anchor="middle" font-size="20" font-family="Arial">'
        "Caso 2 - Curva de dispersão do guia planar difuso isotrópico"
        "</text>",
        f'<line x1="{plot_left}" y1="{plot_bottom}" x2="{plot_right}" y2="{plot_bottom}" stroke="#333" stroke-width="1.5"/>',
        f'<line x1="{plot_left}" y1="{plot_bottom}" x2="{plot_left}" y2="{plot_top}" stroke="#333" stroke-width="1.5"/>',
        f'<text x="{width / 2:.1f}" y="{height - 20}" text-anchor="middle" font-size="16" font-family="Arial">b (profundidade de difusão)</text>',
        f'<text x="24" y="{height / 2:.1f}" transform="rotate(-90 24 {height / 2:.1f})" text-anchor="middle" font-size="16" font-family="Arial">n_eff</text>',
    ]

    for tick_index in range(6):
        x_value = x_min + tick_index * (x_max - x_min) / 5.0
        x_pixel = map_value(x_value, x_min, x_max, plot_left, plot_right)
        svg_parts.append(
            f'<line x1="{x_pixel:.2f}" y1="{plot_bottom}" x2="{x_pixel:.2f}" y2="{plot_bottom + 6}" stroke="#333" stroke-width="1"/>'
        )
        svg_parts.append(
            f'<text x="{x_pixel:.2f}" y="{plot_bottom + 24}" text-anchor="middle" font-size="12" font-family="Arial">{x_value:.2f}</text>'
        )

    for tick_index in range(6):
        y_value = y_min + tick_index * (y_max - y_min) / 5.0
        y_pixel = map_value(y_value, y_min, y_max, plot_bottom, plot_top)
        svg_parts.append(
            f'<line x1="{plot_left - 6}" y1="{y_pixel:.2f}" x2="{plot_left}" y2="{y_pixel:.2f}" stroke="#333" stroke-width="1"/>'
        )
        svg_parts.append(
            f'<text x="{plot_left - 10}" y="{y_pixel + 4:.2f}" text-anchor="end" font-size="12" font-family="Arial">{y_value:.4f}</text>'
        )

    legend_y = plot_top + 10
    for mode_index in sorted(grouped):
        color = MODE_COLORS.get(mode_index, "#444444")
        points = grouped[mode_index]
        polyline_points = []
        for x_value, y_value in points:
            x_pixel = map_value(x_value, x_min, x_max, plot_left, plot_right)
            y_pixel = map_value(y_value, y_min, y_max, plot_bottom, plot_top)
            polyline_points.append((x_pixel, y_pixel))
            svg_parts.append(
                f'<circle cx="{x_pixel:.2f}" cy="{y_pixel:.2f}" r="3" fill="{color}"/>'
            )
        svg_parts.append(
            f'<polyline fill="none" stroke="{color}" stroke-width="2.2" points="{build_polyline(polyline_points)}"/>'
        )
        svg_parts.append(
            f'<line x1="{plot_right - 140}" y1="{legend_y}" x2="{plot_right - 110}" y2="{legend_y}" stroke="{color}" stroke-width="2.2"/>'
        )
        svg_parts.append(
            f'<text x="{plot_right - 100}" y="{legend_y + 4}" font-size="13" font-family="Arial">Modo {mode_index}</text>'
        )
        legend_y += 24

    svg_parts.append("</svg>")
    write_svg(output_path, "\n".join(svg_parts))


def generate_mode1_sensitivity_svg(consolidated_rows: list[dict[str, str]], output_path: Path) -> None:
    width = 900
    height = 560
    left = 90
    right = 40
    top = 40
    bottom = 70

    grouped: defaultdict[str, list[tuple[float, float]]] = defaultdict(list)
    labels: dict[str, str] = {}
    for row in consolidated_rows:
        if row["status"] != "ok" or int(row["mode_index"]) != 1:
            continue
        study_id = row["study_id"]
        labels[study_id] = f"{row['study_id']} ({row['mesh_label']}, ymax={float(row['truncation_ymax']):.0f})"
        grouped[study_id].append((float(row["diffusion_depth"]), float(row["neff"])))

    for points in grouped.values():
        points.sort()

    all_x = [point[0] for points in grouped.values() for point in points]
    all_y = [point[1] for points in grouped.values() for point in points]
    x_min = min(all_x)
    x_max = max(all_x)
    y_min = min(all_y)
    y_max = max(all_y)
    y_padding = 0.02 * max(1.0, y_max - y_min)
    y_min -= y_padding
    y_max += y_padding

    plot_left = left
    plot_right = width - right
    plot_top = top
    plot_bottom = height - bottom
    palette = ["#1b6ef3", "#e36f00", "#1c8c5e", "#9a3ec8"]

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff"/>',
        f'<text x="{width / 2:.1f}" y="24" text-anchor="middle" font-size="20" font-family="Arial">'
        "Sensibilidade numérica - Modo 1"
        "</text>",
        f'<line x1="{plot_left}" y1="{plot_bottom}" x2="{plot_right}" y2="{plot_bottom}" stroke="#333" stroke-width="1.5"/>',
        f'<line x1="{plot_left}" y1="{plot_bottom}" x2="{plot_left}" y2="{plot_top}" stroke="#333" stroke-width="1.5"/>',
    ]

    legend_y = plot_top + 10
    for color_index, study_id in enumerate(sorted(grouped)):
        color = palette[color_index % len(palette)]
        polyline_points = []
        for x_value, y_value in grouped[study_id]:
            x_pixel = map_value(x_value, x_min, x_max, plot_left, plot_right)
            y_pixel = map_value(y_value, y_min, y_max, plot_bottom, plot_top)
            polyline_points.append((x_pixel, y_pixel))
        svg_parts.append(
            f'<polyline fill="none" stroke="{color}" stroke-width="2.2" points="{build_polyline(polyline_points)}"/>'
        )
        svg_parts.append(
            f'<line x1="{plot_right - 250}" y1="{legend_y}" x2="{plot_right - 220}" y2="{legend_y}" stroke="{color}" stroke-width="2.2"/>'
        )
        svg_parts.append(
            f'<text x="{plot_right - 210}" y="{legend_y + 4}" font-size="12" font-family="Arial">{labels[study_id]}</text>'
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
