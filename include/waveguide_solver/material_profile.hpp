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

struct ChannelDiffusedIsotropicProfile {
    double cover_index = 1.0;
    double background_index = 1.44;
    double peak_index = 1.50;
    double core_width = 2.0;
    double core_height = 1.0;
    double core_center_x = 0.0;
    double surface_y = 0.0;
};

struct ChannelGaussianGaussianProfile {
    double cover_index = 1.0;
    double background_index = 1.449137674618944;
    double peak_index = 1.521594558349891;
    double core_width = 1.0;
    double core_height = 1.0;
    double core_center_x = 0.0;
    double surface_y = 0.0;
};

struct ApeLinbo3Profile {
    double cover_index = 1.0;
    double ordinary_index = 2.20;
    double extraordinary_substrate_index = 2.20;
    double delta_extraordinary_index = 0.12;
    double peak_concentration = 0.01;
    double diffusion_width_x = 3.836665;
    double diffusion_depth_y = 3.509986;
    double core_center_x = 0.0;
    double surface_y = 0.0;
};

struct TiDiffusedLinbo3Profile {
    double cover_index = 1.0;
    double extraordinary_substrate_index = 2.2125;
    double ordinary_substrate_index = 2.1383;
    double extraordinary_surface_delta_index = 0.00446;
    double ordinary_surface_delta_index = 0.01217;
    double extraordinary_diffusion_width_x = 4.60;
    double extraordinary_diffusion_depth_y = 4.00;
    double ordinary_diffusion_width_x = 6.23;
    double ordinary_diffusion_depth_y = 4.98;
    double strip_width = 7.0;
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
double evaluate_channel_diffused_isotropic_index(
    const Point2D& point,
    const ChannelDiffusedIsotropicProfile& profile);
double evaluate_channel_diffused_isotropic_index_squared(
    const Point2D& point,
    const ChannelDiffusedIsotropicProfile& profile);
double evaluate_channel_gaussian_gaussian_index(
    const Point2D& point,
    const ChannelGaussianGaussianProfile& profile);
double evaluate_channel_gaussian_gaussian_index_squared(
    const Point2D& point,
    const ChannelGaussianGaussianProfile& profile);
double evaluate_ape_linbo3_concentration(
    const Point2D& point,
    const ApeLinbo3Profile& profile);
double evaluate_ape_linbo3_extraordinary_index(
    const Point2D& point,
    const ApeLinbo3Profile& profile);
double evaluate_ti_diffused_linbo3_extraordinary_index_squared(
    const Point2D& point,
    const TiDiffusedLinbo3Profile& profile);
double evaluate_ti_diffused_linbo3_ordinary_index_squared(
    const Point2D& point,
    const TiDiffusedLinbo3Profile& profile);

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
GlobalNodalMaterialFields make_channel_diffused_isotropic_global_material(
    const Mesh& mesh,
    const ChannelDiffusedIsotropicProfile& profile);
GlobalNodalMaterialFields make_channel_gaussian_gaussian_global_material(
    const Mesh& mesh,
    const ChannelGaussianGaussianProfile& profile);
GlobalNodalMaterialFields make_ape_linbo3_global_material(
    const Mesh& mesh,
    const ApeLinbo3Profile& profile);
GlobalNodalMaterialFields make_ti_diffused_linbo3_global_material(
    const Mesh& mesh,
    const TiDiffusedLinbo3Profile& profile);

ArticleLocalMaterialCoefficients make_rectangular_channel_step_index_element_material(
    const LinearTriangleP1Element& element,
    const RectangularChannelStepIndexProfile& profile);

ArticleLocalMaterialCoefficients make_element_material_from_global_fields(
    const LinearTriangleP1Element& element,
    const GlobalNodalMaterialFields& global_fields);

}  // namespace waveguide
