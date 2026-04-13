#include "waveguide_solver/app.hpp"
#include "waveguide_solver/config.hpp"
#include "waveguide_solver/dense_matrix.hpp"
#include "waveguide_solver/eigensolver.hpp"
#include "waveguide_solver/element.hpp"
#include "waveguide_solver/global_assembly.hpp"
#include "waveguide_solver/local_assembly.hpp"
#include "waveguide_solver/mesh.hpp"

#include <array>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace waveguide {
namespace {

struct CliOptions {
    std::filesystem::path case_file;
    std::filesystem::path output_dir;
    std::string run_label;
    bool show_help = false;
};

void print_usage() {
    std::cout
        << "waveguide_solver\n"
        << "Uso:\n"
        << "  waveguide_solver --case <arquivo.yaml> --output <diretorio> "
           "[--run-label <rotulo>]\n"
        << "  waveguide_solver --help\n";
}

CliOptions parse_arguments(int argc, char** argv) {
    CliOptions options;

    for (int i = 1; i < argc; ++i) {
        const std::string arg = argv[i];

        if (arg == "--help" || arg == "-h") {
            options.show_help = true;
            return options;
        }

        if (arg == "--case") {
            if (i + 1 >= argc) {
                throw std::runtime_error("Missing value after --case");
            }
            options.case_file = argv[++i];
            continue;
        }

        if (arg == "--output") {
            if (i + 1 >= argc) {
                throw std::runtime_error("Missing value after --output");
            }
            options.output_dir = argv[++i];
            continue;
        }

        if (arg == "--run-label") {
            if (i + 1 >= argc) {
                throw std::runtime_error("Missing value after --run-label");
            }
            options.run_label = argv[++i];
            continue;
        }

        throw std::runtime_error("Unknown argument: " + arg);
    }

    if (options.case_file.empty()) {
        throw std::runtime_error("A case file must be provided with --case");
    }

    if (options.output_dir.empty()) {
        throw std::runtime_error("An output directory must be provided with --output");
    }

    return options;
}

std::filesystem::path make_absolute_from_case(
    const std::filesystem::path& case_file,
    const std::string& referenced_path) {
    std::filesystem::path path(referenced_path);
    if (path.is_relative()) {
        path = case_file.parent_path() / path;
    }
    return std::filesystem::absolute(path).lexically_normal();
}

void write_text_file(const std::filesystem::path& path, const std::string& content) {
    std::ofstream output(path);
    if (!output.is_open()) {
        throw std::runtime_error("Could not write file: " + path.string());
    }
    output << content;
}

std::string bool_to_text(bool value) {
    return value ? "yes" : "no";
}

std::string format_number(double value) {
    std::ostringstream stream;
    stream << std::fixed << std::setprecision(6) << value;
    return stream.str();
}

std::string format_matrix2x2(const Matrix2x2& matrix) {
    std::ostringstream stream;
    stream << "[[" << format_number(matrix[0][0]) << ", " << format_number(matrix[0][1])
           << "], [" << format_number(matrix[1][0]) << ", " << format_number(matrix[1][1])
           << "]]";
    return stream.str();
}

std::string format_vector3(const std::array<double, 3>& values) {
    std::ostringstream stream;
    stream << "[" << format_number(values[0]) << ", " << format_number(values[1])
           << ", " << format_number(values[2]) << "]";
    return stream.str();
}

std::string format_gradient(const Gradient2D& gradient) {
    std::ostringstream stream;
    stream << "[" << format_number(gradient[0]) << ", " << format_number(gradient[1])
           << "]";
    return stream.str();
}

std::string mode_index_to_label(std::size_t one_based_index) {
    if (one_based_index >= 1 && one_based_index <= 3) {
        return "TE" + std::to_string(one_based_index - 1);
    }
    return "mode_" + std::to_string(one_based_index);
}

std::string format_map_value_range(const std::map<int, double>& values_by_node_id) {
    if (values_by_node_id.empty()) {
        return "min=0.000000, max=0.000000";
    }

    double min_value = values_by_node_id.begin()->second;
    double max_value = values_by_node_id.begin()->second;
    for (const auto& [node_id, value] : values_by_node_id) {
        (void)node_id;
        min_value = std::min(min_value, value);
        max_value = std::max(max_value, value);
    }

    std::ostringstream stream;
    stream << "min=" << format_number(min_value)
           << ", max=" << format_number(max_value);
    return stream.str();
}

template <typename T>
std::string format_generic_vector(const std::vector<T>& values) {
    std::ostringstream stream;
    stream << "[";
    for (std::size_t i = 0; i < values.size(); ++i) {
        stream << values[i];
        if (i + 1 != values.size()) {
            stream << ", ";
        }
    }
    stream << "]";
    return stream.str();
}

std::string format_local_matrix(const LocalMatrix3& matrix) {
    std::ostringstream stream;
    for (std::size_t i = 0; i < matrix.size(); ++i) {
        stream << "[" << format_number(matrix[i][0]) << ", " << format_number(matrix[i][1])
               << ", " << format_number(matrix[i][2]) << "]";
        if (i + 1 != matrix.size()) {
            stream << "\n";
        }
    }
    return stream.str();
}

std::string format_local_matrix_flags(const LocalMatrix3& matrix) {
    std::ostringstream stream;
    stream << "symmetric=" << bool_to_text(is_symmetric(matrix))
           << ", zero=" << bool_to_text(is_zero_matrix(matrix))
           << ", trace=" << format_number(matrix_trace(matrix));
    return stream.str();
}

std::string format_dense_matrix(const DenseMatrix& matrix) {
    std::ostringstream stream;
    for (std::size_t i = 0; i < matrix.size(); ++i) {
        stream << "[";
        for (std::size_t j = 0; j < matrix[i].size(); ++j) {
            stream << format_number(matrix[i][j]);
            if (j + 1 != matrix[i].size()) {
                stream << ", ";
            }
        }
        stream << "]";
        if (i + 1 != matrix.size()) {
            stream << "\n";
        }
    }
    return stream.str();
}

std::string format_dense_matrix_csv(const DenseMatrix& matrix) {
    std::ostringstream stream;
    for (std::size_t i = 0; i < matrix.size(); ++i) {
        for (std::size_t j = 0; j < matrix[i].size(); ++j) {
            stream << format_number(matrix[i][j]);
            if (j + 1 != matrix[i].size()) {
                stream << ",";
            }
        }
        if (i + 1 != matrix.size()) {
            stream << "\n";
        }
    }
    return stream.str();
}

std::string format_dense_matrix_flags(const DenseMatrix& matrix) {
    std::ostringstream stream;
    stream << "symmetric=" << bool_to_text(is_dense_matrix_symmetric(matrix))
           << ", trace=" << format_number(dense_matrix_trace(matrix))
           << ", rows=" << matrix.size()
           << ", cols=" << (matrix.empty() ? 0 : matrix.front().size());
    return stream.str();
}

std::string determine_run_label(const CliOptions& options,
                                const std::filesystem::path& output_dir) {
    if (!options.run_label.empty()) {
        return options.run_label;
    }
    return output_dir.filename().string();
}

void append_scalar_field_summary(std::ostringstream& stream,
                                 const std::string& label,
                                 const P1ElementScalarField& field) {
    stream << label << "_nodal: " << format_vector3(field.nodal_values) << "\n";
    stream << label << "_centroid_value: " << format_number(field.centroid_value)
           << "\n";
    stream << label << "_reference_gradient: " << format_gradient(field.reference_gradient)
           << "\n";
    stream << label << "_global_gradient: " << format_gradient(field.global_gradient)
           << "\n";
    stream << label << "_is_constant: " << bool_to_text(field.is_constant) << "\n";
}

void append_quadrature_rule_summary(std::ostringstream& stream,
                                    const ReferenceTriangleQuadratureRule& rule) {
    stream << "quadrature_rule: " << rule.name << "\n";
    stream << "quadrature_exactness_degree: " << rule.exactness_degree << "\n";
    stream << "quadrature_point_count: " << rule.points.size() << "\n";
    stream << "quadrature_weight_sum: "
           << format_number(sum_reference_triangle_quadrature_weights(rule)) << "\n";
}

void append_quadrature_point_listing(std::ostringstream& stream,
                                     const ReferenceTriangleQuadratureRule& rule) {
    stream << "quadrature_points:\n";
    for (std::size_t i = 0; i < rule.points.size(); ++i) {
        const ReferenceTriangleQuadraturePoint& point = rule.points[i];
        stream << "  - point_" << (i + 1) << ": xi="
               << format_number(point.reference_coordinates.x)
               << ", eta=" << format_number(point.reference_coordinates.y)
               << ", weight=" << format_number(point.weight)
               << ", N=" << format_vector3(point.shape_values) << "\n";
    }
}

std::string build_eigenvalues_csv(const GeneralizedEigenSolution& solution) {
    std::ostringstream stream;
    stream << "mode_index,eigenvalue_n_eff_squared,status\n";
    for (std::size_t i = 0; i < solution.eigenpairs.size(); ++i) {
        const GeneralizedEigenpair& eigenpair = solution.eigenpairs[i];
        stream << (i + 1) << "," << format_number(eigenpair.eigenvalue) << ","
               << (eigenpair.has_neff ? "ok" : "not_applicable") << "\n";
    }
    return stream.str();
}

std::string build_neff_csv(const GeneralizedEigenSolution& solution) {
    std::ostringstream stream;
    stream << "mode_index,eigenvalue_n_eff_squared,neff,beta,status\n";
    for (std::size_t i = 0; i < solution.eigenpairs.size(); ++i) {
        const GeneralizedEigenpair& eigenpair = solution.eigenpairs[i];
        stream << (i + 1) << "," << format_number(eigenpair.eigenvalue) << ",";
        if (eigenpair.has_neff) {
            stream << format_number(eigenpair.n_eff) << ","
                   << format_number(eigenpair.beta) << ",ok\n";
        } else {
            stream << ",,not_applicable\n";
        }
    }
    return stream.str();
}

std::string build_dispersion_curve_points_csv(const GeneralizedEigenSolution& solution,
                                              double diffusion_depth,
                                              double k0) {
    std::ostringstream stream;
    stream << "b,k0,k0_b,mode_index,mode_label,eigenvalue_n_eff_squared,neff,beta,status\n";
    for (std::size_t i = 0; i < solution.eigenpairs.size(); ++i) {
        const GeneralizedEigenpair& eigenpair = solution.eigenpairs[i];
        stream << format_number(diffusion_depth) << "," << format_number(k0) << ","
               << format_number(k0 * diffusion_depth) << "," << (i + 1) << ","
               << mode_index_to_label(i + 1) << ","
               << format_number(eigenpair.eigenvalue) << ",";
        if (eigenpair.has_neff) {
            stream << format_number(eigenpair.n_eff) << ","
                   << format_number(eigenpair.beta) << ",ok\n";
        } else {
            stream << ",,not_applicable\n";
        }
    }
    return stream.str();
}

std::string build_nodal_material_fields_csv(const Mesh& mesh,
                                            const GlobalNodalMaterialFields& material_fields) {
    std::ostringstream stream;
    stream << "node_id,x,y,nx2,nz2,gz2,refractive_index\n";
    for (const MeshNode& node : mesh.nodes) {
        const double nx2 =
            get_global_material_value(material_fields.nx2_by_node_id, node.id, "nx2");
        const double nz2 =
            get_global_material_value(material_fields.nz2_by_node_id, node.id, "nz2");
        const double gz2 =
            get_global_material_value(material_fields.gz2_by_node_id, node.id, "gz2");
        stream << node.id << "," << format_number(node.point.x) << ","
               << format_number(node.point.y) << "," << format_number(nx2) << ","
               << format_number(nz2) << "," << format_number(gz2) << ","
               << format_number(std::sqrt(std::max(nx2, 0.0))) << "\n";
    }
    return stream.str();
}

}  // namespace

int run_application(int argc, char** argv) {
    try {
        const CliOptions options = parse_arguments(argc, argv);
        if (options.show_help) {
            print_usage();
            return 0;
        }

        const std::filesystem::path case_file =
            std::filesystem::absolute(options.case_file).lexically_normal();
        const CaseConfig config = load_case_config(case_file);

        const std::filesystem::path mesh_file =
            make_absolute_from_case(case_file, config.mesh_file);
        const bool mesh_exists_on_disk = std::filesystem::exists(mesh_file);
        if (!mesh_exists_on_disk) {
            throw std::runtime_error(
                "Referenced mesh file does not exist: " + mesh_file.string());
        }

        const Mesh mesh = load_minimal_mesh(mesh_file);
        const TriangleElement& first_triangle = mesh.triangles.front();
        const LinearTriangleP1Element first_element = mesh.make_p1_element(first_triangle);

        constexpr double kPi = 3.14159265358979323846;
        const double k0 = config.wavelength_um > 0.0 ? (2.0 * kPi / config.wavelength_um)
                                                     : 1.0;
        const ArticleLocalAssemblyOptions local_options =
            make_default_article_local_assembly_options(k0);

        GlobalAssemblyResult global_assembly;
        std::ostringstream material_profile_summary;

        if (config.material_model == "homogeneous_isotropic_constant") {
            global_assembly = assemble_global_homogeneous_isotropic_system(
                mesh, config.refractive_index, local_options);
            material_profile_summary
                << "material_model: homogeneous_isotropic_constant\n"
                << "refractive_index: " << format_number(config.refractive_index) << "\n"
                << "refractive_index_squared: "
                << format_number(config.refractive_index * config.refractive_index) << "\n";
        } else if (config.material_model == "planar_diffuse_isotropic_exponential") {
            const PlanarDiffuseIsotropicProfile profile{
                config.background_index,
                config.delta_index,
                config.diffusion_depth,
            };
            global_assembly = assemble_global_planar_diffuse_isotropic_system(
                mesh, profile, local_options);
            material_profile_summary
                << "material_model: planar_diffuse_isotropic_exponential\n"
                << "background_index: " << format_number(profile.background_index) << "\n"
                << "delta_index: " << format_number(profile.delta_index) << "\n"
                << "diffusion_depth: " << format_number(profile.diffusion_depth) << "\n"
                << "profile_formula: n(y) = n_background + delta_n * exp(-|y|/b)\n";
        } else {
            throw std::runtime_error("Unsupported material.model at runtime: " +
                                     config.material_model);
        }

        const ArticleLocalMaterialCoefficients local_material =
            make_element_material_from_global_fields(
                first_element, global_assembly.material_fields);
        const ArticleLocalMatrices article_local =
            assemble_article_local_matrices(first_element, local_material, local_options);
        const bool constant_reduction_available =
            supports_constant_coefficient_article_reduction(local_material);
        const ArticleLocalMatrices article_local_reference =
            constant_reduction_available
                ? assemble_article_local_matrices_constant_reduction(
                      first_element, local_material, local_options)
                : ArticleLocalMatrices{};

        const GeneralizedEigenSolution eigen_solution =
            solve_generalized_eigenproblem_dense(
                global_assembly.matrices.F_reduced,
                global_assembly.matrices.M_reduced,
                k0,
                static_cast<std::size_t>(config.requested_modes));

        const std::filesystem::path output_dir =
            std::filesystem::absolute(options.output_dir).lexically_normal();
        const std::string run_label = determine_run_label(options, output_dir);
        const std::filesystem::path inputs_dir = output_dir / "inputs";
        const std::filesystem::path logs_dir = output_dir / "logs";
        const std::filesystem::path meta_dir = output_dir / "meta";
        const std::filesystem::path results_dir = output_dir / "results";

        std::filesystem::create_directories(inputs_dir);
        std::filesystem::create_directories(logs_dir);
        std::filesystem::create_directories(meta_dir);
        std::filesystem::create_directories(results_dir);

        std::filesystem::copy_file(
            case_file,
            inputs_dir / "case_snapshot.yaml",
            std::filesystem::copy_options::overwrite_existing);
        std::filesystem::copy_file(
            mesh_file,
            inputs_dir / "mesh_snapshot.mesh",
            std::filesystem::copy_options::overwrite_existing);

        std::ostringstream run_summary;
        run_summary << "status: global_dense_material_cases_ready\n";
        run_summary << "partial_scope_warning: This stage assembles and solves the "
                       "homogeneous isotropic constant case and the first planar diffuse "
                       "isotropic variable-coefficient case.\n";
        run_summary << "schema_version: " << config.schema_version << "\n";
        run_summary << "case_id: " << config.case_id << "\n";
        run_summary << "description: " << config.description << "\n";
        run_summary << "case_file_resolved: " << case_file.string() << "\n";
        run_summary << "case_directory_resolved: " << case_file.parent_path().string()
                    << "\n";
        run_summary << "mesh_file_input: " << config.mesh_file << "\n";
        run_summary << "mesh_file_resolved: " << mesh_file.string() << "\n";
        run_summary << "mesh_exists_on_disk: " << bool_to_text(mesh_exists_on_disk)
                    << "\n";
        run_summary << "output_directory_resolved: " << output_dir.string() << "\n";
        run_summary << "run_label: " << run_label << "\n";
        run_summary << "output_tag: " << config.output_tag << "\n";
        run_summary << "material_model: " << config.material_model << "\n";
        if (config.material_model == "homogeneous_isotropic_constant") {
            run_summary << "refractive_index: " << format_number(config.refractive_index)
                        << "\n";
        } else {
            run_summary << "background_index: " << format_number(config.background_index)
                        << "\n";
            run_summary << "delta_index: " << format_number(config.delta_index) << "\n";
            run_summary << "diffusion_depth: " << format_number(config.diffusion_depth)
                        << "\n";
        }
        run_summary << "boundary_condition: " << config.boundary_condition << "\n";
        run_summary << "requested_modes: " << config.requested_modes << "\n";
        run_summary << "wavelength_um: " << format_number(config.wavelength_um) << "\n";
        run_summary << "k0_used: " << format_number(k0) << "\n";
        run_summary << "k0_b_used: "
                    << format_number(k0 * std::max(config.diffusion_depth, 0.0)) << "\n";
        run_summary << "mesh_format: " << mesh.format << "\n";
        run_summary << "mesh_dimension: " << mesh.dimension << "\n";
        run_summary << "mesh_node_count: " << mesh.nodes.size() << "\n";
        run_summary << "mesh_triangle_count: " << mesh.triangles.size() << "\n";
        run_summary << "local_assembly_available: yes\n";
        run_summary << "global_assembly_available: yes\n";
        run_summary << "eigensolver_available: yes\n";
        run_summary << "local_formulation_model: " << local_material.model_label << "\n";
        append_quadrature_rule_summary(run_summary, local_options.quadrature_rule);
        run_summary << "first_element_id: " << first_element.element_id << "\n";
        run_summary << "first_element_global_node_ids: ["
                    << first_element.global_node_ids[0] << ", "
                    << first_element.global_node_ids[1] << ", "
                    << first_element.global_node_ids[2] << "]\n";
        run_summary << "first_element_area: "
                    << format_number(first_element.coefficients.area) << "\n";
        run_summary << "first_element_orientation: "
                    << to_string(first_element.orientation) << "\n";
        run_summary << "constant_reduction_available: "
                    << bool_to_text(constant_reduction_available) << "\n";
        if (constant_reduction_available) {
            run_summary << "constant_reduction_max_diff_M_local: "
                        << format_number(max_abs_matrix_difference(
                               article_local.M_local, article_local_reference.M_local))
                        << "\n";
            run_summary << "constant_reduction_max_diff_F_local: "
                        << format_number(max_abs_matrix_difference(
                               article_local.F_local, article_local_reference.F_local))
                        << "\n";
        }
        run_summary << "boundary_node_ids: "
                    << format_generic_vector(
                           global_assembly.boundary_condition.constrained_node_ids)
                    << "\n";
        run_summary << "free_node_ids: "
                    << format_generic_vector(global_assembly.boundary_condition.free_node_ids)
                    << "\n";
        run_summary << "constrained_dof_count: "
                    << global_assembly.boundary_condition.constrained_dof_indices.size()
                    << "\n";
        run_summary << "free_dof_count: "
                    << global_assembly.boundary_condition.free_dof_indices.size() << "\n";
        run_summary << "nx2_node_range: "
                    << format_map_value_range(
                           global_assembly.material_fields.nx2_by_node_id)
                    << "\n";
        run_summary << "nz2_node_range: "
                    << format_map_value_range(
                           global_assembly.material_fields.nz2_by_node_id)
                    << "\n";
        run_summary << "gz2_node_range: "
                    << format_map_value_range(
                           global_assembly.material_fields.gz2_by_node_id)
                    << "\n";
        run_summary << "M_local_flags: " << format_local_matrix_flags(article_local.M_local)
                    << "\n";
        run_summary << "F_local_flags: " << format_local_matrix_flags(article_local.F_local)
                    << "\n";
        run_summary << "M_full_flags: "
                    << format_dense_matrix_flags(global_assembly.matrices.M_full) << "\n";
        run_summary << "F_full_flags: "
                    << format_dense_matrix_flags(global_assembly.matrices.F_full) << "\n";
        run_summary << "M_reduced_flags: "
                    << format_dense_matrix_flags(global_assembly.matrices.M_reduced)
                    << "\n";
        run_summary << "F_reduced_flags: "
                    << format_dense_matrix_flags(global_assembly.matrices.F_reduced)
                    << "\n";
        run_summary << "eigensolver_label: " << eigen_solution.solver_label << "\n";
        run_summary << "transformed_matrix_is_symmetric: "
                    << bool_to_text(eigen_solution.transformed_matrix_is_symmetric)
                    << "\n";
        run_summary << "eigenpair_count: " << eigen_solution.eigenpairs.size() << "\n";
        if (!eigen_solution.eigenpairs.empty()) {
            run_summary << "leading_eigenvalue_n_eff_squared: "
                        << format_number(eigen_solution.eigenpairs.front().eigenvalue)
                        << "\n";
            if (eigen_solution.eigenpairs.front().has_neff) {
                run_summary << "leading_n_eff: "
                            << format_number(eigen_solution.eigenpairs.front().n_eff)
                            << "\n";
            }
        }

        write_text_file(meta_dir / "run_summary.txt", run_summary.str());
        write_text_file(results_dir / "material_profile_summary.txt",
                        material_profile_summary.str());

        write_text_file(
            results_dir / "geometry_summary.txt",
            "first_element_id: " + std::to_string(first_element.element_id) + "\n"
            "signed_area: " + format_number(first_element.coefficients.signed_area) + "\n"
            "area: " + format_number(first_element.coefficients.area) + "\n"
            "orientation: " + std::string(to_string(first_element.orientation)) + "\n"
            "jacobian: " + format_matrix2x2(first_element.jacobian.values) + "\n"
            "inverse_jacobian: " + format_matrix2x2(first_element.inverse_jacobian) +
                "\n"
            "b_coefficients: " + format_vector3(first_element.coefficients.b) + "\n"
            "c_coefficients: " + format_vector3(first_element.coefficients.c) + "\n"
            "grad_N1: (" + format_number(first_element.global_shape_gradients[0][0]) +
                ", " + format_number(first_element.global_shape_gradients[0][1]) + ")\n"
            "grad_N2: (" + format_number(first_element.global_shape_gradients[1][0]) +
                ", " + format_number(first_element.global_shape_gradients[1][1]) + ")\n"
            "grad_N3: (" + format_number(first_element.global_shape_gradients[2][0]) +
                ", " + format_number(first_element.global_shape_gradients[2][1]) + ")\n");

        write_text_file(
            results_dir / "local_assembly_audit.txt",
            [&]() {
                std::ostringstream audit;
                audit << "assembly_mode: article_local_term_decomposition\n";
                audit << "integration_mode: numerical_quadrature_on_reference_triangle\n";
                audit << "material_model: " << local_material.model_label << "\n";
                audit << "note: This audit stays at the element level so that the "
                         "global assembly can be traced back to one reusable P1 block.\n";
                audit << "integration_note: The local matrices are evaluated with "
                         "reference-triangle quadrature rather than the article's "
                         "analytic integration tables.\n";
                if (constant_reduction_available) {
                    audit << "reduction_note: In this element, F4 remains zero and the "
                             "quadrature result is compared against the closed-form constant "
                             "reduction.\n";
                } else {
                    audit << "transition_note: This element inherits nodally varying "
                             "isotropic coefficients from the global profile, so the local "
                             "assembly uses the general quadrature path without the constant "
                             "reduction shortcut.\n";
                }
                append_quadrature_rule_summary(audit, local_options.quadrature_rule);
                append_quadrature_point_listing(audit, local_options.quadrature_rule);
                audit << "delta_x: " << bool_to_text(local_material.delta_x) << "\n";
                audit << "delta_z: " << bool_to_text(local_material.delta_z) << "\n";
                audit << "homogeneous: " << bool_to_text(local_material.homogeneous)
                      << "\n";
                audit << "isotropic: " << bool_to_text(local_material.isotropic) << "\n";
                append_scalar_field_summary(audit, "nx2", local_material.nx2);
                append_scalar_field_summary(audit, "nz2", local_material.nz2);
                append_scalar_field_summary(audit, "gz2", local_material.gz2);
                audit << "M_local:\n" << format_local_matrix(article_local.M_local) << "\n";
                audit << "F1_local:\n" << format_local_matrix(article_local.F1_local)
                      << "\n";
                audit << "F2_local:\n" << format_local_matrix(article_local.F2_local)
                      << "\n";
                audit << "F3_local:\n" << format_local_matrix(article_local.F3_local)
                      << "\n";
                audit << "F4_local:\n" << format_local_matrix(article_local.F4_local)
                      << "\n";
                audit << "F_local:\n" << format_local_matrix(article_local.F_local) << "\n";
                audit << "mass_integral:\n"
                      << format_local_matrix(article_local.mass_integral) << "\n";
                audit << "stiffness_x:\n"
                      << format_local_matrix(article_local.stiffness_x) << "\n";
                audit << "stiffness_y:\n"
                      << format_local_matrix(article_local.stiffness_y) << "\n";
                if (constant_reduction_available) {
                    audit << "constant_reduction_reference_M_local:\n"
                          << format_local_matrix(article_local_reference.M_local) << "\n";
                    audit << "constant_reduction_reference_F_local:\n"
                          << format_local_matrix(article_local_reference.F_local) << "\n";
                }
                return audit.str();
            }());

        write_text_file(
            results_dir / "global_assembly_summary.txt",
            [&]() {
                std::ostringstream summary;
                summary << "assembly_mode: " << config.material_model << "\n";
                summary << "equation_note: The global matrices satisfy [F]{E} = "
                           "n_eff^2 [M]{E} after assembling the element matrices from the "
                           "article-oriented local formulation.\n";
                summary << "transition_note: The homogeneous constant case and the planar "
                           "diffuse isotropic case share the same global assembly path; only "
                           "the nodal material fields change before element assembly.\n";
                summary << "node_count: " << global_assembly.node_count << "\n";
                summary << "element_count: " << global_assembly.element_count << "\n";
                summary << "full_matrix_dimension: "
                        << global_assembly.matrices.M_full.size() << "\n";
                summary << "reduced_matrix_dimension: "
                        << global_assembly.matrices.M_reduced.size() << "\n";
                summary << "boundary_condition: "
                        << global_assembly.boundary_condition.label << "\n";
                summary << "boundary_node_ids: "
                        << format_generic_vector(
                               global_assembly.boundary_condition.constrained_node_ids)
                        << "\n";
                summary << "free_node_ids: "
                        << format_generic_vector(
                               global_assembly.boundary_condition.free_node_ids)
                        << "\n";
                summary << "M_full_flags: "
                        << format_dense_matrix_flags(global_assembly.matrices.M_full)
                        << "\n";
                summary << "F_full_flags: "
                        << format_dense_matrix_flags(global_assembly.matrices.F_full)
                        << "\n";
                summary << "M_reduced_flags: "
                        << format_dense_matrix_flags(global_assembly.matrices.M_reduced)
                        << "\n";
                summary << "F_reduced_flags: "
                        << format_dense_matrix_flags(global_assembly.matrices.F_reduced)
                        << "\n";
                summary << "transformed_eigen_matrix_flags: "
                        << format_dense_matrix_flags(eigen_solution.transformed_matrix)
                        << "\n";
                summary << "eigensolver_label: " << eigen_solution.solver_label << "\n";
                summary << "transformed_matrix_is_symmetric: "
                        << bool_to_text(eigen_solution.transformed_matrix_is_symmetric)
                        << "\n";
                summary << "nx2_node_range: "
                        << format_map_value_range(
                               global_assembly.material_fields.nx2_by_node_id)
                        << "\n";
                summary << "nz2_node_range: "
                        << format_map_value_range(
                               global_assembly.material_fields.nz2_by_node_id)
                        << "\n";
                summary << "requested_modes: " << config.requested_modes << "\n";
                summary << "computed_modes: " << eigen_solution.eigenpairs.size() << "\n";
                summary << "k0_used: " << format_number(k0) << "\n";
                summary << "k0_b_used: "
                        << format_number(k0 * std::max(config.diffusion_depth, 0.0))
                        << "\n";
                for (std::size_t i = 0; i < eigen_solution.eigenpairs.size(); ++i) {
                    const GeneralizedEigenpair& eigenpair = eigen_solution.eigenpairs[i];
                    summary << "mode_" << (i + 1) << "_eigenvalue_n_eff_squared: "
                            << format_number(eigenpair.eigenvalue) << "\n";
                    summary << "mode_" << (i + 1)
                            << "_label: " << mode_index_to_label(i + 1) << "\n";
                    if (eigenpair.has_neff) {
                        summary << "mode_" << (i + 1) << "_n_eff: "
                                << format_number(eigenpair.n_eff) << "\n";
                        summary << "mode_" << (i + 1) << "_beta: "
                                << format_number(eigenpair.beta) << "\n";
                    }
                }
                return summary.str();
            }());

        write_text_file(results_dir / "global_M_full.csv",
                        format_dense_matrix_csv(global_assembly.matrices.M_full));
        write_text_file(results_dir / "global_F_full.csv",
                        format_dense_matrix_csv(global_assembly.matrices.F_full));
        write_text_file(results_dir / "global_M_reduced.csv",
                        format_dense_matrix_csv(global_assembly.matrices.M_reduced));
        write_text_file(results_dir / "global_F_reduced.csv",
                        format_dense_matrix_csv(global_assembly.matrices.F_reduced));
        write_text_file(results_dir / "transformed_eigen_matrix.csv",
                        format_dense_matrix_csv(eigen_solution.transformed_matrix));
        write_text_file(results_dir / "nodal_material_fields.csv",
                        build_nodal_material_fields_csv(
                            mesh, global_assembly.material_fields));
        write_text_file(results_dir / "eigenvalues.csv",
                        build_eigenvalues_csv(eigen_solution));
        write_text_file(results_dir / "neff.csv", build_neff_csv(eigen_solution));
        write_text_file(results_dir / "dispersion_curve_points.csv",
                        build_dispersion_curve_points_csv(
                            eigen_solution, config.diffusion_depth, k0));
        write_text_file(results_dir / "modal_summary.csv",
                        build_neff_csv(eigen_solution));

        write_text_file(
            results_dir / "README.txt",
            "This run validates local quadrature-based element matrices, global assembly,\n"
            "Dirichlet elimination on boundary nodes, and a dense generalized eigen solve\n"
            "for either the homogeneous isotropic constant case or the planar diffuse isotropic case.\n");

        std::ostringstream execution_log;
        execution_log << "waveguide_solver execution log\n";
        execution_log << "case_id=" << config.case_id << "\n";
        execution_log << "mesh_file=" << mesh_file.string() << "\n";
        execution_log << "node_count=" << mesh.nodes.size() << "\n";
        execution_log << "element_count=" << mesh.triangles.size() << "\n";
        execution_log << "boundary_condition="
                      << global_assembly.boundary_condition.label << "\n";
        execution_log << "material_model=" << config.material_model << "\n";
        execution_log << "eigensolver_label=" << eigen_solution.solver_label << "\n";
        execution_log << "constrained_nodes="
                      << format_generic_vector(
                             global_assembly.boundary_condition.constrained_node_ids)
                      << "\n";
        execution_log << "free_nodes="
                      << format_generic_vector(global_assembly.boundary_condition.free_node_ids)
                      << "\n";
        execution_log << "computed_modes=" << eigen_solution.eigenpairs.size() << "\n";
        if (!eigen_solution.eigenpairs.empty()) {
            execution_log << "leading_eigenvalue_n_eff_squared="
                          << format_number(eigen_solution.eigenpairs.front().eigenvalue)
                          << "\n";
            if (eigen_solution.eigenpairs.front().has_neff) {
                execution_log << "leading_n_eff="
                              << format_number(eigen_solution.eigenpairs.front().n_eff)
                              << "\n";
            }
        }
        write_text_file(logs_dir / "solver_execution.log", execution_log.str());
        write_text_file(logs_dir / "solver.stdout.log", execution_log.str());

        std::cout << "waveguide_solver: dense global solve completed\n";
        std::cout << "  case id       : " << config.case_id << "\n";
        std::cout << "  run label     : " << run_label << "\n";
        std::cout << "  mesh file     : " << mesh_file.string() << "\n";
        std::cout << "  node count    : " << mesh.nodes.size() << "\n";
        std::cout << "  element count : " << mesh.triangles.size() << "\n";
        std::cout << "  free dofs     : "
                  << global_assembly.boundary_condition.free_dof_indices.size() << "\n";
        if (!eigen_solution.eigenpairs.empty()) {
            std::cout << "  lead n_eff    : ";
            if (eigen_solution.eigenpairs.front().has_neff) {
                std::cout << format_number(eigen_solution.eigenpairs.front().n_eff)
                          << "\n";
            } else {
                std::cout << "not_applicable\n";
            }
        }
        std::cout << "  material      : " << config.material_model << "\n";
        std::cout << "  output folder : " << output_dir.string() << "\n";
        std::cout << "  note          : dense global solver active for constant and planar diffuse isotropic cases\n";

        return 0;
    } catch (const std::exception& error) {
        std::cerr << "waveguide_solver error: " << error.what() << "\n";
        std::cerr << "Use --help for usage information.\n";
        return 1;
    }
}

}  // namespace waveguide
