#!/usr/bin/env python3
"""Generate SVG plots for the Case 1 homogeneous-channel sweep."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


FIG1_X_MIN = 0.0
FIG1_X_MAX = 4.0
FIG1_Y_MIN = 0.0
FIG1_Y_MAX = 1.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate SVG plots from a consolidated Case 1 sweep."
    )
    parser.add_argument(
        "--sweep-root",
        required=True,
        help="Sweep root produced by scripts/run_case1_homogeneous_channel_sweep.py",
    )
    parser.add_argument(
        "--reference-points",
        default=None,
        help="Optional CSV with approximate Fig. 1 points. Defaults to the consolidated copy when present.",
    )
    return parser.parse_args()


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


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


def build_polyline(points: list[tuple[float, float]]) -> str:
    return " ".join(f"{x:.2f},{y:.2f}" for x, y in points)


def append_grid_and_ticks(
    svg_parts: list[str],
    *,
    plot_left: float,
    plot_right: float,
    plot_top: float,
    plot_bottom: float,
) -> None:
    for x_tick in [0.0, 0.8, 1.6, 2.4, 3.2, 4.0]:
        x_pixel = map_value(x_tick, FIG1_X_MIN, FIG1_X_MAX, plot_left, plot_right)
        svg_parts.append(
            f'<line x1="{x_pixel:.2f}" y1="{plot_top}" x2="{x_pixel:.2f}" y2="{plot_bottom}" stroke="#e6e6e6" stroke-width="1"/>'
        )
        svg_parts.append(
            f'<line x1="{x_pixel:.2f}" y1="{plot_bottom}" x2="{x_pixel:.2f}" y2="{plot_bottom + 6}" stroke="#333" stroke-width="1"/>'
        )
        svg_parts.append(
            f'<text x="{x_pixel:.2f}" y="{plot_bottom + 24}" text-anchor="middle" font-size="12" font-family="Arial">{x_tick:.1f}</text>'
        )

    for y_tick in [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]:
        y_pixel = map_value(y_tick, FIG1_Y_MIN, FIG1_Y_MAX, plot_bottom, plot_top)
        svg_parts.append(
            f'<line x1="{plot_left}" y1="{y_pixel:.2f}" x2="{plot_right}" y2="{y_pixel:.2f}" stroke="#e6e6e6" stroke-width="1"/>'
        )
        svg_parts.append(
            f'<line x1="{plot_left - 6}" y1="{y_pixel:.2f}" x2="{plot_left}" y2="{y_pixel:.2f}" stroke="#333" stroke-width="1"/>'
        )
        svg_parts.append(
            f'<text x="{plot_left - 10}" y="{y_pixel + 4:.2f}" text-anchor="end" font-size="12" font-family="Arial">{y_tick:.1f}</text>'
        )


def main() -> None:
    args = parse_args()
    sweep_root = Path(args.sweep_root).resolve()
    consolidated_dir = sweep_root / "consolidated"
    plots_dir = sweep_root / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    reference_rows = read_csv_rows(consolidated_dir / "reference_dispersion.csv")
    reference_points_path = None
    if args.reference_points is not None:
        reference_points_path = Path(args.reference_points).resolve()
    else:
        candidate = consolidated_dir / "fig1_reference_points.csv"
        if candidate.exists():
            reference_points_path = candidate

    external_reference_rows = (
        read_csv_rows(reference_points_path) if reference_points_path and reference_points_path.exists() else []
    )

    fem_points = [
        (float(row["normalized_frequency"]), float(row["normalized_beta"]))
        for row in reference_rows
        if row["status"] == "ok"
        and row["normalized_beta"]
        and float(row["normalized_beta"]) >= FIG1_Y_MIN
    ]
    fem_points.sort()

    external_points = [
        (float(row["normalized_frequency"]), float(row["normalized_beta"]))
        for row in external_reference_rows
    ]
    external_points.sort()

    width = 920
    height = 600
    left = 90
    right = 50
    top = 78
    bottom = 78
    plot_left = left
    plot_right = width - right
    plot_top = top
    plot_bottom = height - bottom

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff"/>',
        '<text x="460" y="28" text-anchor="middle" font-size="21" font-family="Arial">Caso 1 - Guia de canal isotrópico homogêneo</text>',
        '<text x="460" y="50" text-anchor="middle" font-size="13" fill="#555" font-family="Arial">Curva preliminar do modo fundamental Ex-like com a = 2b, b = 1, n1 = 1.0, n2 = 1.43 e n3 = 1.50.</text>',
        f'<line x1="{plot_left}" y1="{plot_bottom}" x2="{plot_right}" y2="{plot_bottom}" stroke="#333" stroke-width="1.5"/>',
        f'<line x1="{plot_left}" y1="{plot_bottom}" x2="{plot_left}" y2="{plot_top}" stroke="#333" stroke-width="1.5"/>',
        f'<text x="{width / 2:.1f}" y="{height - 20}" text-anchor="middle" font-size="16" font-family="Arial">Frequência normalizada</text>',
        f'<text x="28" y="{height / 2:.1f}" transform="rotate(-90 28 {height / 2:.1f})" text-anchor="middle" font-size="16" font-family="Arial">Constante de propagação normalizada</text>',
    ]

    append_grid_and_ticks(
        svg_parts,
        plot_left=plot_left,
        plot_right=plot_right,
        plot_top=plot_top,
        plot_bottom=plot_bottom,
    )

    if fem_points:
        polyline_points = []
        for x_value, y_value in fem_points:
            x_pixel = map_value(x_value, FIG1_X_MIN, FIG1_X_MAX, plot_left, plot_right)
            y_pixel = map_value(y_value, FIG1_Y_MIN, FIG1_Y_MAX, plot_bottom, plot_top)
            polyline_points.append((x_pixel, y_pixel))
            svg_parts.append(
                f'<circle cx="{x_pixel:.2f}" cy="{y_pixel:.2f}" r="3.2" fill="#1b6ef3"/>'
            )
        svg_parts.append(
            f'<polyline fill="none" stroke="#1b6ef3" stroke-width="2.4" points="{build_polyline(polyline_points)}"/>'
        )
        svg_parts.append(
            f'<line x1="{plot_right - 210}" y1="{plot_top + 22}" x2="{plot_right - 176}" y2="{plot_top + 22}" stroke="#1b6ef3" stroke-width="2.4"/>'
        )
        svg_parts.append(
            f'<text x="{plot_right - 162}" y="{plot_top + 26}" font-size="13" font-family="Arial">FEM Ex-like</text>'
        )

    if external_points:
        for x_value, y_value in external_points:
            x_pixel = map_value(x_value, FIG1_X_MIN, FIG1_X_MAX, plot_left, plot_right)
            y_pixel = map_value(y_value, FIG1_Y_MIN, FIG1_Y_MAX, plot_bottom, plot_top)
            svg_parts.append(
                f'<circle cx="{x_pixel:.2f}" cy="{y_pixel:.2f}" r="4.0" fill="#ffffff" stroke="#c23b22" stroke-width="1.8"/>'
            )
        svg_parts.append(
            f'<circle cx="{plot_right - 193:.2f}" cy="{plot_top + 48:.2f}" r="4.0" fill="#ffffff" stroke="#c23b22" stroke-width="1.8"/>'
        )
        svg_parts.append(
            f'<text x="{plot_right - 162}" y="{plot_top + 52}" font-size="13" font-family="Arial">Figura 1 (aproximado)</text>'
        )

    footer_text = (
        "Linha contínua: FEM. Círculos vazados só aparecem quando houver pontos aproximados "
        "da figura disponíveis no diretório consolidado."
    )
    svg_parts.append(
        f'<text x="{plot_left}" y="{height - 46}" font-size="12" fill="#666" font-family="Arial">{footer_text}</text>'
    )
    svg_parts.append("</svg>")

    (plots_dir / "fig1_like_reference.svg").write_text(
        "\n".join(svg_parts), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
