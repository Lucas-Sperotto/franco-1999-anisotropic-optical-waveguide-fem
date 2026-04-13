#pragma once

#include <cstddef>
#include <vector>

namespace waveguide {

using DenseVector = std::vector<double>;
using DenseMatrix = std::vector<DenseVector>;

DenseMatrix make_dense_zero_matrix(std::size_t rows, std::size_t cols);
DenseMatrix make_dense_identity_matrix(std::size_t size);
bool is_dense_matrix_square(const DenseMatrix& matrix);
bool is_dense_matrix_symmetric(const DenseMatrix& matrix, double tolerance = 1.0e-12);
double dense_matrix_trace(const DenseMatrix& matrix);
double max_abs_dense_matrix_difference(const DenseMatrix& lhs, const DenseMatrix& rhs);
DenseMatrix transpose_dense_matrix(const DenseMatrix& matrix);
DenseMatrix multiply_dense_matrices(const DenseMatrix& lhs, const DenseMatrix& rhs);
DenseVector multiply_dense_matrix_vector(const DenseMatrix& matrix, const DenseVector& vector);
DenseMatrix extract_dense_submatrix(const DenseMatrix& matrix,
                                    const std::vector<std::size_t>& indices);
DenseMatrix cholesky_factorize_spd(const DenseMatrix& matrix);
DenseMatrix invert_lower_triangular(const DenseMatrix& lower_triangular);

struct SymmetricEigenDecomposition {
    std::vector<double> eigenvalues;
    DenseMatrix eigenvectors;
};

SymmetricEigenDecomposition jacobi_diagonalize_symmetric(
    const DenseMatrix& matrix,
    double tolerance = 1.0e-12,
    int max_iterations = 200);

}  // namespace waveguide
