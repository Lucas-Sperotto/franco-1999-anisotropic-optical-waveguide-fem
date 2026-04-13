#include "waveguide_solver/global_assembly.hpp"

#include "waveguide_solver/material.hpp"

#include <algorithm>
#include <map>
#include <set>
#include <stdexcept>
#include <utility>

namespace waveguide {
namespace {

using Edge = std::pair<int, int>;

Edge make_sorted_edge(int lhs, int rhs) {
    if (lhs < rhs) {
        return {lhs, rhs};
    }
    return {rhs, lhs};
}

DenseMatrix reduce_dense_matrix(const DenseMatrix& matrix,
                                const std::vector<std::size_t>& free_dofs) {
    return extract_dense_submatrix(matrix, free_dofs);
}

}  // namespace

std::vector<int> detect_boundary_node_ids(const Mesh& mesh) {
    std::map<Edge, int> edge_counts;
    for (const TriangleElement& triangle : mesh.triangles) {
        edge_counts[make_sorted_edge(triangle.node_ids[0], triangle.node_ids[1])] += 1;
        edge_counts[make_sorted_edge(triangle.node_ids[1], triangle.node_ids[2])] += 1;
        edge_counts[make_sorted_edge(triangle.node_ids[2], triangle.node_ids[0])] += 1;
    }

    std::set<int> boundary_node_ids;
    for (const auto& [edge, count] : edge_counts) {
        if (count == 1) {
            boundary_node_ids.insert(edge.first);
            boundary_node_ids.insert(edge.second);
        }
    }

    return {boundary_node_ids.begin(), boundary_node_ids.end()};
}

HomogeneousIsotropicGlobalAssemblyResult assemble_global_homogeneous_isotropic_system(
    const Mesh& mesh,
    double refractive_index,
    const ArticleLocalAssemblyOptions& local_options) {
    const std::size_t node_count = mesh.nodes.size();
    const double refractive_index_squared = refractive_index * refractive_index;

    HomogeneousIsotropicGlobalAssemblyResult result;
    result.node_count = node_count;
    result.element_count = mesh.triangles.size();
    result.refractive_index = refractive_index;
    result.refractive_index_squared = refractive_index_squared;
    result.k0 = local_options.k0;
    result.local_material_model = "homogeneous_isotropic_constant_coefficients";

    result.node_order.reserve(mesh.nodes.size());
    for (std::size_t i = 0; i < mesh.nodes.size(); ++i) {
        result.node_order.push_back(mesh.nodes[i].id);
        result.node_id_to_dof.emplace(mesh.nodes[i].id, i);
    }

    result.matrices.M_full = make_dense_zero_matrix(node_count, node_count);
    result.matrices.F_full = make_dense_zero_matrix(node_count, node_count);

    for (const TriangleElement& triangle : mesh.triangles) {
        const LinearTriangleP1Element element = mesh.make_p1_element(triangle);
        const ArticleLocalMaterialCoefficients material =
            make_homogeneous_isotropic_local_material(element, refractive_index_squared);
        const ArticleLocalMatrices local_matrices =
            assemble_article_local_matrices(element, material, local_options);

        // The global matrices follow the article eigenproblem [F]{E} = n_eff^2 [M]{E}
        // by summing each element contribution into the mesh-level operators.
        for (std::size_t a = 0; a < triangle.node_ids.size(); ++a) {
            const std::size_t global_row =
                result.node_id_to_dof.at(triangle.node_ids[a]);
            for (std::size_t b = 0; b < triangle.node_ids.size(); ++b) {
                const std::size_t global_col =
                    result.node_id_to_dof.at(triangle.node_ids[b]);
                result.matrices.M_full[global_row][global_col] +=
                    local_matrices.M_local[a][b];
                result.matrices.F_full[global_row][global_col] +=
                    local_matrices.F_local[a][b];
            }
        }
    }

    result.boundary_condition.label = "dirichlet_zero_on_boundary_nodes";
    result.boundary_condition.constrained_node_ids = detect_boundary_node_ids(mesh);
    std::set<int> constrained_node_set(result.boundary_condition.constrained_node_ids.begin(),
                                       result.boundary_condition.constrained_node_ids.end());

    for (std::size_t dof = 0; dof < result.node_order.size(); ++dof) {
        const int node_id = result.node_order[dof];
        if (constrained_node_set.count(node_id) != 0) {
            result.boundary_condition.constrained_dof_indices.push_back(dof);
        } else {
            result.boundary_condition.free_node_ids.push_back(node_id);
            result.boundary_condition.free_dof_indices.push_back(dof);
        }
    }

    if (result.boundary_condition.free_dof_indices.empty()) {
        throw std::runtime_error(
            "Dirichlet boundary elimination produced no free degrees of freedom");
    }

    result.matrices.M_reduced = reduce_dense_matrix(
        result.matrices.M_full, result.boundary_condition.free_dof_indices);
    result.matrices.F_reduced = reduce_dense_matrix(
        result.matrices.F_full, result.boundary_condition.free_dof_indices);

    return result;
}

}  // namespace waveguide
