#!/usr/bin/env python3
"""Exact TE benchmark for the planar exponential diffused guide from Conwell [6-19]."""

from __future__ import annotations

import math
from dataclasses import dataclass

from scipy import optimize, special


@dataclass(frozen=True)
class PlanarExactReferenceConfig:
    diffusion_depth: float
    substrate_index: float
    cover_index: float
    delta_index: float


def characteristic_te_order_residual(
    nu: float,
    *,
    k0_d: float,
    config: PlanarExactReferenceConfig,
) -> float:
    """Return the TE characteristic residual in the variable order nu = 2 d p0.

    The implementation follows the characteristic equation of Conwell [6-19]
    for the exponential permittivity profile:

      epsilon(y) = epsilon_s + Delta_epsilon * exp(-y / d),  y >= 0

    with a homogeneous cover above the surface. The paper linearizes the
    substrate permittivity as Delta_epsilon = 2 n_s Delta_n for small Delta_n.
    """

    if k0_d <= 0.0:
        raise ValueError("k0_d must be positive")
    if config.diffusion_depth <= 0.0:
        raise ValueError("diffusion_depth must be positive")

    epsilon_s = config.substrate_index * config.substrate_index
    epsilon_cover = config.cover_index * config.cover_index
    delta_epsilon = 2.0 * config.substrate_index * config.delta_index
    if delta_epsilon <= 0.0:
        raise ValueError("The exact benchmark requires a positive delta_epsilon")

    xi = 2.0 * k0_d * math.sqrt(delta_epsilon)
    j_nu = special.jv(nu, xi)
    if not math.isfinite(j_nu) or abs(j_nu) <= 1.0e-14:
        return math.nan

    lhs = (special.jv(nu - 1.0, xi) - special.jv(nu + 1.0, xi)) / j_nu
    p_cover_times_d = math.sqrt(k0_d * k0_d * (epsilon_s - epsilon_cover) + 0.25 * nu * nu)
    rhs = -2.0 * p_cover_times_d / (k0_d * math.sqrt(delta_epsilon))
    return lhs - rhs


def solve_planar_exact_te_modes(
    *,
    k0_d: float,
    config: PlanarExactReferenceConfig,
    requested_modes: int = 3,
    grid_points: int = 12000,
    residual_tolerance: float = 1.0e-6,
) -> list[dict[str, float | int | str]]:
    if requested_modes <= 0:
        return []

    epsilon_s = config.substrate_index * config.substrate_index
    delta_epsilon = 2.0 * config.substrate_index * config.delta_index
    xi = 2.0 * k0_d * math.sqrt(delta_epsilon)
    if xi <= 1.0e-12:
        return []

    bracket_points = [
        1.0e-7 + (xi - 2.0e-7) * index / grid_points for index in range(grid_points + 1)
    ]

    roots: list[float] = []
    previous_nu: float | None = None
    previous_value: float | None = None

    for nu in bracket_points:
        value = characteristic_te_order_residual(nu, k0_d=k0_d, config=config)
        if (not math.isfinite(value)) or abs(value) > 1.0e8:
            previous_nu = None
            previous_value = None
            continue

        if previous_nu is not None and previous_value is not None and previous_value * value < 0.0:
            try:
                root = optimize.brentq(
                    lambda trial_nu: characteristic_te_order_residual(
                        trial_nu, k0_d=k0_d, config=config
                    ),
                    previous_nu,
                    nu,
                    xtol=1.0e-12,
                    rtol=1.0e-12,
                    maxiter=500,
                )
            except ValueError:
                previous_nu = nu
                previous_value = value
                continue

            if not roots or abs(root - roots[-1]) > 1.0e-7:
                roots.append(root)

        previous_nu = nu
        previous_value = value

    roots.sort(reverse=True)
    valid_roots: list[float] = []
    for nu in roots:
        residual = characteristic_te_order_residual(nu, k0_d=k0_d, config=config)
        if math.isfinite(residual) and abs(residual) <= residual_tolerance:
            valid_roots.append(nu)

    selected_roots = valid_roots[:requested_modes]

    exact_rows: list[dict[str, float | int | str]] = []
    for mode_offset, nu in enumerate(selected_roots):
        n_eff = math.sqrt(epsilon_s + (nu / (2.0 * k0_d)) ** 2)
        residual = characteristic_te_order_residual(nu, k0_d=k0_d, config=config)
        exact_rows.append(
            {
                "mode_index": mode_offset + 1,
                "mode_label": f"TE{mode_offset}",
                "k0_d": k0_d,
                "n_eff": n_eff,
                "nu": nu,
                "residual": residual,
                "source": "article_6_19_exact_te",
            }
        )

    return exact_rows
