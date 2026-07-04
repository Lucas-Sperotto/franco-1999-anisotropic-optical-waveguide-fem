#!/usr/bin/env python3
"""Convert plot pixel coordinates into calibrated data coordinates.

This is a lightweight helper for cases where a reference method is not yet
implemented, but a figure is available and a small number of points were read
manually from image pixels.

Input CSV must contain one row per point and, by default, columns:

    pixel_x,pixel_y

Any extra columns are preserved in the output. Axis calibration uses two known
pixel/value pairs per axis. For the vertical axis, provide the pixel/value pair
for the lower tick and the pixel/value pair for the upper tick; image pixel
coordinates normally increase downward, and the affine map handles that.

Example for Fig. 5 style B(V) data:

    python3 scripts/pixel_plot_to_csv.py \
      --input fig5_pixels.csv \
      --output cases/fig5_gaussian_gaussian_reference_points.csv \
      --x-column V --y-column B \
      --x-pixel-a 90 --x-value-a 0 \
      --x-pixel-b 870 --x-value-b 5 \
      --y-pixel-a 502 --y-value-a 0 \
      --y-pixel-b 70 --y-value-b 1
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path
from typing import Callable, TextIO


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert digitized plot pixel coordinates into calibrated CSV data."
    )
    parser.add_argument("--input", required=True, help="Input CSV path, or '-' for stdin.")
    parser.add_argument("--output", required=True, help="Output CSV path, or '-' for stdout.")
    parser.add_argument("--pixel-x-column", default="pixel_x")
    parser.add_argument("--pixel-y-column", default="pixel_y")
    parser.add_argument("--x-column", default="x", help="Output column name for calibrated x.")
    parser.add_argument("--y-column", default="y", help="Output column name for calibrated y.")
    parser.add_argument("--x-scale", choices=["linear", "log10"], default="linear")
    parser.add_argument("--y-scale", choices=["linear", "log10"], default="linear")
    parser.add_argument("--x-pixel-a", type=float, required=True)
    parser.add_argument("--x-value-a", type=float, required=True)
    parser.add_argument("--x-pixel-b", type=float, required=True)
    parser.add_argument("--x-value-b", type=float, required=True)
    parser.add_argument("--y-pixel-a", type=float, required=True)
    parser.add_argument("--y-value-a", type=float, required=True)
    parser.add_argument("--y-pixel-b", type=float, required=True)
    parser.add_argument("--y-value-b", type=float, required=True)
    parser.add_argument(
        "--drop-pixel-columns",
        action="store_true",
        help="Do not copy pixel_x/pixel_y columns to the output.",
    )
    parser.add_argument(
        "--precision",
        type=int,
        default=9,
        help="Decimal places for calibrated values.",
    )
    return parser.parse_args()


def open_input(path: str) -> TextIO:
    if path == "-":
        return sys.stdin
    return Path(path).open("r", encoding="utf-8", newline="")


def open_output(path: str) -> TextIO:
    if path == "-":
        return sys.stdout
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    return out_path.open("w", encoding="utf-8", newline="")


def parse_float(raw: str, *, column: str, row_number: int) -> float:
    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError(
            f"row {row_number}: column {column!r} is not a valid float: {raw!r}"
        ) from exc
    if not math.isfinite(value):
        raise ValueError(f"row {row_number}: column {column!r} is not finite: {raw!r}")
    return value


def transformed_value(value: float, scale: str) -> float:
    if scale == "linear":
        return value
    if value <= 0.0:
        raise ValueError("log10 axis calibration values must be positive")
    return math.log10(value)


def inverse_transformed_value(value: float, scale: str) -> float:
    if scale == "linear":
        return value
    return 10.0**value


def make_mapper(
    *,
    pixel_a: float,
    value_a: float,
    pixel_b: float,
    value_b: float,
    scale: str,
) -> Callable[[float], float]:
    if abs(pixel_b - pixel_a) < 1.0e-12:
        raise ValueError("axis calibration pixel coordinates must be distinct")

    mapped_a = transformed_value(value_a, scale)
    mapped_b = transformed_value(value_b, scale)

    def mapper(pixel: float) -> float:
        alpha = (pixel - pixel_a) / (pixel_b - pixel_a)
        mapped_value = mapped_a + alpha * (mapped_b - mapped_a)
        return inverse_transformed_value(mapped_value, scale)

    return mapper


def build_fieldnames(
    input_fieldnames: list[str],
    *,
    x_column: str,
    y_column: str,
    pixel_x_column: str,
    pixel_y_column: str,
    drop_pixel_columns: bool,
) -> list[str]:
    fieldnames = [x_column, y_column]
    for name in input_fieldnames:
        if name in fieldnames:
            continue
        if drop_pixel_columns and name in {pixel_x_column, pixel_y_column}:
            continue
        fieldnames.append(name)
    return fieldnames


def main() -> int:
    args = parse_args()
    x_mapper = make_mapper(
        pixel_a=args.x_pixel_a,
        value_a=args.x_value_a,
        pixel_b=args.x_pixel_b,
        value_b=args.x_value_b,
        scale=args.x_scale,
    )
    y_mapper = make_mapper(
        pixel_a=args.y_pixel_a,
        value_a=args.y_value_a,
        pixel_b=args.y_pixel_b,
        value_b=args.y_value_b,
        scale=args.y_scale,
    )

    with open_input(args.input) as input_stream:
        reader = csv.DictReader(input_stream)
        if reader.fieldnames is None:
            raise ValueError("input CSV has no header")
        for required in (args.pixel_x_column, args.pixel_y_column):
            if required not in reader.fieldnames:
                raise ValueError(f"input CSV is missing required column: {required}")

        output_fieldnames = build_fieldnames(
            reader.fieldnames,
            x_column=args.x_column,
            y_column=args.y_column,
            pixel_x_column=args.pixel_x_column,
            pixel_y_column=args.pixel_y_column,
            drop_pixel_columns=args.drop_pixel_columns,
        )

        rows: list[dict[str, str]] = []
        for row_number, row in enumerate(reader, start=2):
            pixel_x = parse_float(
                row[args.pixel_x_column],
                column=args.pixel_x_column,
                row_number=row_number,
            )
            pixel_y = parse_float(
                row[args.pixel_y_column],
                column=args.pixel_y_column,
                row_number=row_number,
            )

            output_row = dict(row)
            if args.drop_pixel_columns:
                output_row.pop(args.pixel_x_column, None)
                output_row.pop(args.pixel_y_column, None)
            output_row[args.x_column] = f"{x_mapper(pixel_x):.{args.precision}f}"
            output_row[args.y_column] = f"{y_mapper(pixel_y):.{args.precision}f}"
            rows.append(output_row)

    with open_output(args.output) as output_stream:
        writer = csv.DictWriter(output_stream, fieldnames=output_fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    if args.output != "-":
        print(f"Wrote {len(rows)} calibrated point(s) -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
