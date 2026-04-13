cmake_minimum_required(VERSION 3.20)

project(waveguide_solver LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_executable(waveguide_solver
    src/app.cpp
    src/config.cpp
    src/main.cpp
)

target_include_directories(waveguide_solver
    PRIVATE
        include
)

if(MSVC)
    target_compile_options(waveguide_solver PRIVATE /W4 /permissive-)
else()
    target_compile_options(waveguide_solver PRIVATE -Wall -Wextra -Wpedantic)
endif()

include(CTest)

if(BUILD_TESTING)
    add_test(NAME waveguide_solver_help
        COMMAND waveguide_solver --help
    )

    add_test(NAME waveguide_solver_smoke
        COMMAND waveguide_solver
            --case ${CMAKE_SOURCE_DIR}/cases/smoke_case.yaml
            --output ${CMAKE_BINARY_DIR}/test_output/smoke
    )
endif()
