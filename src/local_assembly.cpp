#include "waveguide_solver/local_assembly.hpp"

#include <cmath>
#include <stdexcept>

namespace waveguide {
namespace {

constexpr double kTolerance = 1.0e-12;

void validate_constant_reduction_inputs(
    const ArticleLocalMaterialCoefficients& material) {
    if (!supports_constant_coefficient_article_reduction(material)) {
        throw std::runtime_error(
            "Only the constant-coefficient local reduction is implemented at this stage");
    }

    if (std::abs(material.nz2.representative_value) <= kTolerance) {
        throw std::runtime_error("nz2 must be nonzero in the local material model");
    }

    const double reciprocal_check =
        material.nz2.representative_value * material.gz2.representative_value;
    if (std::abs(reciprocal_check - 1.0) > 1.0e-9) {
        throw std::runtime_error(
            "gz2 must satisfy gz2 = 1 / nz2 in the current local material model");
    }
}

}  // namespace

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

LocalScalarFieldCoefficients make_constant_local_scalar_field(double value) {
    return LocalScalarFieldCoefficients{
        {value, value, value},
        value,
        {0.0, 0.0},
        {0.0, 0.0},
        true,
    };
}

ArticleLocalMaterialCoefficients make_homogeneous_isotropic_local_material(
    double refractive_index_squared) {
    const LocalScalarFieldCoefficients nx2 =
        make_constant_local_scalar_field(refractive_index_squared);
    const LocalScalarFieldCoefficients nz2 =
        make_constant_local_scalar_field(refractive_index_squared);
    const LocalScalarFieldCoefficients gz2 =
        make_constant_local_scalar_field(1.0 / refractive_index_squared);

    return ArticleLocalMaterialCoefficients{
        nx2,
        nz2,
        gz2,
        false,
        false,
        true,
        true,
        "homogeneous_isotropic_constant_coefficients",
    };
}

bool supports_constant_coefficient_article_reduction(
    const ArticleLocalMaterialCoefficients& material) {
    return material.nx2.is_constant && material.nz2.is_constant &&
           material.gz2.is_constant && !material.delta_x && !material.delta_z;
}

ArticleLocalMatrices assemble_article_local_matrices(
    const LinearTriangleP1Element& element,
    const ArticleLocalMaterialCoefficients& material,
    const ArticleLocalAssemblyOptions& options) {
    validate_constant_reduction_inputs(material);

    ArticleLocalMatrices matrices;
    matrices.mass_integral = make_consistent_mass_integral_matrix(element);
    matrices.stiffness_x = make_directional_stiffness_x_matrix(element);
    matrices.stiffness_y = make_directional_stiffness_y_matrix(element);

    const double k0_squared = options.k0 * options.k0;

    // Article Eq. (3a): for constant nz2, M_local = k0^2 * nz2 * int(N^T N) dA.
    matrices.M_local =
        scale_local_matrix(matrices.mass_integral,
                           k0_squared * material.nz2.representative_value);

    // Article Eq. (3b), F1: for constant nx2 and nz2, only the mass-like term remains.
    matrices.F1_local =
        scale_local_matrix(matrices.mass_integral,
                           k0_squared * material.nx2.representative_value *
                               material.nz2.representative_value);

    // Article Eq. (3b), F2: in the constant-coefficient reduction, derivative terms of nx2 vanish.
    matrices.F2_local =
        scale_local_matrix(matrices.stiffness_x, material.nx2.representative_value);

    // Article Eq. (3b), F3: in the constant-coefficient reduction, derivative terms of nz2 vanish.
    matrices.F3_local =
        scale_local_matrix(matrices.stiffness_y, material.nz2.representative_value);

    // Article Eq. (3b), F4: this term vanishes when delta_x = delta_z = 0 and gradients are zero.
    matrices.F4_local = make_zero_local_matrix();

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

}  // namespace waveguide
