#include "waveguide_solver/quadrature.hpp"

namespace waveguide {
namespace {

ReferenceTriangleQuadraturePoint make_quadrature_point(double xi,
                                                       double eta,
                                                       double weight) {
    return ReferenceTriangleQuadraturePoint{
        {xi, eta},
        {1.0 - xi - eta, xi, eta},
        weight,
    };
}

}  // namespace

ReferenceTriangleQuadratureRule make_reference_triangle_dunavant_degree4_rule() {
    constexpr double a = 0.445948490915965;
    constexpr double b = 0.108103018168070;
    constexpr double c = 0.091576213509771;
    constexpr double d = 0.816847572980459;
    constexpr double w1 = 0.1116907948390055;
    constexpr double w2 = 0.0549758718276610;

    ReferenceTriangleQuadratureRule rule;
    rule.name = "dunavant_degree_4";
    rule.exactness_degree = 4;
    rule.points = {
        make_quadrature_point(a, b, w1),
        make_quadrature_point(b, a, w1),
        make_quadrature_point(a, a, w1),
        make_quadrature_point(c, d, w2),
        make_quadrature_point(d, c, w2),
        make_quadrature_point(c, c, w2),
    };

    return rule;
}

ReferenceTriangleQuadratureRule make_default_reference_triangle_quadrature_rule() {
    return make_reference_triangle_dunavant_degree4_rule();
}

double sum_reference_triangle_quadrature_weights(
    const ReferenceTriangleQuadratureRule& rule) {
    double sum = 0.0;
    for (const ReferenceTriangleQuadraturePoint& point : rule.points) {
        sum += point.weight;
    }
    return sum;
}

}  // namespace waveguide
