cmake_minimum_required(VERSION 3.20)

project(waveguide_solver LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(waveguide_core
    src/config.cpp
    src/dense_matrix.cpp
    src/eigensolver.cpp
    src/element.cpp
    src/geometry.cpp
    src/global_assembly.cpp
    src/local_assembly.cpp
    src/material.cpp
    src/material_profile.cpp
    src/mesh.cpp
    src/quadrature.cpp
)

target_include_directories(waveguide_core
    PUBLIC
        include
)

if(MSVC)
    target_compile_options(waveguide_core PRIVATE /W4 /permissive-)
else()
    target_compile_options(waveguide_core PRIVATE -Wall -Wextra -Wpedantic)
endif()

add_executable(waveguide_solver
    src/app.cpp
    src/main.cpp
)

target_link_libraries(waveguide_solver
    PRIVATE
        waveguide_core
)

include(CTest)

if(BUILD_TESTING)
    add_executable(waveguide_geometry_tests
        tests/geometry_tests.cpp
    )

    target_link_libraries(waveguide_geometry_tests
        PRIVATE
            waveguide_core
    )

    add_executable(waveguide_global_tests
        tests/global_tests.cpp
    )

    target_link_libraries(waveguide_global_tests
        PRIVATE
            waveguide_core
    )

    add_test(NAME waveguide_solver_help
        COMMAND waveguide_solver --help
    )

    add_test(NAME waveguide_solver_smoke
        COMMAND waveguide_solver
            --case ${CMAKE_SOURCE_DIR}/cases/smoke_case.yaml
            --output ${CMAKE_BINARY_DIR}/test_output/smoke
            --run-label ctest_smoke
    )

    set_tests_properties(waveguide_solver_smoke
        PROPERTIES
            FIXTURES_SETUP waveguide_solver_smoke_fixture
    )

    add_test(NAME waveguide_solver_planar_smoke
        COMMAND waveguide_solver
            --case ${CMAKE_SOURCE_DIR}/cases/planar_diffuse_isotropic_case.yaml
            --output ${CMAKE_BINARY_DIR}/test_output/planar
            --run-label ctest_planar
    )

    set_tests_properties(waveguide_solver_planar_smoke
        PROPERTIES
            FIXTURES_SETUP waveguide_solver_planar_fixture
    )

    add_test(NAME waveguide_geometry_tests
        COMMAND waveguide_geometry_tests
    )

    add_test(NAME waveguide_global_tests
        COMMAND waveguide_global_tests
    )

    add_test(NAME waveguide_solver_smoke_artifacts
        COMMAND ${CMAKE_COMMAND}
            -DSMOKE_OUTPUT_DIR=${CMAKE_BINARY_DIR}/test_output/smoke
            -P ${CMAKE_SOURCE_DIR}/tests/check_smoke_outputs.cmake
    )

    set_tests_properties(waveguide_solver_smoke_artifacts
        PROPERTIES
            FIXTURES_REQUIRED waveguide_solver_smoke_fixture
    )

    add_test(NAME waveguide_solver_planar_smoke_artifacts
        COMMAND ${CMAKE_COMMAND}
            -DSMOKE_OUTPUT_DIR=${CMAKE_BINARY_DIR}/test_output/planar
            -P ${CMAKE_SOURCE_DIR}/tests/check_smoke_outputs.cmake
    )

    set_tests_properties(waveguide_solver_planar_smoke_artifacts
        PROPERTIES
            FIXTURES_REQUIRED waveguide_solver_planar_fixture
    )
endif()
