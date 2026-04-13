if(NOT DEFINED SMOKE_OUTPUT_DIR)
    message(FATAL_ERROR "SMOKE_OUTPUT_DIR was not provided")
endif()

set(required_files
    "${SMOKE_OUTPUT_DIR}/meta/run_summary.txt"
    "${SMOKE_OUTPUT_DIR}/results/local_assembly_audit.txt"
    "${SMOKE_OUTPUT_DIR}/results/global_assembly_summary.txt"
    "${SMOKE_OUTPUT_DIR}/results/eigenvalues.csv"
    "${SMOKE_OUTPUT_DIR}/results/neff.csv"
    "${SMOKE_OUTPUT_DIR}/logs/solver_execution.log"
)

foreach(required_file IN LISTS required_files)
    if(NOT EXISTS "${required_file}")
        message(FATAL_ERROR "Missing expected smoke artifact: ${required_file}")
    endif()
endforeach()
