#pragma once

#include "waveguide_solver/geometry.hpp"

#include <array>
#include <filesystem>
#include <string>
#include <vector>

namespace waveguide {

struct MeshNode {
    int id = 0;
    Point2D point;
};

struct TriangleElement {
    int id = 0;
    std::array<int, 3> node_ids{};
};

struct Mesh {
    std::string format;
    int dimension = 0;
    std::vector<MeshNode> nodes;
    std::vector<TriangleElement> triangles;

    const MeshNode& find_node(int node_id) const;
    TriangleGeometry make_triangle_geometry(const TriangleElement& triangle) const;
};

Mesh load_minimal_mesh(const std::filesystem::path& mesh_file);

}  // namespace waveguide
