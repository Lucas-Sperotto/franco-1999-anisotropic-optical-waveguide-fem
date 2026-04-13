#include "waveguide_solver/dense_matrix.hpp"
#include "waveguide_solver/eigensolver.hpp"
#include "waveguide_solver/global_assembly.hpp"
#include "waveguide_solver/local_assembly.hpp"
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

waveguide::Mesh make_smoke_mesh() {
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

}  // namespace

int main() {
    try {
        const waveguide::Mesh mesh = make_smoke_mesh();
        constexpr double kPi = 3.14159265358979323846;
        const waveguide::ArticleLocalAssemblyOptions local_options =
            waveguide::make_default_article_local_assembly_options(2.0 * kPi / 1.55);
        const waveguide::HomogeneousIsotropicGlobalAssemblyResult assembly =
            waveguide::assemble_global_homogeneous_isotropic_system(mesh, 2.2, local_options);

        expect_true(assembly.node_count == 5, "unexpected node count");
        expect_true(assembly.element_count == 4, "unexpected element count");
        expect_true(assembly.boundary_condition.constrained_node_ids.size() == 4,
                    "unexpected number of boundary nodes");
        expect_true(assembly.boundary_condition.free_node_ids.size() == 1,
                    "unexpected number of interior nodes");
        expect_true(assembly.boundary_condition.free_node_ids.front() == 5,
                    "expected the center node to remain free");

        expect_true(assembly.matrices.M_full.size() == 5,
                    "unexpected full M dimension");
        expect_true(assembly.matrices.F_full.size() == 5,
                    "unexpected full F dimension");
        expect_true(assembly.matrices.M_reduced.size() == 1,
                    "unexpected reduced M dimension");
        expect_true(assembly.matrices.F_reduced.size() == 1,
                    "unexpected reduced F dimension");

        expect_true(waveguide::is_dense_matrix_symmetric(assembly.matrices.M_full),
                    "M_full should be symmetric");
        expect_true(waveguide::is_dense_matrix_symmetric(assembly.matrices.F_full),
                    "F_full should be symmetric");
        expect_true(waveguide::is_dense_matrix_symmetric(assembly.matrices.M_reduced),
                    "M_reduced should be symmetric");
        expect_true(waveguide::is_dense_matrix_symmetric(assembly.matrices.F_reduced),
                    "F_reduced should be symmetric");

        const waveguide::GeneralizedEigenSolution eigen_solution =
            waveguide::solve_symmetric_generalized_eigenproblem(
                assembly.matrices.F_reduced,
                assembly.matrices.M_reduced,
                local_options.k0,
                1);

        expect_true(eigen_solution.eigenpairs.size() == 1,
                    "expected one reduced eigenpair");
        expect_true(eigen_solution.eigenpairs.front().has_neff,
                    "expected a valid n_eff for the smoke mesh");
        expect_true(eigen_solution.eigenpairs.front().eigenvalue > 0.0,
                    "expected a positive generalized eigenvalue");

        const double expected_eigenvalue =
            assembly.matrices.F_reduced[0][0] / assembly.matrices.M_reduced[0][0];
        expect_near(eigen_solution.eigenpairs.front().eigenvalue, expected_eigenvalue,
                    "reduced single-dof eigenvalue", 1.0e-10);
        expect_near(eigen_solution.eigenpairs.front().n_eff,
                    std::sqrt(expected_eigenvalue),
                    "reduced single-dof n_eff", 1.0e-10);

        std::cout << "waveguide_global_tests: all checks passed\n";
        return EXIT_SUCCESS;
    } catch (const std::exception& error) {
        std::cerr << "waveguide_global_tests failure: " << error.what() << "\n";
        return EXIT_FAILURE;
    }
}
