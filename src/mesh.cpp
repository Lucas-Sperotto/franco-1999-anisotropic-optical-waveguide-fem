#include "waveguide_solver/mesh.hpp"

#include <fstream>
#include <set>
#include <sstream>
#include <stdexcept>

namespace waveguide {
namespace {

std::string trim_copy(const std::string& value) {
    const auto begin = value.find_first_not_of(" \t\r\n");
    if (begin == std::string::npos) {
        return {};
    }

    const auto end = value.find_last_not_of(" \t\r\n");
    return value.substr(begin, end - begin + 1);
}

std::string strip_comment(const std::string& line) {
    const auto comment_pos = line.find('#');
    if (comment_pos == std::string::npos) {
        return line;
    }
    return line.substr(0, comment_pos);
}

void validate_mesh(const Mesh& mesh, const std::filesystem::path& mesh_file) {
    if (mesh.format.empty()) {
        throw std::runtime_error("Mesh file is missing required 'format': " +
                                 mesh_file.string());
    }

    if (mesh.format != "simple_mesh_v1") {
        throw std::runtime_error("Unsupported mesh format '" + mesh.format +
                                 "' in " + mesh_file.string());
    }

    if (mesh.dimension != 2) {
        throw std::runtime_error("Only 2D meshes are supported in this stage: " +
                                 mesh_file.string());
    }

    if (mesh.nodes.size() < 3) {
        throw std::runtime_error("Mesh must contain at least 3 nodes: " +
                                 mesh_file.string());
    }

    if (mesh.triangles.empty()) {
        throw std::runtime_error("Mesh must contain at least one triangle: " +
                                 mesh_file.string());
    }

    std::set<int> node_ids;
    for (const MeshNode& node : mesh.nodes) {
        if (!node_ids.insert(node.id).second) {
            throw std::runtime_error("Duplicate node id in mesh: " +
                                     std::to_string(node.id));
        }
    }

    std::set<int> triangle_ids;
    for (const TriangleElement& triangle : mesh.triangles) {
        if (!triangle_ids.insert(triangle.id).second) {
            throw std::runtime_error("Duplicate triangle id in mesh: " +
                                     std::to_string(triangle.id));
        }

        for (int node_id : triangle.node_ids) {
            if (node_ids.count(node_id) == 0) {
                throw std::runtime_error("Triangle references unknown node id " +
                                         std::to_string(node_id) + " in " +
                                         mesh_file.string());
            }
        }

        const LinearTriangleP1Element element = mesh.make_p1_element(triangle);
        if (element.orientation == TriangleOrientation::degenerate) {
            throw std::runtime_error("Degenerate triangle detected in mesh: " +
                                     std::to_string(triangle.id));
        }
    }
}

}  // namespace

const MeshNode& Mesh::find_node(int node_id) const {
    for (const MeshNode& node : nodes) {
        if (node.id == node_id) {
            return node;
        }
    }

    throw std::runtime_error("Node id not found in mesh: " + std::to_string(node_id));
}

TriangleGeometry Mesh::make_triangle_geometry(const TriangleElement& triangle) const {
    return TriangleGeometry{{
        find_node(triangle.node_ids[0]).point,
        find_node(triangle.node_ids[1]).point,
        find_node(triangle.node_ids[2]).point,
    }};
}

LinearTriangleP1Element Mesh::make_p1_element(const TriangleElement& triangle) const {
    return make_linear_triangle_p1_element(
        make_triangle_geometry(triangle),
        triangle.id,
        triangle.node_ids);
}

Mesh load_minimal_mesh(const std::filesystem::path& mesh_file) {
    std::ifstream input(mesh_file);
    if (!input.is_open()) {
        throw std::runtime_error("Could not open mesh file: " + mesh_file.string());
    }

    Mesh mesh;
    std::string line;
    std::size_t line_number = 0;

    while (std::getline(input, line)) {
        ++line_number;
        const std::string stripped = trim_copy(strip_comment(line));
        if (stripped.empty()) {
            continue;
        }

        std::istringstream stream(stripped);
        std::string keyword;
        stream >> keyword;

        if (keyword == "format") {
            if (!(stream >> mesh.format)) {
                throw std::runtime_error("Invalid format entry in mesh file: " +
                                         mesh_file.string());
            }
            continue;
        }

        if (keyword == "dimension") {
            if (!(stream >> mesh.dimension)) {
                throw std::runtime_error("Invalid dimension entry in mesh file: " +
                                         mesh_file.string());
            }
            continue;
        }

        if (keyword == "node") {
            MeshNode node;
            if (!(stream >> node.id >> node.point.x >> node.point.y)) {
                throw std::runtime_error("Invalid node entry in mesh file " +
                                         mesh_file.string() + ":" +
                                         std::to_string(line_number));
            }
            mesh.nodes.push_back(node);
            continue;
        }

        if (keyword == "triangle") {
            TriangleElement triangle;
            if (!(stream >> triangle.id >> triangle.node_ids[0] >>
                  triangle.node_ids[1] >> triangle.node_ids[2])) {
                throw std::runtime_error("Invalid triangle entry in mesh file " +
                                         mesh_file.string() + ":" +
                                         std::to_string(line_number));
            }
            mesh.triangles.push_back(triangle);
            continue;
        }

        throw std::runtime_error("Unknown keyword '" + keyword + "' in mesh file " +
                                 mesh_file.string() + ":" +
                                 std::to_string(line_number));
    }

    validate_mesh(mesh, mesh_file);
    return mesh;
}

}  // namespace waveguide
