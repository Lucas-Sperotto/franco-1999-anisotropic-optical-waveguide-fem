#!/usr/bin/env python3
"""Generate SVG plot for Case 6 (Ti:LiNbO3, Fig. 7): neff, W_x, W_y vs strip_width W.

Reads:  <sweep-root>/consolidated/neff_mode_sizes.csv
Writes: <sweep-root>/plots/fig7_like_reference.svg

Plot mirrors Fig. 7 of Franco et al. (1999): three curves on the same axis
(neff on left Y, W_x and W_y on right Y) vs W (um).
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate neff/W_x/W_y vs W SVG for Case 6 (Ti:LiNbO3)."
    )
    parser.add_argument("--sweep-root", required=True)
    parser.add_argument("--output-name", default="fig7_like_reference.svg")
    return parser.parse_args()


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def parse_float(raw: str) -> float | None:
    v = raw.strip()
    if not v:
        return None
    try:
        return float(v)
    except ValueError:
        return None


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

    data_csv = consolidated_dir / "neff_mode_sizes.csv"
    if not data_csv.exists():
        raise FileNotFoundError(
            f"Data CSV not found: {data_csv}\n"
            "Run consolidate_case6_ti_linbo3_sweep.py first."
        )

    rows = read_csv_rows(data_csv)

    w_pts: list[float] = []
    neff_pts: list[float] = []
    wx_pts: list[tuple[float, float]] = []
    wy_pts: list[tuple[float, float]] = []

    for row in rows:
        w = parse_float(row.get("W_um", ""))
        neff = parse_float(row.get("neff", ""))
        wx = parse_float(row.get("W_x_um", ""))
        wy = parse_float(row.get("W_y_um", ""))

        if w is None or neff is None:
            continue
        if not math.isfinite(w) or not math.isfinite(neff):
            continue

        w_pts.append(w)
        neff_pts.append(neff)
        if wx is not None and math.isfinite(wx) and wx > 0:
            wx_pts.append((w, wx))
        if wy is not None and math.isfinite(wy) and wy > 0:
            wy_pts.append((w, wy))

    w_pts_sorted = sorted(range(len(w_pts)), key=lambda i: w_pts[i])
    w_sorted = [w_pts[i] for i in w_pts_sorted]
    neff_sorted = [neff_pts[i] for i in w_pts_sorted]
    wx_pts.sort()
    wy_pts.sort()

    # Axis limits
    W_MIN = 2.5
    W_MAX = 13.0
    NEFF_MIN = min(neff_sorted) * 0.9995 if neff_sorted else 2.21
    NEFF_MAX = max(neff_sorted) * 1.0005 if neff_sorted else 2.22

    all_sizes = [v for _, v in wx_pts + wy_pts]
    SIZE_MIN = 0.0
    SIZE_MAX = max(all_sizes) * 1.15 if all_sizes else 20.0

    width = 960
    height = 580
    left = 90
    right = 90
    top = 70
    bottom = 78
    plot_left = left
    plot_right = width - right
    plot_top = top
    plot_bottom = height - bottom

    x_ticks = build_even_ticks(W_MIN, W_MAX, 11)
    neff_ticks = build_even_ticks(NEFF_MIN, NEFF_MAX, 5)
    size_ticks = build_even_ticks(SIZE_MIN, SIZE_MAX, 6)

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff"/>',
        f'<text x="{width / 2:.1f}" y="26" text-anchor="middle" '
        f'font-size="19" font-family="Arial" font-weight="bold">'
        f'Caso 6 - Ti:LiNbO&#x2083; — n&#x209B;&#x1D722;&#x1D722;, W_x e W_y vs largura W</text>',
        f'<text x="{width / 2:.1f}" y="46" text-anchor="middle" '
        f'font-size="13" fill="#555" font-family="Arial">'
        f'n&#x2098;&#x2091; = 2.2125, n&#x2092; = 2.1383, &#x3BB; = 1.523 µm, delta_x/delta_z: ON'
        f'</text>',
        # Plot box
        f'<line x1="{plot_left}" y1="{plot_bottom}" x2="{plot_right}" y2="{plot_bottom}" '
        f'stroke="#333" stroke-width="1.5"/>',
        f'<line x1="{plot_left}" y1="{plot_bottom}" x2="{plot_left}" y2="{plot_top}" '
        f'stroke="#333" stroke-width="1.5"/>',
        f'<line x1="{plot_right}" y1="{plot_bottom}" x2="{plot_right}" y2="{plot_top}" '
        f'stroke="#777" stroke-width="1.0"/>',
        # X label
        f'<text x="{(plot_left + plot_right) / 2:.1f}" y="{height - 18}" '
        f'text-anchor="middle" font-size="16" font-family="Arial">'
        f'Largura inicial da faixa de Ti W (µm)</text>',
        # Left Y label (neff)
        f'<text x="20" y="{(plot_top + plot_bottom) / 2:.1f}" '
        f'transform="rotate(-90 20 {(plot_top + plot_bottom) / 2:.1f})" '
        f'text-anchor="middle" font-size="15" fill="#1b6ef3" font-family="Arial">'
        f'Índice efetivo n&#x209B;&#x1D722;&#x1D722;</text>',
        # Right Y label (mode sizes)
        f'<text x="{width - 18}" y="{(plot_top + plot_bottom) / 2:.1f}" '
        f'transform="rotate(90 {width - 18} {(plot_top + plot_bottom) / 2:.1f})" '
        f'text-anchor="middle" font-size="15" fill="#e05c00" font-family="Arial">'
        f'Tamanho de modo W_x, W_y (µm)</text>',
    ]

    # X-axis ticks and grid
    for x_tick in x_ticks:
        x_px = map_value(x_tick, W_MIN, W_MAX, plot_left, plot_right)
        svg_parts.extend([
            f'<line x1="{x_px:.2f}" y1="{plot_top}" x2="{x_px:.2f}" y2="{plot_bottom}" '
            f'stroke="#e6e6e6" stroke-width="1"/>',
            f'<line x1="{x_px:.2f}" y1="{plot_bottom}" x2="{x_px:.2f}" y2="{plot_bottom + 6}" '
            f'stroke="#333" stroke-width="1"/>',
            f'<text x="{x_px:.2f}" y="{plot_bottom + 22}" '
            f'text-anchor="middle" font-size="12" font-family="Arial">{x_tick:.0f}</text>',
        ])

    # Left Y-axis ticks (neff)
    for n_tick in neff_ticks:
        y_px = map_value(n_tick, NEFF_MIN, NEFF_MAX, plot_bottom, plot_top)
        svg_parts.extend([
            f'<line x1="{plot_left}" y1="{y_px:.2f}" x2="{plot_right}" y2="{y_px:.2f}" '
            f'stroke="#e6e6e6" stroke-width="1"/>',
            f'<line x1="{plot_left - 6}" y1="{y_px:.2f}" x2="{plot_left}" y2="{y_px:.2f}" '
            f'stroke="#333" stroke-width="1"/>',
            f'<text x="{plot_left - 10}" y="{y_px + 4:.2f}" '
            f'text-anchor="end" font-size="11" fill="#1b6ef3" font-family="Arial">'
            f'{n_tick:.5f}</text>',
        ])

    # Right Y-axis ticks (mode sizes)
    for s_tick in size_ticks:
        y_px = map_value(s_tick, SIZE_MIN, SIZE_MAX, plot_bottom, plot_top)
        svg_parts.extend([
            f'<line x1="{plot_right}" y1="{y_px:.2f}" x2="{plot_right + 6}" y2="{y_px:.2f}" '
            f'stroke="#555" stroke-width="1"/>',
            f'<text x="{plot_right + 10}" y="{y_px + 4:.2f}" '
            f'text-anchor="start" font-size="11" fill="#555" font-family="Arial">'
            f'{s_tick:.1f}</text>',
        ])

    # neff curve
    if w_sorted and neff_sorted:
        neff_pixels = [
            (
                map_value(w, W_MIN, W_MAX, plot_left, plot_right),
                map_value(n, NEFF_MIN, NEFF_MAX, plot_bottom, plot_top),
            )
            for w, n in zip(w_sorted, neff_sorted)
        ]
        svg_parts.append(
            f'<polyline fill="none" stroke="#1b6ef3" stroke-width="2.4" '
            f'points="{build_polyline_str(neff_pixels)}"/>'
        )
        for x_px, y_px in neff_pixels:
            svg_parts.append(f'<circle cx="{x_px:.2f}" cy="{y_px:.2f}" r="3.5" fill="#1b6ef3"/>')

    # W_x curve
    if wx_pts:
        wx_pixels = [
            (
                map_value(w, W_MIN, W_MAX, plot_left, plot_right),
                map_value(s, SIZE_MIN, SIZE_MAX, plot_bottom, plot_top),
            )
            for w, s in wx_pts
        ]
        svg_parts.append(
            f'<polyline fill="none" stroke="#e05c00" stroke-width="2.2" '
            f'stroke-dasharray="8,4" points="{build_polyline_str(wx_pixels)}"/>'
        )
        for x_px, y_px in wx_pixels:
            svg_parts.append(
                f'<rect x="{x_px - 3:.2f}" y="{y_px - 3:.2f}" width="6" height="6" '
                f'fill="#e05c00"/>'
            )

    # W_y curve
    if wy_pts:
        wy_pixels = [
            (
                map_value(w, W_MIN, W_MAX, plot_left, plot_right),
                map_value(s, SIZE_MIN, SIZE_MAX, plot_bottom, plot_top),
            )
            for w, s in wy_pts
        ]
        svg_parts.append(
            f'<polyline fill="none" stroke="#27a050" stroke-width="2.2" '
            f'stroke-dasharray="4,4" points="{build_polyline_str(wy_pixels)}"/>'
        )
        for x_px, y_px in wy_pixels:
            svg_parts.append(
                f'<polygon points="'
                f'{x_px:.2f},{y_px - 4:.2f} {x_px - 3.5:.2f},{y_px + 3:.2f} '
                f'{x_px + 3.5:.2f},{y_px + 3:.2f}" fill="#27a050"/>'
            )

    # Legend
    legend_items = [
        ("#1b6ef3", "solid", "circle", "neff (Ex11, eixo esquerdo)"),
        ("#e05c00", "8,4", "square", "W_x lateral (eixo direito)"),
        ("#27a050", "4,4", "triangle", "W_y profundidade (eixo direito)"),
    ]
    for i, (color, dash, _shape, label) in enumerate(legend_items):
        ly = plot_top + 16 + i * 22
        lx1 = plot_left + 14
        lx2 = plot_left + 50
        dash_attr = "" if dash == "solid" else f'stroke-dasharray="{dash}"'
        svg_parts.extend([
            f'<line x1="{lx1}" y1="{ly}" x2="{lx2}" y2="{ly}" '
            f'stroke="{color}" stroke-width="2.2" {dash_attr}/>',
            f'<text x="{lx2 + 8}" y="{ly + 4}" '
            f'font-size="12" font-family="Arial">{label}</text>',
        ])

    if not w_sorted:
        svg_parts.append(
            f'<text x="{(plot_left + plot_right) / 2:.1f}" '
            f'y="{(plot_top + plot_bottom) / 2:.1f}" '
            f'text-anchor="middle" font-size="15" fill="#b00" font-family="Arial">'
            f'Sem pontos — execute o sweep e a consolidação primeiro.</text>'
        )

    svg_parts.append(
        f'<text x="{plot_left}" y="{height - 44}" '
        f'font-size="11" fill="#666" font-family="Arial">'
        f'Caso 6: Ti:LiNbO3, lambda=1.523 µm. '
        f'{len(w_sorted)} pts neff, {len(wx_pts)} W_x, {len(wy_pts)} W_y.</text>'
    )
    svg_parts.append("</svg>")

    out_path = plots_dir / args.output_name
    out_path.write_text("\n".join(svg_parts), encoding="utf-8")
    print(f"SVG written: {out_path}")
    print(f"  {len(w_sorted)} neff, {len(wx_pts)} W_x, {len(wy_pts)} W_y points.")


if __name__ == "__main__":
    main()
