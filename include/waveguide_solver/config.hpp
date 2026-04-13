#pragma once

#include <filesystem>
#include <map>
#include <string>

namespace waveguide {

struct CaseConfig {
    std::string case_id = "unnamed_case";
    std::string description = "No description provided.";
    std::string mesh_file;
    int requested_modes = 1;
    double wavelength_um = 0.0;
    std::string output_tag = "default";
    std::map<std::string, std::string> raw_entries;
};

CaseConfig load_case_config(const std::filesystem::path& case_file);

}  // namespace waveguide
