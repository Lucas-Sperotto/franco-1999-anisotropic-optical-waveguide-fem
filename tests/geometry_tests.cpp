#include "waveguide_solver/geometry.hpp"

#include <cmath>
#include <cstdlib>
#include <iostream>
#include <stdexcept>

namespace {

bool nearly_equal(double lhs, double rhs, double tolerance = 1.0e-12) {
    return std::abs(lhs - rhs) <= tolerance;
}

void expect_true(bool condition, const std::string& message) {
    if (!condition) {
        throw std::runtime_error(message);
    }
}

void expect_near(double actual, double expected, const std::string& label) {
    if (!nearly_equal(actual, expected)) {
        throw std::runtime_error(label + " mismatch: expected " +
                                 std::to_string(expected) + ", got " +
                                 std::to_string(actual));
    }
}

}  // namespace

int main() {
    try {
        const waveguide::TriangleGeometry ccw_triangle{{
            waveguide::Point2D{0.0, 0.0},
            waveguide::Point2D{1.0, 0.0},
            waveguide::Point2D{0.0, 1.0},
        }};

        expect_near(waveguide::compute_signed_area(ccw_triangle), 0.5,
                    "signed area (ccw)");
        expect_near(waveguide::compute_area(ccw_triangle), 0.5, "area (ccw)");
        expect_true(
            waveguide::compute_orientation(ccw_triangle) ==
                waveguide::TriangleOrientation::counter_clockwise,
            "expected counter_clockwise orientation for reference triangle");

        const waveguide::P1ShapeGradients gradients =
            waveguide::compute_p1_shape_gradients(ccw_triangle);
        expect_near(gradients[0][0], -1.0, "grad N1 dx");
        expect_near(gradients[0][1], -1.0, "grad N1 dy");
        expect_near(gradients[1][0], 1.0, "grad N2 dx");
        expect_near(gradients[1][1], 0.0, "grad N2 dy");
        expect_near(gradients[2][0], 0.0, "grad N3 dx");
        expect_near(gradients[2][1], 1.0, "grad N3 dy");

        const waveguide::TriangleGeometry cw_triangle{{
            waveguide::Point2D{0.0, 0.0},
            waveguide::Point2D{0.0, 1.0},
            waveguide::Point2D{1.0, 0.0},
        }};

        expect_near(waveguide::compute_signed_area(cw_triangle), -0.5,
                    "signed area (cw)");
        expect_near(waveguide::compute_area(cw_triangle), 0.5, "area (cw)");
        expect_true(
            waveguide::compute_orientation(cw_triangle) ==
                waveguide::TriangleOrientation::clockwise,
            "expected clockwise orientation for reversed triangle");

        std::cout << "waveguide_geometry_tests: all checks passed\n";
        return EXIT_SUCCESS;
    } catch (const std::exception& error) {
        std::cerr << "waveguide_geometry_tests failure: " << error.what() << "\n";
        return EXIT_FAILURE;
    }
}
