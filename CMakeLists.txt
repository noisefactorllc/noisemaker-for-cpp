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
# `CMAKE_CXX_STANDARD` above is a directory variable: it governs this project's
# own targets and is not exported. Without a compile feature on the target
# itself, a consumer that only calls `find_package` + `target_link_libraries`
# compiles the installed headers at the compiler's default standard and fails
# inside headers it did not write. State the requirement where the export set
# can carry it.
target_compile_features(noisemaker-cpu PUBLIC cxx_std_20)
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
# `-ffp-contract=off` is PUBLIC, not PRIVATE. Most of the arithmetic-bearing
# surface of this library -- `glsl::` in `glsl_runtime.hpp`, the matrix and
# vector operators in `glsl_types.hpp` -- is header-inline, so it compiles in
# the *consumer's* translation unit under the consumer's flags. A consumer
# built with the compiler default (`-ffp-contract=fast` for Clang and GCC)
# gets fused multiply-add in those helpers, which is not the arithmetic the
# parity lane validates. The compiler guard matches the one used for warnings
# below: these are the compilers this project's bit-exactness is verified on.
target_compile_options(noisemaker-cpu PUBLIC
  $<$<CXX_COMPILER_ID:AppleClang,Clang,GNU>:-ffp-contract=off>
)
# Warnings stay PRIVATE: they are this project's discipline, not a consumer's.
target_compile_options(noisemaker-cpu PRIVATE
  $<$<CXX_COMPILER_ID:AppleClang,Clang,GNU>:-Wall -Wextra -Wpedantic -Werror>
)
# Task-5's immutable proof artifact intentionally retains one unused context
# parameter and helper. Keep it byte-identical while strict AppleClang warnings
# apply to every other translation unit, including the new typed slice.
set_source_files_properties(src/generated/synth_solid.cpp PROPERTIES
  COMPILE_OPTIONS "$<$<CXX_COMPILER_ID:AppleClang,Clang,GNU>:-Wno-unused-parameter;-Wno-unused-function>"
)
# The generated catalog is metadata-heavy; keep strict diagnostics while
# avoiding multi-minute optimizer memory use for its immutable initializer.
#
# Under sanitizers this one file is also the difference between a job that
# finishes and one that never does: instrumenting its single 7,967-line
# initializer measured 1739s against 30s uninstrumented (58x), while the
# comparably sized typed slice -- same generator, many small functions -- is
# only 2.5x. Excluding it buys real ASan/UBSan coverage of every hand-written
# file, where none existed before because the job always timed out. What is
# given up is instrumentation inside this one translation unit. Be precise
# about what that covers: the bulk is emitted aggregate construction, but the
# TU also allocates (every std::string/vector/map member) and defines
# EffectCatalog::find(), which indexes and returns interior pointers -- so
# find() is the one piece of EXECUTED code here running uninstrumented. Heap
# blocks this TU creates are still tracked by ASan's allocator and still
# checked wherever instrumented code touches them, and find()'s loop is
# .size()-bounded with its memo mutex-guarded in the header. The real fixes,
# both queued in the handoff: emit find() into its own TU so the carve-out
# covers only data, and split the initializer at the emitter.
set_source_files_properties(src/effects/generated/effect_catalog.cpp PROPERTIES
  COMPILE_OPTIONS "$<$<CXX_COMPILER_ID:AppleClang,Clang,GNU>:-O0>"
)
# Only CMAKE_CXX_FLAGS is inspected, which is how CI passes -fsanitize; a
# sanitizer arriving through CMAKE_CXX_FLAGS_<CONFIG> or a toolchain file
# would restore the 29-minute build, so keep passing it here.
if(CMAKE_CXX_FLAGS MATCHES "-fsanitize")
  set_property(SOURCE src/effects/generated/effect_catalog.cpp APPEND
    PROPERTY COMPILE_OPTIONS
    "$<$<CXX_COMPILER_ID:AppleClang,Clang,GNU>:-fno-sanitize=all>")
endif()

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

# The user-facing render CLI. It compiles `corpus_case.cpp` rather than
# reimplementing anything: `noisemaker-render` and `noisemaker-dsl-cpu-case`
# share one compile entry, one `GraphExecutor::execute` call site, one byte
# writer and one rendered-record serializer, so a picture a user renders is the
# picture the parity lane validates.
# It is deliberately kept out of the `noisemaker-for-cppTargets` EXPORT set --
# an exported executable would make `find_package` consumers depend on it --
# but it IS installed, by its own OPTIONAL `install(TARGETS ...)` below, so the
# answer to "how do I run this?" is not a build-tree path forever. OPTIONAL
# keeps `cmake --install` working after a `--target noisemaker-cpu` build,
# which is the constraint the old comment here was really protecting.
add_executable(noisemaker-render
  tools/cli/noisemaker_render.cpp
  tools/benchmark/corpus_case.cpp
)
target_include_directories(noisemaker-render PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/tools/benchmark)
target_link_libraries(noisemaker-render PRIVATE noisemaker-cpu)
target_compile_options(noisemaker-render PRIVATE
  $<$<CXX_COMPILER_ID:AppleClang,Clang,GNU>:-Wall -Wextra -Wpedantic -Werror -ffp-contract=off>
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

# `tests/test_render_cli.py` drives the built binaries rather than the library,
# so it needs them on disk and their paths in the environment. Registering the
# build as a ctest fixture is what makes `ctest` self-sufficient here: CI builds
# only `noisemaker-cpu-tests` before running ctest, so without this setup step
# the CLI test would find no binary and fail for the wrong reason.
find_package(Python3 COMPONENTS Interpreter)
if(Python3_Interpreter_FOUND)
  add_test(NAME noisemaker-render-cli-build
    COMMAND ${CMAKE_COMMAND} --build ${CMAKE_BINARY_DIR}
            --target noisemaker-render noisemaker-dsl-cpu-case
            --config $<CONFIG>)
  set_tests_properties(noisemaker-render-cli-build PROPERTIES FIXTURES_SETUP render-cli)
  add_test(NAME noisemaker-render-cli
    COMMAND ${Python3_EXECUTABLE} -B -m unittest -v tests.test_render_cli
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR})
  set_tests_properties(noisemaker-render-cli PROPERTIES
    FIXTURES_REQUIRED render-cli
    ENVIRONMENT "PYTHONDONTWRITEBYTECODE=1;NOISEMAKER_RENDER_CLI=$<TARGET_FILE:noisemaker-render>;NOISEMAKER_DSL_CPU_CASE=$<TARGET_FILE:noisemaker-dsl-cpu-case>")
else()
  # Not fatal: a consumer who only wants the library must still be able to
  # configure. But a test suite that deregisters itself in silence is the
  # failure mode the fail-closed rule exists to prevent -- without this,
  # `ctest` reports 100% passing on a machine where the one-code-path proof
  # never ran.
  message(WARNING
    "Python3 interpreter not found. These tests are NOT registered and will "
    "NOT run under ctest: noisemaker-render-cli-build, noisemaker-render-cli "
    "(tests/test_render_cli.py -- the proof that noisemaker-render and "
    "noisemaker-dsl-cpu-case produce byte-identical frames and metadata). "
    "Install a Python 3 interpreter to verify this repository; "
    "tests/test_benchmark_cpu_corpus.py, tests/test_dsl_corpus_parity.py and "
    "the typed-generator suites need it too.")
endif()

install(TARGETS noisemaker-cpu
  EXPORT noisemaker-for-cppTargets
  ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
  LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
  RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
  INCLUDES DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
)

# Outside the export set on purpose, and OPTIONAL on purpose: this installs
# the CLI when it has been built and is a no-op when it has not, so
# `cmake --build . --target noisemaker-cpu && cmake --install .` still works.
install(TARGETS noisemaker-render
  RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
  OPTIONAL
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
