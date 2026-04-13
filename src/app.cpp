#include "waveguide_solver/app.hpp"
#include "waveguide_solver/config.hpp"
#include "waveguide_solver/element.hpp"
#include "waveguide_solver/local_assembly.hpp"
#include "waveguide_solver/mesh.hpp"

#include <array>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>

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

std::string format_matrix_flags(const LocalMatrix3& matrix) {
    std::ostringstream stream;
    stream << "symmetric=" << bool_to_text(is_symmetric(matrix))
           << ", zero=" << bool_to_text(is_zero_matrix(matrix))
           << ", trace=" << format_number(matrix_trace(matrix));
    return stream.str();
}

std::string determine_run_label(const CliOptions& options,
                                const std::filesystem::path& output_dir) {
    if (!options.run_label.empty()) {
        return options.run_label;
    }
    return output_dir.filename().string();
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
        const ArticleLocalMaterialCoefficients local_material =
            make_homogeneous_isotropic_local_material(1.0);
        const ArticleLocalAssemblyOptions local_options{k0};
        const ArticleLocalMatrices article_local =
            assemble_article_local_matrices(first_element, local_material, local_options);

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

        write_text_file(
            meta_dir / "run_summary.txt",
            "status: stub_article_local_terms_ready\n"
            "stub_mode: yes\n"
            "stub_warning: Global FEM assembly and the full generalized eigenproblem "
            "are not implemented yet.\n"
            "schema_version: " + std::to_string(config.schema_version) + "\n"
            "case_id: " + config.case_id + "\n"
            "description: " + config.description + "\n"
            "case_file_resolved: " + case_file.string() + "\n"
            "case_directory_resolved: " + case_file.parent_path().string() + "\n"
            "mesh_file_input: " + config.mesh_file + "\n"
            "mesh_file_resolved: " + mesh_file.string() + "\n"
            "mesh_exists_on_disk: " + bool_to_text(mesh_exists_on_disk) + "\n"
            "output_directory_resolved: " + output_dir.string() + "\n"
            "run_label: " + run_label + "\n"
            "output_tag: " + config.output_tag + "\n"
            "requested_modes: " + std::to_string(config.requested_modes) + "\n"
            "wavelength_um: " + format_number(config.wavelength_um) + "\n"
            "mesh_format: " + mesh.format + "\n"
            "mesh_dimension: " + std::to_string(mesh.dimension) + "\n"
            "mesh_node_count: " + std::to_string(mesh.nodes.size()) + "\n"
            "mesh_triangle_count: " + std::to_string(mesh.triangles.size()) + "\n"
            "local_assembly_available: yes\n"
            "local_formulation_model: " + local_material.model_label + "\n"
            "k0_used: " + format_number(k0) + "\n"
            "first_element_id: " + std::to_string(first_element.element_id) + "\n"
            "first_element_global_node_ids: [" +
                std::to_string(first_element.global_node_ids[0]) + ", " +
                std::to_string(first_element.global_node_ids[1]) + ", " +
                std::to_string(first_element.global_node_ids[2]) + "]\n"
            "first_element_jacobian_determinant: " +
                format_number(first_element.jacobian_determinant) + "\n"
            "first_element_signed_area: " +
                format_number(first_element.coefficients.signed_area) + "\n"
            "first_element_area: " + format_number(first_element.coefficients.area) + "\n"
            "first_element_orientation: " +
                std::string(to_string(first_element.orientation)) + "\n"
            "M_local_flags: " + format_matrix_flags(article_local.M_local) + "\n"
            "F1_local_flags: " + format_matrix_flags(article_local.F1_local) + "\n"
            "F2_local_flags: " + format_matrix_flags(article_local.F2_local) + "\n"
            "F3_local_flags: " + format_matrix_flags(article_local.F3_local) + "\n"
            "F4_local_flags: " + format_matrix_flags(article_local.F4_local) + "\n"
            "F_local_flags: " + format_matrix_flags(article_local.F_local) + "\n");

        write_text_file(
            results_dir / "geometry_summary.txt",
            "first_element_id: " + std::to_string(first_element.element_id) + "\n"
            "signed_area: " + format_number(first_element.coefficients.signed_area) + "\n"
            "area: " + format_number(first_element.coefficients.area) + "\n"
            "orientation: " + std::string(to_string(first_element.orientation)) +
                "\n"
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
            "assembly_mode: article_local_term_decomposition\n"
            "material_model: " + local_material.model_label + "\n"
            "note: This audit stays at the element level and does not assemble a global system.\n"
            "reduction_note: constant homogeneous isotropic coefficients imply zero material gradients,\n"
            "so derivative-driven contributions in F2/F3 vanish and F4 is identically zero.\n"
            "M_local:\n" + format_local_matrix(article_local.M_local) + "\n"
            "F1_local:\n" + format_local_matrix(article_local.F1_local) + "\n"
            "F2_local:\n" + format_local_matrix(article_local.F2_local) + "\n"
            "F3_local:\n" + format_local_matrix(article_local.F3_local) + "\n"
            "F4_local:\n" + format_local_matrix(article_local.F4_local) + "\n"
            "F_local:\n" + format_local_matrix(article_local.F_local) + "\n"
            "mass_integral:\n" + format_local_matrix(article_local.mass_integral) + "\n"
            "stiffness_x:\n" + format_local_matrix(article_local.stiffness_x) + "\n"
            "stiffness_y:\n" + format_local_matrix(article_local.stiffness_y) + "\n");

        write_text_file(
            results_dir / "modal_summary.csv",
            "mode_index,status,notes\n"
            "1,pending_implementation,Stub mode: local element assembly only\n");

        write_text_file(
            results_dir / "README.txt",
            "This run validates the case contract, mesh parsing, triangle geometry,\n"
            "and article-oriented local term matrices. Global FEM assembly is not implemented yet.\n");

        std::cout << "waveguide_solver: article-local-term stub run completed\n";
        std::cout << "  case id       : " << config.case_id << "\n";
        std::cout << "  run label     : " << run_label << "\n";
        std::cout << "  mesh file     : " << mesh_file.string() << "\n";
        std::cout << "  element area  : " << format_number(first_element.coefficients.area)
                  << "\n";
        std::cout << "  orientation   : " << to_string(first_element.orientation)
                  << "\n";
        std::cout << "  output folder : " << output_dir.string() << "\n";
        std::cout << "  note          : global FEM assembly not implemented yet\n";

        return 0;
    } catch (const std::exception& error) {
        std::cerr << "waveguide_solver error: " << error.what() << "\n";
        std::cerr << "Use --help for usage information.\n";
        return 1;
    }
}

}  // namespace waveguide
