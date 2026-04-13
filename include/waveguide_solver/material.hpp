#pragma once

#include "waveguide_solver/element.hpp"

#include <array>
#include <string>

namespace waveguide {

struct P1ElementScalarField {
    std::array<double, 3> nodal_values{};
    double centroid_value = 0.0;
    Gradient2D reference_gradient{};
    Gradient2D global_gradient{};
    bool is_constant = true;
};

struct ArticleLocalMaterialCoefficients {
    P1ElementScalarField nx2;
    P1ElementScalarField nz2;
    P1ElementScalarField gz2;
    bool delta_x = false;
    bool delta_z = false;
    bool homogeneous = false;
    bool isotropic = false;
    std::string model_label;
};

P1ElementScalarField make_p1_element_scalar_field(
    const LinearTriangleP1Element& element,
    const std::array<double, 3>& nodal_values);

double evaluate_p1_element_scalar_field(
    const P1ElementScalarField& field,
    const std::array<double, 3>& shape_values);

ArticleLocalMaterialCoefficients make_article_local_material_from_nodal_values(
    const LinearTriangleP1Element& element,
    const std::array<double, 3>& nx2_nodal_values,
    const std::array<double, 3>& nz2_nodal_values,
    bool delta_x = false,
    bool delta_z = false,
    bool homogeneous = false,
    bool isotropic = false,
    const std::string& model_label = "custom_p1_nodal_material");

ArticleLocalMaterialCoefficients make_article_local_material_from_explicit_gz2(
    const LinearTriangleP1Element& element,
    const std::array<double, 3>& nx2_nodal_values,
    const std::array<double, 3>& nz2_nodal_values,
    const std::array<double, 3>& gz2_nodal_values,
    bool delta_x = false,
    bool delta_z = false,
    bool homogeneous = false,
    bool isotropic = false,
    const std::string& model_label = "custom_p1_nodal_material");

ArticleLocalMaterialCoefficients make_homogeneous_isotropic_local_material(
    const LinearTriangleP1Element& element,
    double refractive_index_squared);

ArticleLocalMaterialCoefficients make_constant_anisotropic_local_material(
    const LinearTriangleP1Element& element,
    double nx2_value,
    double nz2_value,
    bool delta_x = false,
    bool delta_z = false);

}  // namespace waveguide
