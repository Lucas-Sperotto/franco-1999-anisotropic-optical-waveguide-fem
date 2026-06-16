#!/usr/bin/env python3
"""APE (Annealed Proton Exchange) diffusion preprocessor.

Replaces the proxy Gaussian concentration formula with parameters derived from
the actual 2D anisotropic diffusion physics.

For an APE process in x-cut LiNbO3:
  - PE stage: step-function initial condition of width w_PE, depth d_PE
  - Anneal stage: 2D anisotropic diffusion with constants Da_x, Da_z

The Gaussian proxy in the C++ code uses:
  C(x, y) = C_peak * exp(-x^2/dx^2) * exp(-y^2/dy^2)

For a point-source PE (w_PE -> 0), after anneal time t_a:
  sigma_x = sqrt(Da_x * t_a),  dx = 2 * sigma_x   (FWHM ~ 2.35*sigma)
  sigma_z = sqrt(Da_z * t_a),  dy = 2 * sigma_z

These are the effective Gaussian parameters that best approximate the real
erf/erfc-based concentration profile (valid when w_PE << sigma_x).

For a finite PE width w_PE and depth d_PE, the exact profile is:
  C_lat(x) = (1/2) * [erf((w_PE/2 + x)/(2*sigma_x)) + erf((w_PE/2 - x)/(2*sigma_x))]
  C_dep(y) = erfc(y / (2*sigma_z))

This module provides:
  - compute_ape_parameters(): derive dx, dy from physical params
  - evaluate_ape_concentration(): exact erf/erfc concentration at a point
  - describe_ape_profile(): human-readable summary
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class ApePhysicalParameters:
    Da_x_um2_per_h: float    # Anneal diffusion coeff in lateral direction (um^2/h)
    Da_z_um2_per_h: float    # Anneal diffusion coeff in depth direction (um^2/h)
    t_anneal_h: float         # Anneal time (hours)
    peak_concentration: float = 1.0   # Normalized peak concentration (0-1)
    w_PE_um: float = 0.0      # Initial PE slab width (um); 0 = point source approx
    d_PE_um: float = 0.0      # Initial PE slab depth (um); 0 = surface source approx


@dataclass
class ApeGaussianApproximation:
    """Effective Gaussian parameters for the proxy formula in the C++ solver."""
    diffusion_width_x: float   # dx parameter (um) for C(x) = exp(-x^2/dx^2)
    diffusion_depth_y: float   # dy parameter (um) for C(y) = exp(-y^2/dy^2)
    peak_concentration: float  # C_peak (1.0 for full exchange)


def compute_ape_gaussian_approximation(params: ApePhysicalParameters) -> ApeGaussianApproximation:
    """Compute effective Gaussian parameters from physical APE diffusion constants.

    For point-source PE (w_PE=0): dx = 2*sigma_x, dy = 2*sigma_z
    For finite-width PE: dx is wider (accounts for initial PE width).
    """
    sigma_x = math.sqrt(params.Da_x_um2_per_h * params.t_anneal_h)
    sigma_z = math.sqrt(params.Da_z_um2_per_h * params.t_anneal_h)

    if params.w_PE_um <= 0.0:
        dx = 2.0 * sigma_x
        dy = 2.0 * sigma_z
    else:
        # Effective lateral width: quadrature sum of PE width and diffusion sigma
        sigma_x_eff = math.sqrt(sigma_x**2 + (params.w_PE_um / 2.0)**2)
        dx = 2.0 * sigma_x_eff
        dy = 2.0 * sigma_z

    return ApeGaussianApproximation(
        diffusion_width_x=dx,
        diffusion_depth_y=dy,
        peak_concentration=params.peak_concentration,
    )


def evaluate_ape_concentration_exact(
    x: float, y: float, params: ApePhysicalParameters
) -> float:
    """Evaluate the exact APE concentration C(x,y) using erf/erfc functions.

    Uses the analytical solution of 2D anisotropic diffusion from:
      - initial lateral profile: step function of width w_PE centered at x=0
      - initial depth profile: step function to depth d_PE (or surface Dirichlet if d_PE=0)
    """
    sigma_x = math.sqrt(params.Da_x_um2_per_h * params.t_anneal_h)
    sigma_z = math.sqrt(params.Da_z_um2_per_h * params.t_anneal_h)

    if y < 0.0:
        return 0.0

    # Lateral profile (x-direction)
    if params.w_PE_um <= 0.0 or sigma_x < 1.0e-12:
        c_lat = math.exp(-x**2 / (4.0 * sigma_x**2)) if sigma_x > 1.0e-12 else float(abs(x) < 1.0e-9)
    else:
        half_w = params.w_PE_um / 2.0
        arg1 = (half_w + x) / (2.0 * sigma_x)
        arg2 = (half_w - x) / (2.0 * sigma_x)
        c_lat = 0.5 * (math.erf(arg1) + math.erf(arg2))

    # Depth profile (z/y direction, semi-infinite medium)
    if sigma_z < 1.0e-12:
        c_dep = 1.0 if y <= params.d_PE_um else 0.0
    elif params.d_PE_um <= 0.0:
        # Surface Dirichlet source: erfc profile
        c_dep = math.erfc(y / (2.0 * sigma_z))
    else:
        # Finite initial slab of depth d_PE: sum of two erfc terms
        c_dep = 0.5 * (math.erfc((y - params.d_PE_um) / (2.0 * sigma_z))
                       + math.erfc((y + params.d_PE_um) / (2.0 * sigma_z)))

    return params.peak_concentration * c_lat * c_dep


def describe_ape_profile(params: ApePhysicalParameters) -> str:
    approx = compute_ape_gaussian_approximation(params)
    sigma_x = math.sqrt(params.Da_x_um2_per_h * params.t_anneal_h)
    sigma_z = math.sqrt(params.Da_z_um2_per_h * params.t_anneal_h)
    lines = [
        "APE diffusion parameters:",
        f"  Da_x = {params.Da_x_um2_per_h} um^2/h  (lateral, x-cut)",
        f"  Da_z = {params.Da_z_um2_per_h} um^2/h  (depth, x-cut)",
        f"  t_anneal = {params.t_anneal_h} h",
        f"  sigma_x = sqrt(Da_x * t) = {sigma_x:.6f} um",
        f"  sigma_z = sqrt(Da_z * t) = {sigma_z:.6f} um",
        f"  w_PE = {params.w_PE_um} um (PE width; 0 = point-source approximation)",
        f"  d_PE = {params.d_PE_um} um (PE depth; 0 = surface source)",
        "",
        "Gaussian approximation (for C++ proxy):",
        f"  diffusion_width_x = {approx.diffusion_width_x:.9f} um",
        f"  diffusion_depth_y = {approx.diffusion_depth_y:.9f} um",
        f"  peak_concentration = {approx.peak_concentration}",
    ]
    return "\n".join(lines)


# Default parameters for Case 5 (Franco 1999, Fig. 6): x-cut LiNbO3, 360 C anneal
CASE5_APE_PARAMS = ApePhysicalParameters(
    Da_x_um2_per_h=0.92,
    Da_z_um2_per_h=0.77,
    t_anneal_h=4.0,
    peak_concentration=1.0,
    w_PE_um=0.0,  # point-source approximation
    d_PE_um=0.0,
)


if __name__ == "__main__":
    print(describe_ape_profile(CASE5_APE_PARAMS))
    approx = compute_ape_gaussian_approximation(CASE5_APE_PARAMS)
    print(f"\nYAML parameters for case5:")
    print(f"  peak_concentration: {approx.peak_concentration}")
    print(f"  diffusion_width_x: {approx.diffusion_width_x:.9f}")
    print(f"  diffusion_depth_y: {approx.diffusion_depth_y:.9f}")
