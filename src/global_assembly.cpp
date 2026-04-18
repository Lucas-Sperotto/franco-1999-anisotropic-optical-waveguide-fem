#include "waveguide_solver/global_assembly.hpp"

#include <algorithm>
#include <cmath>
#include <map>
#include <set>
#include <stdexcept>
#include <utility>

namespace waveguide {
namespace {

using Edge = std::pair<int, int>;

struct DofMapping {
    std::vector<int> representative_node_ids;
    std::map<int, std::size_t> node_id_to_dof;
};

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

long long make_y_level_key(double y) {
    return std::llround(y * 1.0e9);
}

DofMapping build_dof_mapping(const Mesh& mesh, bool planar_x_invariant_reduction) {
    DofMapping mapping;

    if (!planar_x_invariant_reduction) {
        mapping.representative_node_ids.reserve(mesh.nodes.size());
        for (std::size_t i = 0; i < mesh.nodes.size(); ++i) {
            mapping.representative_node_ids.push_back(mesh.nodes[i].id);
            mapping.node_id_to_dof.emplace(mesh.nodes[i].id, i);
        }
        return mapping;
    }

    std::map<long long, std::vector<int>> node_ids_by_y_level;
    for (const MeshNode& node : mesh.nodes) {
        node_ids_by_y_level[make_y_level_key(node.point.y)].push_back(node.id);
    }

    std::size_t dof_index = 0;
    for (const auto& [y_key, node_ids] : node_ids_by_y_level) {
        (void)y_key;
        const int representative_node_id = *std::min_element(node_ids.begin(), node_ids.end());
        mapping.representative_node_ids.push_back(representative_node_id);
        for (int node_id : node_ids) {
            mapping.node_id_to_dof.emplace(node_id, dof_index);
        }
        ++dof_index;
    }

    return mapping;
}

GlobalAssemblyResult initialize_global_assembly_result(
    const Mesh& mesh,
    const GlobalNodalMaterialFields& material_fields,
    const ArticleLocalAssemblyOptions& local_options,
    bool planar_x_invariant_reduction) {
    const DofMapping dof_mapping =
        build_dof_mapping(mesh, planar_x_invariant_reduction);
    const std::size_t dof_count = dof_mapping.representative_node_ids.size();

    GlobalAssemblyResult result;
    result.material_fields = material_fields;
    result.node_count = mesh.nodes.size();
    result.element_count = mesh.triangles.size();
    result.assembled_dof_count = dof_count;
    result.k0 = local_options.k0;
    result.planar_x_invariant_reduction = planar_x_invariant_reduction;
    result.local_material_model = material_fields.model_label;
    result.node_order = dof_mapping.representative_node_ids;
    result.node_id_to_dof = dof_mapping.node_id_to_dof;
    result.matrices.M_full = make_dense_zero_matrix(dof_count, dof_count);
    result.matrices.F_full = make_dense_zero_matrix(dof_count, dof_count);
    return result;
}

void accumulate_triangle_local_matrices(
    const TriangleElement& triangle,
    const ArticleLocalMatrices& local_matrices,
    GlobalAssemblyResult& result) {
    for (std::size_t a = 0; a < triangle.node_ids.size(); ++a) {
        const std::size_t global_row = result.node_id_to_dof.at(triangle.node_ids[a]);
        for (std::size_t b = 0; b < triangle.node_ids.size(); ++b) {
            const std::size_t global_col = result.node_id_to_dof.at(triangle.node_ids[b]);
            result.matrices.M_full[global_row][global_col] += local_matrices.M_local[a][b];
            result.matrices.F_full[global_row][global_col] += local_matrices.F_local[a][b];
        }
    }
}

void finalize_boundary_reduction(const Mesh& mesh,
                                 const std::string& boundary_label,
                                 GlobalAssemblyResult& result) {
    result.boundary_condition.label = boundary_label;
    result.boundary_condition.constrained_node_ids =
        detect_dirichlet_node_ids(mesh, boundary_label);
    std::set<std::size_t> constrained_dof_set;
    for (int node_id : result.boundary_condition.constrained_node_ids) {
        constrained_dof_set.insert(result.node_id_to_dof.at(node_id));
    }

    result.boundary_condition.constrained_dof_indices.assign(
        constrained_dof_set.begin(), constrained_dof_set.end());

    for (std::size_t dof = 0; dof < result.node_order.size(); ++dof) {
        if (constrained_dof_set.count(dof) != 0) {
            continue;
        }

        result.boundary_condition.free_node_ids.push_back(result.node_order[dof]);
        result.boundary_condition.free_dof_indices.push_back(dof);
    }

    if (result.boundary_condition.free_dof_indices.empty()) {
        throw std::runtime_error(
            "Dirichlet boundary elimination produced no free degrees of freedom");
    }

    result.matrices.M_reduced = reduce_dense_matrix(
        result.matrices.M_full, result.boundary_condition.free_dof_indices);
    result.matrices.F_reduced = reduce_dense_matrix(
        result.matrices.F_full, result.boundary_condition.free_dof_indices);
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

std::vector<int> detect_y_extrema_node_ids(const Mesh& mesh) {
    if (mesh.nodes.empty()) {
        return {};
    }

    double min_y = mesh.nodes.front().point.y;
    double max_y = mesh.nodes.front().point.y;
    for (const MeshNode& node : mesh.nodes) {
        min_y = std::min(min_y, node.point.y);
        max_y = std::max(max_y, node.point.y);
    }

    constexpr double kTolerance = 1.0e-9;
    std::vector<int> node_ids;
    node_ids.reserve(mesh.nodes.size());
    for (const MeshNode& node : mesh.nodes) {
        if (std::abs(node.point.y - min_y) <= kTolerance ||
            std::abs(node.point.y - max_y) <= kTolerance) {
            node_ids.push_back(node.id);
        }
    }

    std::sort(node_ids.begin(), node_ids.end());
    node_ids.erase(std::unique(node_ids.begin(), node_ids.end()), node_ids.end());
    return node_ids;
}

std::vector<int> detect_dirichlet_node_ids(const Mesh& mesh,
                                           const std::string& boundary_label) {
    if (boundary_label == "dirichlet_zero_on_boundary" ||
        boundary_label == "dirichlet_zero_on_boundary_nodes") {
        return detect_boundary_node_ids(mesh);
    }

    if (boundary_label == "dirichlet_zero_on_y_extrema") {
        return detect_y_extrema_node_ids(mesh);
    }

    if (boundary_label == "natural_zero_flux_on_boundary" ||
        boundary_label == "open_boundary_natural") {
        // Open-boundary surrogate: keep all external nodes as free dofs so the
        // weak form remains with natural (zero normal flux) boundary treatment.
        return {};
    }

    throw std::runtime_error("Unsupported boundary label in global assembly: " +
                             boundary_label);
}

GlobalAssemblyResult assemble_global_system(
    const Mesh& mesh,
    const GlobalNodalMaterialFields& material_fields,
    const ArticleLocalAssemblyOptions& local_options,
    const std::string& boundary_label,
    bool planar_x_invariant_reduction) {
    GlobalAssemblyResult result = initialize_global_assembly_result(
        mesh, material_fields, local_options, planar_x_invariant_reduction);

    for (const TriangleElement& triangle : mesh.triangles) {
        const LinearTriangleP1Element element = mesh.make_p1_element(triangle);
        const ArticleLocalMaterialCoefficients material =
            make_element_material_from_global_fields(element, material_fields);
        const ArticleLocalMatrices local_matrices =
            assemble_article_local_matrices(element, material, local_options);

        // The global operators still follow the article eigenproblem [F]{E} = n_eff^2 [M]{E},
        // but the element contributions now inherit nodally interpolated material fields.
        accumulate_triangle_local_matrices(triangle, local_matrices, result);
    }

    finalize_boundary_reduction(mesh, boundary_label, result);
    return result;
}

GlobalAssemblyResult assemble_global_homogeneous_isotropic_system(
    const Mesh& mesh,
    double refractive_index,
    const ArticleLocalAssemblyOptions& local_options,
    const std::string& boundary_label,
    bool planar_x_invariant_reduction) {
    return assemble_global_system(
        mesh,
        make_homogeneous_isotropic_global_material(mesh, refractive_index),
        local_options,
        boundary_label,
        planar_x_invariant_reduction);
}

GlobalAssemblyResult assemble_global_planar_diffuse_isotropic_system(
    const Mesh& mesh,
    const PlanarDiffuseIsotropicProfile& profile,
    const ArticleLocalAssemblyOptions& local_options,
    const std::string& boundary_label,
    bool planar_x_invariant_reduction) {
    return assemble_global_system(
        mesh,
        make_planar_diffuse_isotropic_global_material(mesh, profile),
        local_options,
        boundary_label,
        planar_x_invariant_reduction);
}

GlobalAssemblyResult assemble_global_planar_surface_diffuse_isotropic_system(
    const Mesh& mesh,
    const PlanarDiffuseIsotropicProfile& profile,
    const ArticleLocalAssemblyOptions& local_options,
    const std::string& boundary_label,
    bool planar_x_invariant_reduction) {
    return assemble_global_system(
        mesh,
        make_planar_surface_diffuse_isotropic_global_material(mesh, profile),
        local_options,
        boundary_label,
        planar_x_invariant_reduction);
}

GlobalAssemblyResult assemble_global_rectangular_channel_step_index_system(
    const Mesh& mesh,
    const RectangularChannelStepIndexProfile& profile,
    const ArticleLocalAssemblyOptions& local_options,
    const std::string& boundary_label,
    bool planar_x_invariant_reduction) {
    const GlobalNodalMaterialFields material_fields =
        make_rectangular_channel_step_index_global_material(mesh, profile);
    GlobalAssemblyResult result = initialize_global_assembly_result(
        mesh, material_fields, local_options, planar_x_invariant_reduction);

    for (const TriangleElement& triangle : mesh.triangles) {
        const LinearTriangleP1Element element = mesh.make_p1_element(triangle);
        const ArticleLocalMaterialCoefficients material =
            make_rectangular_channel_step_index_element_material(element, profile);
        const ArticleLocalMatrices local_matrices =
            assemble_article_local_matrices(element, material, local_options);
        accumulate_triangle_local_matrices(triangle, local_matrices, result);
    }

    finalize_boundary_reduction(mesh, boundary_label, result);
    return result;
}

}  // namespace waveguide
