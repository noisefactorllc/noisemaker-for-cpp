cmake_minimum_required(VERSION 3.20)

project(noisemaker-for-cpp VERSION 0.1.0 LANGUAGES CXX)

include(GNUInstallDirs)
include(CMakePackageConfigHelpers)

find_package(ZLIB REQUIRED)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(noisemaker-cpu
  src/surface.cpp
  src/numeric.cpp
  src/fdlibm.cpp
  src/sampler.cpp
  src/texture_format.cpp
  src/png.cpp
  src/glsl_runtime.cpp
  src/kernel.cpp
  src/pass_runner.cpp
  src/effects/bit_effects.cpp
  src/generated/synth_solid.cpp
  src/generated/filter_invert.cpp
  src/typed_generated/typed_slice.cpp
  src/effects/scatter/registry.cpp
  src/effects/scatter/wormhole.cpp
  src/effects/scatter/catalog.cpp
  src/effects/generated/effect_catalog.cpp
  src/dsl/error.cpp
  src/dsl/lexer.cpp
  src/dsl/parser.cpp
  src/effects/registry.cpp
  src/dsl/compiler.cpp
  src/graph/resource.cpp
  src/graph/executor.cpp
  src/renderer.cpp
)
target_include_directories(noisemaker-cpu PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>
)
target_link_libraries(noisemaker-cpu PUBLIC ZLIB::ZLIB)
add_library(NoisemakerForCpp::noisemaker-cpu ALIAS noisemaker-cpu)

# Machine-generated and generator-refreshed files emit one dense statement
# per IR node, which trips -Wmisleading-indentation on GCC and newer Clang.
# The warning is purely stylistic for these files; every other warning in
# them, and all warnings elsewhere, remain -Werror.
set_source_files_properties(
  src/typed_generated/typed_slice.cpp
  tests/test_generated_kernels.cpp
  tests/test_typed_slice.cpp
  PROPERTIES COMPILE_OPTIONS
  "$<$<CXX_COMPILER_ID:AppleClang,Clang,GNU>:-Wno-misleading-indentation>")
target_compile_options(noisemaker-cpu PRIVATE
  $<$<CXX_COMPILER_ID:AppleClang,Clang,GNU>:-Wall -Wextra -Wpedantic -Werror -ffp-contract=off>
)
# Task-5's immutable proof artifact intentionally retains one unused context
# parameter and helper. Keep it byte-identical while strict AppleClang warnings
# apply to every other translation unit, including the new typed slice.
set_source_files_properties(src/generated/synth_solid.cpp PROPERTIES
  COMPILE_OPTIONS "$<$<CXX_COMPILER_ID:AppleClang,Clang,GNU>:-Wno-unused-parameter;-Wno-unused-function>"
)
# The generated catalog is metadata-heavy; keep strict diagnostics while
# avoiding multi-minute optimizer memory use for its immutable initializer.
set_source_files_properties(src/effects/generated/effect_catalog.cpp PROPERTIES
  COMPILE_OPTIONS "$<$<CXX_COMPILER_ID:AppleClang,Clang,GNU>:-O0>"
)

add_executable(noisemaker-cpu-tests
  tests/test_main.cpp
  tests/test_surface.cpp
  tests/test_numeric.cpp
  tests/test_sampler.cpp
  tests/test_texture_format.cpp
  tests/test_png.cpp
  tests/test_glsl_types.cpp
  tests/test_glsl_runtime.cpp
  tests/test_kernel.cpp
  tests/test_pass_runner.cpp
  tests/test_generated_kernels.cpp
  tests/test_typed_slice.cpp
  tests/test_scatter_wormhole.cpp
  tests/test_effect_catalog.cpp
  tests/test_dsl_lexer.cpp
  tests/test_dsl_parser.cpp
  tests/test_effect_registry.cpp
  tests/test_dsl_compiler.cpp
  tests/test_graph_resources.cpp
  tests/test_graph_blur.cpp
  tests/test_graph_features.cpp
)
target_link_libraries(noisemaker-cpu-tests PRIVATE noisemaker-cpu ZLIB::ZLIB)
target_compile_options(noisemaker-cpu-tests PRIVATE
  $<$<CXX_COMPILER_ID:AppleClang,Clang,GNU>:-Wall -Wextra -Wpedantic -Werror -ffp-contract=off>
)

add_executable(noisemaker-cpu-example-perlin examples/perlin.cpp)
target_link_libraries(noisemaker-cpu-example-perlin PRIVATE noisemaker-cpu)
target_compile_options(noisemaker-cpu-example-perlin PRIVATE
  $<$<CXX_COMPILER_ID:AppleClang,Clang,GNU>:-Wall -Wextra -Wpedantic -Werror -ffp-contract=off>
)

add_executable(noisemaker-dsl-cpu-case
  tools/benchmark/run_cpp_case.cpp
  tools/benchmark/corpus_case.cpp
)
target_link_libraries(noisemaker-dsl-cpu-case PRIVATE noisemaker-cpu)
target_compile_options(noisemaker-dsl-cpu-case PRIVATE
  $<$<CXX_COMPILER_ID:AppleClang,Clang,GNU>:-Wall -Wextra -Wpedantic -Werror -ffp-contract=off>
)

# The corpus benchmark driver. It shares corpus_case.cpp with the case driver
# above rather than copying its compile/execute path, so there is exactly one
# `require_executable = true` compile entry and one `GraphExecutor::execute`
# call site across both. It is deliberately not registered with `add_test`, not
# linked into `noisemaker-cpu`, and not part of any install or export set: it
# is a measurement tool, not shipped library surface.
#
# `-ffp-contract=off` is not optional here. It is the reason a measured number
# describes the same arithmetic the byte-exact parity lane validates.
set(NOISEMAKER_BENCHMARK_STRICT_FLAGS -Wall -Wextra -Wpedantic -Werror -ffp-contract=off)
string(JOIN " " NOISEMAKER_BENCHMARK_STRICT_FLAGS_TEXT ${NOISEMAKER_BENCHMARK_STRICT_FLAGS})
if(CMAKE_BUILD_TYPE)
  set(NOISEMAKER_BENCHMARK_BUILD_TYPE_TEXT "${CMAKE_BUILD_TYPE}")
else()
  set(NOISEMAKER_BENCHMARK_BUILD_TYPE_TEXT "unspecified")
endif()
add_executable(noisemaker-dsl-cpu-benchmark
  tools/benchmark/run_cpp_benchmark.cpp
  tools/benchmark/corpus_case.cpp
)
target_link_libraries(noisemaker-dsl-cpu-benchmark PRIVATE noisemaker-cpu)
target_compile_options(noisemaker-dsl-cpu-benchmark PRIVATE
  $<$<CXX_COMPILER_ID:AppleClang,Clang,GNU>:${NOISEMAKER_BENCHMARK_STRICT_FLAGS}>
)
# The emitted record must never claim a flag set the target was not built
# with, so both the compile options and the recorded string come from the one
# list above.
target_compile_definitions(noisemaker-dsl-cpu-benchmark PRIVATE
  NOISEMAKER_BENCHMARK_FLAGS="${NOISEMAKER_BENCHMARK_STRICT_FLAGS_TEXT}"
  NOISEMAKER_BENCHMARK_BUILD_TYPE="${NOISEMAKER_BENCHMARK_BUILD_TYPE_TEXT}"
)

add_executable(noisemaker-dsl-frontend-oracle tests/test_dsl_lexer.cpp)
target_compile_definitions(noisemaker-dsl-frontend-oracle PRIVATE NOISEMAKER_DSL_ORACLE_MAIN)
target_link_libraries(noisemaker-dsl-frontend-oracle PRIVATE noisemaker-cpu)
target_compile_options(noisemaker-dsl-frontend-oracle PRIVATE
  $<$<CXX_COMPILER_ID:AppleClang,Clang,GNU>:-Wall -Wextra -Wpedantic -Werror -ffp-contract=off>
)

add_executable(noisemaker-dsl-parser-oracle tests/test_dsl_parser.cpp)
target_compile_definitions(noisemaker-dsl-parser-oracle PRIVATE NOISEMAKER_DSL_PARSER_ORACLE_MAIN)
target_link_libraries(noisemaker-dsl-parser-oracle PRIVATE noisemaker-cpu)
target_compile_options(noisemaker-dsl-parser-oracle PRIVATE
  $<$<CXX_COMPILER_ID:AppleClang,Clang,GNU>:-Wall -Wextra -Wpedantic -Werror -ffp-contract=off>
)

add_executable(noisemaker-dsl-compiler-oracle tests/test_dsl_compiler.cpp)
target_compile_definitions(noisemaker-dsl-compiler-oracle PRIVATE NOISEMAKER_DSL_COMPILER_ORACLE_MAIN)
target_link_libraries(noisemaker-dsl-compiler-oracle PRIVATE noisemaker-cpu)
target_compile_options(noisemaker-dsl-compiler-oracle PRIVATE
  $<$<CXX_COMPILER_ID:AppleClang,Clang,GNU>:-Wall -Wextra -Wpedantic -Werror -ffp-contract=off>
)

enable_testing()
add_test(NAME noisemaker-cpu-tests COMMAND noisemaker-cpu-tests)

install(TARGETS noisemaker-cpu
  EXPORT noisemaker-for-cppTargets
  ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
  LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
  RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
  INCLUDES DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
)

install(DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/include/noisemaker/
  DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/noisemaker
  FILES_MATCHING PATTERN "*.hpp"
)

install(EXPORT noisemaker-for-cppTargets
  FILE noisemaker-for-cppTargets.cmake
  NAMESPACE NoisemakerForCpp::
  DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/noisemaker-for-cpp
)

configure_package_config_file(
  ${CMAKE_CURRENT_SOURCE_DIR}/cmake/noisemaker-for-cppConfig.cmake.in
  ${CMAKE_CURRENT_BINARY_DIR}/noisemaker-for-cppConfig.cmake
  INSTALL_DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/noisemaker-for-cpp
  NO_CHECK_REQUIRED_COMPONENTS_MACRO
)

write_basic_package_version_file(
  ${CMAKE_CURRENT_BINARY_DIR}/noisemaker-for-cppConfigVersion.cmake
  VERSION ${PROJECT_VERSION}
  COMPATIBILITY SameMajorVersion
)

install(FILES
  ${CMAKE_CURRENT_BINARY_DIR}/noisemaker-for-cppConfig.cmake
  ${CMAKE_CURRENT_BINARY_DIR}/noisemaker-for-cppConfigVersion.cmake
  DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/noisemaker-for-cpp
)
