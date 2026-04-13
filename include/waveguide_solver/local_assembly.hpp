#pragma once

#include "waveguide_solver/element.hpp"
#include "waveguide_solver/material.hpp"
#include "waveguide_solver/quadrature.hpp"

#include <array>

namespace waveguide {

using LocalMatrix3 = std::array<std::array<double, 3>, 3>;

struct ArticleLocalAssemblyOptions {
    double k0 = 1.0;
    ReferenceTriangleQuadratureRule quadrature_rule;
};

struct ArticleLocalMatrices {
    LocalMatrix3 M_local{};
    LocalMatrix3 F1_local{};
    LocalMatrix3 F2_local{};
    LocalMatrix3 F3_local{};
    LocalMatrix3 F4_local{};
    LocalMatrix3 F_local{};

    // Auxiliary directional pieces used to audit the constant-coefficient reduction.
    LocalMatrix3 mass_integral{};
    LocalMatrix3 stiffness_x{};
    LocalMatrix3 stiffness_y{};
};

ArticleLocalAssemblyOptions make_default_article_local_assembly_options(
    double k0 = 1.0);
LocalMatrix3 make_zero_local_matrix();
LocalMatrix3 add_local_matrices(const LocalMatrix3& lhs, const LocalMatrix3& rhs);
LocalMatrix3 subtract_local_matrices(const LocalMatrix3& lhs, const LocalMatrix3& rhs);
LocalMatrix3 scale_local_matrix(const LocalMatrix3& matrix, double scale);
LocalMatrix3 make_reference_p1_mass_matrix();
LocalMatrix3 make_consistent_mass_integral_matrix(const LinearTriangleP1Element& element);
LocalMatrix3 make_directional_stiffness_x_matrix(const LinearTriangleP1Element& element);
LocalMatrix3 make_directional_stiffness_y_matrix(const LinearTriangleP1Element& element);
bool supports_constant_coefficient_article_reduction(
    const ArticleLocalMaterialCoefficients& material);
ArticleLocalMatrices assemble_article_local_matrices_constant_reduction(
    const LinearTriangleP1Element& element,
    const ArticleLocalMaterialCoefficients& material,
    const ArticleLocalAssemblyOptions& options);
ArticleLocalMatrices assemble_article_local_matrices(
    const LinearTriangleP1Element& element,
    const ArticleLocalMaterialCoefficients& material,
    const ArticleLocalAssemblyOptions& options);
bool is_zero_matrix(const LocalMatrix3& matrix, double tolerance = 1.0e-12);
bool is_symmetric(const LocalMatrix3& matrix, double tolerance = 1.0e-12);
double matrix_trace(const LocalMatrix3& matrix);
double max_abs_matrix_difference(const LocalMatrix3& lhs, const LocalMatrix3& rhs);

}  // namespace waveguide
