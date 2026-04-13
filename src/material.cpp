#include "waveguide_solver/material.hpp"

#include <cmath>
#include <stdexcept>

namespace waveguide {
namespace {

constexpr double kTolerance = 1.0e-12;

bool are_all_equal(const std::array<double, 3>& values) {
    return std::abs(values[0] - values[1]) <= kTolerance &&
           std::abs(values[1] - values[2]) <= kTolerance;
}

Gradient2D accumulate_gradient(const std::array<double, 3>& nodal_values,
                               const P1ShapeGradients& gradients) {
    Gradient2D result{0.0, 0.0};

    for (std::size_t i = 0; i < nodal_values.size(); ++i) {
        result[0] += nodal_values[i] * gradients[i][0];
        result[1] += nodal_values[i] * gradients[i][1];
    }

    return result;
}

std::array<double, 3> make_reciprocal_nodal_values(
    const std::array<double, 3>& nodal_values) {
    std::array<double, 3> reciprocals{};
    for (std::size_t i = 0; i < nodal_values.size(); ++i) {
        if (std::abs(nodal_values[i]) <= kTolerance) {
            throw std::runtime_error(
                "nz2 nodal values must be nonzero to derive gz2 nodal values");
        }
        reciprocals[i] = 1.0 / nodal_values[i];
    }
    return reciprocals;
}

void validate_reciprocal_nodal_relation(const std::array<double, 3>& nz2_nodal_values,
                                        const std::array<double, 3>& gz2_nodal_values) {
    for (std::size_t i = 0; i < nz2_nodal_values.size(); ++i) {
        if (std::abs(nz2_nodal_values[i]) <= kTolerance) {
            throw std::runtime_error("nz2 nodal values must be nonzero");
        }

        const double reciprocal_check = nz2_nodal_values[i] * gz2_nodal_values[i];
        if (std::abs(reciprocal_check - 1.0) > 1.0e-9) {
            throw std::runtime_error(
                "gz2 nodal values must satisfy gz2 = 1 / nz2 at each element node");
        }
    }
}

}  // namespace

P1ElementScalarField make_p1_element_scalar_field(
    const LinearTriangleP1Element& element,
    const std::array<double, 3>& nodal_values) {
    P1ElementScalarField field;
    field.nodal_values = nodal_values;
    field.centroid_value =
        (nodal_values[0] + nodal_values[1] + nodal_values[2]) / 3.0;
    field.reference_gradient =
        accumulate_gradient(nodal_values, element.reference_shape_gradients);
    field.global_gradient =
        accumulate_gradient(nodal_values, element.global_shape_gradients);
    field.is_constant = are_all_equal(nodal_values);
    return field;
}

double evaluate_p1_element_scalar_field(
    const P1ElementScalarField& field,
    const std::array<double, 3>& shape_values) {
    double value = 0.0;
    for (std::size_t i = 0; i < shape_values.size(); ++i) {
        value += field.nodal_values[i] * shape_values[i];
    }
    return value;
}

ArticleLocalMaterialCoefficients make_article_local_material_from_nodal_values(
    const LinearTriangleP1Element& element,
    const std::array<double, 3>& nx2_nodal_values,
    const std::array<double, 3>& nz2_nodal_values,
    bool delta_x,
    bool delta_z,
    bool homogeneous,
    bool isotropic,
    const std::string& model_label) {
    return make_article_local_material_from_explicit_gz2(
        element,
        nx2_nodal_values,
        nz2_nodal_values,
        make_reciprocal_nodal_values(nz2_nodal_values),
        delta_x,
        delta_z,
        homogeneous,
        isotropic,
        model_label);
}

ArticleLocalMaterialCoefficients make_article_local_material_from_explicit_gz2(
    const LinearTriangleP1Element& element,
    const std::array<double, 3>& nx2_nodal_values,
    const std::array<double, 3>& nz2_nodal_values,
    const std::array<double, 3>& gz2_nodal_values,
    bool delta_x,
    bool delta_z,
    bool homogeneous,
    bool isotropic,
    const std::string& model_label) {
    validate_reciprocal_nodal_relation(nz2_nodal_values, gz2_nodal_values);

    ArticleLocalMaterialCoefficients material;
    material.nx2 = make_p1_element_scalar_field(element, nx2_nodal_values);
    material.nz2 = make_p1_element_scalar_field(element, nz2_nodal_values);
    material.gz2 = make_p1_element_scalar_field(element, gz2_nodal_values);
    material.delta_x = delta_x;
    material.delta_z = delta_z;
    material.homogeneous = homogeneous;
    material.isotropic = isotropic;
    material.model_label = model_label;
    return material;
}

ArticleLocalMaterialCoefficients make_homogeneous_isotropic_local_material(
    const LinearTriangleP1Element& element,
    double refractive_index_squared) {
    const std::array<double, 3> isotropic_values{
        refractive_index_squared,
        refractive_index_squared,
        refractive_index_squared,
    };

    return make_article_local_material_from_nodal_values(
        element,
        isotropic_values,
        isotropic_values,
        false,
        false,
        true,
        true,
        "homogeneous_isotropic_constant_coefficients");
}

ArticleLocalMaterialCoefficients make_constant_anisotropic_local_material(
    const LinearTriangleP1Element& element,
    double nx2_value,
    double nz2_value,
    bool delta_x,
    bool delta_z) {
    const std::array<double, 3> nx2_values{nx2_value, nx2_value, nx2_value};
    const std::array<double, 3> nz2_values{nz2_value, nz2_value, nz2_value};

    return make_article_local_material_from_nodal_values(
        element,
        nx2_values,
        nz2_values,
        delta_x,
        delta_z,
        true,
        false,
        "constant_anisotropic_coefficients");
}

}  // namespace waveguide
