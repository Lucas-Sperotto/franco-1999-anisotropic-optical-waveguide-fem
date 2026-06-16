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
    std::string material_model;
    double refractive_index = 0.0;
    double background_index = 0.0;
    double cover_index = 0.0;
    double substrate_index = 0.0;
    double core_index = 0.0;
    double peak_index = 0.0;
    double delta_index = 0.0;
    double diffusion_depth = 0.0;
    bool linearized_permittivity = false;
    double core_width = 0.0;
    double core_height = 0.0;
    double core_center_x = 0.0;
    double surface_y = 0.0;
    double ordinary_index = 0.0;
    double extraordinary_substrate_index = 0.0;
    double ordinary_substrate_index = 0.0;
    double delta_extraordinary_index = 0.0;
    double peak_concentration = 0.0;
    double diffusion_width_x = 0.0;
    double diffusion_depth_y = 0.0;
    double extraordinary_surface_delta_index = 0.0;
    double ordinary_surface_delta_index = 0.0;
    double extraordinary_diffusion_width_x = 0.0;
    double extraordinary_diffusion_depth_y = 0.0;
    double ordinary_diffusion_width_x = 0.0;
    double ordinary_diffusion_depth_y = 0.0;
    double strip_width = 0.0;
    std::string boundary_condition;
    int requested_modes = 1;
    double wavelength_um = 0.0;
    bool planar_x_invariant_reduction = false;
    std::string output_tag;
    std::map<std::string, std::string> raw_entries;
};

CaseConfig load_case_config(const std::filesystem::path& case_file);

}  // namespace waveguide
