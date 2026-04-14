#include "waveguide_solver/material_profile.hpp"

#include <array>
#include <cmath>
#include <stdexcept>

namespace waveguide {
namespace {

std::array<double, 3> gather_nodal_values(const std::map<int, double>& field_by_node_id,
                                          const std::array<int, 3>& node_ids,
                                          const std::string& field_label) {
    return {
        get_global_material_value(field_by_node_id, node_ids[0], field_label),
        get_global_material_value(field_by_node_id, node_ids[1], field_label),
        get_global_material_value(field_by_node_id, node_ids[2], field_label),
    };
}

void validate_diffusion_depth(double diffusion_depth) {
    if (diffusion_depth <= 0.0) {
        throw std::runtime_error(
            "The planar diffuse isotropic profile requires a positive diffusion_depth");
    }
}

double resolve_cover_index(const PlanarDiffuseIsotropicProfile& profile) {
    return profile.cover_index > 0.0 ? profile.cover_index
                                     : profile.background_index;
}

void validate_rectangular_channel_profile(
    const RectangularChannelStepIndexProfile& profile) {
    if (profile.cover_index <= 0.0 || profile.substrate_index <= 0.0 ||
        profile.core_index <= 0.0) {
        throw std::runtime_error(
            "The rectangular channel step-index profile requires positive indices");
    }
    if (profile.core_width <= 0.0 || profile.core_height <= 0.0) {
        throw std::runtime_error(
            "The rectangular channel step-index profile requires positive core dimensions");
    }
}

bool is_point_inside_rectangular_channel_core(
    const Point2D& point,
    const RectangularChannelStepIndexProfile& profile) {
    constexpr double kTolerance = 1.0e-12;
    const double half_width = 0.5 * profile.core_width;
    return point.x >= profile.core_center_x - half_width - kTolerance &&
           point.x <= profile.core_center_x + half_width + kTolerance &&
           point.y >= profile.surface_y - kTolerance &&
           point.y <= profile.surface_y + profile.core_height + kTolerance;
}

double evaluate_rectangular_channel_step_index_squared(
    const Point2D& point,
    const RectangularChannelStepIndexProfile& profile) {
    if (is_point_inside_rectangular_channel_core(point, profile)) {
        return profile.core_index * profile.core_index;
    }
    if (point.y < profile.surface_y) {
        return profile.cover_index * profile.cover_index;
    }
    return profile.substrate_index * profile.substrate_index;
}

Point2D compute_triangle_centroid(const TriangleGeometry& geometry) {
    return Point2D{
        (geometry.vertices[0].x + geometry.vertices[1].x + geometry.vertices[2].x) /
            3.0,
        (geometry.vertices[0].y + geometry.vertices[1].y + geometry.vertices[2].y) /
            3.0,
    };
}

}  // namespace

double get_global_material_value(const std::map<int, double>& field_by_node_id,
                                 int node_id,
                                 const std::string& field_label) {
    const auto it = field_by_node_id.find(node_id);
    if (it == field_by_node_id.end()) {
        throw std::runtime_error("Missing nodal material value for field '" + field_label +
                                 "' at node id " + std::to_string(node_id));
    }
    return it->second;
}

double evaluate_planar_diffuse_isotropic_index(
    double y,
    const PlanarDiffuseIsotropicProfile& profile) {
    validate_diffusion_depth(profile.diffusion_depth);
    return profile.background_index +
           profile.delta_index * std::exp(-std::abs(y) / profile.diffusion_depth);
}

double evaluate_planar_surface_diffuse_isotropic_index(
    double y,
    const PlanarDiffuseIsotropicProfile& profile) {
    validate_diffusion_depth(profile.diffusion_depth);
    if (y < profile.surface_coordinate) {
        return resolve_cover_index(profile);
    }

    return profile.background_index +
           profile.delta_index *
               std::exp(-(y - profile.surface_coordinate) / profile.diffusion_depth);
}

double evaluate_planar_diffuse_isotropic_index_squared(
    double y,
    const PlanarDiffuseIsotropicProfile& profile) {
    const double refractive_index =
        evaluate_planar_diffuse_isotropic_index(y, profile);
    return refractive_index * refractive_index;
}

double evaluate_planar_surface_diffuse_isotropic_index_squared(
    double y,
    const PlanarDiffuseIsotropicProfile& profile) {
    validate_diffusion_depth(profile.diffusion_depth);

    if (y < profile.surface_coordinate) {
        const double cover_index = resolve_cover_index(profile);
        return cover_index * cover_index;
    }

    const double depth = y - profile.surface_coordinate;
    const double exponential_weight =
        std::exp(-depth / profile.diffusion_depth);

    if (profile.linearized_permittivity) {
        return profile.background_index * profile.background_index +
               2.0 * profile.background_index * profile.delta_index *
                   exponential_weight;
    }

    const double refractive_index =
        profile.background_index + profile.delta_index * exponential_weight;
    return refractive_index * refractive_index;
}

GlobalNodalMaterialFields make_homogeneous_isotropic_global_material(
    const Mesh& mesh,
    double refractive_index) {
    if (refractive_index <= 0.0) {
        throw std::runtime_error(
            "The homogeneous isotropic profile requires a positive refractive index");
    }

    const double refractive_index_squared = refractive_index * refractive_index;
    GlobalNodalMaterialFields fields;
    fields.delta_x = false;
    fields.delta_z = false;
    fields.homogeneous = true;
    fields.isotropic = true;
    fields.model_label = "homogeneous_isotropic_constant_coefficients";

    for (const MeshNode& node : mesh.nodes) {
        fields.nx2_by_node_id.emplace(node.id, refractive_index_squared);
        fields.nz2_by_node_id.emplace(node.id, refractive_index_squared);
        fields.gz2_by_node_id.emplace(node.id, 1.0 / refractive_index_squared);
    }

    return fields;
}

GlobalNodalMaterialFields make_planar_diffuse_isotropic_global_material(
    const Mesh& mesh,
    const PlanarDiffuseIsotropicProfile& profile) {
    validate_diffusion_depth(profile.diffusion_depth);

    GlobalNodalMaterialFields fields;
    fields.delta_x = false;
    fields.delta_z = true;
    fields.homogeneous = false;
    fields.isotropic = true;
    fields.model_label = "planar_diffuse_isotropic_exponential";

    for (const MeshNode& node : mesh.nodes) {
        const double refractive_index_squared =
            evaluate_planar_diffuse_isotropic_index_squared(node.point.y, profile);
        fields.nx2_by_node_id.emplace(node.id, refractive_index_squared);
        fields.nz2_by_node_id.emplace(node.id, refractive_index_squared);
        fields.gz2_by_node_id.emplace(node.id, 1.0 / refractive_index_squared);
    }

    return fields;
}

GlobalNodalMaterialFields make_planar_surface_diffuse_isotropic_global_material(
    const Mesh& mesh,
    const PlanarDiffuseIsotropicProfile& profile) {
    validate_diffusion_depth(profile.diffusion_depth);

    GlobalNodalMaterialFields fields;
    fields.delta_x = false;
    fields.delta_z = true;
    fields.homogeneous = false;
    fields.isotropic = true;
    fields.model_label = "planar_diffuse_isotropic_surface_exponential";

    for (const MeshNode& node : mesh.nodes) {
        const double refractive_index_squared =
            evaluate_planar_surface_diffuse_isotropic_index_squared(node.point.y, profile);
        fields.nx2_by_node_id.emplace(node.id, refractive_index_squared);
        fields.nz2_by_node_id.emplace(node.id, refractive_index_squared);
        fields.gz2_by_node_id.emplace(node.id, 1.0 / refractive_index_squared);
    }

    return fields;
}

GlobalNodalMaterialFields make_rectangular_channel_step_index_global_material(
    const Mesh& mesh,
    const RectangularChannelStepIndexProfile& profile) {
    validate_rectangular_channel_profile(profile);

    GlobalNodalMaterialFields fields;
    fields.delta_x = false;
    fields.delta_z = false;
    fields.homogeneous = false;
    fields.isotropic = true;
    fields.model_label = "rectangular_channel_step_index";

    for (const MeshNode& node : mesh.nodes) {
        const double refractive_index_squared =
            evaluate_rectangular_channel_step_index_squared(node.point, profile);
        fields.nx2_by_node_id.emplace(node.id, refractive_index_squared);
        fields.nz2_by_node_id.emplace(node.id, refractive_index_squared);
        fields.gz2_by_node_id.emplace(node.id, 1.0 / refractive_index_squared);
    }

    return fields;
}

ArticleLocalMaterialCoefficients make_rectangular_channel_step_index_element_material(
    const LinearTriangleP1Element& element,
    const RectangularChannelStepIndexProfile& profile) {
    validate_rectangular_channel_profile(profile);
    const Point2D centroid = compute_triangle_centroid(element.geometry);
    const double refractive_index_squared =
        evaluate_rectangular_channel_step_index_squared(centroid, profile);
    return make_homogeneous_isotropic_local_material(
        element, refractive_index_squared);
}

ArticleLocalMaterialCoefficients make_element_material_from_global_fields(
    const LinearTriangleP1Element& element,
    const GlobalNodalMaterialFields& global_fields) {
    return make_article_local_material_from_explicit_gz2(
        element,
        gather_nodal_values(global_fields.nx2_by_node_id,
                            element.global_node_ids,
                            "nx2"),
        gather_nodal_values(global_fields.nz2_by_node_id,
                            element.global_node_ids,
                            "nz2"),
        gather_nodal_values(global_fields.gz2_by_node_id,
                            element.global_node_ids,
                            "gz2"),
        global_fields.delta_x,
        global_fields.delta_z,
        global_fields.homogeneous,
        global_fields.isotropic,
        global_fields.model_label);
}

}  // namespace waveguide
