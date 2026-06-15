#!/usr/bin/env python3
"""Generate SVG dispersion-curve plot for Case 3 (channel diffused isotropic, circular profile).

Reads:  <sweep-root>/consolidated/dispersion_curve.csv
Writes: <sweep-root>/plots/fig4_like_reference.svg

The plot mirrors Fig. 4 of Franco et al. (1999):
  X-axis: normalised frequency V = (k0*b/pi)*sqrt(n3av^2 - n2^2)
  Y-axis: normalised propagation constant B = (neff^2 - n2^2)/(n3av^2 - n2^2)

Known limitation (T-005): delta_x/delta_z gradient terms are disabled in the
material profile; the result is therefore an approximation of the full
anisotropic formulation.
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path


# Axis bounds matching the reference figure.
# B_MAX is extended to 1.5 to accommodate computed values > 1.0 that arise
# when delta_x/delta_z are disabled (T-005): without gradient terms the solver
# overestimates confinement and neff > n3av, giving B > 1.
FIG4_V_MIN = 0.0
FIG4_V_MAX = 5.0
FIG4_B_MIN = 0.0
FIG4_B_MAX = 1.5
# Reference figure upper limit (for visual reference line)
FIG4_B_REF_MAX = 1.0

LIMITATION_NOTE = "delta_x/delta_z desativados (T-005: F não-simétrica)"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a B-vs-V dispersion-curve SVG for Case 3 "
            "(channel diffused isotropic, circular profile)."
        )
    )
    parser.add_argument(
        "--sweep-root",
        required=True,
        help="Sweep root produced by run_case3_channel_diffused_sweep.py.",
    )
    parser.add_argument(
        "--output-name",
        default="fig4_like_reference.svg",
        help="SVG filename written under <sweep-root>/plots/.",
    )
    parser.add_argument(
        "--show-unguided",
        action="store_true",
        help="Include FEM points flagged as unguided in the plot.",
    )
    return parser.parse_args()


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def map_value(
    value: float,
    v_min: float,
    v_max: float,
    p_min: float,
    p_max: float,
) -> float:
    if abs(v_max - v_min) < 1.0e-12:
        return 0.5 * (p_min + p_max)
    alpha = (value - v_min) / (v_max - v_min)
    return p_min + alpha * (p_max - p_min)


def build_polyline_str(points: list[tuple[float, float]]) -> str:
    return " ".join(f"{x:.2f},{y:.2f}" for x, y in points)


def build_even_ticks(v_min: float, v_max: float, count: int) -> list[float]:
    if count <= 1:
        return [v_min]
    step = (v_max - v_min) / float(count - 1)
    return [v_min + step * i for i in range(count)]


def read_finite_point(
    row: dict[str, str],
    x_key: str,
    y_key: str,
) -> tuple[float, float] | None:
    try:
        x = float(row[x_key])
        y = float(row[y_key])
    except (KeyError, ValueError):
        return None
    if not math.isfinite(x) or not math.isfinite(y):
        return None
    return x, y


def main() -> None:
    args = parse_args()
    sweep_root = Path(args.sweep_root).resolve()
    consolidated_dir = sweep_root / "consolidated"
    plots_dir = sweep_root / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    dispersion_csv = consolidated_dir / "dispersion_curve.csv"
    if not dispersion_csv.exists():
        raise FileNotFoundError(
            f"Dispersion curve CSV not found: {dispersion_csv}\n"
            "Run consolidate_case3_channel_diffused_sweep.py first."
        )

    rows = read_csv_rows(dispersion_csv)

    fem_points: list[tuple[float, float]] = []
    for row in rows:
        if not args.show_unguided and row.get("guided", "yes") != "yes":
            continue
        pt = read_finite_point(row, "V", "B")
        if pt is None:
            continue
        v_val, b_val = pt
        if FIG4_V_MIN <= v_val <= FIG4_V_MAX and FIG4_B_MIN <= b_val <= FIG4_B_MAX:
            fem_points.append(pt)
    fem_points.sort()

    # --- SVG layout ---
    width = 920
    height = 600
    left = 90
    right = 50
    top = 90        # extra top margin for limitation note
    bottom = 78
    plot_left = left
    plot_right = width - right
    plot_top = top
    plot_bottom = height - bottom

    x_ticks = build_even_ticks(FIG4_V_MIN, FIG4_V_MAX, 11)   # 0.0, 0.5, 1.0, …, 5.0
    y_ticks = build_even_ticks(FIG4_B_MIN, FIG4_B_MAX, 7)    # 0.0, 0.25, …, 1.5

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff"/>',
        # Title
        f'<text x="{width / 2:.1f}" y="28" text-anchor="middle" '
        f'font-size="20" font-family="Arial" font-weight="bold">'
        f'Caso 3 - Guia de canal difuso isotrópico (perfil circular)</text>',
        # Subtitle (parameters)
        f'<text x="{width / 2:.1f}" y="50" text-anchor="middle" '
        f'font-size="13" fill="#555" font-family="Arial">'
        f'n1=1.00, n2=1.44, n3m=1.50, n3av=1.47, a=2.0 µm, b=1.0 µm'
        f'</text>',
        # Limitation note as a highlighted text box
        f'<rect x="{plot_left}" y="62" width="{plot_right - plot_left}" height="20" '
        f'fill="#fff8dc" stroke="#c8a000" stroke-width="1" rx="3"/>',
        f'<text x="{(plot_left + plot_right) / 2:.1f}" y="76" '
        f'text-anchor="middle" font-size="12" fill="#7a5c00" font-family="Arial">'
        f'Nota (T-005): {LIMITATION_NOTE} — resultado é aproximação do modelo completo'
        f'</text>',
        # Axes
        f'<line x1="{plot_left}" y1="{plot_bottom}" x2="{plot_right}" y2="{plot_bottom}" '
        f'stroke="#333" stroke-width="1.5"/>',
        f'<line x1="{plot_left}" y1="{plot_bottom}" x2="{plot_left}" y2="{plot_top}" '
        f'stroke="#333" stroke-width="1.5"/>',
        # Axis labels
        f'<text x="{(plot_left + plot_right) / 2:.1f}" y="{height - 20}" '
        f'text-anchor="middle" font-size="16" font-family="Arial">'
        f'Frequência normalizada V</text>',
        f'<text x="26" y="{(plot_top + plot_bottom) / 2:.1f}" '
        f'transform="rotate(-90 26 {(plot_top + plot_bottom) / 2:.1f})" '
        f'text-anchor="middle" font-size="16" font-family="Arial">'
        f'Constante de propagação normalizada B</text>',
    ]

    # Dashed reference line at B=1.0 (upper limit of Fig. 4 axis)
    b_ref_y = map_value(FIG4_B_REF_MAX, FIG4_B_MIN, FIG4_B_MAX, plot_bottom, plot_top)
    svg_parts.append(
        f'<line x1="{plot_left}" y1="{b_ref_y:.2f}" x2="{plot_right}" y2="{b_ref_y:.2f}" '
        f'stroke="#aaa" stroke-width="1" stroke-dasharray="6,4"/>'
    )
    svg_parts.append(
        f'<text x="{plot_right + 4}" y="{b_ref_y + 4:.2f}" '
        f'font-size="11" fill="#888" font-family="Arial">B=1 (ref)</text>'
    )

    # Grid + X-axis ticks
    for x_tick in x_ticks:
        x_px = map_value(x_tick, FIG4_V_MIN, FIG4_V_MAX, plot_left, plot_right)
        svg_parts.append(
            f'<line x1="{x_px:.2f}" y1="{plot_top}" x2="{x_px:.2f}" y2="{plot_bottom}" '
            f'stroke="#e6e6e6" stroke-width="1"/>'
        )
        svg_parts.append(
            f'<line x1="{x_px:.2f}" y1="{plot_bottom}" x2="{x_px:.2f}" y2="{plot_bottom + 6}" '
            f'stroke="#333" stroke-width="1"/>'
        )
        label = f"{x_tick:.1f}" if (x_tick * 10) % 5 == 0 else f"{x_tick:.0f}"
        svg_parts.append(
            f'<text x="{x_px:.2f}" y="{plot_bottom + 24}" '
            f'text-anchor="middle" font-size="12" font-family="Arial">{x_tick:.1f}</text>'
        )

    # Grid + Y-axis ticks
    for y_tick in y_ticks:
        y_px = map_value(y_tick, FIG4_B_MIN, FIG4_B_MAX, plot_bottom, plot_top)
        svg_parts.append(
            f'<line x1="{plot_left}" y1="{y_px:.2f}" x2="{plot_right}" y2="{y_px:.2f}" '
            f'stroke="#e6e6e6" stroke-width="1"/>'
        )
        svg_parts.append(
            f'<line x1="{plot_left - 6}" y1="{y_px:.2f}" x2="{plot_left}" y2="{y_px:.2f}" '
            f'stroke="#333" stroke-width="1"/>'
        )
        svg_parts.append(
            f'<text x="{plot_left - 10}" y="{y_px + 4:.2f}" '
            f'text-anchor="end" font-size="12" font-family="Arial">{y_tick:.1f}</text>'
        )

    # FEM curve
    if fem_points:
        pixel_points = [
            (
                map_value(v, FIG4_V_MIN, FIG4_V_MAX, plot_left, plot_right),
                map_value(b, FIG4_B_MIN, FIG4_B_MAX, plot_bottom, plot_top),
            )
            for v, b in fem_points
        ]
        svg_parts.append(
            f'<polyline fill="none" stroke="#1b6ef3" stroke-width="2.4" '
            f'points="{build_polyline_str(pixel_points)}"/>'
        )
        for x_px, y_px in pixel_points:
            svg_parts.append(
                f'<circle cx="{x_px:.2f}" cy="{y_px:.2f}" r="3.5" fill="#1b6ef3"/>'
            )

        # Legend
        legend_x1 = plot_right - 220
        legend_x2 = plot_right - 186
        legend_tx = plot_right - 172
        legend_y = plot_top + 24
        svg_parts.append(
            f'<line x1="{legend_x1}" y1="{legend_y}" x2="{legend_x2}" y2="{legend_y}" '
            f'stroke="#1b6ef3" stroke-width="2.4"/>'
        )
        svg_parts.append(
            f'<circle cx="{(legend_x1 + legend_x2) / 2:.2f}" cy="{legend_y}" r="3.5" '
            f'fill="#1b6ef3"/>'
        )
        svg_parts.append(
            f'<text x="{legend_tx}" y="{legend_y + 4}" '
            f'font-size="13" font-family="Arial">FEM (perfil circular)</text>'
        )
    else:
        # No data — draw a note inside the plot area
        svg_parts.append(
            f'<text x="{(plot_left + plot_right) / 2:.1f}" '
            f'y="{(plot_top + plot_bottom) / 2:.1f}" '
            f'text-anchor="middle" font-size="15" fill="#b00" font-family="Arial">'
            f'Sem pontos disponíveis — execute o sweep e a consolidação primeiro.'
            f'</text>'
        )

    # Footer
    footer = (
        f"Case 3 sweep. FEM em azul. Curva é aproximação (T-005: delta_x/delta_z desativados). "
        f"{len(fem_points)} pontos plotados."
    )
    svg_parts.append(
        f'<text x="{plot_left}" y="{height - 46}" '
        f'font-size="11" fill="#666" font-family="Arial">{footer}</text>'
    )

    svg_parts.append("</svg>")

    out_path = plots_dir / args.output_name
    out_path.write_text("\n".join(svg_parts), encoding="utf-8")
    print(f"SVG written: {out_path}")
    print(f"  {len(fem_points)} FEM point(s) plotted.")


if __name__ == "__main__":
    main()
