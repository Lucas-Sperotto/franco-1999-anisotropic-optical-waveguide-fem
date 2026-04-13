#include "waveguide_solver/local_assembly.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace waveguide {
namespace {

constexpr double kTolerance = 1.0e-12;

void validate_quadrature_rule(const ReferenceTriangleQuadratureRule& rule) {
    if (rule.points.empty()) {
        throw std::runtime_error(
            "The reference-triangle quadrature rule must contain at least one point");
    }

    if (sum_reference_triangle_quadrature_weights(rule) <= 0.0) {
        throw std::runtime_error(
            "The reference-triangle quadrature rule must have positive total weight");
    }
}

void validate_constant_reduction_inputs(
    const ArticleLocalMaterialCoefficients& material) {
    if (!supports_constant_coefficient_article_reduction(material)) {
        throw std::runtime_error(
            "Constant reduction requires nodally constant nx2, nz2, and gz2");
    }

    const double reciprocal_check =
        material.nz2.centroid_value * material.gz2.centroid_value;
    if (std::abs(reciprocal_check - 1.0) > 1.0e-9) {
        throw std::runtime_error(
            "Constant reduction requires gz2 = 1 / nz2 for the element value");
    }
}

const ReferenceTriangleQuadratureRule& resolve_quadrature_rule(
    const ArticleLocalAssemblyOptions& options,
    ReferenceTriangleQuadratureRule& fallback_rule) {
    if (!options.quadrature_rule.points.empty()) {
        return options.quadrature_rule;
    }

    fallback_rule = make_default_reference_triangle_quadrature_rule();
    return fallback_rule;
}

}  // namespace

ArticleLocalAssemblyOptions make_default_article_local_assembly_options(double k0) {
    return ArticleLocalAssemblyOptions{
        k0,
        make_default_reference_triangle_quadrature_rule(),
    };
}

LocalMatrix3 make_zero_local_matrix() {
    return {{
        {{0.0, 0.0, 0.0}},
        {{0.0, 0.0, 0.0}},
        {{0.0, 0.0, 0.0}},
    }};
}

LocalMatrix3 add_local_matrices(const LocalMatrix3& lhs, const LocalMatrix3& rhs) {
    LocalMatrix3 result = make_zero_local_matrix();
    for (std::size_t i = 0; i < result.size(); ++i) {
        for (std::size_t j = 0; j < result[i].size(); ++j) {
            result[i][j] = lhs[i][j] + rhs[i][j];
        }
    }
    return result;
}

LocalMatrix3 subtract_local_matrices(const LocalMatrix3& lhs, const LocalMatrix3& rhs) {
    LocalMatrix3 result = make_zero_local_matrix();
    for (std::size_t i = 0; i < result.size(); ++i) {
        for (std::size_t j = 0; j < result[i].size(); ++j) {
            result[i][j] = lhs[i][j] - rhs[i][j];
        }
    }
    return result;
}

LocalMatrix3 scale_local_matrix(const LocalMatrix3& matrix, double scale) {
    LocalMatrix3 result = make_zero_local_matrix();
    for (std::size_t i = 0; i < result.size(); ++i) {
        for (std::size_t j = 0; j < result[i].size(); ++j) {
            result[i][j] = scale * matrix[i][j];
        }
    }
    return result;
}

LocalMatrix3 make_reference_p1_mass_matrix() {
    return {{
        {{2.0 / 24.0, 1.0 / 24.0, 1.0 / 24.0}},
        {{1.0 / 24.0, 2.0 / 24.0, 1.0 / 24.0}},
        {{1.0 / 24.0, 1.0 / 24.0, 2.0 / 24.0}},
    }};
}

LocalMatrix3 make_consistent_mass_integral_matrix(const LinearTriangleP1Element& element) {
    return scale_local_matrix(make_reference_p1_mass_matrix(),
                              std::abs(element.jacobian_determinant));
}

LocalMatrix3 make_directional_stiffness_x_matrix(const LinearTriangleP1Element& element) {
    LocalMatrix3 matrix = make_zero_local_matrix();
    const double area = element.coefficients.area;

    for (std::size_t i = 0; i < matrix.size(); ++i) {
        for (std::size_t j = 0; j < matrix[i].size(); ++j) {
            matrix[i][j] =
                area * element.global_shape_gradients[i][0] *
                element.global_shape_gradients[j][0];
        }
    }

    return matrix;
}

LocalMatrix3 make_directional_stiffness_y_matrix(const LinearTriangleP1Element& element) {
    LocalMatrix3 matrix = make_zero_local_matrix();
    const double area = element.coefficients.area;

    for (std::size_t i = 0; i < matrix.size(); ++i) {
        for (std::size_t j = 0; j < matrix[i].size(); ++j) {
            matrix[i][j] =
                area * element.global_shape_gradients[i][1] *
                element.global_shape_gradients[j][1];
        }
    }

    return matrix;
}

bool supports_constant_coefficient_article_reduction(
    const ArticleLocalMaterialCoefficients& material) {
    return material.nx2.is_constant && material.nz2.is_constant &&
           material.gz2.is_constant;
}

ArticleLocalMatrices assemble_article_local_matrices_constant_reduction(
    const LinearTriangleP1Element& element,
    const ArticleLocalMaterialCoefficients& material,
    const ArticleLocalAssemblyOptions& options) {
    validate_constant_reduction_inputs(material);

    ArticleLocalMatrices matrices;
    matrices.mass_integral = make_consistent_mass_integral_matrix(element);
    matrices.stiffness_x = make_directional_stiffness_x_matrix(element);
    matrices.stiffness_y = make_directional_stiffness_y_matrix(element);

    const double k0_squared = options.k0 * options.k0;

    // Article Eq. (3a): constant nz2 reduces M_local to a mass-like term.
    matrices.M_local = scale_local_matrix(matrices.mass_integral,
                                          k0_squared * material.nz2.centroid_value);

    // Article Eq. (3b), F1: constant nx2 and nz2 preserve only the mass-like coupling.
    matrices.F1_local =
        scale_local_matrix(matrices.mass_integral,
                           k0_squared * material.nx2.centroid_value *
                               material.nz2.centroid_value);

    // Article Eq. (3b), F2: constant nx2 removes derivative-of-material contributions.
    matrices.F2_local =
        scale_local_matrix(matrices.stiffness_x, material.nx2.centroid_value);

    // Article Eq. (3b), F3: constant nz2 removes derivative-of-material contributions.
    matrices.F3_local =
        scale_local_matrix(matrices.stiffness_y, material.nz2.centroid_value);

    // Article Eq. (3b), F4: constant gz2 makes the x-gradient coupling vanish.
    matrices.F4_local = make_zero_local_matrix();

    matrices.F_local = add_local_matrices(
        subtract_local_matrices(
            subtract_local_matrices(matrices.F1_local, matrices.F2_local),
            matrices.F3_local),
        matrices.F4_local);

    return matrices;
}

ArticleLocalMatrices assemble_article_local_matrices(
    const LinearTriangleP1Element& element,
    const ArticleLocalMaterialCoefficients& material,
    const ArticleLocalAssemblyOptions& options) {
    ReferenceTriangleQuadratureRule fallback_rule;
    const ReferenceTriangleQuadratureRule& quadrature_rule =
        resolve_quadrature_rule(options, fallback_rule);
    validate_quadrature_rule(quadrature_rule);

    ArticleLocalMatrices matrices;
    matrices.mass_integral = make_consistent_mass_integral_matrix(element);
    matrices.stiffness_x = make_directional_stiffness_x_matrix(element);
    matrices.stiffness_y = make_directional_stiffness_y_matrix(element);

    const double abs_det_j = std::abs(element.jacobian_determinant);
    const double k0_squared = options.k0 * options.k0;
    const double delta_x = material.delta_x ? 1.0 : 0.0;
    const double delta_z = material.delta_z ? 1.0 : 0.0;
    const double dnx2_dx = material.nx2.global_gradient[0];
    const double dnz2_dy = material.nz2.global_gradient[1];
    const double dgz2_dx = material.gz2.global_gradient[0];

    for (const ReferenceTriangleQuadraturePoint& quadrature_point :
         quadrature_rule.points) {
        const double weight = abs_det_j * quadrature_point.weight;
        const auto& shape_values = quadrature_point.shape_values;
        const double nx2 =
            evaluate_p1_element_scalar_field(material.nx2, shape_values);
        const double nz2 =
            evaluate_p1_element_scalar_field(material.nz2, shape_values);

        for (std::size_t a = 0; a < shape_values.size(); ++a) {
            const double Na = shape_values[a];
            const double dNa_dx = element.global_shape_gradients[a][0];
            const double dNa_dy = element.global_shape_gradients[a][1];

            for (std::size_t b = 0; b < shape_values.size(); ++b) {
                const double Nb = shape_values[b];
                const double dNb_dx = element.global_shape_gradients[b][0];
                const double dNb_dy = element.global_shape_gradients[b][1];
                const double shape_mass = Na * Nb;

                // Article Eq. (3a): M_local = k0^2 * int(nz2 * N^T N) dA.
                matrices.M_local[a][b] += weight * k0_squared * nz2 * shape_mass;

                // Article Eq. (3b), F1: mass-like nx2 * nz2 contribution.
                matrices.F1_local[a][b] +=
                    weight * k0_squared * nx2 * nz2 * shape_mass;

                // Article Eq. (3b), F2: x-direction stiffness plus the delta_x material-gradient term.
                matrices.F2_local[a][b] +=
                    weight * (nx2 * dNa_dx * dNb_dx +
                              delta_x * dNa_dx * dnx2_dx * Nb);

                // Article Eq. (3b), F3: y-direction stiffness plus the delta_z material-gradient term.
                matrices.F3_local[a][b] +=
                    weight * (nz2 * dNa_dy * dNb_dy +
                              delta_z * Na * dnz2_dy * dNb_dy);

                // Article Eq. (3b), F4: x-gradient coupling driven by gz2 and nx2 variations.
                matrices.F4_local[a][b] +=
                    weight *
                    (delta_x * delta_z * nz2 * dgz2_dx * dnx2_dx * shape_mass +
                     delta_z * nz2 * dgz2_dx * nx2 * Na * dNb_dx);
            }
        }
    }

    matrices.F_local = add_local_matrices(
        subtract_local_matrices(
            subtract_local_matrices(matrices.F1_local, matrices.F2_local),
            matrices.F3_local),
        matrices.F4_local);

    return matrices;
}

bool is_zero_matrix(const LocalMatrix3& matrix, double tolerance) {
    for (const auto& row : matrix) {
        for (double value : row) {
            if (std::abs(value) > tolerance) {
                return false;
            }
        }
    }
    return true;
}

bool is_symmetric(const LocalMatrix3& matrix, double tolerance) {
    for (std::size_t i = 0; i < matrix.size(); ++i) {
        for (std::size_t j = i + 1; j < matrix[i].size(); ++j) {
            if (std::abs(matrix[i][j] - matrix[j][i]) > tolerance) {
                return false;
            }
        }
    }
    return true;
}

double matrix_trace(const LocalMatrix3& matrix) {
    return matrix[0][0] + matrix[1][1] + matrix[2][2];
}

double max_abs_matrix_difference(const LocalMatrix3& lhs, const LocalMatrix3& rhs) {
    double max_difference = 0.0;
    for (std::size_t i = 0; i < lhs.size(); ++i) {
        for (std::size_t j = 0; j < lhs[i].size(); ++j) {
            max_difference =
                std::max(max_difference, std::abs(lhs[i][j] - rhs[i][j]));
        }
    }
    return max_difference;
}

}  // namespace waveguide
