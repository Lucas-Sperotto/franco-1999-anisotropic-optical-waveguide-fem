#pragma once

#include <filesystem>
#include <map>
#include <string>

namespace waveguide {

struct CaseConfig {
    int schema_version = 0;
    std::string case_id;
    std::string description;
    std::string mesh_file;
    int requested_modes = 1;
    double wavelength_um = 0.0;
    std::string output_tag;
    std::map<std::string, std::string> raw_entries;
};

CaseConfig load_case_config(const std::filesystem::path& case_file);

}  // namespace waveguide
