#include "waveguide_solver/eigensolver.hpp"

#include <algorithm>
#include <cmath>
#include <numeric>
#include <stdexcept>

namespace waveguide {
namespace {

DenseMatrix symmetrize_dense_matrix(const DenseMatrix& matrix) {
    if (!is_dense_matrix_square(matrix)) {
        throw std::runtime_error("Symmetrization requires a square dense matrix");
    }

    DenseMatrix result = matrix;
    for (std::size_t i = 0; i < result.size(); ++i) {
        for (std::size_t j = i + 1; j < result[i].size(); ++j) {
            const double average = 0.5 * (result[i][j] + result[j][i]);
            result[i][j] = average;
            result[j][i] = average;
        }
    }
    return result;
}

DenseVector extract_dense_matrix_column(const DenseMatrix& matrix, std::size_t column) {
    DenseVector result(matrix.size(), 0.0);
    for (std::size_t row = 0; row < matrix.size(); ++row) {
        result[row] = matrix[row][column];
    }
    return result;
}

DenseVector normalize_dense_vector(const DenseVector& vector) {
    double squared_norm = 0.0;
    for (double value : vector) {
        squared_norm += value * value;
    }

    if (squared_norm <= 0.0) {
        return vector;
    }

    const double inverse_norm = 1.0 / std::sqrt(squared_norm);
    DenseVector normalized = vector;
    for (double& value : normalized) {
        value *= inverse_norm;
    }
    return normalized;
}

}  // namespace

GeneralizedEigenSolution solve_symmetric_generalized_eigenproblem(
    const DenseMatrix& F_matrix,
    const DenseMatrix& M_matrix,
    double k0,
    std::size_t requested_modes) {
    if (!is_dense_matrix_square(F_matrix) || !is_dense_matrix_square(M_matrix)) {
        throw std::runtime_error(
            "The generalized eigenproblem requires square dense matrices");
    }

    if (F_matrix.size() != M_matrix.size()) {
        throw std::runtime_error(
            "The generalized eigenproblem requires matrices of the same dimension");
    }

    if (F_matrix.empty()) {
        throw std::runtime_error(
            "The generalized eigenproblem requires at least one free degree of freedom");
    }

    if (!is_dense_matrix_symmetric(F_matrix) || !is_dense_matrix_symmetric(M_matrix)) {
        throw std::runtime_error(
            "The current dense generalized eigensolver expects symmetric F and M");
    }

    const DenseMatrix lower = cholesky_factorize_spd(M_matrix);
    const DenseMatrix lower_inverse = invert_lower_triangular(lower);
    DenseMatrix transformed =
        multiply_dense_matrices(lower_inverse, multiply_dense_matrices(
                                                   F_matrix,
                                                   transpose_dense_matrix(lower_inverse)));
    transformed = symmetrize_dense_matrix(transformed);

    SymmetricEigenDecomposition decomposition =
        jacobi_diagonalize_symmetric(transformed);

    std::vector<std::size_t> order(decomposition.eigenvalues.size());
    std::iota(order.begin(), order.end(), 0);
    std::sort(order.begin(), order.end(), [&](std::size_t lhs, std::size_t rhs) {
        return decomposition.eigenvalues[lhs] > decomposition.eigenvalues[rhs];
    });

    if (requested_modes == 0 || requested_modes > order.size()) {
        requested_modes = order.size();
    }

    GeneralizedEigenSolution solution;
    solution.transformed_matrix = transformed;
    solution.eigenpairs.reserve(requested_modes);

    const DenseMatrix lower_inverse_transpose = transpose_dense_matrix(lower_inverse);

    for (std::size_t mode = 0; mode < requested_modes; ++mode) {
        const std::size_t index = order[mode];
        GeneralizedEigenpair eigenpair;
        eigenpair.eigenvalue = decomposition.eigenvalues[index];

        const DenseVector reduced_mode =
            normalize_dense_vector(multiply_dense_matrix_vector(
                lower_inverse_transpose,
                extract_dense_matrix_column(decomposition.eigenvectors, index)));
        eigenpair.reduced_mode = reduced_mode;

        if (eigenpair.eigenvalue >= 0.0) {
            eigenpair.has_neff = true;
            eigenpair.n_eff = std::sqrt(eigenpair.eigenvalue);
            eigenpair.beta = k0 * eigenpair.n_eff;
        }

        solution.eigenpairs.push_back(eigenpair);
    }

    return solution;
}

}  // namespace waveguide
