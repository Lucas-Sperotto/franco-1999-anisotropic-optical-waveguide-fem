#pragma once

#include <array>

namespace waveguide {

struct Point2D {
    double x = 0.0;
    double y = 0.0;
};

struct TriangleGeometry {
    std::array<Point2D, 3> vertices;
};

enum class TriangleOrientation {
    clockwise,
    counter_clockwise,
    degenerate
};

using Gradient2D = std::array<double, 2>;
using P1ShapeGradients = std::array<Gradient2D, 3>;

double compute_signed_area(const TriangleGeometry& triangle);
double compute_area(const TriangleGeometry& triangle);
TriangleOrientation compute_orientation(const TriangleGeometry& triangle);
P1ShapeGradients compute_p1_shape_gradients(const TriangleGeometry& triangle);
const char* to_string(TriangleOrientation orientation);

}  // namespace waveguide
