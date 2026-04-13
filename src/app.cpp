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
        const HomogeneousIsotropicLocalMatrices first_element_matrices =
            assemble_basic_homogeneous_isotropic_local_matrices(first_element);

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
            "status: stub_local_element_ready\n"
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
            "first_element_mass_trace: " +
                format_number(matrix_trace(first_element_matrices.consistent_mass)) + "\n"
            "first_element_stiffness_trace: " +
                format_number(matrix_trace(first_element_matrices.laplacian_stiffness)) +
                "\n"
            "first_element_mass_symmetric: " +
                bool_to_text(is_symmetric(first_element_matrices.consistent_mass)) + "\n"
            "first_element_stiffness_symmetric: " +
                bool_to_text(is_symmetric(first_element_matrices.laplacian_stiffness)) +
                "\n");

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
            "assembly_mode: homogeneous_isotropic_unit_coefficients\n"
            "note: These are reusable local matrices for the element level only.\n"
            "consistent_mass_matrix:\n" +
                format_local_matrix(first_element_matrices.consistent_mass) + "\n"
            "laplacian_stiffness_matrix:\n" +
                format_local_matrix(first_element_matrices.laplacian_stiffness) + "\n");

        write_text_file(
            results_dir / "modal_summary.csv",
            "mode_index,status,notes\n"
            "1,pending_implementation,Stub mode: local element assembly only\n");

        write_text_file(
            results_dir / "README.txt",
            "This run validates the case contract, mesh parsing, triangle geometry,\n"
            "and basic local element matrices. Global FEM assembly is not implemented yet.\n");

        std::cout << "waveguide_solver: local-element stub run completed\n";
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
