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

using Matrix2x2 = std::array<std::array<double, 2>, 2>;
using Gradient2D = std::array<double, 2>;
using P1ShapeGradients = std::array<Gradient2D, 3>;

enum class TriangleOrientation {
    clockwise,
    counter_clockwise,
    degenerate
};

struct Jacobian2D {
    Matrix2x2 values{};
};

struct TriangleGeometricCoefficients {
    std::array<double, 3> b{};
    std::array<double, 3> c{};
    double jacobian_determinant = 0.0;
    double signed_area = 0.0;
    double area = 0.0;
};

Jacobian2D compute_jacobian(const TriangleGeometry& triangle);
double compute_jacobian_determinant(const Jacobian2D& jacobian);
Matrix2x2 compute_inverse_jacobian(const Jacobian2D& jacobian);
Gradient2D map_reference_gradient_to_global(const Jacobian2D& jacobian,
                                            const Gradient2D& reference_gradient);
P1ShapeGradients get_reference_p1_shape_gradients();
TriangleGeometricCoefficients compute_geometric_coefficients(
    const TriangleGeometry& triangle);
double compute_signed_area(const TriangleGeometry& triangle);
double compute_area(const TriangleGeometry& triangle);
TriangleOrientation compute_orientation(const TriangleGeometry& triangle);
P1ShapeGradients compute_p1_shape_gradients(const TriangleGeometry& triangle);
const char* to_string(TriangleOrientation orientation);

}  // namespace waveguide
