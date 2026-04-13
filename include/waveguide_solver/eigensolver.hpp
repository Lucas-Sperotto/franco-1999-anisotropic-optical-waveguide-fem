#pragma once

#include "waveguide_solver/dense_matrix.hpp"

#include <cstddef>
#include <string>
#include <vector>

namespace waveguide {

struct GeneralizedEigenpair {
    double eigenvalue = 0.0;
    double n_eff = 0.0;
    double beta = 0.0;
    bool has_neff = false;
    DenseVector reduced_mode;
};

struct GeneralizedEigenSolution {
    DenseMatrix transformed_matrix;
    bool transformed_matrix_is_symmetric = false;
    std::string solver_label;
    std::vector<GeneralizedEigenpair> eigenpairs;
};

GeneralizedEigenSolution solve_symmetric_generalized_eigenproblem(
    const DenseMatrix& F_matrix,
    const DenseMatrix& M_matrix,
    double k0,
    std::size_t requested_modes = 0);

GeneralizedEigenSolution solve_generalized_eigenproblem_dense(
    const DenseMatrix& F_matrix,
    const DenseMatrix& M_matrix,
    double k0,
    std::size_t requested_modes = 0);

}  // namespace waveguide
