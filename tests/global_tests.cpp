#include "waveguide_solver/dense_matrix.hpp"
#include "waveguide_solver/eigensolver.hpp"
#include "waveguide_solver/global_assembly.hpp"
#include "waveguide_solver/local_assembly.hpp"
#include "waveguide_solver/material_profile.hpp"
#include "waveguide_solver/mesh.hpp"

#include <cmath>
#include <cstdlib>
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

        expect_true(constant_wrapper.node_count == 5, "unexpected node count");
        expect_true(constant_wrapper.element_count == 4, "unexpected element count");
        expect_true(constant_wrapper.boundary_condition.constrained_node_ids.size() == 4,
                    "unexpected number of boundary nodes");
        expect_true(constant_wrapper.boundary_condition.free_node_ids.size() == 1,
                    "unexpected number of interior nodes");
        expect_true(constant_wrapper.boundary_condition.free_node_ids.front() == 5,
                    "expected the center node to remain free");

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
            0.01,
            1.0,
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

        std::cout << "waveguide_global_tests: all checks passed\n";
        return EXIT_SUCCESS;
    } catch (const std::exception& error) {
        std::cerr << "waveguide_global_tests failure: " << error.what() << "\n";
        return EXIT_FAILURE;
    }
}
