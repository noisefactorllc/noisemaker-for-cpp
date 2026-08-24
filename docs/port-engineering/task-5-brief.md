# Task 5: deterministic AOT kernel and pass-runner proof

## Objective

Prove the production architecture end to end on the two canonical programs `synth/solid:solid` and `filter/invert:inv`:

1. a self-contained, standard-library-only Python developer tool reads pinned vendored GLSL fixtures;
2. it normalizes/parses them and emits deterministic strongly typed C++;
3. normal CMake compiles only committed C++ outputs, with no Python, Node, network, CDN, or sibling-repository dependency;
4. native binding factories and a pass runner render the two programs with tested bottom-left GLSL coordinates and top-down `Surface` storage.

This is a two-program architectural proof, not permission to widen to the full catalog in this task.

## Constraints and workflow

- Work only in `.`.
- Do not invoke Git or any indirect Git operation. No branch/worktree/commit/PR.
- Use strict incremental TDD. Capture honest red/green evidence in `docs/port-engineering/task-5-report.md`.
- Use `apply_patch` for all source/fixture edits. Do not create repo-local process/spec/report docs.
- Preserve existing APIs and 45-test baseline.
- C++20; runtime dependencies remain standard library plus existing zlib.
- Generator is Python 3 standard library only. It is an explicit developer/CI tool, never a normal CMake dependency.
- Checked-in generated C++ must contain no absolute paths, wall-clock timestamps, nondeterministic iteration order, runtime Python/Node hooks, sibling paths, or network access.
- Adaptation of the MIT sibling Python transpiler is allowed, but the C++ emitter and output/package logic must be native to this repository.

## Canonical fixture provenance

Vendor exact bytes from these local canonical source files using `apply_patch`:

- `../noisemaker/shaders/effects/synth/solid/glsl/solid.glsl`
  - size 273
  - raw SHA-256 `82afae3ccf523d1938cd02eadc6bfae5e4440a9b22a4f5629688d1d05856287c`
  - stripped SHA-256 `1ad5094ee24be64efc809666858121a0e6a8f4b7b2f5c75830d47f19cbc88ad6`
- `../noisemaker/shaders/effects/filter/invert/glsl/inv.glsl`
  - size 658
  - raw SHA-256 `18cea484b4d9ab8cbd3db2189777400d7adfeea1c3798dc9ef0e3112d46f6e99`
  - stripped SHA-256 `4fe48ede46e557c77668c2393428a38d0cfb1884bea97f2d5716079c2b8ae08e`

The checked-in CPU source lock and upstream snapshot identify revision `a024dc3a960cc44af454abc7aebce50456c194e6`. Record this revision in fixture provenance, but do not claim that the current sibling working tree was HEAD/clean verified because that would require a forbidden Git operation. The generation tool verifies the vendored bytes/hashes only.

Suggested fixture layout:

```text
tools/glslcpp/fixtures/a024dc3a960cc44af454abc7aebce50456c194e6/
  manifest.json
  synth_solid.glsl
  filter_invert.glsl
```

The fixture manifest is small, schema-versioned JSON with sorted program entries, revision, relative source path, raw/stripped hash, program key, output name, and pass-binding metadata needed for these two factories. No rolling CDN payload.

## Native kernel seam

Create `include/noisemaker/kernel.hpp` with:

```cpp
namespace noisemaker {

struct KernelState {
  virtual ~KernelState() = default;
};

using PixelFn = void (*)(
    const KernelState&,
    const glsl::PixelContext&,
    glsl::Vec4& output) noexcept;

class BoundKernel {
 public:
  BoundKernel(std::shared_ptr<const KernelState> state, PixelFn pixel);
  void run_pixel(const glsl::PixelContext& context,
                 glsl::Vec4& output) const noexcept;
  // read-only accessors needed by pass runner are acceptable
 private:
  std::shared_ptr<const KernelState> state_;
  PixelFn pixel_;
};
}
```

- Reject null state or function pointer with `std::invalid_argument` at construction.
- State is allocated/captured once at bind time. Per-pixel execution performs no allocation, map/variant/string lookup, or `std::function` dispatch.
- A private generated `State final : KernelState` plus localized `static_cast` trampoline is acceptable.
- `run_pixel` is noexcept; all binding validation happens in the generated factory.

## Pass runner seam

Create `include/noisemaker/pass_runner.hpp` and `src/pass_runner.cpp`:

```cpp
Surface run_pass(const BoundKernel& kernel,
                 std::size_t width,
                 std::size_t height,
                 float time = 0.0f,
                 float seed = 1.0f,
                 std::uint32_t frame = 0,
                 float delta_time = 0.0f);
```

For top-down storage row `y` and column `x`, construct:

- `frag_coord = Vec4(x + 0.5, height - y - 0.5, 0, 1)`;
- `uv = Vec2(frag_coord.x / width, frag_coord.y / height)`;
- `resolution = Vec2(width, height)`;
- supplied time/seed/frame/delta.

Call the raw pixel function, narrow/store four lanes in the result `Surface`. `Surface` retains dimension/bounds authority. Cache state/function access outside the inner loop if the public seam permits it.

## Generated public factories

Create `include/noisemaker/generated/catalog.hpp` declaring exactly:

```cpp
BoundKernel bind_synth_solid(const glsl::Bindings& bindings);
BoundKernel bind_filter_invert(const glsl::Bindings& bindings);
```

Commit generated sources under `src/generated/` plus `src/generated/manifest.json`. Suggested source names:

- `synth_solid.cpp`
- `filter_invert.cpp`

Each generated source has a deterministic banner with schema, pinned revision, program key, and source SHA. No timestamps or absolute paths.

### Solid contract

- Bind `color` as exact `glsl::Vec3`, fallback zero.
- Bind `alpha` as exact `float`, fallback zero.
- Typed pixel body implements `fragColor = vec4(color * alpha, alpha)` using the Task-4 deferred-expression/storage ABI.

### Invert contract

- Require sampler `inputTex`; factory throws existing `KernelBindingError` if missing.
- Bind `mode` as exact `std::int32_t`, fallback 0.
- Compute `texSize`, `uv = gl_FragCoord.xy / vec2(texSize)`, and nearest bottom-left sampling through existing tested sampler primitives.
- Mode 0: `rgb = 1.0 - rgb`.
- Mode 1: `rgb = min(rgb, 1.0 - rgb)`.
- Preserve alpha.
- No binding/variant/map lookup occurs inside the pixel function.

## Generator tool

Create a private tool package under `tools/glslcpp/`. A suitable bounded file set is:

- `__init__.py`
- `lexer.py`
- `preprocess.py`
- `parser.py`
- `types.py`
- `emit_cpp.py`
- `generate_kernels.py`
- fixture directory/manifest above

You may adapt the sibling Python port's standard-library lexer, preprocessor, parser, type map, scopes, and overload selection. Do not copy its Python source emitter, dynamic runtime calls, kernel loader, CDN/build plumbing, or mutable-AST behavior.

The C++ emitter must genuinely derive the typed bodies from normalized ASTs. It may support only the syntax/builtins exercised by these fixtures in Task 5, but unsupported nodes must raise a deterministic `GeneratorError` with program key and source location/context—never silently fall back to hand-authored source.

The tool supports:

```sh
python3 tools/glslcpp/generate_kernels.py --check
python3 tools/glslcpp/generate_kernels.py --write
```

- Resolve all paths relative to the tool/repository, never CWD or a home path.
- Verify fixture size/raw/stripped hashes before parsing.
- Load and validate every input, normalize, parse, and render every declared output fully in memory before any `--write` mutation.
- `--write` writes only the fixed declared generated paths, preferably atomically, and removes nothing outside that declared set.
- `--check` regenerates in memory and byte-compares every declared output and generated manifest; fail on missing, extra declared generated files, hash/source drift, or output drift.
- Sort program keys/output tables; fixed UTF-8, LF, indentation, banner, and final newline.
- `src/generated/manifest.json` contains generator schema/version, revision, each input hash, and each generated source hash. Do not hash the manifest into itself.
- Normal CMake does not execute this tool or find Python.

## Tests

Create:

- `tests/test_kernel.cpp`
- `tests/test_pass_runner.cpp`
- `tests/test_generated_kernels.cpp`
- `tests/test_generator.py` (stdlib `unittest`; explicit developer test, not default CMake)

Required coverage:

1. `BoundKernel` rejects null state/function and retains state lifetime.
2. Pass runner emits correct asymmetric 2x2 `frag_coord`/`uv`, writes top-down, and propagates time/seed/frame/delta.
3. Solid on 16x16 with color `(0.2,0.4,0.6)`, alpha 1 yields every RGBA8 pixel `[51,102,153,255]`.
4. Solid alpha 0.5 proves premultiplication and alpha storage: first pixel `[26,51,77,128]` for the same color.
5. Invert mode 0 of `[51,102,153,255]` yields `[204,153,102,255]`.
6. Invert mode 1 of `[204,102,153,255]` yields `[51,102,102,255]`, preserving alpha.
7. Asymmetric 2x2 input proves bottom-left shader addressing maps back to unchanged top-down storage under identity coordinates.
8. Missing input sampler and wrong uniform alternative fail at bind time, not inside the loop.
9. Generated pixel source contains typed state/direct calls and contains no `UniformValue`, binding lookup, `std::function`, Python/Node, or sibling path in its body.
10. Generator test proves identical generation twice, stable program ordering, exact committed-output comparison, fixture-hash rejection, unsupported-AST failure, and absence of absolute paths/timestamps.
11. `--check` succeeds on the committed tree.

Tests must not replace the generator with hand-authored expected output. The checked-in generated source itself is the deterministic golden; Python tests call generator functions/in-memory output and compare bytes.

## CMake and verification

Add kernel, pass-runner, and committed generated sources to the library and the three C++ tests to the existing binary. Do not add Python discovery or code generation to normal configure/build.

Run and record:

```sh
python3 tests/test_generator.py
python3 tools/glslcpp/generate_kernels.py --check
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build --parallel
build/noisemaker-cpu-tests
ctest --test-dir build --output-on-failure
```

## Report

Write `docs/port-engineering/task-5-report.md` with:

- exact red/green commands and results;
- files created/changed;
- provenance/hash verification;
- generator subset/unsupported semantics;
- final Python/C++/CTest counts;
- any assertion that lacks honest original red-before-production evidence;
- remaining concerns before scaling beyond two programs.
