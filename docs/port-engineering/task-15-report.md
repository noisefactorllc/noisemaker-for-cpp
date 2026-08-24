# Task 15 report: strict counted-for v1 slice

Date: 2026-08-10  
Repository: `.`  
Pinned corpus revision: `a024dc3a960cc44af454abc7aebce50456c194e6`

## Result

Task 15 is complete and stops at its independent-review boundary. The native
typed slice now contains exactly 107 sorted programs. Together with the two
immutable generated factories, the public catalog contains exactly 109 sorted
unique factories and leaves exactly `212 - 109 = 103` corpus programs without
a native public factory.

The increment is the corrected, audited 36-program loop-only set. It does not
admit the eight deferred programs that require top-level integer constants,
sampler helper parameters, or effective loop depth four. The authoritative
non-empty define maps for morphology, relief, scatter, strokes, hatch,
low-poly, and oil-paint are preserved exactly.

## Counted-loop proof

The parser and frozen typed IR admit only increasing integer loops of the
forms `for (int i=L; i<B; i++)` and `for (int i=L; i<=B; ++i)`. Bounds are
integer literals, the exact function-local read-only integer-constant form,
or the exact reverb `clamp(iterations, 1, 8)` proof. Stable symbol identity
links initializer, condition, update, and any local bound.

Every admitted loop carries immutable evidence for trip count, lexical depth,
effective call-stack depth, lexical product, and entrypoint charge. The
validator recomputes this evidence, and the emitter independently recomputes
it before lowering. Both fail closed on malformed identity, unproved loops,
returns from loops, call cycles, more than 128 trips, effective depth above 3,
products above 4,096, or entrypoint charge above 4,096. Unsupported whole-
program proofs report the first offending loop's frozen source line and
column. `while`, `do-while`, decrement, step arithmetic, swapped and dynamic
bounds, and increment/decrement outside an admitted header remain rejected.

Independent review found that the initial gate rejected a cyclic call graph
only when a loop was also present. The corrected validator and emitter reject
call cycles unconditionally. A mutually recursive, loop-free helper fixture
now proves rejection at both layers; no admitted program or generated C++
artifact changed.

Native output uses ordinary C++ `for`, `break`, and `continue`. It introduces
no interpreter, heap-backed loop state, per-pixel maps, strings, variants,
allocations, or dynamic dispatch.

## Bindings and catalog truth

The 36 factories expose 235 exact name-keyed bindings: 189 uniforms and 46
samplers. Every required uniform and sampler route has a fail-closed missing-
binding test, and representative wrong types are rejected. Reverb is covered
at both one and eight iterations. The public catalog test locks 109 sorted
unique factories and 103 remaining public-unported programs.

Renderer scalar uniforms now preserve canonical JavaScript Number precision
as `double` in generated state. `Bindings::get_number()` accepts exact double
bindings and widens legacy float bindings without changing their value.
Vector uniforms remain Float32 vectors. The oracle table preserves the source
provenance of post-spread system values, including mandala's widened-F32
aspect value.

## Canonical precision corrections

Three exact mismatches were diagnosed against instrumented canonical kernels;
the frozen oracle was never changed:

1. Chrome exposed that helper-backed vector-vector arithmetic returns an
   ordinary JavaScript Array whose later scalar `.map()` remains binary64.
   The emitter now preserves that scalar-map precision until a real storage or
   builtin boundary.
2. Low-poly exposed that authored scalar uniforms remain JavaScript Numbers,
   while system vector bindings remain Float32. The scalar binding path was
   split accordingly.
3. Synth/cell exposed interprocedural container provenance. An exact
   `vecN(integralCall()) / scalar` helper return is classified by stable
   signature ID as an ordinary-array return. Its canonical outer `cpu_float`
   boundary is retained once, while non-mutated caller scalar-map chains use
   `FloatExpr<N>` until storage. Mutated locals and vector-vector declarations
   remain concrete `VecN` storage. The formerly divergent first output lane is
   now exactly `0x3d2726a1`.

Paired generator/runtime regressions cover deferred float-vector lanes,
integral swizzle conversion versus whole integral-call conversion, direct
ordinary-array helper returns, mutated-local materialization, concrete
vector-vector declarations, scalar binding provenance, and FloatExpr
swizzles.

## Frozen oracle evidence

The accepted artifact is
`docs/port-engineering/task-15-oracles.json`, SHA-256
`e001c89f58ac970206a50dbf0974ce096e6fd71b5a3f2e389e315b0cfb16bdc8`.
Its generator is `docs/port-engineering/task-15-oracle-generator.mjs`.

All 38 `(key, variant)` observations pass exactly: 36 default variants plus
reverb at one and eight iterations. Every 9x7 render uses the complete fixture
(`time=.375`, `frame=7`, `deltaTime=1/60`, `seed=19`, tile offset `[2,1]`,
full resolution `[13,11]`) and distinct 11x9 formula surfaces for all sampler
routes. Every row matches its exact little-endian Float32 SHA-256, RGBA8
SHA-256, twelve exact Float32-bit probes, and an immediate repeat render.
Prior Task 11, 12, 13, and 14 oracle suites remain green.

## Generated and immutable hashes

- Task 15 corrected brief: `5c50686a46eec3860e39cc77e1765e0339dd74109df110b1c3042aa35870d0e8`
- Task 15 implementation-risk audit: `e6b17733dc6acd80ae0f1a22a4a68aa0a5bc80a8db0927dd59f6f143080afef4`
- Task 15 oracle artifact: `e001c89f58ac970206a50dbf0974ce096e6fd71b5a3f2e389e315b0cfb16bdc8`
- `src/typed_generated/typed_slice.cpp`: `d4c33446716290f79a1d02749a6d0301ea35c1caf8e2a995ba64aae2591fac9b`
- `src/typed_generated/typed_manifest.json`: `9eebfb8fb293e2acbfa6bb92d9e6fc96ece789ab67455707f459e93fd9e56bae`
- `tools/glslcpp/typed_slice.json`: `d90f5018f6ed53373bf815f32412d750d113183ba8b04d4bc30f8740a916b5cb`
- `include/noisemaker/generated/catalog.hpp`: `ea681d1d4c1781f90a0af7a675dcad286517581047074b2fb3d7a00f5d2a6cde`
- Immutable `src/generated/synth_solid.cpp`: `4a88533b90ce71268461f2d6fc2ad71025deb830e403c878b424b7b0ef822363`
- Immutable `src/generated/filter_invert.cpp`: `06dd8cf0dacb86fb4ae11ebc822fd8103f648bc98d8272bc526c4507b2d4f1b7`

## Verification

All final commands completed with exit status 0:

- `python3 -m unittest discover -s tests -p 'test_*.py' -v`: post-review
  rerun, 84 tests in 180.380 seconds, `OK`.
- `python3 tools/glslcpp/check_corpus.py --check`: `check_corpus: ok`.
- `python3 tools/glslcpp/check_semantics.py --check`:
  `check_semantics: bodies ok (212 programs)`.
- `python3 tools/glslcpp/generate_kernels.py --check`: no legacy drift.
- `python3 tools/glslcpp/generate_typed_slice.py --check`: typed slice OK,
  exactly 107 programs.
- `node docs/port-engineering/task-15-oracle-generator.mjs --check`:
  prior artifact verified, 38 vectors, no write.
- Fresh Debug configure/build in
  `/tmp/noisemaker-cpp-task15-debug-qO9NE5`: AppleClang 16.0.0, strict
  `-Wall -Wextra -Wpedantic -Werror -ffp-contract=off`, clean build.
- Fresh Debug direct executable: exactly 95 `PASS` results; Debug CTest 1/1.
- Fresh Release configure/build in
  `/tmp/noisemaker-cpp-task15-release-0OoGF9`: same compiler and strict flags,
  clean build.
- Fresh Release direct executable: exactly 95 `PASS` results; Release CTest
  1/1.

## Changed repository files

- `include/noisemaker/generated/catalog.hpp`
- `include/noisemaker/glsl_runtime.hpp`
- `include/noisemaker/glsl_types.hpp`
- `src/typed_generated/typed_manifest.json`
- `src/typed_generated/typed_slice.cpp`
- `tests/test_generated_kernels.cpp`
- `tests/test_glsl_runtime.cpp`
- `tests/test_glsl_types.cpp`
- `tests/test_semantic.py`
- `tests/test_typed_generator.py`
- `tests/test_typed_slice.cpp`
- `tools/glslcpp/emit_typed_cpp.py`
- `tools/glslcpp/frontend/loop_proof.py`
- `tools/glslcpp/frontend/typed_ir.py`
- `tools/glslcpp/generate_typed_slice.py`
- `tools/glslcpp/typed_slice.json`

## Review boundary

Task 15 is ready for independent review. No Task 16 or later-frontier
repository work is included in this report.
