#include "waveguide_solver/dense_matrix.hpp"
#include "waveguide_solver/eigensolver.hpp"
#include "waveguide_solver/global_assembly.hpp"
#include "waveguide_solver/local_assembly.hpp"
#include "waveguide_solver/material_profile.hpp"
#include "waveguide_solver/mesh.hpp"

#include <cmath>
#include <cstdlib>
#include <filesystem>
#include <iostream>
#include <stdexcept>
#include <string>

namespace {

bool nearly_equal(double lhs, double rhs, double tolerance = 1.0e-12) {
    return std::abs(lhs - rhs) <= tolerance;
}

void expect_true(bool condition, const std::string& message) {
    if (!condition) {
        throw std::runtime_error(message);
    }
}

void expect_near(double actual,
                 double expected,
                 const std::string& label,
                 double tolerance = 1.0e-12) {
    if (!nearly_equal(actual, expected, tolerance)) {
        throw std::runtime_error(label + " mismatch: expected " +
                                 std::to_string(expected) + ", got " +
                                 std::to_string(actual));
    }
}

waveguide::Mesh make_constant_smoke_mesh() {
    waveguide::Mesh mesh;
    mesh.format = "simple_mesh_v1";
    mesh.dimension = 2;
    mesh.nodes = {
        {1, {0.0, 0.0}},
        {2, {1.0, 0.0}},
        {3, {1.0, 1.0}},
        {4, {0.0, 1.0}},
        {5, {0.5, 0.5}},
    };
    mesh.triangles = {
        {1, {1, 2, 5}},
        {2, {2, 3, 5}},
        {3, {3, 4, 5}},
        {4, {4, 1, 5}},
    };
    return mesh;
}

waveguide::Mesh make_planar_variable_mesh() {
    waveguide::Mesh mesh;
    mesh.format = "simple_mesh_v1";
    mesh.dimension = 2;
    mesh.nodes = {
        {1, {-2.0, -2.0}},
        {2, {0.0, -2.0}},
        {3, {2.0, -2.0}},
        {4, {-2.0, -1.0}},
        {5, {0.0, -1.0}},
        {6, {2.0, -1.0}},
        {7, {-2.0, 0.0}},
        {8, {0.0, 0.0}},
        {9, {2.0, 0.0}},
        {10, {-2.0, 1.0}},
        {11, {0.0, 1.0}},
        {12, {2.0, 1.0}},
        {13, {-2.0, 2.0}},
        {14, {0.0, 2.0}},
        {15, {2.0, 2.0}},
    };
    mesh.triangles = {
        {1, {1, 2, 5}},   {2, {1, 5, 4}},   {3, {2, 3, 6}},   {4, {2, 6, 5}},
        {5, {4, 5, 8}},   {6, {4, 8, 7}},   {7, {5, 6, 9}},   {8, {5, 9, 8}},
        {9, {7, 8, 11}},  {10, {7, 11, 10}}, {11, {8, 9, 12}}, {12, {8, 12, 11}},
        {13, {10, 11, 14}}, {14, {10, 14, 13}}, {15, {11, 12, 15}}, {16, {11, 15, 14}},
    };
    return mesh;
}

waveguide::Mesh make_rectangular_channel_mesh() {
    waveguide::Mesh mesh;
    mesh.format = "simple_mesh_v1";
    mesh.dimension = 2;
    mesh.nodes = {
        {1, {-2.0, -2.0}},  {2, {-1.0, -2.0}}, {3, {0.0, -2.0}},
        {4, {1.0, -2.0}},   {5, {2.0, -2.0}},  {6, {-2.0, 0.0}},
        {7, {-1.0, 0.0}},   {8, {0.0, 0.0}},   {9, {1.0, 0.0}},
        {10, {2.0, 0.0}},   {11, {-2.0, 1.0}}, {12, {-1.0, 1.0}},
        {13, {0.0, 1.0}},   {14, {1.0, 1.0}},  {15, {2.0, 1.0}},
        {16, {-2.0, 3.0}},  {17, {-1.0, 3.0}}, {18, {0.0, 3.0}},
        {19, {1.0, 3.0}},   {20, {2.0, 3.0}},
    };
    mesh.triangles = {
        {1, {1, 2, 7}},    {2, {1, 7, 6}},    {3, {2, 3, 8}},    {4, {2, 8, 7}},
        {5, {3, 4, 9}},    {6, {3, 9, 8}},    {7, {4, 5, 10}},   {8, {4, 10, 9}},
        {9, {6, 7, 12}},   {10, {6, 12, 11}}, {11, {7, 8, 13}},  {12, {7, 13, 12}},
        {13, {8, 9, 14}},  {14, {8, 14, 13}}, {15, {9, 10, 15}}, {16, {9, 15, 14}},
        {17, {11, 12, 17}}, {18, {11, 17, 16}}, {19, {12, 13, 18}}, {20, {12, 18, 17}},
        {21, {13, 14, 19}}, {22, {13, 19, 18}}, {23, {14, 15, 20}}, {24, {14, 20, 19}},
    };
    return mesh;
}

waveguide::Mesh load_case3_channel_reference_mesh() {
    const std::filesystem::path repo_relative_path{
        "meshes/channel_a2b_b1_reference.mesh"};
    if (std::filesystem::exists(repo_relative_path)) {
        return waveguide::load_minimal_mesh(repo_relative_path);
    }

    const std::filesystem::path build_relative_path{
        "../meshes/channel_a2b_b1_reference.mesh"};
    if (std::filesystem::exists(build_relative_path)) {
        return waveguide::load_minimal_mesh(build_relative_path);
    }

    throw std::runtime_error(
        "Could not locate meshes/channel_a2b_b1_reference.mesh for case 3 sanity test");
}

}  // namespace

int main() {
    try {
        constexpr double kPi = 3.14159265358979323846;
        const waveguide::ArticleLocalAssemblyOptions local_options =
            waveguide::make_default_article_local_assembly_options(2.0 * kPi / 1.55);

        const waveguide::Mesh constant_mesh = make_constant_smoke_mesh();
        const waveguide::GlobalAssemblyResult constant_wrapper =
            waveguide::assemble_global_homogeneous_isotropic_system(
                constant_mesh, 2.2, local_options);
        const waveguide::GlobalAssemblyResult constant_generic =
            waveguide::assemble_global_system(
                constant_mesh,
                waveguide::make_homogeneous_isotropic_global_material(constant_mesh, 2.2),
                local_options);
        const waveguide::GlobalAssemblyResult constant_natural =
            waveguide::assemble_global_homogeneous_isotropic_system(
                constant_mesh,
                2.2,
                local_options,
                "natural_zero_flux_on_boundary",
                false);

        expect_true(constant_wrapper.node_count == 5, "unexpected node count");
        expect_true(constant_wrapper.element_count == 4, "unexpected element count");
        expect_true(constant_wrapper.boundary_condition.constrained_node_ids.size() == 4,
                    "unexpected number of boundary nodes");
        expect_true(constant_wrapper.boundary_condition.free_node_ids.size() == 1,
                    "unexpected number of interior nodes");
        expect_true(constant_wrapper.boundary_condition.free_node_ids.front() == 5,
                    "expected the center node to remain free");
        expect_true(constant_natural.boundary_condition.constrained_node_ids.empty(),
                    "natural boundary should not constrain nodes");
        expect_true(constant_natural.boundary_condition.free_node_ids.size() ==
                        constant_mesh.nodes.size(),
                    "natural boundary should keep all nodes free");

        expect_true(constant_wrapper.matrices.M_full.size() == 5,
                    "unexpected full M dimension");
        expect_true(constant_wrapper.matrices.F_full.size() == 5,
                    "unexpected full F dimension");
        expect_true(constant_wrapper.matrices.M_reduced.size() == 1,
                    "unexpected reduced M dimension");
        expect_true(constant_wrapper.matrices.F_reduced.size() == 1,
                    "unexpected reduced F dimension");

        expect_true(waveguide::is_dense_matrix_symmetric(constant_wrapper.matrices.M_full),
                    "M_full should be symmetric");
        expect_true(waveguide::is_dense_matrix_symmetric(constant_wrapper.matrices.F_full),
                    "F_full should be symmetric");
        expect_true(waveguide::is_dense_matrix_symmetric(constant_wrapper.matrices.M_reduced),
                    "M_reduced should be symmetric");
        expect_true(waveguide::is_dense_matrix_symmetric(constant_wrapper.matrices.F_reduced),
                    "F_reduced should be symmetric");

        expect_near(waveguide::max_abs_dense_matrix_difference(
                        constant_wrapper.matrices.M_full,
                        constant_generic.matrices.M_full),
                    0.0, "constant wrapper/generic M_full");
        expect_near(waveguide::max_abs_dense_matrix_difference(
                        constant_wrapper.matrices.F_full,
                        constant_generic.matrices.F_full),
                    0.0, "constant wrapper/generic F_full");

        waveguide::GlobalNodalMaterialFields anisotropic_fields;
        anisotropic_fields.delta_x = false;
        anisotropic_fields.delta_z = false;
        anisotropic_fields.homogeneous = true;
        anisotropic_fields.isotropic = false;
        anisotropic_fields.model_label = "constant_anisotropic_contract_test";
        for (const waveguide::MeshNode& node : constant_mesh.nodes) {
            anisotropic_fields.nx2_by_node_id.emplace(node.id, 2.30 * 2.30);
            anisotropic_fields.nz2_by_node_id.emplace(node.id, 2.10 * 2.10);
            anisotropic_fields.gz2_by_node_id.emplace(node.id, 1.0 / (2.10 * 2.10));
        }

        const waveguide::GlobalAssemblyResult anisotropic_assembly =
            waveguide::assemble_global_system(
                constant_mesh, anisotropic_fields, local_options);

        expect_true(
            waveguide::is_dense_matrix_symmetric(anisotropic_assembly.matrices.M_full),
            "constant anisotropic M_full should remain symmetric");
        expect_true(
            waveguide::is_dense_matrix_symmetric(anisotropic_assembly.matrices.F_full),
            "constant anisotropic F_full should remain symmetric");
        expect_true(
            waveguide::max_abs_dense_matrix_difference(
                anisotropic_assembly.matrices.M_full,
                constant_generic.matrices.M_full) > 1.0e-6,
            "anisotropic M_full should differ from the equivalent isotropic assembly");
        expect_true(
            waveguide::max_abs_dense_matrix_difference(
                anisotropic_assembly.matrices.F_full,
                constant_generic.matrices.F_full) > 1.0e-6,
            "anisotropic F_full should differ from the equivalent isotropic assembly");

        const waveguide::GeneralizedEigenSolution anisotropic_eigen_solution =
            waveguide::solve_generalized_eigenproblem_dense(
                anisotropic_assembly.matrices.F_reduced,
                anisotropic_assembly.matrices.M_reduced,
                local_options.k0,
                1);

        expect_true(anisotropic_eigen_solution.eigenpairs.size() == 1,
                    "expected one anisotropic contract eigenpair");
        expect_true(anisotropic_eigen_solution.eigenpairs.front().has_neff,
                    "expected a valid n_eff for the anisotropic contract test");
        expect_true(anisotropic_eigen_solution.transformed_matrix_is_symmetric,
                    "constant anisotropic transformed matrix should be symmetric");

        const waveguide::GeneralizedEigenSolution constant_eigen_solution =
            waveguide::solve_generalized_eigenproblem_dense(
                constant_wrapper.matrices.F_reduced,
                constant_wrapper.matrices.M_reduced,
                local_options.k0,
                1);

        expect_true(constant_eigen_solution.eigenpairs.size() == 1,
                    "expected one reduced eigenpair");
        expect_true(constant_eigen_solution.eigenpairs.front().has_neff,
                    "expected a valid n_eff for the smoke mesh");
        expect_true(constant_eigen_solution.transformed_matrix_is_symmetric,
                    "the constant transformed matrix should be symmetric");
        expect_true(constant_eigen_solution.solver_label == "symmetric_jacobi",
                    "expected the symmetric dense solver path");

        const double expected_eigenvalue =
            constant_wrapper.matrices.F_reduced[0][0] /
            constant_wrapper.matrices.M_reduced[0][0];
        expect_near(constant_eigen_solution.eigenpairs.front().eigenvalue,
                    expected_eigenvalue,
                    "reduced single-dof eigenvalue", 1.0e-10);
        expect_near(constant_eigen_solution.eigenpairs.front().n_eff,
                    std::sqrt(expected_eigenvalue),
                    "reduced single-dof n_eff", 1.0e-10);

        const waveguide::Mesh planar_mesh = make_planar_variable_mesh();
        const waveguide::PlanarDiffuseIsotropicProfile planar_profile{
            2.20,
            2.20,
            0.01,
            1.0,
            0.0,
            false,
        };
        const waveguide::GlobalNodalMaterialFields planar_fields =
            waveguide::make_planar_diffuse_isotropic_global_material(
                planar_mesh, planar_profile);
        const waveguide::GlobalAssemblyResult planar_assembly =
            waveguide::assemble_global_system(planar_mesh, planar_fields, local_options);

        expect_true(planar_assembly.boundary_condition.free_node_ids.size() == 3,
                    "expected three interior nodes for the planar mesh");
        expect_true(planar_assembly.boundary_condition.free_node_ids[0] == 5 &&
                        planar_assembly.boundary_condition.free_node_ids[1] == 8 &&
                        planar_assembly.boundary_condition.free_node_ids[2] == 11,
                    "unexpected planar free-node set");
        expect_true(waveguide::is_dense_matrix_symmetric(planar_assembly.matrices.M_full),
                    "planar M_full should remain symmetric");
        expect_true(!waveguide::is_dense_matrix_symmetric(planar_assembly.matrices.F_full),
                    "planar F_full should become non-symmetric with the diffused profile");
        expect_true(!waveguide::is_dense_matrix_symmetric(planar_assembly.matrices.F_reduced),
                    "planar F_reduced should become non-symmetric with the diffused profile");

        const double center_nx2 =
            waveguide::get_global_material_value(planar_fields.nx2_by_node_id, 8, "nx2");
        const double lower_nx2 =
            waveguide::get_global_material_value(planar_fields.nx2_by_node_id, 5, "nx2");
        expect_true(center_nx2 > lower_nx2,
                    "the planar profile should peak at y = 0");

        const waveguide::GeneralizedEigenSolution planar_eigen_solution =
            waveguide::solve_generalized_eigenproblem_dense(
                planar_assembly.matrices.F_reduced,
                planar_assembly.matrices.M_reduced,
                local_options.k0,
                3);

        expect_true(planar_eigen_solution.eigenpairs.size() == 3,
                    "expected three planar eigenpairs");
        expect_true(!planar_eigen_solution.transformed_matrix_is_symmetric,
                    "the planar transformed matrix should reflect the non-symmetric case");
        expect_true(planar_eigen_solution.solver_label == "general_qr",
                    "expected the general dense QR path");
        expect_true(planar_eigen_solution.eigenpairs.front().has_neff,
                    "expected a valid leading n_eff for the planar case");
        expect_true(planar_eigen_solution.eigenpairs.front().eigenvalue >
                        planar_eigen_solution.eigenpairs.back().eigenvalue,
                    "expected eigenpairs to be sorted in descending order");

        const waveguide::PlanarDiffuseIsotropicProfile source_planar_profile{
            2.20,
            1.00,
            0.01,
            1.0,
            0.0,
            true,
        };
        const waveguide::GlobalAssemblyResult source_planar_assembly =
            waveguide::assemble_global_planar_surface_diffuse_isotropic_system(
                planar_mesh,
                source_planar_profile,
                local_options,
                "dirichlet_zero_on_y_extrema",
                true);

        expect_true(source_planar_assembly.planar_x_invariant_reduction,
                    "expected the source-based planar case to use x-invariant reduction");
        expect_true(source_planar_assembly.assembled_dof_count == 5,
                    "expected one global dof per y level in the x-invariant planar case");
        expect_true(source_planar_assembly.boundary_condition.free_dof_indices.size() == 3,
                    "expected three free y levels after truncation on y extrema");
        expect_true(
            waveguide::get_global_material_value(
                source_planar_assembly.material_fields.nx2_by_node_id, 2, "nx2") ==
                1.0,
            "expected the cover permittivity to match n0 = 1.0 above the surface");
        expect_true(
            waveguide::get_global_material_value(
                source_planar_assembly.material_fields.nx2_by_node_id, 8, "nx2") >
                waveguide::get_global_material_value(
                    source_planar_assembly.material_fields.nx2_by_node_id, 11, "nx2"),
            "expected the diffused profile to decay with depth inside the substrate");

        const waveguide::GeneralizedEigenSolution source_planar_eigen_solution =
            waveguide::solve_generalized_eigenproblem_dense(
                source_planar_assembly.matrices.F_reduced,
                source_planar_assembly.matrices.M_reduced,
                local_options.k0,
                3);

        expect_true(source_planar_eigen_solution.eigenpairs.size() == 3,
                    "expected three x-invariant source-planar eigenpairs");
        expect_true(source_planar_eigen_solution.eigenpairs[0].has_neff &&
                        source_planar_eigen_solution.eigenpairs[1].has_neff &&
                        source_planar_eigen_solution.eigenpairs[2].has_neff,
                    "expected valid n_eff values for the first three source-planar modes");
        expect_true(source_planar_eigen_solution.eigenpairs[0].n_eff >
                        source_planar_eigen_solution.eigenpairs[1].n_eff &&
                        source_planar_eigen_solution.eigenpairs[1].n_eff >
                            source_planar_eigen_solution.eigenpairs[2].n_eff,
                    "expected the source-planar modal indices to be strictly ordered");
        expect_true(source_planar_eigen_solution.eigenpairs[0].n_eff -
                        source_planar_eigen_solution.eigenpairs[1].n_eff >
                            1.0e-4,
                    "expected visible modal separation in the x-invariant planar case");

        const waveguide::Mesh channel_mesh = make_rectangular_channel_mesh();
        const waveguide::RectangularChannelStepIndexProfile channel_profile{
            1.0,
            1.43,
            1.50,
            2.0,
            1.0,
            0.0,
            0.0,
        };
        const double channel_frequency_normalized = 2.0;
        const double channel_k0 =
            channel_frequency_normalized * kPi /
            std::sqrt(channel_profile.core_index * channel_profile.core_index -
                      channel_profile.substrate_index *
                          channel_profile.substrate_index);
        const waveguide::ArticleLocalAssemblyOptions channel_local_options =
            waveguide::make_default_article_local_assembly_options(channel_k0);
        const waveguide::GlobalAssemblyResult channel_assembly =
            waveguide::assemble_global_rectangular_channel_step_index_system(
                channel_mesh, channel_profile, channel_local_options);

        expect_true(
            waveguide::get_global_material_value(
                channel_assembly.material_fields.nx2_by_node_id, 3, "nx2") == 1.0,
            "expected cover node to keep n1^2");
        expect_true(
            waveguide::get_global_material_value(
                channel_assembly.material_fields.nx2_by_node_id, 8, "nx2") ==
                channel_profile.core_index * channel_profile.core_index,
            "expected core node to keep n3^2");
        expect_true(
            waveguide::get_global_material_value(
                channel_assembly.material_fields.nx2_by_node_id, 18, "nx2") ==
                channel_profile.substrate_index * channel_profile.substrate_index,
            "expected deep substrate node to keep n2^2");
        expect_true(waveguide::is_dense_matrix_symmetric(channel_assembly.matrices.M_full),
                    "channel M_full should be symmetric");
        expect_true(waveguide::is_dense_matrix_symmetric(channel_assembly.matrices.F_full),
                    "channel F_full should be symmetric");
        expect_true(channel_assembly.boundary_condition.free_dof_indices.size() == 6,
                    "unexpected number of free dofs in the channel mesh");

        const waveguide::GeneralizedEigenSolution channel_eigen_solution =
            waveguide::solve_generalized_eigenproblem_dense(
                channel_assembly.matrices.F_reduced,
                channel_assembly.matrices.M_reduced,
                channel_local_options.k0,
                1);

        expect_true(channel_eigen_solution.transformed_matrix_is_symmetric,
                    "the channel transformed matrix should be symmetric");
        expect_true(channel_eigen_solution.solver_label == "symmetric_jacobi",
                    "expected the symmetric dense solver path for the channel case");
        expect_true(channel_eigen_solution.eigenpairs.size() == 1,
                    "expected one channel eigenpair");
        expect_true(channel_eigen_solution.eigenpairs.front().has_neff,
                    "expected a valid channel n_eff");
        expect_true(channel_eigen_solution.eigenpairs.front().n_eff >
                        channel_profile.substrate_index &&
                        channel_eigen_solution.eigenpairs.front().n_eff <
                            channel_profile.core_index,
                    "expected the leading channel n_eff to lie between n2 and n3");

        const waveguide::ChannelDiffusedIsotropicProfile diffused_channel_profile{
            1.0,
            1.44,
            1.50,
            2.0,
            1.0,
            0.0,
            0.0,
        };
        expect_near(
            waveguide::evaluate_channel_diffused_isotropic_index(
                waveguide::Point2D{0.0, 0.0}, diffused_channel_profile),
            diffused_channel_profile.peak_index,
            "diffused channel center index");
        expect_near(
            waveguide::evaluate_channel_diffused_isotropic_index(
                waveguide::Point2D{1.0, 0.0}, diffused_channel_profile),
            diffused_channel_profile.background_index,
            "diffused channel lateral boundary index");
        expect_near(
            waveguide::evaluate_channel_diffused_isotropic_index(
                waveguide::Point2D{0.0, 1.0}, diffused_channel_profile),
            diffused_channel_profile.background_index,
            "diffused channel depth boundary index");

        const waveguide::Mesh diffused_channel_mesh =
            load_case3_channel_reference_mesh();
        const double average_core_index_for_fig4 = 1.47;
        const double diffused_channel_k0 =
            channel_frequency_normalized * kPi /
            (diffused_channel_profile.core_height *
             std::sqrt(average_core_index_for_fig4 * average_core_index_for_fig4 -
                       diffused_channel_profile.background_index *
                           diffused_channel_profile.background_index));
        const waveguide::ArticleLocalAssemblyOptions diffused_channel_local_options =
            waveguide::make_default_article_local_assembly_options(diffused_channel_k0);
        const waveguide::GlobalAssemblyResult diffused_channel_assembly =
            waveguide::assemble_global_channel_diffused_isotropic_system(
                diffused_channel_mesh,
                diffused_channel_profile,
                diffused_channel_local_options);

        expect_true(
            waveguide::is_dense_matrix_symmetric(
                diffused_channel_assembly.matrices.M_full),
            "diffused channel M_full should be symmetric");
        expect_true(
            waveguide::is_dense_matrix_symmetric(
                diffused_channel_assembly.matrices.F_full),
            "diffused channel F_full should be symmetric");

        const waveguide::GeneralizedEigenSolution diffused_channel_eigen_solution =
            waveguide::solve_generalized_eigenproblem_dense(
                diffused_channel_assembly.matrices.F_reduced,
                diffused_channel_assembly.matrices.M_reduced,
                diffused_channel_local_options.k0,
                1);

        expect_true(diffused_channel_eigen_solution.eigenpairs.size() == 1,
                    "expected one diffused channel eigenpair");
        expect_true(diffused_channel_eigen_solution.eigenpairs.front().has_neff,
                    "expected a valid diffused channel n_eff");
        expect_true(diffused_channel_eigen_solution.eigenpairs.front().n_eff >
                        diffused_channel_profile.background_index &&
                        diffused_channel_eigen_solution.eigenpairs.front().n_eff <
                            diffused_channel_profile.peak_index,
                    "expected the leading diffused channel n_eff to lie between n_background and n_peak");

        const double gaussian_background_index = std::sqrt(2.1);
        const waveguide::ChannelGaussianGaussianProfile gaussian_channel_profile{
            1.0,
            gaussian_background_index,
            1.05 * gaussian_background_index,
            1.0,
            1.0,
            0.0,
            0.0,
        };
        expect_near(
            waveguide::evaluate_channel_gaussian_gaussian_index(
                waveguide::Point2D{0.0, 0.0}, gaussian_channel_profile),
            gaussian_channel_profile.peak_index,
            "Gaussian-Gaussian channel center index");
        expect_near(
            waveguide::evaluate_channel_gaussian_gaussian_index(
                waveguide::Point2D{0.5, 0.0}, gaussian_channel_profile),
            gaussian_channel_profile.background_index +
                (gaussian_channel_profile.peak_index -
                 gaussian_channel_profile.background_index) *
                    std::exp(-1.0),
            "Gaussian-Gaussian channel x half-width index");
        expect_near(
            waveguide::evaluate_channel_gaussian_gaussian_index(
                waveguide::Point2D{0.0, 1.0}, gaussian_channel_profile),
            gaussian_channel_profile.background_index +
                (gaussian_channel_profile.peak_index -
                 gaussian_channel_profile.background_index) *
                    std::exp(-1.0),
            "Gaussian-Gaussian channel depth b index");
        expect_near(
            waveguide::evaluate_channel_gaussian_gaussian_index(
                waveguide::Point2D{0.0, -0.5}, gaussian_channel_profile),
            gaussian_channel_profile.cover_index,
            "Gaussian-Gaussian channel cover index");

        const double gaussian_frequency_normalized = 5.0;
        const double gaussian_channel_k0 =
            gaussian_frequency_normalized * kPi /
            (gaussian_channel_profile.core_height *
             std::sqrt(gaussian_channel_profile.peak_index *
                           gaussian_channel_profile.peak_index -
                       gaussian_channel_profile.background_index *
                           gaussian_channel_profile.background_index));
        const waveguide::ArticleLocalAssemblyOptions gaussian_channel_local_options =
            waveguide::make_default_article_local_assembly_options(gaussian_channel_k0);
        const waveguide::GlobalAssemblyResult gaussian_channel_assembly =
            waveguide::assemble_global_channel_gaussian_gaussian_system(
                diffused_channel_mesh,
                gaussian_channel_profile,
                gaussian_channel_local_options);

        expect_true(
            waveguide::is_dense_matrix_symmetric(
                gaussian_channel_assembly.matrices.M_full),
            "Gaussian-Gaussian channel M_full should be symmetric while gradient flags are disabled");
        expect_true(
            waveguide::is_dense_matrix_symmetric(
                gaussian_channel_assembly.matrices.F_full),
            "Gaussian-Gaussian channel F_full should be symmetric while gradient flags are disabled");

        const waveguide::GeneralizedEigenSolution gaussian_channel_eigen_solution =
            waveguide::solve_generalized_eigenproblem_dense(
                gaussian_channel_assembly.matrices.F_reduced,
                gaussian_channel_assembly.matrices.M_reduced,
                gaussian_channel_local_options.k0,
                1);

        expect_true(gaussian_channel_eigen_solution.eigenpairs.size() == 1,
                    "expected one Gaussian-Gaussian channel eigenpair");
        expect_true(gaussian_channel_eigen_solution.eigenpairs.front().has_neff,
                    "expected a valid Gaussian-Gaussian channel n_eff");

        const waveguide::ApeLinbo3Profile ape_profile{
            1.0,
            2.20,
            2.20,
            0.12,
            0.01,
            3.836665,
            3.509986,
            0.0,
            0.0,
        };
        const double expected_ape_peak =
            ape_profile.extraordinary_substrate_index +
            ape_profile.delta_extraordinary_index * (1.0 - std::exp(-0.11));
        expect_near(
            waveguide::evaluate_ape_linbo3_concentration(
                waveguide::Point2D{0.0, 0.0}, ape_profile),
            ape_profile.peak_concentration,
            "APE LiNbO3 center concentration");
        expect_near(
            waveguide::evaluate_ape_linbo3_extraordinary_index(
                waveguide::Point2D{0.0, 0.0}, ape_profile),
            expected_ape_peak,
            "APE LiNbO3 center extraordinary index");
        expect_near(
            waveguide::evaluate_ape_linbo3_extraordinary_index(
                waveguide::Point2D{0.0, -0.5}, ape_profile),
            ape_profile.cover_index,
            "APE LiNbO3 cover index");

        const waveguide::GlobalAssemblyResult ape_assembly =
            waveguide::assemble_global_ape_linbo3_system(
                diffused_channel_mesh,
                ape_profile,
                waveguide::make_default_article_local_assembly_options(
                    2.0 * kPi / 0.6328));
        const double ape_center_nx2 =
            waveguide::get_global_material_value(
                ape_assembly.material_fields.nx2_by_node_id, 105, "nx2");
        const double ape_center_nz2 =
            waveguide::get_global_material_value(
                ape_assembly.material_fields.nz2_by_node_id, 105, "nz2");
        expect_true(ape_center_nx2 > ape_center_nz2,
                    "APE LiNbO3 should perturb only the extraordinary/nx branch");
        expect_true(
            waveguide::is_dense_matrix_symmetric(ape_assembly.matrices.F_full),
            "APE LiNbO3 F_full should remain symmetric while gradient flags are disabled");

        const waveguide::GeneralizedEigenSolution ape_eigen_solution =
            waveguide::solve_generalized_eigenproblem_dense(
                ape_assembly.matrices.F_reduced,
                ape_assembly.matrices.M_reduced,
                2.0 * kPi / 0.6328,
                1);
        expect_true(ape_eigen_solution.eigenpairs.size() == 1,
                    "expected one APE LiNbO3 eigenpair");
        expect_true(ape_eigen_solution.eigenpairs.front().has_neff,
                    "expected a valid APE LiNbO3 n_eff");

        const waveguide::TiDiffusedLinbo3Profile ti_profile{
            1.0,
            2.2125,
            2.1383,
            0.00446,
            0.01217,
            4.60,
            4.00,
            6.23,
            4.98,
            7.0,
            0.0,
            0.0,
        };
        const double ti_center_extraordinary_n2 =
            waveguide::evaluate_ti_diffused_linbo3_extraordinary_index_squared(
                waveguide::Point2D{0.0, 0.0}, ti_profile);
        const double ti_center_ordinary_n2 =
            waveguide::evaluate_ti_diffused_linbo3_ordinary_index_squared(
                waveguide::Point2D{0.0, 0.0}, ti_profile);
        expect_true(ti_center_extraordinary_n2 >
                        ti_profile.extraordinary_substrate_index *
                            ti_profile.extraordinary_substrate_index,
                    "Ti:LiNbO3 extraordinary branch should increase at the strip center");
        expect_true(ti_center_ordinary_n2 >
                        ti_profile.ordinary_substrate_index *
                            ti_profile.ordinary_substrate_index,
                    "Ti:LiNbO3 ordinary branch should increase at the strip center");
        expect_true(ti_center_extraordinary_n2 != ti_center_ordinary_n2,
                    "Ti:LiNbO3 ordinary and extraordinary branches should remain distinct");
        expect_near(
            waveguide::evaluate_ti_diffused_linbo3_extraordinary_index_squared(
                waveguide::Point2D{0.0, -0.5}, ti_profile),
            ti_profile.cover_index * ti_profile.cover_index,
            "Ti:LiNbO3 cover extraordinary branch");

        const waveguide::GlobalAssemblyResult ti_assembly =
            waveguide::assemble_global_ti_diffused_linbo3_system(
                diffused_channel_mesh,
                ti_profile,
                waveguide::make_default_article_local_assembly_options(
                    2.0 * kPi / 1.523));
        expect_true(
            waveguide::is_dense_matrix_symmetric(ti_assembly.matrices.F_full),
            "Ti:LiNbO3 F_full should remain symmetric while gradient flags are disabled");
        expect_true(
            waveguide::max_abs_dense_matrix_difference(
                ti_assembly.matrices.M_full,
                gaussian_channel_assembly.matrices.M_full) > 1.0e-6,
            "Ti:LiNbO3 assembly should differ from the isotropic Gaussian channel");

        const waveguide::GeneralizedEigenSolution ti_eigen_solution =
            waveguide::solve_generalized_eigenproblem_dense(
                ti_assembly.matrices.F_reduced,
                ti_assembly.matrices.M_reduced,
                2.0 * kPi / 1.523,
                1);
        expect_true(ti_eigen_solution.eigenpairs.size() == 1,
                    "expected one Ti:LiNbO3 eigenpair");
        expect_true(ti_eigen_solution.eigenpairs.front().has_neff,
                    "expected a valid Ti:LiNbO3 n_eff");

        std::cout << "waveguide_global_tests: all checks passed\n";
        return EXIT_SUCCESS;
    } catch (const std::exception& error) {
        std::cerr << "waveguide_global_tests failure: " << error.what() << "\n";
        return EXIT_FAILURE;
    }
}
