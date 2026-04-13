#include "waveguide_solver/local_assembly.hpp"

#include <cmath>

namespace waveguide {

LocalMatrix3 make_zero_local_matrix() {
    return {{
        {{0.0, 0.0, 0.0}},
        {{0.0, 0.0, 0.0}},
        {{0.0, 0.0, 0.0}},
    }};
}

LocalMatrix3 make_reference_p1_mass_matrix() {
    return {{
        {{2.0 / 24.0, 1.0 / 24.0, 1.0 / 24.0}},
        {{1.0 / 24.0, 2.0 / 24.0, 1.0 / 24.0}},
        {{1.0 / 24.0, 1.0 / 24.0, 2.0 / 24.0}},
    }};
}

HomogeneousIsotropicLocalMatrices assemble_basic_homogeneous_isotropic_local_matrices(
    const LinearTriangleP1Element& element) {
    HomogeneousIsotropicLocalMatrices matrices;

    const double integration_scale = std::abs(element.jacobian_determinant);
    const double area = element.coefficients.area;
    const LocalMatrix3 reference_mass = make_reference_p1_mass_matrix();

    for (std::size_t i = 0; i < matrices.consistent_mass.size(); ++i) {
        for (std::size_t j = 0; j < matrices.consistent_mass[i].size(); ++j) {
            matrices.consistent_mass[i][j] = integration_scale * reference_mass[i][j];

            const double gradient_dot =
                element.global_shape_gradients[i][0] * element.global_shape_gradients[j][0] +
                element.global_shape_gradients[i][1] * element.global_shape_gradients[j][1];
            matrices.laplacian_stiffness[i][j] = area * gradient_dot;
        }
    }

    return matrices;
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
