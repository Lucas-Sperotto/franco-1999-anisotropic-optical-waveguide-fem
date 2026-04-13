#pragma once

#include "waveguide_solver/geometry.hpp"

#include <array>
#include <string>
#include <vector>

namespace waveguide {

struct ReferenceTriangleQuadraturePoint {
    Point2D reference_coordinates;
    std::array<double, 3> shape_values{};
    double weight = 0.0;
};

struct ReferenceTriangleQuadratureRule {
    std::string name;
    int exactness_degree = 0;
    std::vector<ReferenceTriangleQuadraturePoint> points;
};

ReferenceTriangleQuadratureRule make_reference_triangle_dunavant_degree4_rule();
ReferenceTriangleQuadratureRule make_default_reference_triangle_quadrature_rule();
double sum_reference_triangle_quadrature_weights(
    const ReferenceTriangleQuadratureRule& rule);

}  // namespace waveguide
