#pragma once

#include "waveguide_solver/dense_matrix.hpp"
#include "waveguide_solver/local_assembly.hpp"
#include "waveguide_solver/material_profile.hpp"
#include "waveguide_solver/mesh.hpp"

#include <cstddef>
#include <map>
#include <string>
#include <vector>

namespace waveguide {

struct DirichletBoundaryCondition {
    std::string label = "dirichlet_zero_on_boundary_nodes";
    std::vector<int> constrained_node_ids;
    std::vector<int> free_node_ids;
    std::vector<std::size_t> constrained_dof_indices;
    std::vector<std::size_t> free_dof_indices;
};

struct GlobalSystemMatrices {
    DenseMatrix M_full;
    DenseMatrix F_full;
    DenseMatrix M_reduced;
    DenseMatrix F_reduced;
};

struct GlobalAssemblyResult {
    GlobalSystemMatrices matrices;
    std::vector<int> node_order;
    std::map<int, std::size_t> node_id_to_dof;
    DirichletBoundaryCondition boundary_condition;
    GlobalNodalMaterialFields material_fields;
    std::size_t node_count = 0;
    std::size_t element_count = 0;
    std::size_t assembled_dof_count = 0;
    double k0 = 1.0;
    bool planar_x_invariant_reduction = false;
    std::string local_material_model;
};

std::vector<int> detect_boundary_node_ids(const Mesh& mesh);
std::vector<int> detect_y_extrema_node_ids(const Mesh& mesh);
std::vector<int> detect_dirichlet_node_ids(const Mesh& mesh,
                                           const std::string& boundary_label);
GlobalAssemblyResult assemble_global_system(
    const Mesh& mesh,
    const GlobalNodalMaterialFields& material_fields,
    const ArticleLocalAssemblyOptions& local_options,
    const std::string& boundary_label = "dirichlet_zero_on_boundary_nodes",
    bool planar_x_invariant_reduction = false);
GlobalAssemblyResult assemble_global_homogeneous_isotropic_system(
    const Mesh& mesh,
    double refractive_index,
    const ArticleLocalAssemblyOptions& local_options,
    const std::string& boundary_label = "dirichlet_zero_on_boundary_nodes",
    bool planar_x_invariant_reduction = false);
GlobalAssemblyResult assemble_global_planar_diffuse_isotropic_system(
    const Mesh& mesh,
    const PlanarDiffuseIsotropicProfile& profile,
    const ArticleLocalAssemblyOptions& local_options,
    const std::string& boundary_label = "dirichlet_zero_on_boundary_nodes",
    bool planar_x_invariant_reduction = false);
GlobalAssemblyResult assemble_global_planar_surface_diffuse_isotropic_system(
    const Mesh& mesh,
    const PlanarDiffuseIsotropicProfile& profile,
    const ArticleLocalAssemblyOptions& local_options,
    const std::string& boundary_label = "dirichlet_zero_on_y_extrema",
    bool planar_x_invariant_reduction = false);
GlobalAssemblyResult assemble_global_rectangular_channel_step_index_system(
    const Mesh& mesh,
    const RectangularChannelStepIndexProfile& profile,
    const ArticleLocalAssemblyOptions& local_options,
    const std::string& boundary_label = "dirichlet_zero_on_boundary_nodes",
    bool planar_x_invariant_reduction = false);

}  // namespace waveguide
