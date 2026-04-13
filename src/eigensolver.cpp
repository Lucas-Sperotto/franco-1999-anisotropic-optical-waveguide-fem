#include "waveguide_solver/eigensolver.hpp"

#include <algorithm>
#include <cmath>
#include <numeric>
#include <stdexcept>

namespace waveguide {
namespace {

constexpr double kQrTolerance = 1.0e-12;

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

double compute_lower_triangular_norm(const DenseMatrix& matrix) {
    double norm = 0.0;
    for (std::size_t i = 1; i < matrix.size(); ++i) {
        for (std::size_t j = 0; j < i; ++j) {
            norm += std::abs(matrix[i][j]);
        }
    }
    return norm;
}

struct DenseQrDecomposition {
    DenseMatrix Q;
    DenseMatrix R;
};

DenseQrDecomposition qr_decompose_modified_gram_schmidt(const DenseMatrix& matrix) {
    if (!is_dense_matrix_square(matrix)) {
        throw std::runtime_error("QR decomposition requires a square dense matrix");
    }

    const std::size_t size = matrix.size();
    DenseQrDecomposition decomposition;
    decomposition.Q = make_dense_zero_matrix(size, size);
    decomposition.R = make_dense_zero_matrix(size, size);

    std::vector<DenseVector> columns(size, DenseVector(size, 0.0));
    for (std::size_t j = 0; j < size; ++j) {
        columns[j] = extract_dense_matrix_column(matrix, j);
    }

    for (std::size_t j = 0; j < size; ++j) {
        DenseVector v = columns[j];

        for (std::size_t i = 0; i < j; ++i) {
            double projection = 0.0;
            for (std::size_t k = 0; k < size; ++k) {
                projection += decomposition.Q[k][i] * columns[j][k];
            }
            decomposition.R[i][j] = projection;
            for (std::size_t k = 0; k < size; ++k) {
                v[k] -= projection * decomposition.Q[k][i];
            }
        }

        double norm = 0.0;
        for (double value : v) {
            norm += value * value;
        }
        norm = std::sqrt(norm);
        decomposition.R[j][j] = norm;

        if (norm <= kQrTolerance) {
            continue;
        }

        for (std::size_t k = 0; k < size; ++k) {
            decomposition.Q[k][j] = v[k] / norm;
        }
    }

    return decomposition;
}

std::vector<double> qr_iterate_general_eigenvalues(DenseMatrix matrix,
                                                   double tolerance = 1.0e-12,
                                                   int max_iterations = 1000) {
    if (!is_dense_matrix_square(matrix)) {
        throw std::runtime_error("QR iteration requires a square dense matrix");
    }

    const std::size_t size = matrix.size();
    if (size == 0) {
        return {};
    }

    for (int iteration = 0; iteration < max_iterations; ++iteration) {
        if (compute_lower_triangular_norm(matrix) <= tolerance) {
            break;
        }

        const double shift = matrix[size - 1][size - 1];
        DenseMatrix shifted = matrix;
        for (std::size_t i = 0; i < size; ++i) {
            shifted[i][i] -= shift;
        }

        const DenseQrDecomposition decomposition =
            qr_decompose_modified_gram_schmidt(shifted);
        matrix = multiply_dense_matrices(decomposition.R, decomposition.Q);
        for (std::size_t i = 0; i < size; ++i) {
            matrix[i][i] += shift;
        }
    }

    std::vector<double> eigenvalues(size, 0.0);
    for (std::size_t i = 0; i < size; ++i) {
        eigenvalues[i] = matrix[i][i];
    }
    return eigenvalues;
}

GeneralizedEigenSolution finalize_eigen_solution_from_values(
    const DenseMatrix& transformed_matrix,
    const std::vector<double>& eigenvalues,
    double k0,
    std::size_t requested_modes,
    const std::string& solver_label) {
    std::vector<std::size_t> order(eigenvalues.size());
    std::iota(order.begin(), order.end(), 0);
    std::sort(order.begin(), order.end(), [&](std::size_t lhs, std::size_t rhs) {
        return eigenvalues[lhs] > eigenvalues[rhs];
    });

    if (requested_modes == 0 || requested_modes > order.size()) {
        requested_modes = order.size();
    }

    GeneralizedEigenSolution solution;
    solution.transformed_matrix = transformed_matrix;
    solution.transformed_matrix_is_symmetric =
        is_dense_matrix_symmetric(transformed_matrix, 1.0e-10);
    solution.solver_label = solver_label;
    solution.eigenpairs.reserve(requested_modes);

    for (std::size_t mode = 0; mode < requested_modes; ++mode) {
        const std::size_t index = order[mode];
        GeneralizedEigenpair eigenpair;
        eigenpair.eigenvalue = eigenvalues[index];
        if (eigenpair.eigenvalue >= 0.0) {
            eigenpair.has_neff = true;
            eigenpair.n_eff = std::sqrt(eigenpair.eigenvalue);
            eigenpair.beta = k0 * eigenpair.n_eff;
        }
        solution.eigenpairs.push_back(eigenpair);
    }

    return solution;
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

    const SymmetricEigenDecomposition decomposition =
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

    const std::vector<double> eigenvalues =
        qr_iterate_general_eigenvalues(transformed, 1.0e-10, 4000);

    return finalize_eigen_solution_from_values(
        transformed,
        eigenvalues,
        k0,
        requested_modes,
        "general_qr");
}

}  // namespace waveguide
