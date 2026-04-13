cmake_minimum_required(VERSION 3.20)

project(waveguide_solver LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(waveguide_core
    src/config.cpp
    src/element.cpp
    src/geometry.cpp
    src/local_assembly.cpp
    src/mesh.cpp
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

    add_test(NAME waveguide_solver_help
        COMMAND waveguide_solver --help
    )

    add_test(NAME waveguide_solver_smoke
        COMMAND waveguide_solver
            --case ${CMAKE_SOURCE_DIR}/cases/smoke_case.yaml
            --output ${CMAKE_BINARY_DIR}/test_output/smoke
            --run-label ctest_smoke
    )

    add_test(NAME waveguide_geometry_tests
        COMMAND waveguide_geometry_tests
    )
endif()
