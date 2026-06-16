#!/usr/bin/env python3
"""Generate SVG dispersion-curve plot for Case 5 (APE LiNbO3, Fig. 6).

Reads:  <sweep-root>/consolidated/dispersion_curve.csv
Writes: <sweep-root>/plots/fig6_like_reference.svg

Plot mirrors Fig. 6 of Franco et al. (1999):
  X-axis: normalised frequency V = (2*dy/lambda)*NA
  Y-axis: normalised propagation constant B = (neff^2 - ne_s^2)/(ne_max^2 - ne_s^2)
  4 Ex mode curves.
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path


FIG6_V_MIN = 0.0
FIG6_V_MAX = 14.0
FIG6_B_MIN = 0.0
FIG6_B_MAX = 1.0

MODE_COLORS = ["#1b6ef3", "#e05c00", "#27a050", "#9b30d6"]
MODE_LABELS = ["Ex11 (modo 1)", "Ex12 (modo 2)", "Ex13 (modo 3)", "Ex14 (modo 4)"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a B-vs-V dispersion-curve SVG for Case 5 (APE LiNbO3)."
    )
    parser.add_argument("--sweep-root", required=True)
    parser.add_argument("--output-name", default="fig6_like_reference.svg")
    return parser.parse_args()


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def map_value(value: float, v_min: float, v_max: float, p_min: float, p_max: float) -> float:
    if abs(v_max - v_min) < 1.0e-12:
        return 0.5 * (p_min + p_max)
    return p_min + (value - v_min) / (v_max - v_min) * (p_max - p_min)


def build_polyline_str(points: list[tuple[float, float]]) -> str:
    return " ".join(f"{x:.2f},{y:.2f}" for x, y in points)


def build_even_ticks(v_min: float, v_max: float, count: int) -> list[float]:
    if count <= 1:
        return [v_min]
    step = (v_max - v_min) / float(count - 1)
    return [v_min + step * i for i in range(count)]


def main() -> None:
    args = parse_args()
    sweep_root = Path(args.sweep_root).resolve()
    consolidated_dir = sweep_root / "consolidated"
    plots_dir = sweep_root / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    dispersion_csv = consolidated_dir / "dispersion_curve.csv"
    if not dispersion_csv.exists():
        raise FileNotFoundError(
            f"Dispersion CSV not found: {dispersion_csv}\n"
            "Run consolidate_case5_ape_linbo3_sweep.py first."
        )

    rows = read_csv_rows(dispersion_csv)

    modes_data: dict[int, list[tuple[float, float]]] = {}
    for row in rows:
        try:
            v_val = float(row["V"])
            b_val = float(row["B"])
            m_idx = int(row["mode_index"])
        except (KeyError, ValueError):
            continue
        if not (math.isfinite(v_val) and math.isfinite(b_val)):
            continue
        if FIG6_V_MIN <= v_val <= FIG6_V_MAX and FIG6_B_MIN <= b_val <= FIG6_B_MAX:
            modes_data.setdefault(m_idx, []).append((v_val, b_val))

    for pts in modes_data.values():
        pts.sort()

    width = 920
    height = 580
    left = 90
    right = 50
    top = 70
    bottom = 78
    plot_left = left
    plot_right = width - right
    plot_top = top
    plot_bottom = height - bottom

    x_ticks = build_even_ticks(FIG6_V_MIN, FIG6_V_MAX, 8)
    y_ticks = build_even_ticks(FIG6_B_MIN, FIG6_B_MAX, 6)

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff"/>',
        f'<text x="{width / 2:.1f}" y="26" text-anchor="middle" '
        f'font-size="19" font-family="Arial" font-weight="bold">'
        f'Caso 5 - Guia APE LiNbO&#x2083; anisotrópico (x-cut)</text>',
        f'<text x="{width / 2:.1f}" y="46" text-anchor="middle" '
        f'font-size="13" fill="#555" font-family="Arial">'
        f'ne_s=2.20, &#x394;ne=0.12, Da_x=0.92, Da_z=0.77 µm²/h, &#x3BB;=0.6328 µm, C_peak=1.0'
        f'</text>',
        f'<line x1="{plot_left}" y1="{plot_bottom}" x2="{plot_right}" y2="{plot_bottom}" '
        f'stroke="#333" stroke-width="1.5"/>',
        f'<line x1="{plot_left}" y1="{plot_bottom}" x2="{plot_left}" y2="{plot_top}" '
        f'stroke="#333" stroke-width="1.5"/>',
        f'<text x="{(plot_left + plot_right) / 2:.1f}" y="{height - 18}" '
        f'text-anchor="middle" font-size="16" font-family="Arial">'
        f'Frequência normalizada V = (2 d&#x1D67A; / &#x3BB;) &#x00B7; NA</text>',
        f'<text x="26" y="{(plot_top + plot_bottom) / 2:.1f}" '
        f'transform="rotate(-90 26 {(plot_top + plot_bottom) / 2:.1f})" '
        f'text-anchor="middle" font-size="16" font-family="Arial">'
        f'Constante de propagação normalizada B</text>',
    ]

    for x_tick in x_ticks:
        x_px = map_value(x_tick, FIG6_V_MIN, FIG6_V_MAX, plot_left, plot_right)
        svg_parts.extend([
            f'<line x1="{x_px:.2f}" y1="{plot_top}" x2="{x_px:.2f}" y2="{plot_bottom}" '
            f'stroke="#e6e6e6" stroke-width="1"/>',
            f'<line x1="{x_px:.2f}" y1="{plot_bottom}" x2="{x_px:.2f}" y2="{plot_bottom + 6}" '
            f'stroke="#333" stroke-width="1"/>',
            f'<text x="{x_px:.2f}" y="{plot_bottom + 22}" '
            f'text-anchor="middle" font-size="12" font-family="Arial">{x_tick:.0f}</text>',
        ])

    for y_tick in y_ticks:
        y_px = map_value(y_tick, FIG6_B_MIN, FIG6_B_MAX, plot_bottom, plot_top)
        svg_parts.extend([
            f'<line x1="{plot_left}" y1="{y_px:.2f}" x2="{plot_right}" y2="{y_px:.2f}" '
            f'stroke="#e6e6e6" stroke-width="1"/>',
            f'<line x1="{plot_left - 6}" y1="{y_px:.2f}" x2="{plot_left}" y2="{y_px:.2f}" '
            f'stroke="#333" stroke-width="1"/>',
            f'<text x="{plot_left - 10}" y="{y_px + 4:.2f}" '
            f'text-anchor="end" font-size="12" font-family="Arial">{y_tick:.2f}</text>',
        ])

    total_points = 0
    legend_y_start = plot_top + 10
    for i, (mode_idx, pts) in enumerate(sorted(modes_data.items())):
        color = MODE_COLORS[i % len(MODE_COLORS)]
        label = MODE_LABELS[i] if i < len(MODE_LABELS) else f"modo {mode_idx}"

        pixel_points = [
            (
                map_value(v, FIG6_V_MIN, FIG6_V_MAX, plot_left, plot_right),
                map_value(b, FIG6_B_MIN, FIG6_B_MAX, plot_bottom, plot_top),
            )
            for v, b in pts
        ]
        total_points += len(pixel_points)

        svg_parts.append(
            f'<polyline fill="none" stroke="{color}" stroke-width="2.2" '
            f'points="{build_polyline_str(pixel_points)}"/>'
        )
        for x_px, y_px in pixel_points:
            svg_parts.append(
                f'<circle cx="{x_px:.2f}" cy="{y_px:.2f}" r="3.0" fill="{color}"/>'
            )

        leg_y = legend_y_start + i * 22
        leg_x1 = plot_right - 220
        leg_x2 = plot_right - 186
        svg_parts.extend([
            f'<line x1="{leg_x1}" y1="{leg_y}" x2="{leg_x2}" y2="{leg_y}" '
            f'stroke="{color}" stroke-width="2.2"/>',
            f'<circle cx="{(leg_x1 + leg_x2) / 2:.2f}" cy="{leg_y}" r="3.0" fill="{color}"/>',
            f'<text x="{leg_x2 + 6}" y="{leg_y + 4}" '
            f'font-size="12" font-family="Arial">{label}</text>',
        ])

    if not modes_data:
        svg_parts.append(
            f'<text x="{(plot_left + plot_right) / 2:.1f}" '
            f'y="{(plot_top + plot_bottom) / 2:.1f}" '
            f'text-anchor="middle" font-size="15" fill="#b00" font-family="Arial">'
            f'Sem pontos — execute o sweep e a consolidação primeiro.</text>'
        )

    svg_parts.append(
        f'<text x="{plot_left}" y="{height - 44}" '
        f'font-size="11" fill="#666" font-family="Arial">'
        f'Caso 5: APE LiNbO3, C_peak=1.0, preprocessador de difusão físico. '
        f'{total_points} pontos plotados ({len(modes_data)} modos).</text>'
    )
    svg_parts.append("</svg>")

    out_path = plots_dir / args.output_name
    out_path.write_text("\n".join(svg_parts), encoding="utf-8")
    print(f"SVG written: {out_path}")
    print(f"  {total_points} FEM point(s) plotted across {len(modes_data)} mode(s).")


if __name__ == "__main__":
    main()
