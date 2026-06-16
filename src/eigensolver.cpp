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




// Solves Ax=b using Gaussian elimination with partial pivoting.
// a_copy is modified in place. Returns false if the matrix is singular.
bool solve_linear_system_gaussian(DenseMatrix a_copy, DenseVector& b, DenseVector& x) {
    const std::size_t n = a_copy.size();
    x.assign(n, 0.0);
    for (std::size_t col = 0; col < n; ++col) {
        std::size_t pivot_row = col;
        double max_val = std::abs(a_copy[col][col]);
        for (std::size_t row = col + 1; row < n; ++row) {
            if (std::abs(a_copy[row][col]) > max_val) {
                max_val = std::abs(a_copy[row][col]);
                pivot_row = row;
            }
        }
        if (max_val < 1.0e-14) return false;
        if (pivot_row != col) {
            std::swap(a_copy[col], a_copy[pivot_row]);
            std::swap(b[col], b[pivot_row]);
        }
        for (std::size_t row = col + 1; row < n; ++row) {
            const double factor = a_copy[row][col] / a_copy[col][col];
            for (std::size_t k = col; k < n; ++k) a_copy[row][k] -= factor * a_copy[col][k];
            b[row] -= factor * b[col];
        }
    }
    for (std::size_t i = n; i-- > 0;) {
        x[i] = b[i];
        for (std::size_t j = i + 1; j < n; ++j) x[i] -= a_copy[i][j] * x[j];
        x[i] /= a_copy[i][i];
    }
    return true;
}

// Inverse iteration: find eigenvector of A nearest to `lambda`.
// Gram-Schmidt deflates against already_found vectors.
DenseVector inverse_iteration_eigenvector(const DenseMatrix& a, double lambda,
                                          const std::vector<DenseVector>& already_found,
                                          int max_iter = 60) {
    const std::size_t n = a.size();
    DenseMatrix shifted = a;
    for (std::size_t i = 0; i < n; ++i) shifted[i][i] -= lambda;

    DenseVector v(n, 0.0);
    v[n / 2] = 1.0;

    for (int iter = 0; iter < max_iter; ++iter) {
        for (const DenseVector& found : already_found) {
            double dot = 0.0;
            for (std::size_t i = 0; i < n; ++i) dot += v[i] * found[i];
            for (std::size_t i = 0; i < n; ++i) v[i] -= dot * found[i];
        }
        v = normalize_dense_vector(v);
        DenseVector rhs = v;
        DenseVector v_new(n, 0.0);
        if (!solve_linear_system_gaussian(shifted, rhs, v_new)) break;
        v = v_new;
    }
    return normalize_dense_vector(v);
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
            "The symmetric dense generalized eigensolver expects symmetric F and M");
    }

    const DenseMatrix lower = cholesky_factorize_spd(M_matrix);
    const DenseMatrix lower_inverse = invert_lower_triangular(lower);
    DenseMatrix transformed =
        multiply_dense_matrices(lower_inverse, multiply_dense_matrices(
                                                   F_matrix,
                                                   transpose_dense_matrix(lower_inverse)));
    transformed = symmetrize_dense_matrix(transformed);

    const int jacobi_max_iter =
        std::max(200, 5 * static_cast<int>(transformed.size()) *
                          static_cast<int>(transformed.size()));
    const SymmetricEigenDecomposition decomposition =
        jacobi_diagonalize_symmetric(transformed, 1.0e-12, jacobi_max_iter);

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
    solution.transformed_matrix_is_symmetric = true;
    solution.solver_label = "symmetric_jacobi";
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

GeneralizedEigenSolution solve_generalized_eigenproblem_dense(
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

    if (!is_dense_matrix_symmetric(M_matrix)) {
        throw std::runtime_error(
            "The dense generalized eigensolver requires a symmetric positive-definite M");
    }

    if (is_dense_matrix_symmetric(F_matrix)) {
        return solve_symmetric_generalized_eigenproblem(
            F_matrix, M_matrix, k0, requested_modes);
    }

    const DenseMatrix lower = cholesky_factorize_spd(M_matrix);
    const DenseMatrix lower_inverse = invert_lower_triangular(lower);
    const DenseMatrix transformed =
        multiply_dense_matrices(lower_inverse, multiply_dense_matrices(
                                                   F_matrix,
                                                   transpose_dense_matrix(lower_inverse)));

    const std::size_t n = transformed.size();
    const std::size_t n_modes =
        (requested_modes == 0 || requested_modes > n) ? n : requested_modes;

    // Step 1: Jacobi on the symmetrized transformed matrix gives reliable eigenvalue
    // estimates near the true non-symmetric eigenvalues (the non-symmetric correction
    // is small: typically < 0.3%).  This avoids the QR convergence-order problem
    // (QR converges smallest eigenvalues first, leaving the fundamental mode—the
    // largest—as the least accurate) and the power-iteration problem (power iteration
    // finds the largest-|λ| eigenvalue, which can be a large spurious negative one
    // introduced by steep gradient terms in anisotropic profiles like Ti:LiNbO3).
    const DenseMatrix transformed_sym = symmetrize_dense_matrix(transformed);
    const int jacobi_max_iter =
        std::max(200, 5 * static_cast<int>(n) * static_cast<int>(n));
    const SymmetricEigenDecomposition sym_decomp =
        jacobi_diagonalize_symmetric(transformed_sym, 1.0e-12, jacobi_max_iter);

    std::vector<std::size_t> order(n);
    std::iota(order.begin(), order.end(), 0);
    std::sort(order.begin(), order.end(), [&](std::size_t a, std::size_t b) {
        return sym_decomp.eigenvalues[a] > sym_decomp.eigenvalues[b];
    });

    // Step 2: For each requested mode, use the symmetric eigenvalue as the initial
    // shift for inverse iteration on the FULL non-symmetric transformed matrix.
    // Inverse iteration with shift λ₀ converges to the eigenvector with eigenvalue
    // nearest to λ₀, regardless of the sign or magnitude of other eigenvalues.
    //
    // Step 3: Refine the eigenvalue via the Rayleigh quotient Q^T A Q, which is
    // quadratically more accurate than the shift or the symmetric estimate.
    const DenseMatrix lower_inverse_transpose = transpose_dense_matrix(lower_inverse);

    GeneralizedEigenSolution solution;
    solution.transformed_matrix = transformed;
    solution.transformed_matrix_is_symmetric = false;
    solution.solver_label = "general_nonsym_refined";
    solution.eigenpairs.reserve(n_modes);

    std::vector<DenseVector> found_vecs;
    for (std::size_t mode = 0; mode < n_modes; ++mode) {
        const double lambda_shift = sym_decomp.eigenvalues[order[mode]];

        const DenseVector y =
            inverse_iteration_eigenvector(transformed, lambda_shift, found_vecs, 60);
        found_vecs.push_back(y);

        // Rayleigh quotient for accurate non-symmetric eigenvalue
        const DenseVector ay = multiply_dense_matrix_vector(transformed, y);
        double lambda_refined = 0.0;
        for (std::size_t i = 0; i < n; ++i) lambda_refined += y[i] * ay[i];

        GeneralizedEigenpair eigenpair;
        eigenpair.eigenvalue = lambda_refined;

        eigenpair.reduced_mode = normalize_dense_vector(
            multiply_dense_matrix_vector(lower_inverse_transpose, y));

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
