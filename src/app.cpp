#include "waveguide_solver/app.hpp"
#include "waveguide_solver/config.hpp"

#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>

namespace waveguide {
namespace {

struct CliOptions {
    std::filesystem::path case_file;
    std::filesystem::path output_dir;
    bool show_help = false;
};

void print_usage() {
    std::cout
        << "waveguide_solver\n"
        << "Uso:\n"
        << "  waveguide_solver --case <arquivo.yaml> --output <diretorio>\n"
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
        const bool mesh_exists = std::filesystem::exists(mesh_file);
        if (!mesh_exists) {
            throw std::runtime_error(
                "Referenced mesh file does not exist: " + mesh_file.string());
        }

        const std::filesystem::path output_dir =
            std::filesystem::absolute(options.output_dir).lexically_normal();
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

        write_text_file(
            meta_dir / "run_summary.txt",
            "status: infrastructure_stub\n"
            "case_id: " + config.case_id + "\n"
            "description: " + config.description + "\n"
            "case_file: " + case_file.string() + "\n"
            "mesh_file: " + mesh_file.string() + "\n"
            "mesh_exists: " + bool_to_text(mesh_exists) + "\n"
            "requested_modes: " + std::to_string(config.requested_modes) + "\n"
            "wavelength_um: " + std::to_string(config.wavelength_um) + "\n"
            "output_tag: " + config.output_tag + "\n"
            "note: numerical formulation not implemented yet\n");

        write_text_file(
            results_dir / "modal_summary.csv",
            "mode_index,status,notes\n"
            "1,pending_implementation,Infrastructure smoke run only\n");

        write_text_file(
            results_dir / "README.txt",
            "This run validates repository structure, case loading, path resolution,\n"
            "and output generation. No finite element formulation is implemented yet.\n");

        std::cout << "waveguide_solver: infrastructure smoke run completed\n";
        std::cout << "  case id       : " << config.case_id << "\n";
        std::cout << "  mesh file     : " << mesh_file.string() << "\n";
        std::cout << "  output folder : " << output_dir.string() << "\n";
        std::cout << "  note          : FEM formulation not implemented yet\n";

        return 0;
    } catch (const std::exception& error) {
        std::cerr << "waveguide_solver error: " << error.what() << "\n";
        std::cerr << "Use --help for usage information.\n";
        return 1;
    }
}

}  // namespace waveguide
