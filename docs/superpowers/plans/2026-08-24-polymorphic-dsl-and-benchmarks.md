# Polymorphic DSL and Reproducible Benchmarks Implementation Plan

> **Execution rule:** implement tasks on local `main`; this repository forbids
> worktrees, feature branches, and pull requests. Use external temporary build
> and oracle directories and remove them after each bounded run.

**Goal:** Port the `noisemaker-for-cpu` Polymorphic DSL into dependency-free
C++20, execute every currently supported effect graph with exact JS CPU pixel
parity, and benchmark identical source-bound programs on C++, JS CPU, WebGL2,
and WebGPU.

**Architecture:** Generate an ordered typed effect catalog from the frozen CPU
authority. Compile source through typed lexer/parser/semantic stages into an
immutable execution plan. Execute the plan with a resource-owning CPU graph
runtime that binds existing authenticated kernels. Drive all platforms from a
single reproducibility manifest and compare raw top-down RGBA8.

**Technology:** C++20, CMake 3.20+, existing zlib dependency, Python 3 standard
library for orchestration, Node for frozen-authority export, Playwright only in
the upstream shader driver.

**Design:** `docs/superpowers/specs/2026-08-24-polymorphic-dsl-and-benchmarks-design.md`

---

## Task 1: Authenticate the backend census, source closure, and ABI

**Files:**

- Create: `tools/dsl/generate_backend_compatibility.py`
- Create: `src/effects/generated/backend_compatibility.json`
- Create: `tests/test_backend_compatibility.py`
- Modify only if needed to expose existing typed IR data:
  `tools/glslcpp/generate_typed_slice.py`
- Modify only through its generator if its schema changes:
  `src/typed_generated/typed_manifest.json`

**Step 1: Write failing authority and census tests**

Require explicit `--cpu-root` and `--shader-git`. Compute a behavioral lock over
sorted regular files beneath CPU `src/`, `scripts/upstream/source-lock.js`,
`package.json`, and `package-lock.json`. Individually pin CPU package.json
SHA-256 `c7d8aec82725078b4d31d379323901e83bdfba0a0289ff8428beecdac2c9d78a`
and package-lock SHA-256
`724bfaf208346605cae0ce9a74d0e84c76dd3aeb8fedb44fb894ad03c4dad03d`.
Validate upstream commit
`117a236679d1db3ab8f0e278230ece277b57564c`, root tree
`a7a997dfdc807697adba008729dcdfdfcfbaf53c`, source-lock digest
`66f4e9337810ca839dddaba047dadc0c15e903e0f662f189ee6d08ff84fb62c4`,
upstream package.json SHA-256
`109e0617b53eca612d6265672e010744ee3284aea26555eee1f614c3ddc33c8a`,
and upstream package-lock SHA-256
`033762c49845652b36ea91b75653c63ed62c45bd2fb455ab66567ff4b356109f`.

The backend census must prove 213 fragment rows, 211 unique fragment keys, the
two exact duplicate keys `filter/invert:inv` and `synth/solid:solid`, and the
separate scatter key `filter/wormhole:deposit`. A forged duplicate, missing
scatter registration, unclassified binding, output mismatch, or source drift
must fail.

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_backend_compatibility
```

Expected: FAIL because the compatibility generator and manifest do not exist.

**Step 2: Implement no-mutation per-program source closure**

Map each of the 212 frozen corpus rows from
`sources/<namespace>/<effect>/<file>` to
`shaders/effects/<namespace>/<effect>/glsl/<file>` and read pinned blobs with
`git cat-file`, never checkout. Record old/new raw hashes and sizes. The expected
initial classification is 205 `raw_exact`, six `semantic_exact` comment-only
updates, and one `incompatible` key, `filter/text:text`.

For a `semantic_exact` result require two independent comparisons: canonical
GLSL tokens without comments/locations and typed IR serialized without source
spans. If either differs, classify incompatible. Never call arbitrary whitespace
normalization sufficient proof.

**Step 3: Generate typed binding/output/capability ABI**

Derive ABI from the same typed IR consumed by the C++ emitter, not by parsing
generated C++ text. For every fragment key record ordered uniforms with C++
types, samplers, outputs, derivative use, exact output extent, factory, source
hash, and compatibility transform. A single fragment output matches by
canonical slot/cardinality while retaining the graph's logical route name;
MRT requires exact ordered physical output names. For scatter, record its
explicit adapter contract. Classify each required binding source as effect parameter, pass
literal, pass-derived, reserved runtime state, resource, or external texture.

The reserved set includes resolution, full resolution, render scale, tile
offset, time, frame, seed, and delta time. Any binding without a proven source,
any output count above the current executor contract, unsupported draw mode,
or unsupported dimensionality is incompatible even if its key exists.

**Step 4: Canonicalize duplicate factories by evidence**

Keep legacy direct factories public, but emit one graph-canonical entry per
unique program key using source hash, binding ABI, output ABI, and factory
identity metadata. Do not compare function pointers. Inequivalent duplicate
metadata is a generation error.

**Step 5: Make the manifest deterministic and green**

`--check` must regenerate outside the repo and byte-compare. Tests verify every
reference pass has exactly one status and every status has structured reasons.
Run the focused test twice and compare manifest SHA-256.

**Step 6: Commit exact task files**

```bash
git add tools/dsl/generate_backend_compatibility.py src/effects/generated/backend_compatibility.json tests/test_backend_compatibility.py tools/glslcpp/generate_typed_slice.py src/typed_generated/typed_manifest.json
git commit -m "test: authenticate the C++ backend against the CPU authority"
```

## Task 2: Lock catalog provenance and generate typed metadata

**Files:**

- Create: `tools/dsl/export_cpu_catalog.mjs`
- Create: `tools/dsl/generate_effect_catalog.py`
- Create: `include/noisemaker/effects/catalog_types.hpp`
- Create: `include/noisemaker/effects/catalog.hpp`
- Create: `src/effects/generated/effect_catalog.cpp`
- Create: `src/effects/generated/effect_catalog.provenance.json`
- Create: `tests/test_effect_catalog_generator.py`
- Create: `tests/test_effect_catalog.cpp`
- Modify: `CMakeLists.txt`

**Step 1: Write failing generator admission tests**

Test explicit `--cpu-root`, behavioral-lock rejection, upstream-lock rejection,
unknown-schema rejection, `--check`, deterministic byte output, and the ordered
authority counts 205 definitions, 305 passes, and 295 reference program keys.
Consume Task 1's compatibility manifest and derive all backend/executable/
incomplete counts from its statuses rather than hard-coding an upper bound.
Assert the first and last IDs and hash the complete ordered normalized record
stream.

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_effect_catalog_generator
```

Expected: FAIL because the exporter and generated catalog do not exist.

**Step 2: Define the minimum typed catalog model**

Implement ordered `Value`, `DimensionExpression`, `ParameterDefinition`,
`TextureDefinition`, `PassDefinition`, `EffectDefinition`,
`CatalogProvenance`, `ProgramCompatibility`, and `EffectCatalog`. The schema
must retain every observed raw field: parameter define/uniform/zero/enum/
texture/color-mode/CPU-only metadata; pass name/program/count/repeat/
conditions/viewport/blend/draw/output metadata; and effect directory, aliases,
external texture, loop/iteration, and every image/volume/geometry/XYZ/velocity/
RGBA output. Use vectors for observable order and secondary indices only for
lookup. Add native tests for blur ordering, dynamic dimensions, format mapping,
external textures, point outputs, and canonical duplicate resolution.

**Step 3: Implement strict export and generation**

The Node exporter imports the CPU `effectRecords` from the explicit root and
emits canonical JSON. The Python generator validates the complete observed key
schema and CPU behavioral/source-lock provenance, joins Task 1's authenticated
compatibility rows, and emits C++ and provenance JSON. Unknown fields or a
reference pass without exactly one compatibility row terminate generation.
Numeric literals must round-trip JavaScript doubles, including tagged NaN,
infinities, and negative zero in test/oracle serialization.

Run the generator into an external temporary directory first, inspect its
size, then install the intentional files with `apply_patch` or the generator's
explicit output mode. Never write cache files in the repo.

**Step 4: Make the gates green**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_effect_catalog_generator
cmake -S . -B /private/tmp/noisemaker-cpp-dsl-build -DCMAKE_BUILD_TYPE=Release
cmake --build /private/tmp/noisemaker-cpp-dsl-build --parallel
/private/tmp/noisemaker-cpp-dsl-build/noisemaker-cpu-tests
```

Expected: generator test green; native catalog tests green; strict warnings
green.

**Step 5: Commit exact task files**

```bash
git add CMakeLists.txt tools/dsl/export_cpu_catalog.mjs tools/dsl/generate_effect_catalog.py include/noisemaker/effects/catalog_types.hpp include/noisemaker/effects/catalog.hpp src/effects/generated/effect_catalog.cpp src/effects/generated/effect_catalog.provenance.json tests/test_effect_catalog_generator.py tests/test_effect_catalog.cpp
git commit -m "feat: generate the CPU effect catalog for C++"
```

## Task 3: Port the exact DSL lexer and diagnostics

**Files:**

- Create: `include/noisemaker/dsl/error.hpp`
- Create: `include/noisemaker/dsl/token.hpp`
- Create: `include/noisemaker/dsl/lexer.hpp`
- Create: `src/dsl/error.cpp`
- Create: `src/dsl/lexer.cpp`
- Create: `tests/fixtures/dsl/frontend-cases.json`
- Create: `tests/oracles/dsl_frontend_expected.txt`
- Create: `tests/test_dsl_lexer.cpp`
- Create: `tests/test_dsl_frontend_oracle.py`
- Create: `tools/dsl/js_frontend_oracle.mjs`
- Modify: `CMakeLists.txt`

**Step 1: Add red tests from the JS lexer contract**

Cover whitespace, both comments, EOF locations, valid and malformed exponent
forms (`1e`, `1e+`, `1e-`), tagged non-finite/negative-zero values, strings and
escapes, all color lengths, keywords, context-neutral tokens, surface lexemes,
punctuation/operators, unexpected characters, and unterminated strings/comments.
Astral-character cases must place non-BMP input before tokens, within strings
and comments, and before EOF/errors so UTF-8 bytes, Unicode scalars, and UTF-16
positions cannot accidentally agree.

Run native and oracle tests; confirm failure due missing APIs.

**Step 2: Implement source cursor and `DslError`**

Track UTF-8 input bytes separately while exposing JavaScript-compatible UTF-16
index and one-based UTF-16 column; newline resets column to one. Preserve
original lexemes as UTF-8. Make `what()` deterministic and expose structured
location fields.

**Step 3: Implement the ordered lexer**

Port `src/dsl/tokenize.js` rule-for-rule. Do not broaden identifier Unicode or
number grammar. Ensure `render` remains a keyword; contextual acceptance is a
parser responsibility.

**Step 4: Compare canonical token streams to JS**

Use the Node oracle only to generate/verify the checked-in expected stream from
the validated authority root. The Python test invokes the C++ oracle mode and
diffs exact text including locations and errors.

**Step 5: Verify and commit**

Run the focused native/oracle tests plus the full native executable, then
commit with `feat: port the Polymorphic DSL lexer`.

## Task 4: Port the typed parser

**Files:**

- Create: `include/noisemaker/dsl/ast.hpp`
- Create: `include/noisemaker/dsl/parser.hpp`
- Create: `src/dsl/parser.cpp`
- Create: `tests/test_dsl_parser.cpp`
- Extend: `tests/fixtures/dsl/frontend-cases.json`
- Extend: `tests/oracles/dsl_frontend_expected.txt`
- Modify: `tools/dsl/js_frontend_oracle.mjs`
- Modify: `CMakeLists.txt`

**Step 1: Write failing AST and diagnostic tests**

Port every case from the reference `test/dsl.test.js` parser surface, plus
operator precedence, unary nesting, parenthesized values, vector width, dotted
identifiers, read named arguments, mixed arguments, render namespace context,
duplicate render, and surface range failures.

**Step 2: Implement typed AST values and recursive-descent parser**

Represent values with typed nodes and explicit source locations. Preserve call
and argument order. Port reference precedence and contextual rules exactly.

**Step 3: Add canonical AST serialization for tests**

Serialization is a test/inspection adapter, not the runtime data model. Use
stable field and list order and exact double formatting.

**Step 4: Verify and commit**

Run parser, frontend oracle, lexer regression, and full native tests. Commit
with `feat: port the typed Polymorphic DSL parser`.

## Task 5: Implement effect normalization and semantic compilation

**Files:**

- Create: `include/noisemaker/effects/registry.hpp`
- Create: `include/noisemaker/dsl/compiler.hpp`
- Create: `include/noisemaker/graph/execution_plan.hpp`
- Create: `src/effects/registry.cpp`
- Create: `src/dsl/compiler.cpp`
- Create: `tests/test_effect_registry.cpp`
- Create: `tests/test_dsl_compiler.cpp`
- Create: `tests/oracles/dsl_compiler_expected.txt`
- Modify: `tools/dsl/js_frontend_oracle.mjs`
- Modify: `tests/test_dsl_frontend_oracle.py`
- Modify: `CMakeLists.txt`

**Step 1: Write failing registry and compiler tests**

Cover ordered namespace resolution, aliases, every parameter type, defaults,
required values, choices, dotted enums, finite/integer checks, min/max,
surfaces, partial merge behavior, duplicate bindings, domain transitions,
loop balance, generator placement, last-write render selection, malformed-
exponent NaN propagation/rejection, and unknown effects/parameters.

**Step 2: Implement normalization**

Evaluate DSL arithmetic as double. Clone arrays by value. Normalize parameters
in catalog order, apply aliases before lookup, and preserve explicit parameter
names for runtime define behavior. Match JS error types/messages and never
coerce invalid values.

**Step 3: Compile immutable execution plans**

Port `compileDsl` semantics into ordered chains/steps. Add compatibility
validation that reports effect ID and exact per-pass missing/source/ABI/output/
capability reasons from Task 1. Pure inspection may disable the executability
requirement; render paths may not. Preserve which parameters were explicitly
supplied so runtime seed override behavior remains decidable.

**Step 4: Exact plan oracle**

Normalize definitions to IDs and serialize values/source locations. Compare
the complete fixture corpus with JS. Include at least one accepted plan for
each effect domain and exact failed plans for unsupported execution.

**Step 5: Verify and commit**

Run generator `--check`, all DSL tests, full native tests, and strict build.
Commit with `feat: compile DSL into typed CPU execution plans`.

## Task 6: Add a resource-owning graph executor and blur vertical slice

**Files:**

- Create: `include/noisemaker/graph/resource.hpp`
- Create: `include/noisemaker/graph/executor.hpp`
- Create: `include/noisemaker/renderer.hpp`
- Create: `src/graph/resource.cpp`
- Create: `src/graph/executor.cpp`
- Create: `src/renderer.cpp`
- Create: `tests/test_graph_resources.cpp`
- Create: `tests/test_graph_blur.cpp`
- Create: `tests/fixtures/dsl/blur.dsl`
- Create: `tests/oracles/dsl_blur_rgba8.inc`
- Create: `tools/dsl/js_render_oracle.mjs`
- Create: `tests/test_dsl_render_oracle.py`
- Modify: `CMakeLists.txt`

**Step 1: Write red resource lifetime and graph validation tests**

Cover missing producers, read-before-write, duplicate outputs, absent surface
reads, unknown/dynamic dimensions, canonical format mapping, stable texture
pointer lifetime across arena growth, cleanup on binding/execution failure,
and the exact 16,777,216-pixel allocation boundary. Include caller seed/external
surfaces whose original scope ends before binding, then force owning-vector
reallocation to prove the pointee address remains stable.

**Step 2: Implement `GraphResource` and deterministic ownership**

Wrap `Surface` with logical name, format, and extent. Store resources as
`std::unique_ptr<GraphResource>` in an owning arena and map names to stable
pointers. Copy seed surfaces and external textures into the arena at render
start, preserving dimensions/filter. Keep `BoundKernel` per pass invocation.
Quantize immediately after writes. Preserve existing `Surface` and `run_pass`
APIs.

**Step 3: Write the failing exact blur oracle**

Use one DSL file:

```text
search synth, filter
solid(color: #3a7).blur(radiusX: 3, radiusY: 2).write(o0)
render(o0)
```

Require Task 1 to classify both blur programs source- and ABI-compatible.
Generate final top-down RGBA8 from the validated public JS CPU renderer at two
non-square extents. Confirm the C++ test fails before adding executor routing.
Intermediate traces are optional diagnostics because the reference public API
does not expose pass resources.

**Step 4: Implement ordinary multi-pass execution**

Resolve current input, typed dimension expressions, declared resources, pass
textures, uniforms, repeat, conditions, destinations, formats, and final output.
Materialize the complete typed uniform-source ABI, including resolution,
fullResolution, renderScale, tileOffset, time, frame, seed, and deltaTime.
Apply the reference global-seed override only when effect seed was defaulted.
Bind the exact canonical program and reject any missing binding before entry.

**Step 5: Make blur exact and commit**

Require zero RGBA8 byte mismatches and retain optional bit-exact checkpoints
only where an independently source-bound reference trace exists. Run ASan/
UBSan in an external build in addition to strict Release.
Commit with `feat: execute multipass DSL graphs on CPU`.

## Task 7: Expand execution across the census-admitted effect intersection

**Files:**

- Create: `tests/fixtures/dsl/executable-corpus.json`
- Create: `tests/oracles/dsl_executable_corpus.sha256`
- Create: `tests/test_dsl_executable_corpus.py`
- Create: `tools/dsl/generate_executable_corpus.mjs`
- Extend: `src/graph/executor.cpp`
- Extend: `tests/test_graph_resources.cpp`
- Modify generated catalog only through its generator if authority data changes

**Step 1: Generate deterministic default programs**

For each census-admitted definition, choose a domain-correct starter/input,
explicit deterministic seed, non-square small extent, and legal parameters.
Include multi-pass, conditions, string repeat/count, custom viewport, format,
secondary surface, external texture, explicit linear-filter sampling, and
parameter polymorphism buckets. Record
every exclusion with structured missing/source/ABI/output/capability reasons.
The count is generated; it is never copied from the pre-DSL static estimate.

**Step 2: Add a red JS-to-C++ corpus comparer**

The comparer invokes both renderers, compares dimensions and every RGBA8 byte,
reports first mismatch coordinate/channel and hashes, and cannot update oracle
data. Use bounded batches so a failure identifies one effect without leaving
large raw frames in the repo.

**Step 3: Implement executor features by failing bucket**

Add only behavior demanded by an admitted effect. For each bucket, diagnose
the first JS/C++ divergence at the earliest pass/resource, add a focused native
regression, then rerun the bucket. Never add tolerances or normalize values to
hide a mismatch.

**Step 4: Integrate wormhole scatter explicitly**

Route the authenticated `filter/wormhole:deposit` pass through the existing
scatter registry. Validate draw mode and output contract before invocation.
Make executor initialization register built-in adapters (or require an explicit
initialized registry) and prove dispatch without test-side hidden setup.
Ordinary kernel fallback for scatter is prohibited.

**Step 5: Resolve source-incompatible admitted candidates**

`filter/text:text` begins source-incompatible against `117a236...`. Either port
and independently review the pinned source before admitting it, or keep it
failed closed with an exact compatibility reason. Comment-only source updates
are admitted only through Task 1's dual semantic proof. Do not alter counts to
make the target appear met.

**Step 6: Verify the full generated intersection and commit**

Run the exact corpus twice and require identical manifest hashes, then run the
full strict native/Python/generated matrix. Commit with
`feat: render the supported DSL effect corpus exactly`.

## Task 8: Add public renderer API, inspection, and CLI

**Files:**

- Create: `tools/noisemaker_cpp_main.cpp`
- Create: `include/noisemaker/render_result.hpp`
- Create: `src/render_result.cpp`
- Create: `tests/test_renderer.cpp`
- Create: `tests/test_cli.py`
- Extend: `tests/cmake_package_consumer/main.cpp`
- Modify: `CMakeLists.txt`

**Step 1: Write failing API, CLI, and install-consumer tests**

Test defaults, explicit width/height/time/frame/seed/one-shot mode, seed
surfaces, external textures, copy/ownership semantics, missing external-input errors, stdin/file
DSL, raw RGBA8 and PNG output, inspect canonical plan, catalog availability,
deterministic errors, no partial output on failure, the exact surface-pixel cap,
and installed package DSL rendering.

**Step 2: Implement API and CLI**

Expose `Renderer::render`. Keep timing metadata separate from deterministic
output. Implement `render`, `inspect`, `catalog`, and private
`benchmark-driver` modes without adding a general JSON dependency; canonical
serialization is narrow and owned.

**Step 3: Verify and commit**

Run CLI, install/package consumer, exact render corpus, and full strict matrix.
Commit with `feat: expose the C++ DSL renderer and CLI`.

## Task 9: Build the source-bound CPU reproducibility harness

**Files:**

- Create: `bench/programs/manifest.json`
- Create: `bench/programs/solid.dsl`
- Create: `bench/programs/blur.dsl`
- Create: `bench/programs/showcase.dsl`
- Create: `bench/drivers/cpu_reference.mjs`
- Create: `bench/run.py`
- Create: `bench/schema/result.schema.json`
- Create: `tests/test_benchmark_manifest.py`
- Create: `tests/test_benchmark_cpu_exact.py`

**Step 1: Write red manifest and pin tests**

Reject changed DSL bytes, missing hashes, mismatched CPU behavioral/source
locks, incompatible backend rows, unknown runtime versions, insufficient sample
counts, and mixed timing modes. Require the same render options for all drivers.

**Step 2: Implement C++ and JS CPU drivers**

Each driver emits raw top-down RGBA8 to an external result path and a canonical
metadata record. The common `compile_and_render` mode invokes each public
top-level render API per sample because JS CPU recompiles DSL and includes
result clone/pool cleanup. Process startup and hashing remain outside timing.
Use five warmups and at least 30 measured renders. A C++ `render_only` mode may
be reported separately but must not be presented as a JS comparison.

**Step 3: Implement the custom exact comparer**

Compare raw bytes directly, calculate mismatch count, first mismatch, maximum
channel delta, per-platform SHA-256, median, p95, and megapixels/second. A CPU
mismatch exits nonzero and preserves only a small diagnostic record, not both
full frames.

**Step 4: Verify and commit**

Run correctness-only twice and compare result manifests after excluding timing
samples. Run one bounded benchmark smoke. Commit with
`feat: add source-bound CPU DSL benchmarks`.

## Task 10: Add pinned upstream WebGL2 and WebGPU drivers

**Files:**

- Create: `bench/drivers/upstream_shader.mjs`
- Create: `bench/drivers/upstream_page.html`
- Extend: `bench/run.py`
- Extend: `bench/schema/result.schema.json`
- Create: `tests/test_benchmark_shader_pin.py`
- Create: `tests/test_benchmark_shader_smoke.py`

**Step 1: Prove the source mismatch gate**

Point the harness at the live upstream checkout and assert it refuses the
known digest mismatch. Require Git object `117a236...`, archive its full root
tree `a7a997df...` into an external temporary directory, and validate the
source lock, root/browser module closure, manifest, package.json, and the pinned
Playwright 1.62.1 package lock before browser startup. If the commit object or
runtime dependencies are unavailable, fail without mutating either checkout.

Install the archived dependency tree in that external root using
`npm ci --ignore-scripts` with an external npm cache. Resolve a Playwright-
compatible Chromium from an explicit external `PLAYWRIGHT_BROWSERS_PATH`;
install it into that disposable root if needed, record package integrity,
browser version, and executable SHA-256, and remove the entire root after the
bounded run. Dependency or browser mismatch fails before page launch.

**Step 2: Add direct deterministic browser rendering**

Launch a fixed-size page, construct upstream `CanvasRenderer`, load its
manifest, compile the exact DSL bytes, disable RAF, and use a fresh renderer to
capture the documented first frame at pinned time before any warmup. Read the
physical output surface. Remove only documented dynamic fields from graph
hashing. Never use screenshots or PNG hashes.

Normalize and compare CPU/shader graph semantics before pixels: effect IDs,
explicit/default parameters, program/pass order, routes, dimensions, formats,
repeat/conditions, and final surface. If exact correspondence cannot be proven,
label the result `same-dsl-bytes` rather than semantic parity.

**Step 3: Separate correctness and timing paths**

Correctness reads raw top-down RGBA8 from its fresh renderer. Benchmarking uses
a separate fresh renderer, exactly five recorded warmups and at least 30
samples; frame progression is recorded and never reused as a frame-zero oracle.
Timing provides fenced per-frame latency, batched throughput, and readback-
inclusive modes as separate records. Capture browser, Playwright, WebGL, and
WebGPU provenance, requested/actual formats, float render/filter capabilities,
and any fallback. Reject format/capability substitution. Refuse the currently
observed Playwright lock/install mismatch until dependencies are reconciled.

**Step 4: Compare all platforms and commit**

Run the small common program corpus on C++, JS CPU, WebGL2, and WebGPU. Require
C++/JS exactness. Record GPU exact differences without tolerance or false
parity claims. Commit with `feat: benchmark identical DSL on upstream shaders`.

## Task 11: Full verification, review, and handoff to remaining kernels

**Files:**

- Modify: `README.md`
- Create: `docs/POLYMORPHIC-DSL.md`
- Create: `docs/BENCHMARKING.md`
- Create: `docs/port-engineering/REMAINING-PROGRAMS.md`
- Update: `docs/port-engineering/NEXT_CODING_AGENT_HANDOFF.md`

**Step 1: Repair documentation against live evidence**

Document exact effect/program counts, supported and failed-closed scopes, API,
CLI, authority pins, benchmark protocol, and generated-file procedure. Remove
stale 197/199 claims only after the new live census test supplies the values.

**Step 2: Run the complete bounded matrix**

Use fresh external Release, Debug, ASan, and UBSan builds; generator `--check`;
all Python tests with bytecode disabled; native CTest; package-consumer install;
the full census-admitted effect corpus twice; and all-platform reproducibility
smoke. The recorded census must reconcile fragment, scatter, source, ABI,
capability, executable, and incomplete totals exactly.
Record exact commands, counts, hashes, compiler versions, and disk usage.

**Step 3: Run formal code review**

Invoke `superpowers:requesting-code-review` as explicitly authorized. Address
every important finding using `superpowers:receiving-code-review`, rerun the
affected focused gates, then rerun the complete matrix. Request an independent
final re-review.

**Step 4: Commit the verified DSL frontier**

Stage exact task files only and commit with a message describing executable
scope and source-bound parity. Do not amend the pre-DSL checkpoint.

**Step 5: Continue through the remaining-kernel frontier**

Use the generated `REMAINING-PROGRAMS.md` manifest as the queue for every
missing or incompatible program key. Each landed key must pass source
authentication, binding/output/capability admission, native kernel tests, DSL
graph integration, and exact full-program pixel parity before its owning effect
becomes executable.

**Step 6: Publication gate**

Only after all requested coding and pixel parity are complete: remove or
rewrite private engineering history from the intended public tree, verify MIT
OSS metadata and clean-room package consumption, perform the authorized public
repository creation/push in the usual Noise Factor pattern, and verify the
public clone/build/test path. No branch, worktree, PR, or force push.
