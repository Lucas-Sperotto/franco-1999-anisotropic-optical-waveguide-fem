#include "waveguide_solver/config.hpp"

#include <cctype>
#include <fstream>
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

        config.raw_entries[full_key] = value;
    }

    config.case_id =
        get_optional_entry(config, "case.id", config.case_id);
    config.description =
        get_optional_entry(config, "case.description", config.description);
    config.mesh_file = require_entry(config, "mesh.file");
    config.output_tag =
        get_optional_entry(config, "output.tag", config.case_id);

    const auto requested_modes =
        get_optional_entry(config, "solver.requested_modes", "1");
    config.requested_modes = std::stoi(requested_modes);

    const auto wavelength =
        get_optional_entry(config, "solver.wavelength_um", "0.0");
    config.wavelength_um = std::stod(wavelength);

    return config;
}

}  // namespace waveguide
