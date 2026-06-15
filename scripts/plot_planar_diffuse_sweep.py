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
FIG2_X_MAX = 150.0
FIG2_Y_MIN = 2.198
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
    parser.add_argument(
        "--legend-y-offset",
        type=float,
        default=0.0,
        help="Additional vertical offset, in SVG pixels, applied to legend blocks.",
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


def build_even_ticks(value_min: float, value_max: float, count: int) -> list[float]:
    if count <= 1:
        return [value_min]
    step = (value_max - value_min) / float(count - 1)
    return [value_min + step * index for index in range(count)]


def padded_max(values: list[float], minimum: float) -> float:
    if not values:
        return minimum
    return max(minimum, max(values) * 1.10)


def format_error_tick(value: float, value_max: float) -> str:
    if value_max >= 1.0:
        return f"{value:.1f}"
    if value_max >= 0.01:
        return f"{value:.3f}"
    return f"{value:.4f}"


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
            f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#ffffff"/><stop offset="100%" stop-color="#f7f9fc"/></linearGradient></defs>',
            f'<rect x="0" y="0" width="{width}" height="{height}" fill="url(#bg)"/>',
            f'<text x="{width / 2:.1f}" y="30" text-anchor="middle" font-size="21" font-family="Arial">{title}</text>',
            f'<text x="{width / 2:.1f}" y="52" text-anchor="middle" font-size="13" fill="#4d5b6b" font-family="Arial">{subtitle}</text>',
            f'<rect x="{plot_left - 1}" y="{plot_top - 1}" width="{plot_right - plot_left + 2}" height="{plot_bottom - plot_top + 2}" fill="#ffffff" stroke="#d6dbe4" stroke-width="1"/>',
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
    reference_rows: list[dict[str, str]],
    analytic_reference_rows: list[dict[str, str]],
    output_path: Path,
    legend_y_offset: float,
) -> None:
    width = 960
    height = 620
    left = 90
    right = 50
    top = 78
    bottom = 78

    grouped: defaultdict[str, list[tuple[float, float]]] = defaultdict(list)
    for row in reference_rows:
        if row["status"] != "ok":
            continue
        grouped[row["mode_label"]].append((float(row["k0_b"]), float(row["neff"])))

    analytic_grouped: defaultdict[str, list[tuple[float, float]]] = defaultdict(list)
    for row in analytic_reference_rows:
        analytic_grouped[row["mode_label"]].append((float(row["k0_b"]), float(row["neff"])))

    for points in grouped.values():
        points.sort()
    for points in analytic_grouped.values():
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
        subtitle="Comparação preliminar FEM vs. solução TE exata do artigo [6-19]; não é validação final.",
        x_label="k0 b",
        y_label="n_eff",
    )

    append_grid_and_ticks(
        svg_parts,
        plot_left=plot_left,
        plot_right=plot_right,
        plot_top=plot_top,
        plot_bottom=plot_bottom,
        x_values=[0.0, 30.0, 60.0, 90.0, 120.0, 150.0],
        y_values=[2.198, 2.200, 2.202, 2.204, 2.206, 2.208],
        x_min=FIG2_X_MIN,
        x_max=FIG2_X_MAX,
        y_min=FIG2_Y_MIN,
        y_max=FIG2_Y_MAX,
    )

    legend_y = plot_top + 20 + legend_y_offset
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
            f'<text x="{plot_right - 76}" y="{legend_y + 4}" font-size="13" font-family="Arial">{mode_label} FEM</text>'
        )
        legend_y += 24

        analytic_points = analytic_grouped.get(mode_label, [])
        if analytic_points:
            analytic_polyline_points = []
            for x_value, y_value in analytic_points:
                x_pixel = map_value(x_value, FIG2_X_MIN, FIG2_X_MAX, plot_left, plot_right)
                y_pixel = map_value(y_value, FIG2_Y_MIN, FIG2_Y_MAX, plot_bottom, plot_top)
                analytic_polyline_points.append((x_pixel, y_pixel))
                svg_parts.append(
                    f'<rect x="{x_pixel - 2.7:.2f}" y="{y_pixel - 2.7:.2f}" width="5.4" height="5.4" fill="#ffffff" stroke="{color}" stroke-width="1.2"/>'
                )
            svg_parts.append(
                f'<polyline fill="none" stroke="{color}" stroke-width="1.6" stroke-dasharray="8 6" points="{build_polyline(analytic_polyline_points)}"/>'
            )
            svg_parts.append(
                f'<line x1="{plot_right - 120}" y1="{legend_y}" x2="{plot_right - 88}" y2="{legend_y}" stroke="{color}" stroke-width="1.6" stroke-dasharray="8 6"/>'
            )
            svg_parts.append(
                f'<text x="{plot_right - 76}" y="{legend_y + 4}" font-size="13" font-family="Arial">{mode_label} exato</text>'
            )
            legend_y += 24

    svg_parts.append(
        f'<text x="{plot_left}" y="{height - 46}" font-size="12" fill="#566173" font-family="Arial">Linha contínua e pontos cheios: FEM. Linha tracejada e quadrados vazados: solução TE exata de [6-19].</text>'
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
        subtitle="Mesmo eixo k0 b da figura de referência, com perfil planar unilateral e d = 1.0.",
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
        x_values=[0.0, 30.0, 60.0, 90.0, 120.0, 150.0],
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


def generate_error_svg(error_rows: list[dict[str, str]], output_path: Path) -> None:
    grouped: defaultdict[str, list[tuple[float, float]]] = defaultdict(list)
    for row in error_rows:
        if not row.get("absolute_relative_error_percent", ""):
            continue
        grouped[row["mode_label"]].append(
            (
                float(row["k0_b"]),
                float(row["absolute_relative_error_percent"]),
            )
        )

    for points in grouped.values():
        points.sort()

    all_points = [point for points in grouped.values() for point in points]
    if not all_points:
        return

    x_min = min(0.0, min(point[0] for point in all_points))
    x_max = max(FIG2_X_MAX, max(point[0] for point in all_points))
    y_min = 0.0
    y_max = padded_max([point[1] for point in all_points], minimum=0.001)

    width = 960
    height = 620
    left = 90
    right = 50
    top = 78
    bottom = 78

    svg_parts: list[str] = []
    plot_left, plot_right, plot_top, plot_bottom = append_plot_frame(
        svg_parts,
        width=width,
        height=height,
        left=left,
        right=right,
        top=top,
        bottom=bottom,
        title="Caso 2 - Erro relativo vs frequência",
        subtitle="Erro relativo absoluto do FEM contra a solução TE exata do guia planar difuso.",
        x_label="k0 b",
        y_label="Erro relativo absoluto (%)",
    )

    x_ticks = build_even_ticks(x_min, x_max, 6)
    y_ticks = build_even_ticks(y_min, y_max, 6)
    for x_tick in x_ticks:
        x_pixel = map_value(x_tick, x_min, x_max, plot_left, plot_right)
        svg_parts.append(
            f'<line x1="{x_pixel:.2f}" y1="{plot_top}" x2="{x_pixel:.2f}" y2="{plot_bottom}" stroke="#e6e6e6" stroke-width="1"/>'
        )
        svg_parts.append(
            f'<line x1="{x_pixel:.2f}" y1="{plot_bottom}" x2="{x_pixel:.2f}" y2="{plot_bottom + 6}" stroke="#333" stroke-width="1"/>'
        )
        svg_parts.append(
            f'<text x="{x_pixel:.2f}" y="{plot_bottom + 24}" text-anchor="middle" font-size="12" font-family="Arial">{x_tick:.0f}</text>'
        )

    for y_tick in y_ticks:
        y_pixel = map_value(y_tick, y_min, y_max, plot_bottom, plot_top)
        svg_parts.append(
            f'<line x1="{plot_left}" y1="{y_pixel:.2f}" x2="{plot_right}" y2="{y_pixel:.2f}" stroke="#e6e6e6" stroke-width="1"/>'
        )
        svg_parts.append(
            f'<line x1="{plot_left - 6}" y1="{y_pixel:.2f}" x2="{plot_left}" y2="{y_pixel:.2f}" stroke="#333" stroke-width="1"/>'
        )
        svg_parts.append(
            f'<text x="{plot_left - 10}" y="{y_pixel + 4:.2f}" text-anchor="end" font-size="12" font-family="Arial">{format_error_tick(y_tick, y_max)}</text>'
        )

    legend_y = plot_top + 20
    for mode_label in ("TE0", "TE1", "TE2"):
        points = grouped.get(mode_label, [])
        if not points:
            continue
        color = MODE_COLORS.get(mode_label, "#444444")
        polyline_points = [
            (
                map_value(x_value, x_min, x_max, plot_left, plot_right),
                map_value(y_value, y_min, y_max, plot_bottom, plot_top),
            )
            for x_value, y_value in points
        ]
        svg_parts.append(
            f'<polyline fill="none" stroke="{color}" stroke-width="2.2" points="{build_polyline(polyline_points)}"/>'
        )
        for x_pixel, y_pixel in polyline_points:
            svg_parts.append(
                f'<circle cx="{x_pixel:.2f}" cy="{y_pixel:.2f}" r="3.0" fill="{color}"/>'
            )
        svg_parts.append(
            f'<line x1="{plot_right - 150}" y1="{legend_y}" x2="{plot_right - 118}" y2="{legend_y}" stroke="{color}" stroke-width="2.2"/>'
        )
        svg_parts.append(
            f'<text x="{plot_right - 106}" y="{legend_y + 4}" font-size="13" font-family="Arial">{mode_label}</text>'
        )
        legend_y += 24

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
    analytic_reference_rows = read_csv_rows(consolidated_dir / "analytic_reference.csv")
    error_rows = read_csv_rows(consolidated_dir / "fem_vs_exact_comparison.csv")

    generate_reference_dispersion_svg(
        reference_rows,
        analytic_reference_rows,
        plots_dir / "fig2_like_reference.svg",
        args.legend_y_offset,
    )
    generate_mode1_sensitivity_svg(
        consolidated_rows, plots_dir / "mode1_sensitivity.svg"
    )
    generate_error_svg(error_rows, plots_dir / "fig2_error_vs_frequency.svg")

    print(f"Gráficos gerados em: {plots_dir}")


if __name__ == "__main__":
    main()
