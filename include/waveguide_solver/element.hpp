#pragma once

#include "waveguide_solver/geometry.hpp"

#include <array>

namespace waveguide {

struct LinearTriangleP1Element {
    int element_id = 0;
    std::array<int, 3> global_node_ids{};
    TriangleGeometry geometry;
    Jacobian2D jacobian;
    Matrix2x2 inverse_jacobian{};
    double jacobian_determinant = 0.0;
    TriangleOrientation orientation = TriangleOrientation::degenerate;
    TriangleGeometricCoefficients coefficients;
    P1ShapeGradients reference_shape_gradients{};
    P1ShapeGradients global_shape_gradients{};
};

LinearTriangleP1Element make_linear_triangle_p1_element(
    const TriangleGeometry& geometry,
    int element_id = 0,
    std::array<int, 3> global_node_ids = {});

}  // namespace waveguide
