#include "waveguide_solver/geometry.hpp"

#include <cmath>
#include <stdexcept>

namespace waveguide {
namespace {

constexpr double kDegenerateTolerance = 1.0e-14;

}  // namespace

Jacobian2D compute_jacobian(const TriangleGeometry& triangle) {
    const Point2D& a = triangle.vertices[0];
    const Point2D& b = triangle.vertices[1];
    const Point2D& c = triangle.vertices[2];

    Jacobian2D jacobian;
    jacobian.values = {{
        {{b.x - a.x, c.x - a.x}},
        {{b.y - a.y, c.y - a.y}},
    }};
    return jacobian;
}

double compute_jacobian_determinant(const Jacobian2D& jacobian) {
    return jacobian.values[0][0] * jacobian.values[1][1] -
           jacobian.values[0][1] * jacobian.values[1][0];
}

Matrix2x2 compute_inverse_jacobian(const Jacobian2D& jacobian) {
    const double determinant = compute_jacobian_determinant(jacobian);
    if (std::abs(determinant) <= kDegenerateTolerance) {
        throw std::runtime_error("Cannot invert a degenerate triangle Jacobian");
    }

    return {{
        {{jacobian.values[1][1] / determinant, -jacobian.values[0][1] / determinant}},
        {{-jacobian.values[1][0] / determinant, jacobian.values[0][0] / determinant}},
    }};
}

Gradient2D map_reference_gradient_to_global(const Jacobian2D& jacobian,
                                            const Gradient2D& reference_gradient) {
    const Matrix2x2 inverse_jacobian = compute_inverse_jacobian(jacobian);

    return {
        inverse_jacobian[0][0] * reference_gradient[0] +
            inverse_jacobian[1][0] * reference_gradient[1],
        inverse_jacobian[0][1] * reference_gradient[0] +
            inverse_jacobian[1][1] * reference_gradient[1],
    };
}

P1ShapeGradients get_reference_p1_shape_gradients() {
    return {{
        {{-1.0, -1.0}},
        {{1.0, 0.0}},
        {{0.0, 1.0}},
    }};
}

TriangleGeometricCoefficients compute_geometric_coefficients(
    const TriangleGeometry& triangle) {
    const Point2D& a = triangle.vertices[0];
    const Point2D& b = triangle.vertices[1];
    const Point2D& c = triangle.vertices[2];

    const Jacobian2D jacobian = compute_jacobian(triangle);
    const double determinant = compute_jacobian_determinant(jacobian);
    if (std::abs(determinant) <= kDegenerateTolerance) {
        throw std::runtime_error("Cannot compute coefficients for a degenerate triangle");
    }

    TriangleGeometricCoefficients coefficients;
    coefficients.b = {{
        b.y - c.y,
        c.y - a.y,
        a.y - b.y,
    }};
    coefficients.c = {{
        c.x - b.x,
        a.x - c.x,
        b.x - a.x,
    }};
    coefficients.jacobian_determinant = determinant;
    coefficients.signed_area = 0.5 * determinant;
    coefficients.area = std::abs(coefficients.signed_area);
    return coefficients;
}

double compute_signed_area(const TriangleGeometry& triangle) {
    return 0.5 * compute_jacobian_determinant(compute_jacobian(triangle));
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
    const Jacobian2D jacobian = compute_jacobian(triangle);
    const P1ShapeGradients reference_gradients = get_reference_p1_shape_gradients();

    P1ShapeGradients gradients{};
    for (std::size_t i = 0; i < gradients.size(); ++i) {
        gradients[i] = map_reference_gradient_to_global(jacobian, reference_gradients[i]);
    }

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
