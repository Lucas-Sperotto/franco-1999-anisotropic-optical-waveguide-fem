#include "waveguide_solver/element.hpp"
#include "waveguide_solver/geometry.hpp"
#include "waveguide_solver/local_assembly.hpp"
#include "waveguide_solver/material.hpp"
#include "waveguide_solver/quadrature.hpp"

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

void expect_matrix_near(const waveguide::LocalMatrix3& actual,
                        const waveguide::LocalMatrix3& expected,
                        const std::string& label,
                        double tolerance = 1.0e-12) {
    for (std::size_t i = 0; i < actual.size(); ++i) {
        for (std::size_t j = 0; j < actual[i].size(); ++j) {
            expect_near(actual[i][j], expected[i][j],
                        label + "[" + std::to_string(i) + "," + std::to_string(j) + "]",
                        tolerance);
        }
    }
}

void expect_matrix_finite(const waveguide::LocalMatrix3& matrix,
                          const std::string& label) {
    for (std::size_t i = 0; i < matrix.size(); ++i) {
        for (std::size_t j = 0; j < matrix[i].size(); ++j) {
            if (!std::isfinite(matrix[i][j])) {
                throw std::runtime_error(label + " contains a non-finite value");
            }
        }
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

        const waveguide::ReferenceTriangleQuadratureRule quadrature_rule =
            waveguide::make_default_reference_triangle_quadrature_rule();
        expect_true(quadrature_rule.points.size() == 6,
                    "unexpected quadrature point count");
        expect_near(waveguide::sum_reference_triangle_quadrature_weights(quadrature_rule),
                    0.5, "quadrature weight sum", 1.0e-14);

        const waveguide::ArticleLocalAssemblyOptions options =
            waveguide::make_default_article_local_assembly_options(1.0);

        const waveguide::ArticleLocalMaterialCoefficients isotropic_material =
            waveguide::make_homogeneous_isotropic_local_material(element, 1.0);
        const waveguide::ArticleLocalMatrices isotropic_general =
            waveguide::assemble_article_local_matrices(element, isotropic_material, options);
        const waveguide::ArticleLocalMatrices isotropic_reduction =
            waveguide::assemble_article_local_matrices_constant_reduction(
                element, isotropic_material, options);

        expect_true(isotropic_general.M_local.size() == 3,
                    "M_local has unexpected row count");
        expect_true(isotropic_general.M_local[0].size() == 3,
                    "M_local has unexpected column count");
        expect_true(isotropic_general.F_local.size() == 3,
                    "F_local has unexpected row count");

        expect_matrix_near(isotropic_general.M_local, isotropic_reduction.M_local,
                           "isotropic reduction M");
        expect_matrix_near(isotropic_general.F1_local, isotropic_reduction.F1_local,
                           "isotropic reduction F1");
        expect_matrix_near(isotropic_general.F2_local, isotropic_reduction.F2_local,
                           "isotropic reduction F2");
        expect_matrix_near(isotropic_general.F3_local, isotropic_reduction.F3_local,
                           "isotropic reduction F3");
        expect_matrix_near(isotropic_general.F4_local, isotropic_reduction.F4_local,
                           "isotropic reduction F4");
        expect_matrix_near(isotropic_general.F_local, isotropic_reduction.F_local,
                           "isotropic reduction F");

        expect_true(waveguide::is_symmetric(isotropic_general.M_local),
                    "M_local should be symmetric");
        expect_true(waveguide::is_symmetric(isotropic_general.F1_local),
                    "F1_local should be symmetric");
        expect_true(waveguide::is_symmetric(isotropic_general.F2_local),
                    "F2_local should be symmetric in the constant reduction");
        expect_true(waveguide::is_symmetric(isotropic_general.F3_local),
                    "F3_local should be symmetric in the constant reduction");
        expect_true(waveguide::is_symmetric(isotropic_general.F_local),
                    "F_local should be symmetric in the constant reduction");
        expect_true(waveguide::is_zero_matrix(isotropic_general.F4_local),
                    "F4_local should vanish for the homogeneous isotropic case");

        expect_near(isotropic_general.M_local[0][0], 2.0 / 24.0, "M11");
        expect_near(isotropic_general.M_local[0][1], 1.0 / 24.0, "M12");
        expect_near(isotropic_general.M_local[1][1], 2.0 / 24.0, "M22");
        expect_near(isotropic_general.M_local[2][2], 2.0 / 24.0, "M33");
        expect_near(isotropic_general.F2_local[0][0], 0.5, "F2_11");
        expect_near(isotropic_general.F2_local[0][1], -0.5, "F2_12");
        expect_near(isotropic_general.F3_local[0][0], 0.5, "F3_11");
        expect_near(isotropic_general.F3_local[0][2], -0.5, "F3_13");
        expect_near(isotropic_general.F_local[0][0], -22.0 / 24.0, "F_11");
        expect_near(isotropic_general.F_local[0][1], 13.0 / 24.0, "F_12");
        expect_near(isotropic_general.F_local[0][2], 13.0 / 24.0, "F_13");

        const waveguide::ArticleLocalMaterialCoefficients anisotropic_constant_material =
            waveguide::make_constant_anisotropic_local_material(
                element, 4.0, 9.0, true, true);
        const waveguide::ArticleLocalMatrices anisotropic_constant_general =
            waveguide::assemble_article_local_matrices(
                element, anisotropic_constant_material, options);
        const waveguide::ArticleLocalMatrices anisotropic_constant_reduction =
            waveguide::assemble_article_local_matrices_constant_reduction(
                element, anisotropic_constant_material, options);

        expect_matrix_near(anisotropic_constant_general.M_local,
                           anisotropic_constant_reduction.M_local,
                           "anisotropic constant reduction M");
        expect_matrix_near(anisotropic_constant_general.F1_local,
                           anisotropic_constant_reduction.F1_local,
                           "anisotropic constant reduction F1");
        expect_matrix_near(anisotropic_constant_general.F2_local,
                           anisotropic_constant_reduction.F2_local,
                           "anisotropic constant reduction F2");
        expect_matrix_near(anisotropic_constant_general.F3_local,
                           anisotropic_constant_reduction.F3_local,
                           "anisotropic constant reduction F3");
        expect_matrix_near(anisotropic_constant_general.F4_local,
                           anisotropic_constant_reduction.F4_local,
                           "anisotropic constant reduction F4");
        expect_true(waveguide::is_zero_matrix(anisotropic_constant_general.F4_local),
                    "F4_local should still vanish when the anisotropic coefficients are constant");
        expect_true(waveguide::is_symmetric(anisotropic_constant_general.F2_local),
                    "F2_local should stay symmetric when d(nx2)/dx = 0");
        expect_true(waveguide::is_symmetric(anisotropic_constant_general.F3_local),
                    "F3_local should stay symmetric when d(nz2)/dy = 0");

        const waveguide::ArticleLocalMaterialCoefficients variable_material =
            waveguide::make_article_local_material_from_nodal_values(
                element,
                {1.0, 2.0, 1.5},
                {2.0, 3.0, 4.0},
                true,
                true,
                false,
                false,
                "variable_nodal_coefficients");
        const waveguide::ArticleLocalMatrices variable_general =
            waveguide::assemble_article_local_matrices(element, variable_material, options);

        expect_true(!waveguide::supports_constant_coefficient_article_reduction(
                        variable_material),
                    "variable material should not be tagged as a constant reduction");
        expect_near(variable_material.nx2.global_gradient[0], 1.0, "grad nx2 dx");
        expect_near(variable_material.nx2.global_gradient[1], 0.5, "grad nx2 dy");
        expect_near(variable_material.nz2.global_gradient[0], 1.0, "grad nz2 dx");
        expect_near(variable_material.nz2.global_gradient[1], 2.0, "grad nz2 dy");
        expect_near(variable_material.gz2.global_gradient[0], -1.0 / 6.0,
                    "grad gz2 dx", 1.0e-12);
        expect_near(variable_material.gz2.global_gradient[1], -0.25,
                    "grad gz2 dy", 1.0e-12);

        expect_matrix_finite(variable_general.M_local, "variable M_local");
        expect_matrix_finite(variable_general.F1_local, "variable F1_local");
        expect_matrix_finite(variable_general.F2_local, "variable F2_local");
        expect_matrix_finite(variable_general.F3_local, "variable F3_local");
        expect_matrix_finite(variable_general.F4_local, "variable F4_local");
        expect_matrix_finite(variable_general.F_local, "variable F_local");

        expect_true(waveguide::is_symmetric(variable_general.M_local),
                    "M_local should remain symmetric under nodal interpolation");
        expect_true(waveguide::is_symmetric(variable_general.F1_local),
                    "F1_local should remain symmetric under nodal interpolation");
        expect_true(!waveguide::is_symmetric(variable_general.F2_local),
                    "F2_local should become non-symmetric when d(nx2)/dx is nonzero");
        expect_true(!waveguide::is_symmetric(variable_general.F3_local),
                    "F3_local should become non-symmetric when d(nz2)/dy is nonzero");
        expect_true(!waveguide::is_symmetric(variable_general.F4_local),
                    "F4_local should become non-symmetric when the gz2 coupling is active");
        expect_true(!waveguide::is_zero_matrix(variable_general.F4_local),
                    "F4_local should be finite and nonzero in the variable case");
        expect_true(!waveguide::is_symmetric(variable_general.F_local),
                    "F_local should inherit non-symmetry from the diffused terms");

        const waveguide::LocalMatrix3 expected_variable_f =
            waveguide::add_local_matrices(
                waveguide::subtract_local_matrices(
                    waveguide::subtract_local_matrices(variable_general.F1_local,
                                                      variable_general.F2_local),
                    variable_general.F3_local),
                variable_general.F4_local);
        expect_matrix_near(variable_general.F_local, expected_variable_f,
                           "variable F combination", 1.0e-12);

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
