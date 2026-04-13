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

double evaluate_planar_diffuse_isotropic_index_squared(
    double y,
    const PlanarDiffuseIsotropicProfile& profile) {
    const double refractive_index =
        evaluate_planar_diffuse_isotropic_index(y, profile);
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
