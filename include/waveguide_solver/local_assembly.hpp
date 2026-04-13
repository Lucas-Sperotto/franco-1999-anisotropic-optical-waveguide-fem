#pragma once

#include "waveguide_solver/element.hpp"

#include <array>

namespace waveguide {

using LocalMatrix3 = std::array<std::array<double, 3>, 3>;

struct HomogeneousIsotropicLocalMatrices {
    LocalMatrix3 consistent_mass{};
    LocalMatrix3 laplacian_stiffness{};
};

LocalMatrix3 make_zero_local_matrix();
LocalMatrix3 make_reference_p1_mass_matrix();
HomogeneousIsotropicLocalMatrices assemble_basic_homogeneous_isotropic_local_matrices(
    const LinearTriangleP1Element& element);
bool is_symmetric(const LocalMatrix3& matrix, double tolerance = 1.0e-12);
double matrix_trace(const LocalMatrix3& matrix);

}  // namespace waveguide
