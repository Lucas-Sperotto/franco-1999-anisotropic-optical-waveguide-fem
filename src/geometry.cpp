#include "waveguide_solver/geometry.hpp"

#include <cmath>
#include <stdexcept>

namespace waveguide {
namespace {

constexpr double kDegenerateTolerance = 1.0e-14;

}  // namespace

double compute_signed_area(const TriangleGeometry& triangle) {
    const Point2D& a = triangle.vertices[0];
    const Point2D& b = triangle.vertices[1];
    const Point2D& c = triangle.vertices[2];

    return 0.5 * ((b.x - a.x) * (c.y - a.y) - (c.x - a.x) * (b.y - a.y));
}

double compute_area(const TriangleGeometry& triangle) {
    return std::abs(compute_signed_area(triangle));
}

TriangleOrientation compute_orientation(const TriangleGeometry& triangle) {
    const double signed_area = compute_signed_area(triangle);
    if (signed_area > kDegenerateTolerance) {
        return TriangleOrientation::counter_clockwise;
    }
    if (signed_area < -kDegenerateTolerance) {
        return TriangleOrientation::clockwise;
    }
    return TriangleOrientation::degenerate;
}

P1ShapeGradients compute_p1_shape_gradients(const TriangleGeometry& triangle) {
    const Point2D& a = triangle.vertices[0];
    const Point2D& b = triangle.vertices[1];
    const Point2D& c = triangle.vertices[2];

    const double signed_area = compute_signed_area(triangle);
    const double denominator = 2.0 * signed_area;
    if (std::abs(denominator) <= 2.0 * kDegenerateTolerance) {
        throw std::runtime_error("Cannot compute P1 gradients for a degenerate triangle");
    }

    P1ShapeGradients gradients{};

    gradients[0] = {(b.y - c.y) / denominator, (c.x - b.x) / denominator};
    gradients[1] = {(c.y - a.y) / denominator, (a.x - c.x) / denominator};
    gradients[2] = {(a.y - b.y) / denominator, (b.x - a.x) / denominator};

    return gradients;
}

const char* to_string(TriangleOrientation orientation) {
    switch (orientation) {
        case TriangleOrientation::clockwise:
            return "clockwise";
        case TriangleOrientation::counter_clockwise:
            return "counter_clockwise";
        case TriangleOrientation::degenerate:
            return "degenerate";
    }

    return "unknown";
}

}  // namespace waveguide
