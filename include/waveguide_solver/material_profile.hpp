#pragma once

#include "waveguide_solver/material.hpp"
#include "waveguide_solver/mesh.hpp"

#include <map>
#include <string>

namespace waveguide {

struct GlobalNodalMaterialFields {
    std::map<int, double> nx2_by_node_id;
    std::map<int, double> nz2_by_node_id;
    std::map<int, double> gz2_by_node_id;
    bool delta_x = false;
    bool delta_z = false;
    bool homogeneous = false;
    bool isotropic = false;
    std::string model_label;
};

struct PlanarDiffuseIsotropicProfile {
    double background_index = 2.20;
    double cover_index = 2.20;
    double delta_index = 0.01;
    double diffusion_depth = 1.0;
    double surface_coordinate = 0.0;
    bool linearized_permittivity = false;
};

struct RectangularChannelStepIndexProfile {
    double cover_index = 1.0;
    double substrate_index = 1.43;
    double core_index = 1.50;
    double core_width = 2.0;
    double core_height = 1.0;
    double core_center_x = 0.0;
    double surface_y = 0.0;
};

double get_global_material_value(const std::map<int, double>& field_by_node_id,
                                 int node_id,
                                 const std::string& field_label);

double evaluate_planar_diffuse_isotropic_index(
    double y,
    const PlanarDiffuseIsotropicProfile& profile);

double evaluate_planar_surface_diffuse_isotropic_index(
    double y,
    const PlanarDiffuseIsotropicProfile& profile);

double evaluate_planar_diffuse_isotropic_index_squared(
    double y,
    const PlanarDiffuseIsotropicProfile& profile);

double evaluate_planar_surface_diffuse_isotropic_index_squared(
    double y,
    const PlanarDiffuseIsotropicProfile& profile);

GlobalNodalMaterialFields make_homogeneous_isotropic_global_material(
    const Mesh& mesh,
    double refractive_index);

GlobalNodalMaterialFields make_planar_diffuse_isotropic_global_material(
    const Mesh& mesh,
    const PlanarDiffuseIsotropicProfile& profile);

GlobalNodalMaterialFields make_planar_surface_diffuse_isotropic_global_material(
    const Mesh& mesh,
    const PlanarDiffuseIsotropicProfile& profile);

GlobalNodalMaterialFields make_rectangular_channel_step_index_global_material(
    const Mesh& mesh,
    const RectangularChannelStepIndexProfile& profile);

ArticleLocalMaterialCoefficients make_rectangular_channel_step_index_element_material(
    const LinearTriangleP1Element& element,
    const RectangularChannelStepIndexProfile& profile);

ArticleLocalMaterialCoefficients make_element_material_from_global_fields(
    const LinearTriangleP1Element& element,
    const GlobalNodalMaterialFields& global_fields);

}  // namespace waveguide
