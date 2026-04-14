#include "waveguide_solver/config.hpp"

#include <cctype>
#include <fstream>
#include <map>
#include <sstream>
#include <stdexcept>

namespace waveguide {
namespace {

std::string trim_copy(const std::string& value) {
    std::size_t begin = 0;
    while (begin < value.size() &&
           std::isspace(static_cast<unsigned char>(value[begin])) != 0) {
        ++begin;
    }

    std::size_t end = value.size();
    while (end > begin &&
           std::isspace(static_cast<unsigned char>(value[end - 1])) != 0) {
        --end;
    }

    return value.substr(begin, end - begin);
}

std::string strip_inline_comment(const std::string& line) {
    const auto comment_pos = line.find('#');
    if (comment_pos == std::string::npos) {
        return line;
    }
    return line.substr(0, comment_pos);
}

std::string unquote(std::string value) {
    if (value.size() >= 2) {
        const char first = value.front();
        const char last = value.back();
        if ((first == '"' && last == '"') || (first == '\'' && last == '\'')) {
            return value.substr(1, value.size() - 2);
        }
    }
    return value;
}

std::string require_entry(const CaseConfig& config, const std::string& key) {
    const auto it = config.raw_entries.find(key);
    if (it == config.raw_entries.end() || it->second.empty()) {
        throw std::runtime_error("Missing required case entry: " + key);
    }
    return it->second;
}

std::string get_optional_entry(const CaseConfig& config,
                               const std::string& key,
                               const std::string& fallback) {
    const auto it = config.raw_entries.find(key);
    if (it == config.raw_entries.end() || it->second.empty()) {
        return fallback;
    }
    return it->second;
}

int parse_required_int(const CaseConfig& config, const std::string& key) {
    const std::string value = require_entry(config, key);
    try {
        return std::stoi(value);
    } catch (const std::exception&) {
        throw std::runtime_error("Expected integer value for case entry: " + key);
    }
}

int parse_required_positive_int(const CaseConfig& config, const std::string& key) {
    const int value = parse_required_int(config, key);
    if (value <= 0) {
        throw std::runtime_error("Expected positive integer value for case entry: " +
                                 key);
    }
    return value;
}

double parse_required_double(const CaseConfig& config, const std::string& key) {
    const std::string value = require_entry(config, key);
    try {
        return std::stod(value);
    } catch (const std::invalid_argument&) {
        throw std::runtime_error("Expected floating-point value for case entry: " +
                                 key);
    } catch (const std::out_of_range&) {
        throw std::runtime_error("Floating-point value out of range for case entry: " +
                                 key);
    }
}

double parse_required_nonnegative_double(const CaseConfig& config,
                                         const std::string& key) {
    const std::string value = require_entry(config, key);
    try {
        const double parsed = std::stod(value);
        if (parsed < 0.0) {
            throw std::runtime_error("Expected nonnegative value for case entry: " +
                                     key);
        }
        return parsed;
    } catch (const std::invalid_argument&) {
        throw std::runtime_error("Expected floating-point value for case entry: " +
                                 key);
    } catch (const std::out_of_range&) {
        throw std::runtime_error("Floating-point value out of range for case entry: " +
                                 key);
    }
}

double parse_required_positive_double(const CaseConfig& config,
                                      const std::string& key) {
    const std::string value = require_entry(config, key);
    try {
        const double parsed = std::stod(value);
        if (parsed <= 0.0) {
            throw std::runtime_error("Expected positive value for case entry: " + key);
        }
        return parsed;
    } catch (const std::invalid_argument&) {
        throw std::runtime_error("Expected floating-point value for case entry: " +
                                 key);
    } catch (const std::out_of_range&) {
        throw std::runtime_error("Floating-point value out of range for case entry: " +
                                 key);
    }
}

double parse_optional_positive_double(const CaseConfig& config,
                                      const std::string& key,
                                      double fallback) {
    const auto it = config.raw_entries.find(key);
    if (it == config.raw_entries.end() || it->second.empty()) {
        return fallback;
    }

    try {
        const double parsed = std::stod(it->second);
        if (parsed <= 0.0) {
            throw std::runtime_error("Expected positive value for case entry: " + key);
        }
        return parsed;
    } catch (const std::invalid_argument&) {
        throw std::runtime_error("Expected floating-point value for case entry: " +
                                 key);
    } catch (const std::out_of_range&) {
        throw std::runtime_error("Floating-point value out of range for case entry: " +
                                 key);
    }
}

bool parse_optional_bool(const CaseConfig& config,
                         const std::string& key,
                         bool fallback) {
    const auto it = config.raw_entries.find(key);
    if (it == config.raw_entries.end() || it->second.empty()) {
        return fallback;
    }

    const std::string value = trim_copy(it->second);
    if (value == "true" || value == "yes" || value == "on" || value == "1") {
        return true;
    }

    if (value == "false" || value == "no" || value == "off" || value == "0") {
        return false;
    }

    throw std::runtime_error("Expected boolean value for case entry: " + key);
}

void validate_schema_version(int schema_version) {
    constexpr int kSupportedSchemaVersion = 1;
    if (schema_version != kSupportedSchemaVersion) {
        throw std::runtime_error("Unsupported case schema_version: " +
                                 std::to_string(schema_version) +
                                 ". Supported version: " +
                                 std::to_string(kSupportedSchemaVersion));
    }
}

void validate_material_model(const std::string& material_model) {
    if (material_model != "homogeneous_isotropic_constant" &&
        material_model != "planar_diffuse_isotropic_exponential" &&
        material_model != "planar_diffuse_isotropic_surface_exponential" &&
        material_model != "rectangular_channel_step_index") {
        throw std::runtime_error(
            "Unsupported material.model '" + material_model +
            "'. Supported models: homogeneous_isotropic_constant, "
            "planar_diffuse_isotropic_exponential, "
            "planar_diffuse_isotropic_surface_exponential, "
            "rectangular_channel_step_index");
    }
}

void validate_boundary_condition(const std::string& boundary_condition) {
    if (boundary_condition != "dirichlet_zero_on_boundary" &&
        boundary_condition != "dirichlet_zero_on_boundary_nodes" &&
        boundary_condition != "dirichlet_zero_on_y_extrema") {
        throw std::runtime_error(
            "Unsupported boundary.condition '" + boundary_condition +
            "'. Supported boundary conditions: dirichlet_zero_on_boundary, "
            "dirichlet_zero_on_boundary_nodes, dirichlet_zero_on_y_extrema");
    }
}

}  // namespace

CaseConfig load_case_config(const std::filesystem::path& case_file) {
    std::ifstream input(case_file);
    if (!input.is_open()) {
        throw std::runtime_error("Could not open case file: " + case_file.string());
    }

    CaseConfig config;
    std::string current_section;
    std::string line;
    std::size_t line_number = 0;

    while (std::getline(input, line)) {
        ++line_number;

        const std::string without_comment = strip_inline_comment(line);
        const std::string trimmed = trim_copy(without_comment);
        if (trimmed.empty()) {
            continue;
        }

        const auto first_non_space = without_comment.find_first_not_of(' ');
        const std::size_t indent =
            first_non_space == std::string::npos ? 0 : first_non_space;

        if (!trimmed.empty() && trimmed.back() == ':') {
            current_section = trim_copy(trimmed.substr(0, trimmed.size() - 1));
            continue;
        }

        const auto separator = trimmed.find(':');
        if (separator == std::string::npos) {
            std::ostringstream error;
            error << "Invalid YAML-like line at " << case_file.string() << ":"
                  << line_number << " -> " << trimmed;
            throw std::runtime_error(error.str());
        }

        const std::string key = trim_copy(trimmed.substr(0, separator));
        std::string value = trim_copy(trimmed.substr(separator + 1));
        value = unquote(value);

        std::string full_key = key;
        if (indent > 0 && !current_section.empty()) {
            full_key = current_section + "." + key;
        }

        const auto [it, inserted] = config.raw_entries.emplace(full_key, value);
        if (!inserted) {
            throw std::runtime_error("Duplicate case entry encountered: " + full_key);
        }
    }

    config.schema_version = parse_required_int(config, "schema_version");
    validate_schema_version(config.schema_version);

    config.case_id = require_entry(config, "case.id");
    config.description = require_entry(config, "case.description");
    config.mesh_file = require_entry(config, "mesh.file");
    config.material_model = require_entry(config, "material.model");
    validate_material_model(config.material_model);

    if (config.material_model == "homogeneous_isotropic_constant") {
        config.refractive_index =
            parse_required_positive_double(config, "material.refractive_index");
    } else if (config.material_model == "planar_diffuse_isotropic_exponential" ||
               config.material_model == "planar_diffuse_isotropic_surface_exponential") {
        config.background_index =
            parse_required_positive_double(config, "material.background_index");
        config.cover_index = parse_optional_positive_double(
            config, "material.cover_index", config.background_index);
        config.delta_index =
            parse_required_nonnegative_double(config, "material.delta_index");
        config.diffusion_depth =
            parse_required_positive_double(config, "material.diffusion_depth");
        config.linearized_permittivity =
            parse_optional_bool(config, "material.linearized_permittivity", false);
    } else if (config.material_model == "rectangular_channel_step_index") {
        config.cover_index =
            parse_required_positive_double(config, "material.cover_index");
        config.substrate_index =
            parse_required_positive_double(config, "material.substrate_index");
        config.core_index =
            parse_required_positive_double(config, "material.core_index");
        config.core_width =
            parse_required_positive_double(config, "material.core_width");
        config.core_height =
            parse_required_positive_double(config, "material.core_height");
        config.core_center_x =
            parse_required_double(config, "material.core_center_x");
        config.surface_y =
            parse_required_double(config, "material.surface_y");
    }

    config.boundary_condition =
        get_optional_entry(config, "boundary.condition",
                           "dirichlet_zero_on_boundary");
    validate_boundary_condition(config.boundary_condition);
    config.output_tag =
        get_optional_entry(config, "output.tag", config.case_id);
    config.requested_modes =
        parse_required_positive_int(config, "solver.requested_modes");
    config.wavelength_um =
        parse_required_nonnegative_double(config, "solver.wavelength_um");
    config.planar_x_invariant_reduction =
        parse_optional_bool(config, "solver.planar_x_invariant_reduction", false);

    return config;
}

}  // namespace waveguide
