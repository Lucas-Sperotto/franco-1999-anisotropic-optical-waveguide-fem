#include "waveguide_solver/element.hpp"
#include "waveguide_solver/geometry.hpp"
#include "waveguide_solver/local_assembly.hpp"

#include <cmath>
#include <cstdlib>
#include <iostream>
#include <stdexcept>

namespace {

bool nearly_equal(double lhs, double rhs, double tolerance = 1.0e-12) {
    return std::abs(lhs - rhs) <= tolerance;
}

void expect_true(bool condition, const std::string& message) {
    if (!condition) {
        throw std::runtime_error(message);
    }
}

void expect_near(double actual, double expected, const std::string& label) {
    if (!nearly_equal(actual, expected)) {
        throw std::runtime_error(label + " mismatch: expected " +
                                 std::to_string(expected) + ", got " +
                                 std::to_string(actual));
    }
}

}  // namespace

int main() {
    try {
        const waveguide::TriangleGeometry ccw_triangle{{
            waveguide::Point2D{0.0, 0.0},
            waveguide::Point2D{1.0, 0.0},
            waveguide::Point2D{0.0, 1.0},
        }};

        const waveguide::Jacobian2D jacobian =
            waveguide::compute_jacobian(ccw_triangle);
        expect_near(jacobian.values[0][0], 1.0, "jacobian j11");
        expect_near(jacobian.values[0][1], 0.0, "jacobian j12");
        expect_near(jacobian.values[1][0], 0.0, "jacobian j21");
        expect_near(jacobian.values[1][1], 1.0, "jacobian j22");
        expect_near(waveguide::compute_jacobian_determinant(jacobian), 1.0,
                    "jacobian determinant");

        expect_near(waveguide::compute_signed_area(ccw_triangle), 0.5,
                    "signed area (ccw)");
        expect_near(waveguide::compute_area(ccw_triangle), 0.5, "area (ccw)");
        expect_true(
            waveguide::compute_orientation(ccw_triangle) ==
                waveguide::TriangleOrientation::counter_clockwise,
            "expected counter_clockwise orientation for reference triangle");

        const waveguide::TriangleGeometricCoefficients coefficients =
            waveguide::compute_geometric_coefficients(ccw_triangle);
        expect_near(coefficients.b[0], -1.0, "b1");
        expect_near(coefficients.b[1], 1.0, "b2");
        expect_near(coefficients.b[2], 0.0, "b3");
        expect_near(coefficients.c[0], -1.0, "c1");
        expect_near(coefficients.c[1], 0.0, "c2");
        expect_near(coefficients.c[2], 1.0, "c3");

        const waveguide::P1ShapeGradients gradients =
            waveguide::compute_p1_shape_gradients(ccw_triangle);
        expect_near(gradients[0][0], -1.0, "grad N1 dx");
        expect_near(gradients[0][1], -1.0, "grad N1 dy");
        expect_near(gradients[1][0], 1.0, "grad N2 dx");
        expect_near(gradients[1][1], 0.0, "grad N2 dy");
        expect_near(gradients[2][0], 0.0, "grad N3 dx");
        expect_near(gradients[2][1], 1.0, "grad N3 dy");

        const waveguide::LinearTriangleP1Element element =
            waveguide::make_linear_triangle_p1_element(ccw_triangle, 7, {1, 2, 3});
        expect_true(element.element_id == 7, "unexpected element id");
        expect_true(element.global_node_ids[0] == 1 &&
                        element.global_node_ids[1] == 2 &&
                        element.global_node_ids[2] == 3,
                    "unexpected local-to-global node map");
        expect_near(element.jacobian_determinant, 1.0, "element detJ");
        expect_true(
            element.orientation == waveguide::TriangleOrientation::counter_clockwise,
            "unexpected element orientation");

        const waveguide::HomogeneousIsotropicLocalMatrices local_matrices =
            waveguide::assemble_basic_homogeneous_isotropic_local_matrices(element);
        expect_true(local_matrices.consistent_mass.size() == 3,
                    "mass matrix has unexpected row count");
        expect_true(local_matrices.consistent_mass[0].size() == 3,
                    "mass matrix has unexpected column count");
        expect_true(local_matrices.laplacian_stiffness.size() == 3,
                    "stiffness matrix has unexpected row count");
        expect_true(waveguide::is_symmetric(local_matrices.consistent_mass),
                    "mass matrix should be symmetric");
        expect_true(waveguide::is_symmetric(local_matrices.laplacian_stiffness),
                    "stiffness matrix should be symmetric");

        expect_near(local_matrices.consistent_mass[0][0], 2.0 / 24.0, "M11");
        expect_near(local_matrices.consistent_mass[0][1], 1.0 / 24.0, "M12");
        expect_near(local_matrices.consistent_mass[1][1], 2.0 / 24.0, "M22");
        expect_near(local_matrices.consistent_mass[2][2], 2.0 / 24.0, "M33");

        expect_near(local_matrices.laplacian_stiffness[0][0], 1.0, "K11");
        expect_near(local_matrices.laplacian_stiffness[0][1], -0.5, "K12");
        expect_near(local_matrices.laplacian_stiffness[0][2], -0.5, "K13");
        expect_near(local_matrices.laplacian_stiffness[1][1], 0.5, "K22");
        expect_near(local_matrices.laplacian_stiffness[1][2], 0.0, "K23");
        expect_near(local_matrices.laplacian_stiffness[2][2], 0.5, "K33");

        const waveguide::TriangleGeometry cw_triangle{{
            waveguide::Point2D{0.0, 0.0},
            waveguide::Point2D{0.0, 1.0},
            waveguide::Point2D{1.0, 0.0},
        }};

        const waveguide::Jacobian2D cw_jacobian =
            waveguide::compute_jacobian(cw_triangle);
        expect_near(waveguide::compute_jacobian_determinant(cw_jacobian), -1.0,
                    "jacobian determinant (cw)");
        expect_near(waveguide::compute_signed_area(cw_triangle), -0.5,
                    "signed area (cw)");
        expect_near(waveguide::compute_area(cw_triangle), 0.5, "area (cw)");
        expect_true(
            waveguide::compute_orientation(cw_triangle) ==
                waveguide::TriangleOrientation::clockwise,
            "expected clockwise orientation for reversed triangle");

        std::cout << "waveguide_geometry_tests: all checks passed\n";
        return EXIT_SUCCESS;
    } catch (const std::exception& error) {
        std::cerr << "waveguide_geometry_tests failure: " << error.what() << "\n";
        return EXIT_FAILURE;
    }
}
