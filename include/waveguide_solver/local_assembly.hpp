#pragma once

#include "waveguide_solver/element.hpp"

#include <array>
#include <string>

namespace waveguide {

using LocalMatrix3 = std::array<std::array<double, 3>, 3>;

struct LocalScalarFieldCoefficients {
    std::array<double, 3> nodal_values{};
    double representative_value = 0.0;
    Gradient2D reference_gradient{};
    Gradient2D global_gradient{};
    bool is_constant = true;
};

struct ArticleLocalMaterialCoefficients {
    LocalScalarFieldCoefficients nx2;
    LocalScalarFieldCoefficients nz2;
    LocalScalarFieldCoefficients gz2;
    bool delta_x = false;
    bool delta_z = false;
    bool homogeneous = true;
    bool isotropic = false;
    std::string model_label;
};

struct ArticleLocalAssemblyOptions {
    double k0 = 1.0;
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

LocalMatrix3 make_zero_local_matrix();
LocalMatrix3 add_local_matrices(const LocalMatrix3& lhs, const LocalMatrix3& rhs);
LocalMatrix3 subtract_local_matrices(const LocalMatrix3& lhs, const LocalMatrix3& rhs);
LocalMatrix3 scale_local_matrix(const LocalMatrix3& matrix, double scale);
LocalMatrix3 make_reference_p1_mass_matrix();
LocalMatrix3 make_consistent_mass_integral_matrix(const LinearTriangleP1Element& element);
LocalMatrix3 make_directional_stiffness_x_matrix(const LinearTriangleP1Element& element);
LocalMatrix3 make_directional_stiffness_y_matrix(const LinearTriangleP1Element& element);
LocalScalarFieldCoefficients make_constant_local_scalar_field(double value);
ArticleLocalMaterialCoefficients make_homogeneous_isotropic_local_material(
    double refractive_index_squared);
bool supports_constant_coefficient_article_reduction(
    const ArticleLocalMaterialCoefficients& material);
ArticleLocalMatrices assemble_article_local_matrices(
    const LinearTriangleP1Element& element,
    const ArticleLocalMaterialCoefficients& material,
    const ArticleLocalAssemblyOptions& options);
bool is_zero_matrix(const LocalMatrix3& matrix, double tolerance = 1.0e-12);
bool is_symmetric(const LocalMatrix3& matrix, double tolerance = 1.0e-12);
double matrix_trace(const LocalMatrix3& matrix);

}  // namespace waveguide
