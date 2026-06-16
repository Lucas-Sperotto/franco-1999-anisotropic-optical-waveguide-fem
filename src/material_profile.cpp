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

void validate_channel_diffused_isotropic_profile(
    const ChannelDiffusedIsotropicProfile& profile) {
    if (profile.cover_index <= 0.0 || profile.background_index <= 0.0 ||
        profile.peak_index <= 0.0) {
        throw std::runtime_error(
            "The channel diffused isotropic profile requires positive indices");
    }
    if (profile.peak_index <= profile.background_index) {
        throw std::runtime_error(
            "The channel diffused isotropic profile requires peak_index > background_index");
    }
    if (profile.core_width <= 0.0 || profile.core_height <= 0.0) {
        throw std::runtime_error(
            "The channel diffused isotropic profile requires positive core dimensions");
    }
}

void validate_channel_gaussian_gaussian_profile(
    const ChannelGaussianGaussianProfile& profile) {
    if (profile.cover_index <= 0.0 || profile.background_index <= 0.0 ||
        profile.peak_index <= 0.0) {
        throw std::runtime_error(
            "The Gaussian-Gaussian channel profile requires positive indices");
    }
    if (profile.peak_index <= profile.background_index) {
        throw std::runtime_error(
            "The Gaussian-Gaussian channel profile requires peak_index > background_index");
    }
    if (profile.core_width <= 0.0 || profile.core_height <= 0.0) {
        throw std::runtime_error(
            "The Gaussian-Gaussian channel profile requires positive core dimensions");
    }
}

void validate_ape_linbo3_profile(const ApeLinbo3Profile& profile) {
    if (profile.cover_index <= 0.0 || profile.ordinary_index <= 0.0 ||
        profile.extraordinary_substrate_index <= 0.0) {
        throw std::runtime_error("The APE LiNbO3 profile requires positive indices");
    }
    if (profile.delta_extraordinary_index < 0.0) {
        throw std::runtime_error(
            "The APE LiNbO3 profile requires a nonnegative delta_extraordinary_index");
    }
    if (profile.peak_concentration < 0.0 || profile.peak_concentration > 1.0) {
        throw std::runtime_error(
            "The APE LiNbO3 profile requires 0 <= peak_concentration <= 1");
    }
    if (profile.diffusion_width_x <= 0.0 || profile.diffusion_depth_y <= 0.0) {
        throw std::runtime_error(
            "The APE LiNbO3 profile requires positive diffusion dimensions");
    }
}

void validate_ti_diffused_linbo3_profile(const TiDiffusedLinbo3Profile& profile) {
    if (profile.cover_index <= 0.0 ||
        profile.extraordinary_substrate_index <= 0.0 ||
        profile.ordinary_substrate_index <= 0.0) {
        throw std::runtime_error(
            "The Ti:LiNbO3 profile requires positive substrate indices");
    }
    if (profile.extraordinary_surface_delta_index < 0.0 ||
        profile.ordinary_surface_delta_index < 0.0) {
        throw std::runtime_error(
            "The Ti:LiNbO3 profile requires nonnegative surface index changes");
    }
    if (profile.extraordinary_diffusion_width_x <= 0.0 ||
        profile.extraordinary_diffusion_depth_y <= 0.0 ||
        profile.ordinary_diffusion_width_x <= 0.0 ||
        profile.ordinary_diffusion_depth_y <= 0.0 ||
        profile.strip_width <= 0.0) {
        throw std::runtime_error(
            "The Ti:LiNbO3 profile requires positive diffusion dimensions and strip_width");
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

bool is_point_inside_channel_diffused_core(
    const Point2D& point,
    const ChannelDiffusedIsotropicProfile& profile) {
    constexpr double kTolerance = 1.0e-12;
    const double half_width = 0.5 * profile.core_width;
    return point.x >= profile.core_center_x - half_width - kTolerance &&
           point.x <= profile.core_center_x + half_width + kTolerance &&
           point.y >= profile.surface_y - kTolerance &&
           point.y <= profile.surface_y + profile.core_height + kTolerance;
}

Point2D compute_triangle_centroid(const TriangleGeometry& geometry) {
    return Point2D{
        (geometry.vertices[0].x + geometry.vertices[1].x + geometry.vertices[2].x) /
            3.0,
        (geometry.vertices[0].y + geometry.vertices[1].y + geometry.vertices[2].y) /
            3.0,
    };
}

double square(double value) {
    return value * value;
}

double evaluate_ti_lateral_weight(double x, double strip_width, double diffusion_width) {
    const double scale = strip_width / (2.0 * diffusion_width);
    const double normalized_x = 2.0 * x / strip_width;
    return 0.5 * (std::erf(scale * (1.0 + normalized_x)) +
                  std::erf(scale * (1.0 - normalized_x)));
}

double evaluate_ti_branch_index_squared(double x,
                                        double y,
                                        double substrate_index,
                                        double surface_delta_index,
                                        double diffusion_width_x,
                                        double diffusion_depth_y,
                                        double strip_width) {
    const double lateral_weight =
        evaluate_ti_lateral_weight(x, strip_width, diffusion_width_x);
    const double depth_weight = std::exp(-(y * y) /
                                         (diffusion_depth_y * diffusion_depth_y));
    const double substrate_squared = square(substrate_index);
    const double surface_squared = square(substrate_index + surface_delta_index);
    return substrate_squared +
           (surface_squared - substrate_squared) * depth_weight * lateral_weight;
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

double evaluate_channel_diffused_isotropic_index(
    const Point2D& point,
    const ChannelDiffusedIsotropicProfile& profile) {
    validate_channel_diffused_isotropic_profile(profile);

    if (point.y < profile.surface_y) {
        return profile.cover_index;
    }
    if (!is_point_inside_channel_diffused_core(point, profile)) {
        return profile.background_index;
    }

    // TODO: docs/05 defines the circular profile using coordinates from the
    // diffusion origin but does not encode the figure orientation in the case
    // schema. This maps that origin to (core_center_x, surface_y), with y > 0
    // into the substrate, matching the current channel meshes.
    const double x = point.x - profile.core_center_x;
    const double y = point.y - profile.surface_y;
    const double half_width = 0.5 * profile.core_width;
    const double length_squared =
        std::abs(y) >= std::abs(x)
            ? profile.core_height * profile.core_height + x * x
            : half_width * half_width + y * y;
    const double radius_squared = x * x + y * y;
    return profile.background_index +
           ((profile.background_index - profile.peak_index) / length_squared) *
               (radius_squared - length_squared);
}

double evaluate_channel_diffused_isotropic_index_squared(
    const Point2D& point,
    const ChannelDiffusedIsotropicProfile& profile) {
    const double refractive_index =
        evaluate_channel_diffused_isotropic_index(point, profile);
    return refractive_index * refractive_index;
}

double evaluate_channel_gaussian_gaussian_index(
    const Point2D& point,
    const ChannelGaussianGaussianProfile& profile) {
    validate_channel_gaussian_gaussian_profile(profile);

    if (point.y < profile.surface_y) {
        return profile.cover_index;
    }

    const double x = point.x - profile.core_center_x;
    const double y = point.y - profile.surface_y;
    const double gaussian_x =
        std::exp(-4.0 * x * x / (profile.core_width * profile.core_width));
    const double gaussian_y =
        std::exp(-(y * y) / (profile.core_height * profile.core_height));
    const double profile_weight = gaussian_x * gaussian_y;

    return profile.background_index +
           (profile.peak_index - profile.background_index) * profile_weight;
}

double evaluate_channel_gaussian_gaussian_index_squared(
    const Point2D& point,
    const ChannelGaussianGaussianProfile& profile) {
    const double refractive_index =
        evaluate_channel_gaussian_gaussian_index(point, profile);
    return refractive_index * refractive_index;
}

double evaluate_ape_linbo3_concentration(
    const Point2D& point,
    const ApeLinbo3Profile& profile) {
    validate_ape_linbo3_profile(profile);

    if (point.y < profile.surface_y) {
        return 0.0;
    }

    const double x = point.x - profile.core_center_x;
    const double y = point.y - profile.surface_y;
    const double lateral_weight =
        std::exp(-(x * x) / (profile.diffusion_width_x * profile.diffusion_width_x));
    const double depth_weight =
        std::exp(-(y * y) / (profile.diffusion_depth_y * profile.diffusion_depth_y));
    return profile.peak_concentration * lateral_weight * depth_weight;
}

double evaluate_ape_linbo3_extraordinary_index(
    const Point2D& point,
    const ApeLinbo3Profile& profile) {
    validate_ape_linbo3_profile(profile);

    if (point.y < profile.surface_y) {
        return profile.cover_index;
    }

    const double concentration =
        evaluate_ape_linbo3_concentration(point, profile);
    return profile.extraordinary_substrate_index +
           profile.delta_extraordinary_index *
               (1.0 - std::exp(-11.0 * concentration));
}

double evaluate_ti_diffused_linbo3_extraordinary_index_squared(
    const Point2D& point,
    const TiDiffusedLinbo3Profile& profile) {
    validate_ti_diffused_linbo3_profile(profile);

    if (point.y < profile.surface_y) {
        return square(profile.cover_index);
    }

    return evaluate_ti_branch_index_squared(
        point.x - profile.core_center_x,
        point.y - profile.surface_y,
        profile.extraordinary_substrate_index,
        profile.extraordinary_surface_delta_index,
        profile.extraordinary_diffusion_width_x,
        profile.extraordinary_diffusion_depth_y,
        profile.strip_width);
}

double evaluate_ti_diffused_linbo3_ordinary_index_squared(
    const Point2D& point,
    const TiDiffusedLinbo3Profile& profile) {
    validate_ti_diffused_linbo3_profile(profile);

    if (point.y < profile.surface_y) {
        return square(profile.cover_index);
    }

    return evaluate_ti_branch_index_squared(
        point.x - profile.core_center_x,
        point.y - profile.surface_y,
        profile.ordinary_substrate_index,
        profile.ordinary_surface_delta_index,
        profile.ordinary_diffusion_width_x,
        profile.ordinary_diffusion_depth_y,
        profile.strip_width);
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

GlobalNodalMaterialFields make_channel_diffused_isotropic_global_material(
    const Mesh& mesh,
    const ChannelDiffusedIsotropicProfile& profile) {
    validate_channel_diffused_isotropic_profile(profile);

    GlobalNodalMaterialFields fields;
    // BLOCKER (T-005): n(x,y) varies in both x and y inside the core
    // (Eqs. 7-9, docs/05), so both flags should be true. However, docs/02 §3b
    // explicitly states that F2, F3, F4 become non-symmetric when delta flags
    // are active. Flags remain false until the non-symmetric route is audited
    // for the final sweeps of these 2D profiles.
    fields.delta_x = false;
    fields.delta_z = false;
    fields.homogeneous = false;
    fields.isotropic = true;
    fields.model_label = "channel_diffused_isotropic_circular";

    for (const MeshNode& node : mesh.nodes) {
        const double refractive_index_squared =
            evaluate_channel_diffused_isotropic_index_squared(node.point, profile);
        fields.nx2_by_node_id.emplace(node.id, refractive_index_squared);
        fields.nz2_by_node_id.emplace(node.id, refractive_index_squared);
        fields.gz2_by_node_id.emplace(node.id, 1.0 / refractive_index_squared);
    }

    return fields;
}

GlobalNodalMaterialFields make_channel_gaussian_gaussian_global_material(
    const Mesh& mesh,
    const ChannelGaussianGaussianProfile& profile) {
    validate_channel_gaussian_gaussian_profile(profile);

    GlobalNodalMaterialFields fields;
    fields.delta_x = true;
    fields.delta_z = true;
    fields.homogeneous = false;
    fields.isotropic = true;
    fields.model_label = "channel_diffused_isotropic_gaussian_gaussian";

    for (const MeshNode& node : mesh.nodes) {
        const double refractive_index_squared =
            evaluate_channel_gaussian_gaussian_index_squared(node.point, profile);
        fields.nx2_by_node_id.emplace(node.id, refractive_index_squared);
        fields.nz2_by_node_id.emplace(node.id, refractive_index_squared);
        fields.gz2_by_node_id.emplace(node.id, 1.0 / refractive_index_squared);
    }

    return fields;
}

GlobalNodalMaterialFields make_ape_linbo3_global_material(
    const Mesh& mesh,
    const ApeLinbo3Profile& profile) {
    validate_ape_linbo3_profile(profile);

    GlobalNodalMaterialFields fields;
    fields.delta_x = true;
    fields.delta_z = true;
    fields.homogeneous = false;
    fields.isotropic = false;
    fields.model_label = "ape_linbo3_anisotropic_sanity";

    for (const MeshNode& node : mesh.nodes) {
        double nx2 = square(profile.cover_index);
        double nz2 = square(profile.cover_index);
        if (node.point.y >= profile.surface_y) {
            const double extraordinary_index =
                evaluate_ape_linbo3_extraordinary_index(node.point, profile);
            nx2 = square(extraordinary_index);
            nz2 = square(profile.ordinary_index);
        }
        fields.nx2_by_node_id.emplace(node.id, nx2);
        fields.nz2_by_node_id.emplace(node.id, nz2);
        fields.gz2_by_node_id.emplace(node.id, 1.0 / nz2);
    }

    return fields;
}

GlobalNodalMaterialFields make_ti_diffused_linbo3_global_material(
    const Mesh& mesh,
    const TiDiffusedLinbo3Profile& profile) {
    validate_ti_diffused_linbo3_profile(profile);

    GlobalNodalMaterialFields fields;
    fields.delta_x = true;
    fields.delta_z = true;
    fields.homogeneous = false;
    fields.isotropic = false;
    fields.model_label = "ti_diffused_linbo3_anisotropic";

    for (const MeshNode& node : mesh.nodes) {
        const double nx2 =
            evaluate_ti_diffused_linbo3_extraordinary_index_squared(node.point, profile);
        const double nz2 =
            evaluate_ti_diffused_linbo3_ordinary_index_squared(node.point, profile);
        fields.nx2_by_node_id.emplace(node.id, nx2);
        fields.nz2_by_node_id.emplace(node.id, nz2);
        fields.gz2_by_node_id.emplace(node.id, 1.0 / nz2);
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
