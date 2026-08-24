# Task 14 report: source-const scalar-local lowering slice

Date: 2026-08-10  
Repository: `.`  
Pinned corpus revision: `a024dc3a960cc44af454abc7aebce50456c194e6`

## Result

Task 14 is complete and stops at its independent-review boundary. Exactly six
typed CPU factories were added:

1. `filter/pixelSort:finalize`
2. `filter/pixelSort:prepare`
3. `filter/skew:skew`
4. `filter/tetraCosine:tetraCosine`
5. `filter/tile:tile`
6. `synth/osc2d:osc2d`

Each entry has the authoritative empty define map `{}`. The typed generated
slice is now exactly 71 sorted programs. Together with the two immutable
Task-5 factories, the public catalog is exactly 73 sorted unique factories,
leaving exactly `212 - 73 = 139` corpus programs without a native public
factory. No Task 15 or later-frontier work was performed.

## Source-const proof and lowering

The validator admits only non-interface, initialized, source-`const`
declarations of exact scalar type `float`. It does not add a general `globals`
capability. Initializers retain typed IR and are validated before the normal
capability audit. The admitted initializer expression grammar is deliberately
narrow: numeric literals, stable-symbol references to earlier admitted
source constants, unary `+`/`-`, and binary `+`, `-`, `*`, `/`.

Stable symbol IDs, rather than text spellings, form the dependency graph.
Declaration order proves that every dependency points backward and therefore
that the graph is acyclic; forward references and dependency cycles are
rejected. A whole-program identity-based audit walks every helper and `main`
and rejects direct or compound assignments, prefix or postfix increment and
decrement, and writes through swizzles, indexes, or members rooted in an
admitted source constant.

The emitter independently revalidates initializer IR and the write audit. For
each generated helper or `pixel` function, it computes the transitive
dependency closure of only the source constants referenced by that function
and emits one ordinary function-local `const double` per dependency in source
order. Helpers and `pixel` are localized independently, and unused constants
are not emitted. The generated translation unit contains ten indented
function-local `PI`/`TAU` declarations and no unindented namespace/global or
`static` source-constant declaration. There is no ambient lookup, function-
static state, or C++ static storage.

The existing numeric-literal emitter remains the only path used for constant
initializers, preserving Float32 construction/storage behavior. No
compatibility transform, numeric exception, new dependency, placeholder
kernel, or hand-translated shader body was added.

Malformed-IR tests exercise forward references, a two-node cycle, direct and
compound assignment, prefix/postfix increment and decrement, and writes
through swizzles, indexes, and members. Each malformed case is rejected by
both the validator and emitter audits. Semantic tests also lock initializer
retention, stable symbol identity, source order, and read-only use.

## Runtime boundary found by native compilation

The first native build exposed one existing runtime overload boundary used by
the generated tetra-cosine body: `pow(Vec3, FloatExpr<3>)`. A failing compile
reproduced the exact AppleClang overload error before implementation. The
runtime now delegates that combination to the existing vector `pow` semantics
by materializing the exponent expression as `Vec<N, float>`. Compile-time
availability and runtime component results `(2, 3, 4)` are covered by the
GLSL runtime tests. This is an expression-materialization overload, not a new
language capability.

## Bindings and effect truth

All six factories expose their exact authored uniform and sampler signatures.
Every required uniform is tested for absence and a representative wrong type;
all six required sampler positions are tested independently for absence. The
tests cover 55 distinct required uniforms and fail closed.

Pixel-sort `prepare` remains only the caller-fed luminance preparation pass,
and `finalize` remains only the caller-fed final pass consuming both sorted
`inputTex` and `originalTex`. Rank, brightest, and gather/sort passes remain
explicitly unported and reject lookup. Skew, tetra-cosine, and tile are
independent one-pass filters over caller-provided input. Osc2d is an
independent texture-free generator. No render-graph adapter was added.

## Frozen oracle evidence

The accepted artifact is
`docs/port-engineering/task-14-oracles.json`, SHA-256
`3d77b3d357e697d41fdb6842f78dbc403afa3f317f3c76708e94923b2b52a104`.
Its provenance is schema `noisemaker-task14-canonical-oracles-v1`, pinned
revision `a024dc3a960cc44af454abc7aebce50456c194e6`, Node `v24.7.0`, and API
`canonicalKernelFactories+bindCanonicalKernel+runPass+Surface`.

All 30 unique `(key, variant)` rows are embedded and pass exactly: 4 prepare,
4 finalize, 4 skew, 5 tetra-cosine, 5 tile, and 8 osc2d. Every 9x7 top-down
render matches its exact little-endian Float32 SHA-256, RGBA8 SHA-256, and
twelve exact Float32-bit probes at pixel indices 0, 31, and 62, then repeats
byte-identically. The canonical resolution/aspect overwrite and per-case
time, seed, tile-offset, full-resolution, and scalar bindings are preserved.
Formula surfaces use the frozen tags and dimensions: 1 at 5x3, 23 at 4x6,
37 at 7x2, and 53 at 3x5. Tile and osc2d additionally assert the required
all-alpha-one behavior.

Prior oracle suites remain green, including Task 11's 94 cases, Task 12's 120
cases, and Task 13's 21 cases.

## Generated and immutable hashes

- Task 14 brief: `8d529ac797cc3330da2d17a34eafe14806fe569680d6366513d10d354461d62a`
- Task 14 oracle artifact: `3d77b3d357e697d41fdb6842f78dbc403afa3f317f3c76708e94923b2b52a104`
- `src/typed_generated/typed_slice.cpp`: `dad6e98f28ed499dc1892c3366173b39dbd9e94718ab97af2118c698d1346546`
- `src/typed_generated/typed_manifest.json`: `5c4f456960843241308a2736a61f7ba5ca808839de7c87ec40d5b67bce38eab1`
- Immutable `src/generated/synth_solid.cpp`: `4a88533b90ce71268461f2d6fc2ad71025deb830e403c878b424b7b0ef822363`
- Immutable `src/generated/filter_invert.cpp`: `06dd8cf0dacb86fb4ae11ebc822fd8103f648bc98d8272bc526c4507b2d4f1b7`

The generated manifest records the same typed-translation-unit SHA-256 shown
above.

## Verification

All commands completed with exit status 0:

- `python3 -m unittest discover -s tests -p 'test_*.py' -v`: `Ran 71 tests
  in 342.429s`, `OK`.
- `python3 tools/glslcpp/check_corpus.py --check`: `check_corpus: ok`.
- `python3 tools/glslcpp/check_semantics.py --check`:
  `check_semantics: bodies ok (212 programs)`; its locked report preserves
  622 metadata candidates and 646 successful variants.
- `python3 tools/glslcpp/generate_kernels.py --check`: legacy generated output
  has no drift.
- `python3 tools/glslcpp/generate_typed_slice.py --check`: typed slice OK,
  exactly 71 programs.
- Fresh Debug configure/build in
  `/tmp/noisemaker-cpp-task14-debug-019fea3a`: AppleClang 16.0.0, strict
  `-Wall -Wextra -Wpedantic -Werror -ffp-contract=off`, clean build.
- Fresh Debug direct executable: exactly 88 `PASS` results.
- Fresh Debug CTest: 1/1 passed, 0 failed.
- Fresh Release configure/build in
  `/tmp/noisemaker-cpp-task14-release-019fea3a`: AppleClang 16.0.0, the same
  strict flags, clean build.
- Fresh Release direct executable: exactly 88 `PASS` results.
- Fresh Release CTest: 1/1 passed, 0 failed.

The public catalog test locks 73 sorted unique factories and 139 remaining
public-unported corpus programs. The generator tests lock the six-key Task 14
set, empty defines, 71/73/139 counts, and the unchanged capability/type
vocabulary.

## Stop boundary

Task 14 is ready for independent review. No Task 15 repository changes or
later language-frontier work are authorized or included.
