#include "waveguide_solver/element.hpp"

#include <cmath>
#include <stdexcept>

namespace waveguide {
namespace {

constexpr double kTolerance = 1.0e-12;

void validate_gradient_consistency(const LinearTriangleP1Element& element) {
    for (std::size_t i = 0; i < element.global_shape_gradients.size(); ++i) {
        const double expected_dx =
            element.coefficients.b[i] / element.jacobian_determinant;
        const double expected_dy =
            element.coefficients.c[i] / element.jacobian_determinant;

        if (std::abs(element.global_shape_gradients[i][0] - expected_dx) > kTolerance ||
            std::abs(element.global_shape_gradients[i][1] - expected_dy) > kTolerance) {
            throw std::runtime_error(
                "Inconsistent P1 gradient reconstruction for triangle element");
        }
    }
}

}  // namespace

LinearTriangleP1Element make_linear_triangle_p1_element(
    const TriangleGeometry& geometry,
    int element_id,
    std::array<int, 3> global_node_ids) {
    LinearTriangleP1Element element;
    element.element_id = element_id;
    element.global_node_ids = global_node_ids;
    element.geometry = geometry;
    element.jacobian = compute_jacobian(geometry);
    element.inverse_jacobian = compute_inverse_jacobian(element.jacobian);
    element.jacobian_determinant = compute_jacobian_determinant(element.jacobian);
    element.orientation = compute_orientation(geometry);
    element.coefficients = compute_geometric_coefficients(geometry);
    element.reference_shape_gradients = get_reference_p1_shape_gradients();
    element.global_shape_gradients = compute_p1_shape_gradients(geometry);

    validate_gradient_consistency(element);
    return element;
}

}  // namespace waveguide
