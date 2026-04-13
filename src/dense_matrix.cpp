#include "waveguide_solver/dense_matrix.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace waveguide {
namespace {

constexpr double kTolerance = 1.0e-12;

void validate_rectangular_matrix(const DenseMatrix& matrix) {
    if (matrix.empty()) {
        return;
    }

    const std::size_t column_count = matrix.front().size();
    for (const DenseVector& row : matrix) {
        if (row.size() != column_count) {
            throw std::runtime_error("Dense matrix rows must all have the same size");
        }
    }
}

}  // namespace

DenseMatrix make_dense_zero_matrix(std::size_t rows, std::size_t cols) {
    return DenseMatrix(rows, DenseVector(cols, 0.0));
}

DenseMatrix make_dense_identity_matrix(std::size_t size) {
    DenseMatrix identity = make_dense_zero_matrix(size, size);
    for (std::size_t i = 0; i < size; ++i) {
        identity[i][i] = 1.0;
    }
    return identity;
}

bool is_dense_matrix_square(const DenseMatrix& matrix) {
    validate_rectangular_matrix(matrix);
    if (matrix.empty()) {
        return true;
    }
    return matrix.size() == matrix.front().size();
}

bool is_dense_matrix_symmetric(const DenseMatrix& matrix, double tolerance) {
    if (!is_dense_matrix_square(matrix)) {
        return false;
    }

    for (std::size_t i = 0; i < matrix.size(); ++i) {
        for (std::size_t j = i + 1; j < matrix[i].size(); ++j) {
            if (std::abs(matrix[i][j] - matrix[j][i]) > tolerance) {
                return false;
            }
        }
    }

    return true;
}

double dense_matrix_trace(const DenseMatrix& matrix) {
    if (!is_dense_matrix_square(matrix)) {
        throw std::runtime_error("Trace requires a square dense matrix");
    }

    double trace = 0.0;
    for (std::size_t i = 0; i < matrix.size(); ++i) {
        trace += matrix[i][i];
    }
    return trace;
}

double max_abs_dense_matrix_difference(const DenseMatrix& lhs, const DenseMatrix& rhs) {
    validate_rectangular_matrix(lhs);
    validate_rectangular_matrix(rhs);
    if (lhs.size() != rhs.size() ||
        (!lhs.empty() && !rhs.empty() && lhs.front().size() != rhs.front().size())) {
        throw std::runtime_error(
            "Dense matrices must have the same dimensions to compare them");
    }

    double max_difference = 0.0;
    for (std::size_t i = 0; i < lhs.size(); ++i) {
        for (std::size_t j = 0; j < lhs[i].size(); ++j) {
            max_difference =
                std::max(max_difference, std::abs(lhs[i][j] - rhs[i][j]));
        }
    }
    return max_difference;
}

DenseMatrix transpose_dense_matrix(const DenseMatrix& matrix) {
    validate_rectangular_matrix(matrix);
    if (matrix.empty()) {
        return {};
    }

    DenseMatrix transpose = make_dense_zero_matrix(matrix.front().size(), matrix.size());
    for (std::size_t i = 0; i < matrix.size(); ++i) {
        for (std::size_t j = 0; j < matrix[i].size(); ++j) {
            transpose[j][i] = matrix[i][j];
        }
    }
    return transpose;
}

DenseMatrix multiply_dense_matrices(const DenseMatrix& lhs, const DenseMatrix& rhs) {
    validate_rectangular_matrix(lhs);
    validate_rectangular_matrix(rhs);

    if (lhs.empty() || rhs.empty()) {
        return {};
    }

    if (lhs.front().size() != rhs.size()) {
        throw std::runtime_error("Incompatible dense matrix dimensions for multiplication");
    }

    DenseMatrix result = make_dense_zero_matrix(lhs.size(), rhs.front().size());
    for (std::size_t i = 0; i < lhs.size(); ++i) {
        for (std::size_t k = 0; k < rhs.size(); ++k) {
            for (std::size_t j = 0; j < rhs[k].size(); ++j) {
                result[i][j] += lhs[i][k] * rhs[k][j];
            }
        }
    }
    return result;
}

DenseVector multiply_dense_matrix_vector(const DenseMatrix& matrix,
                                         const DenseVector& vector) {
    validate_rectangular_matrix(matrix);
    if (!matrix.empty() && matrix.front().size() != vector.size()) {
        throw std::runtime_error(
            "Incompatible dense matrix/vector dimensions for multiplication");
    }

    DenseVector result(matrix.size(), 0.0);
    for (std::size_t i = 0; i < matrix.size(); ++i) {
        for (std::size_t j = 0; j < matrix[i].size(); ++j) {
            result[i] += matrix[i][j] * vector[j];
        }
    }
    return result;
}

DenseMatrix extract_dense_submatrix(const DenseMatrix& matrix,
                                    const std::vector<std::size_t>& indices) {
    if (!is_dense_matrix_square(matrix)) {
        throw std::runtime_error("Submatrix extraction requires a square dense matrix");
    }

    DenseMatrix result = make_dense_zero_matrix(indices.size(), indices.size());
    for (std::size_t i = 0; i < indices.size(); ++i) {
        for (std::size_t j = 0; j < indices.size(); ++j) {
            result[i][j] = matrix[indices[i]][indices[j]];
        }
    }
    return result;
}

DenseMatrix cholesky_factorize_spd(const DenseMatrix& matrix) {
    if (!is_dense_matrix_square(matrix)) {
        throw std::runtime_error("Cholesky factorization requires a square dense matrix");
    }

    const std::size_t size = matrix.size();
    DenseMatrix lower = make_dense_zero_matrix(size, size);

    for (std::size_t i = 0; i < size; ++i) {
        for (std::size_t j = 0; j <= i; ++j) {
            double sum = matrix[i][j];
            for (std::size_t k = 0; k < j; ++k) {
                sum -= lower[i][k] * lower[j][k];
            }

            if (i == j) {
                if (sum <= kTolerance) {
                    throw std::runtime_error(
                        "Dense matrix is not positive definite for Cholesky factorization");
                }
                lower[i][j] = std::sqrt(sum);
            } else {
                lower[i][j] = sum / lower[j][j];
            }
        }
    }

    return lower;
}

DenseMatrix invert_lower_triangular(const DenseMatrix& lower_triangular) {
    if (!is_dense_matrix_square(lower_triangular)) {
        throw std::runtime_error(
            "Lower-triangular inversion requires a square dense matrix");
    }

    const std::size_t size = lower_triangular.size();
    DenseMatrix inverse = make_dense_zero_matrix(size, size);

    for (std::size_t column = 0; column < size; ++column) {
        DenseVector solution(size, 0.0);
        for (std::size_t i = 0; i < size; ++i) {
            double rhs = (i == column) ? 1.0 : 0.0;
            for (std::size_t j = 0; j < i; ++j) {
                rhs -= lower_triangular[i][j] * solution[j];
            }

            if (std::abs(lower_triangular[i][i]) <= kTolerance) {
                throw std::runtime_error(
                    "Cannot invert singular lower-triangular matrix");
            }

            solution[i] = rhs / lower_triangular[i][i];
        }

        for (std::size_t row = 0; row < size; ++row) {
            inverse[row][column] = solution[row];
        }
    }

    return inverse;
}

SymmetricEigenDecomposition jacobi_diagonalize_symmetric(
    const DenseMatrix& matrix,
    double tolerance,
    int max_iterations) {
    if (!is_dense_matrix_square(matrix)) {
        throw std::runtime_error("Jacobi diagonalization requires a square dense matrix");
    }

    if (!is_dense_matrix_symmetric(matrix, tolerance * 100.0)) {
        throw std::runtime_error("Jacobi diagonalization requires a symmetric matrix");
    }

    const std::size_t size = matrix.size();
    SymmetricEigenDecomposition decomposition;
    decomposition.eigenvalues.resize(size, 0.0);
    decomposition.eigenvectors = make_dense_identity_matrix(size);

    if (size == 0) {
        return decomposition;
    }

    DenseMatrix working = matrix;

    for (int iteration = 0; iteration < max_iterations; ++iteration) {
        double max_off_diagonal = 0.0;
        std::size_t p = 0;
        std::size_t q = 0;

        for (std::size_t i = 0; i < size; ++i) {
            for (std::size_t j = i + 1; j < size; ++j) {
                const double value = std::abs(working[i][j]);
                if (value > max_off_diagonal) {
                    max_off_diagonal = value;
                    p = i;
                    q = j;
                }
            }
        }

        if (max_off_diagonal <= tolerance) {
            break;
        }

        const double a_pp = working[p][p];
        const double a_qq = working[q][q];
        const double a_pq = working[p][q];
        const double phi = 0.5 * std::atan2(2.0 * a_pq, a_qq - a_pp);
        const double cosine = std::cos(phi);
        const double sine = std::sin(phi);

        for (std::size_t k = 0; k < size; ++k) {
            if (k == p || k == q) {
                continue;
            }

            const double a_kp = working[k][p];
            const double a_kq = working[k][q];
            working[k][p] = cosine * a_kp - sine * a_kq;
            working[p][k] = working[k][p];
            working[k][q] = sine * a_kp + cosine * a_kq;
            working[q][k] = working[k][q];
        }

        working[p][p] =
            cosine * cosine * a_pp - 2.0 * sine * cosine * a_pq +
            sine * sine * a_qq;
        working[q][q] =
            sine * sine * a_pp + 2.0 * sine * cosine * a_pq +
            cosine * cosine * a_qq;
        working[p][q] = 0.0;
        working[q][p] = 0.0;

        for (std::size_t k = 0; k < size; ++k) {
            const double v_kp = decomposition.eigenvectors[k][p];
            const double v_kq = decomposition.eigenvectors[k][q];
            decomposition.eigenvectors[k][p] = cosine * v_kp - sine * v_kq;
            decomposition.eigenvectors[k][q] = sine * v_kp + cosine * v_kq;
        }
    }

    for (std::size_t i = 0; i < size; ++i) {
        decomposition.eigenvalues[i] = working[i][i];
    }

    return decomposition;
}

}  // namespace waveguide
