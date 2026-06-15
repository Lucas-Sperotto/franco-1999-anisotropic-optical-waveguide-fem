#!/usr/bin/env python3
"""Generate field/profile figures for the Case 1 and Case 2 delivery report."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate modal-field and index-profile figures for Cases 1 and 2."
    )
    parser.add_argument("--case1-run", required=True, help="Point run for Case 1.")
    parser.add_argument("--case2-run", required=True, help="Point run for Case 2.")
    parser.add_argument("--output-dir", required=True, help="Destination for PNG figures.")
    return parser.parse_args()


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def load_simple_mesh(path: Path) -> tuple[dict[int, tuple[float, float]], list[tuple[int, int, int]]]:
    nodes: dict[int, tuple[float, float]] = {}
    triangles: list[tuple[int, int, int]] = []

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        parts = line.split()
        if parts[0] == "node":
            nodes[int(parts[1])] = (float(parts[2]), float(parts[3]))
        elif parts[0] in {"triangle", "element"}:
            triangles.append((int(parts[2]), int(parts[3]), int(parts[4])))

    if not nodes or not triangles:
        raise RuntimeError(f"Could not load nodes/triangles from mesh: {path}")
    return nodes, triangles


def make_triangulation(
    mesh_path: Path,
) -> tuple[mtri.Triangulation, list[int], list[float], list[float]]:
    nodes, triangles = load_simple_mesh(mesh_path)
    node_ids = sorted(nodes)
    index_by_node_id = {node_id: index for index, node_id in enumerate(node_ids)}
    x_values = [nodes[node_id][0] for node_id in node_ids]
    y_values = [nodes[node_id][1] for node_id in node_ids]
    triangle_indices = [
        [index_by_node_id[node_id] for node_id in triangle] for triangle in triangles
    ]
    return mtri.Triangulation(x_values, y_values, triangle_indices), node_ids, x_values, y_values


def values_by_node(rows: list[dict[str, str]], key: str) -> dict[int, float]:
    return {int(row["node_id"]): float(row[key]) for row in rows if row.get(key, "")}


def parse_node_id_list_from_summary(path: Path, key: str) -> list[int]:
    pattern = re.compile(rf"^{re.escape(key)}:\s*\[(.*)\]\s*$")
    for line in path.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line.strip())
        if not match:
            continue
        body = match.group(1).strip()
        if not body:
            return []
        return [int(token.strip()) for token in body.split(",")]
    raise RuntimeError(f"Could not find '{key}' in {path}")


def read_dense_csv_matrix(path: Path) -> np.ndarray:
    matrix = np.loadtxt(path, delimiter=",")
    if matrix.ndim != 2:
        raise RuntimeError(f"Expected a 2D matrix in {path}")
    return matrix


def reconstruct_case2_fem_modes(
    *,
    run_dir: Path,
    mesh_nodes: dict[int, tuple[float, float]],
    mode_count: int,
) -> tuple[list[dict[int, float]], list[tuple[str, float, float]]]:
    results_dir = run_dir / "results"
    f_reduced = read_dense_csv_matrix(results_dir / "global_F_reduced.csv")
    m_reduced = read_dense_csv_matrix(results_dir / "global_M_reduced.csv")
    if f_reduced.shape != m_reduced.shape:
        raise RuntimeError("Reduced F and M matrices must have the same shape")

    operator = np.linalg.solve(m_reduced, f_reduced)
    eigenvalues, eigenvectors = np.linalg.eig(operator)
    order = np.argsort(eigenvalues.real)[::-1]

    free_node_ids = parse_node_id_list_from_summary(
        results_dir / "global_assembly_summary.txt",
        "free_node_ids",
    )
    if len(free_node_ids) != f_reduced.shape[0]:
        raise RuntimeError(
            "Number of free nodes does not match the reduced matrix dimension"
        )

    y_key_by_node_id = {
        node_id: round(point[1] * 1.0e9) for node_id, point in mesh_nodes.items()
    }

    mode_values: list[dict[int, float]] = []
    metadata: list[tuple[str, float, float]] = []
    for output_mode_index, eigen_index in enumerate(order[:mode_count], start=0):
        eigenvalue = float(eigenvalues[eigen_index].real)
        vector = eigenvectors[:, eigen_index]
        real_vector = vector.real
        if np.linalg.norm(vector.imag) > 1.0e-8 * max(np.linalg.norm(real_vector), 1.0):
            raise RuntimeError("Complex modal vector is not negligible for Case 2")

        max_abs = float(np.max(np.abs(real_vector))) or 1.0
        real_vector = real_vector / max_abs
        peak_index = int(np.argmax(np.abs(real_vector)))
        if real_vector[peak_index] < 0.0:
            real_vector = -real_vector

        values_by_y_key = {
            y_key_by_node_id[node_id]: float(real_vector[index])
            for index, node_id in enumerate(free_node_ids)
        }
        values = {
            node_id: values_by_y_key.get(y_key, 0.0)
            for node_id, y_key in y_key_by_node_id.items()
        }
        mode_label = f"TE{output_mode_index}"
        mode_values.append(values)
        metadata.append((mode_label, eigenvalue, float(np.sqrt(eigenvalue))))

    return mode_values, metadata


def write_case2_fem_modes_csv(
    *,
    path: Path,
    mesh_nodes: dict[int, tuple[float, float]],
    mode_values: list[dict[int, float]],
    metadata: list[tuple[str, float, float]],
) -> None:
    labels = [label for label, _, _ in metadata]
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["node_id", "x", "y", *labels])
        for node_id in sorted(mesh_nodes):
            x, y = mesh_nodes[node_id]
            writer.writerow(
                [
                    node_id,
                    f"{x:.6f}",
                    f"{y:.6f}",
                    *[f"{values[node_id]:.6f}" for values in mode_values],
                ]
            )


def make_levels(vmin: float, vmax: float, count: int = 33) -> list[float]:
    if vmin == vmax:
        padding = abs(vmin) if vmin != 0.0 else 1.0
        vmin -= padding
        vmax += padding
    step = (vmax - vmin) / float(count - 1)
    return [vmin + index * step for index in range(count)]


def plot_scalar_field(
    *,
    triangulation: mtri.Triangulation,
    node_ids: list[int],
    values: dict[int, float],
    output_path: Path,
    title: str,
    color_label: str,
    cmap: str,
    symmetric: bool,
    overlay: str,
) -> None:
    ordered_values = [values[node_id] for node_id in node_ids]

    fig, ax = plt.subplots(figsize=(8.4, 5.2), constrained_layout=True)
    if symmetric:
        max_abs = max(abs(value) for value in ordered_values) or 1.0
        plot = ax.tricontourf(
            triangulation,
            ordered_values,
            levels=make_levels(-max_abs, max_abs),
            cmap=cmap,
            extend="both",
        )
    else:
        value_min = min(ordered_values)
        value_max = max(ordered_values)
        plot = ax.tricontourf(
            triangulation,
            ordered_values,
            levels=make_levels(value_min, value_max),
            cmap=cmap,
            extend="both",
        )

    ax.triplot(triangulation, color="#222222", linewidth=0.25, alpha=0.18)
    x_min = min(triangulation.x)
    x_max = max(triangulation.x)
    y_min = min(triangulation.y)
    y_max = max(triangulation.y)
    x_span = x_max - x_min
    y_span = y_max - y_min
    if overlay == "case1_core":
        ax.axhline(0.0, color="#111111", linewidth=1.0, alpha=0.85)
        ax.plot([-1.0, 1.0, 1.0, -1.0, -1.0], [0.0, 0.0, 1.0, 1.0, 0.0],
                color="#111111", linewidth=1.6)
        ax.text(x_min + 0.03 * x_span, y_min + 0.08 * y_span, "cobertura / ar",
                fontsize=9, color="#111111")
        ax.text(x_min + 0.03 * x_span, 0.0 + 0.16 * y_span, "substrato",
                fontsize=9, color="#111111")
    elif overlay == "case2_surface":
        ax.axhline(0.0, color="#111111", linewidth=1.2)
        ax.text(x_min + 0.03 * x_span, y_min + 0.08 * y_span, "cobertura / ar",
                fontsize=9, color="#111111")
        ax.text(x_min + 0.03 * x_span, 0.0 + 0.16 * y_span, "substrato difundido",
                fontsize=9, color="#111111")

    ax.set_title(title)
    ax.set_xlabel("x")
    ax.set_ylabel("y numerico (eixo invertido: profundidade para baixo)")
    ax.set_aspect("equal", adjustable="box")
    ax.invert_yaxis()
    fig.colorbar(plot, ax=ax, label=color_label)
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def plot_boundary_conditions(
    *,
    triangulation: mtri.Triangulation,
    output_path: Path,
    title: str,
    overlay: str,
) -> None:
    x_min = min(triangulation.x)
    x_max = max(triangulation.x)
    y_min = min(triangulation.y)
    y_max = max(triangulation.y)
    x_span = x_max - x_min
    y_span = y_max - y_min

    fig, ax = plt.subplots(figsize=(8.4, 5.2), constrained_layout=True)
    ax.triplot(triangulation, color="#777777", linewidth=0.35, alpha=0.25)

    if overlay == "case1":
        ax.plot(
            [x_min, x_max, x_max, x_min, x_min],
            [y_min, y_min, y_max, y_max, y_min],
            color="#d62728",
            linewidth=3.0,
            label="Dirichlet: E=0 no contorno externo",
        )
        ax.axhline(0.0, color="#111111", linewidth=1.1, alpha=0.8)
        ax.plot(
            [-1.0, 1.0, 1.0, -1.0, -1.0],
            [0.0, 0.0, 1.0, 1.0, 0.0],
            color="#111111",
            linewidth=1.6,
            label="interface material, sem CC imposta",
        )
        ax.text(
            x_min + 0.03 * x_span,
            y_max - 0.10 * y_span,
            "Neumann: nenhum contorno externo nesta rodada",
            fontsize=9,
            color="#333333",
        )
    elif overlay == "case2":
        ax.plot(
            [x_min, x_max],
            [y_min, y_min],
            color="#d62728",
            linewidth=3.0,
            label="Dirichlet: E=0 em y_min",
        )
        ax.plot(
            [x_min, x_max],
            [y_max, y_max],
            color="#d62728",
            linewidth=3.0,
            label="Dirichlet: E=0 em y_max",
        )
        ax.plot(
            [x_min, x_min],
            [y_min, y_max],
            color="#1f77b4",
            linewidth=2.0,
            linestyle="--",
            label="Neumann natural nas laterais",
        )
        ax.plot(
            [x_max, x_max],
            [y_min, y_max],
            color="#1f77b4",
            linewidth=2.0,
            linestyle="--",
        )
        ax.axhline(0.0, color="#111111", linewidth=1.1, alpha=0.8)
        ax.text(
            x_min + 0.03 * x_span,
            0.0 + 0.10 * y_span,
            "interface ar/substrato, sem CC imposta",
            fontsize=9,
            color="#333333",
        )
    else:
        raise RuntimeError(f"Unsupported boundary overlay: {overlay}")

    ax.set_title(title)
    ax.set_xlabel("x")
    ax.set_ylabel("y numerico (eixo invertido: profundidade para baixo)")
    ax.set_aspect("equal", adjustable="box")
    ax.invert_yaxis()
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.10), frameon=True)
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def main() -> None:
    args = parse_args()
    case1_run = Path(args.case1_run).resolve()
    case2_run = Path(args.case2_run).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    case1_mesh = case1_run / "inputs" / "mesh_snapshot.mesh"
    case2_mesh = case2_run / "inputs" / "mesh_snapshot.mesh"
    case1_triangulation, case1_node_ids, _, _ = make_triangulation(case1_mesh)
    case2_triangulation, case2_node_ids, _, _ = make_triangulation(case2_mesh)
    case2_nodes, _ = load_simple_mesh(case2_mesh)

    case1_material_rows = read_csv_rows(case1_run / "results" / "nodal_material_fields.csv")
    case2_material_rows = read_csv_rows(case2_run / "results" / "nodal_material_fields.csv")
    case1_modal_rows = read_csv_rows(case1_run / "results" / "modal_fields.csv")

    plot_scalar_field(
        triangulation=case1_triangulation,
        node_ids=case1_node_ids,
        values=values_by_node(case1_material_rows, "refractive_index"),
        output_path=output_dir / "case1_index_profile.png",
        title="Caso 1 - perfil de indice do guia retangular",
        color_label="n(x,y)",
        cmap="viridis",
        symmetric=False,
        overlay="case1_core",
    )
    plot_boundary_conditions(
        triangulation=case1_triangulation,
        output_path=output_dir / "case1_boundary_conditions.png",
        title="Caso 1 - condicoes de contorno",
        overlay="case1",
    )
    for mode_label in ["mode_1", "mode_2"]:
        plot_scalar_field(
            triangulation=case1_triangulation,
            node_ids=case1_node_ids,
            values=values_by_node(case1_modal_rows, mode_label),
            output_path=output_dir / f"case1_{mode_label}_field_v2p00.png",
            title=f"Caso 1 - campo Ex normalizado ({mode_label}, V=2.0)",
            color_label="Ex / max|Ex|",
            cmap="coolwarm",
            symmetric=True,
            overlay="case1_core",
        )

    plot_scalar_field(
        triangulation=case2_triangulation,
        node_ids=case2_node_ids,
        values=values_by_node(case2_material_rows, "refractive_index"),
        output_path=output_dir / "case2_index_profile_k0b40.png",
        title="Caso 2 - perfil de indice planar difuso (k0 b=40)",
        color_label="n(y)",
        cmap="viridis",
        symmetric=False,
        overlay="case2_surface",
    )
    case2_mode_values, case2_mode_metadata = reconstruct_case2_fem_modes(
        run_dir=case2_run,
        mesh_nodes=case2_nodes,
        mode_count=2,
    )
    write_case2_fem_modes_csv(
        path=output_dir / "case2_fem_modal_fields_k0b40.csv",
        mesh_nodes=case2_nodes,
        mode_values=case2_mode_values,
        metadata=case2_mode_metadata,
    )
    for values, (mode_label, eigenvalue, neff) in zip(
        case2_mode_values,
        case2_mode_metadata,
    ):
        plot_scalar_field(
            triangulation=case2_triangulation,
            node_ids=case2_node_ids,
            values=values,
            output_path=output_dir / f"case2_{mode_label.lower()}_field_k0b40.png",
            title=(
                f"Caso 2 - campo Ex FEM normalizado "
                f"({mode_label}, k0 d=40, n_eff={neff:.6f})"
            ),
            color_label="Ex / max|Ex|",
            cmap="coolwarm",
            symmetric=True,
            overlay="case2_surface",
        )
    plot_boundary_conditions(
        triangulation=case2_triangulation,
        output_path=output_dir / "case2_boundary_conditions.png",
        title="Caso 2 - condicoes de contorno",
        overlay="case2",
    )


if __name__ == "__main__":
    main()
