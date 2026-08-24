# Polymorphic DSL and Reproducible Benchmark Design

Date: 2026-08-24

Status: approved for implementation

Behavioral authority: `noisemaker-for-cpu`

Shader comparison platform: pinned `noisemaker` upstream snapshot

## Outcome

`noisemaker-for-cpp` will accept the same Polymorphic DSL source as
`noisemaker-for-cpu`, compile it into a dependency-free typed C++ execution
plan, and render that plan through the already authenticated generated C++
kernels. A reproducibility harness will run the exact same DSL bytes on C++,
the JavaScript CPU reference, and the upstream shader runtime, producing
source-bound correctness and performance records.

The DSL catalog describes all 205 reference definitions. The current backend
has 213 fragment-catalog rows, 211 unique fragment program keys, and one
separately registered scatter program (`filter/wormhole:deposit`). The two
duplicate fragment rows are legacy aliases for `filter/invert:inv` and
`synth/solid:solid`. This gives an upper-bound intersection of 212 unique
backend programs and 167 definitions, but those numbers are not an admission
claim: a generated compatibility census must first prove source closure,
binding ABI, output ABI, draw mode, dimensionality, and runtime capability for
every pass. The executable count is derived from that census and may be lower.

Rendering fails closed before execution if any pass is absent or incompatible;
it never skips a pass, substitutes a similar effect, or infers capability from
key presence alone. The same graph executor becomes the integration seam for
incompatible and missing programs as they are ported.

## Authority and pinning

The source of behavioral truth is the exact `noisemaker-for-cpu` snapshot used
to generate the C++ catalog and oracle fixtures. The catalog generator records:

- a behavioral-lock SHA-256 over the complete ordered `noisemaker-for-cpu`
  runtime authority under `src/`, the upstream source-lock module, and package
  manifest/lock;
- the CPU repository revision when available, or the behavioral-lock identity
  when the frozen authority is not a Git checkout;
- the CPU upstream snapshot revision;
- the CPU source-lock SHA-256;
- the generated catalog SHA-256;
- the ordered counts of definitions, passes, and unique program keys.

At design time the CPU snapshot reports upstream revision
`117a236679d1db3ab8f0e278230ece277b57564c` and source-lock digest
`66f4e9337810ca839dddaba047dadc0c15e903e0f662f189ee6d08ff84fb62c4`.
The live upstream shader checkout has different content and must not be used
for an authority claim. The benchmark runner therefore accepts explicit
`--cpu-root` and `--shader-git` paths. It materializes commit `117a236...` with
`git archive` into an external temporary directory only after the commit object
is present, then records and verifies the commit tree, source-lock digest,
browser/runtime source closure, manifest hash, and package-lock hash. If the
content-addressed commit or any complete browser dependency source is absent,
the shader lane fails before browser startup. The live upstream checkout is
never mutated.

The archived shader dependency tree is installed with pinned npm into an
external temporary root (`npm ci --ignore-scripts` with an external cache).
The Playwright package version/integrity and the selected Chromium version and
executable hash are recorded. A compatible browser may be installed into an
external `PLAYWRIGHT_BROWSERS_PATH` for the bounded run and is removed with that
root; an absent or mismatched dependency/browser fails before rendering.

The existing C++ programs are separately authenticated against that CPU pin.
The compatibility manifest records, per program, the old corpus source hashes,
the pinned source hashes, a token/typed-IR semantic hash, generated factory
hash, binding ABI, output ABI, and explicit scatter status. Comment-only raw
source drift is compatible only when independently normalized token and typed
IR hashes are identical. Any semantic drift makes the key unavailable until it
is regenerated and its pixel oracles are renewed.

## Scope

In scope:

- exact CPU DSL tokenization, parsing, diagnostics, bindings, partials,
  arithmetic, vectors, colors, search-order lookup, chain validation, surface
  reads/writes, and render selection;
- a checked-in, deterministic, typed effect catalog generated from the CPU
  reference's ordered effect records;
- typed parameter normalization, defaults, aliases, enums, choices, range
  checks, and surface references;
- ordinary and multi-pass image graphs, per-resource dimensions and formats,
  repeat/condition handling, and the existing wormhole scatter adapter;
- exact C++ versus JavaScript CPU RGBA8 parity for every admitted DSL fixture;
- same-source WebGL2 and WebGPU correctness captures and performance reports;
- an installed C++ API and a `noisemaker-cpp` command-line renderer/inspector;
- deterministic corpus, output, graph, and environment manifests.

Out of scope for the first execution boundary, but explicitly represented and
failed closed:

- every program the generated backend compatibility census classifies missing
  or incompatible, including volume/3D, feedback simulations, point-state
  pipelines, and loop render programs;
- JavaScript closures, MIDI, audio automation, or arbitrary runtime scripting;
- copying Qt, OpenGL, or shader-compilation runtime code;
- treating a performance number as a release gate before stable machine and
  browser baselines exist.

## Architecture

```text
canonical CPU effect records              Polymorphic DSL source
            |                                      |
   deterministic generator                    lexer/parser
            |                                      |
   typed constexpr-like catalog          semantic compiler
            |                                      |
            +----------> typed execution plan <----+
                                   |
                         availability validation
                                   |
                      resource-owning graph executor
                                   |
                   generated catalog / BoundKernel / scatter
                                   |
                         top-down CPU Surface RGBA8
```

The Qt port is a semantic reference for ordered tokens, diagnostics, typed IR,
and compiler staging. It is not a runtime dependency. The C++ implementation
uses standard C++20 containers and strings and keeps Qt/JSON/OpenGL out of the
library.

### Public layers

1. `noisemaker::dsl`
   - `tokenize(source, source_name)`
   - `parse(source, source_name)`
   - `compile(source, registry, options)`
   - stable source locations and `DslError`
2. `noisemaker::effects`
   - ordered `EffectCatalog` and `EffectRegistry`
   - definitions, parameters, passes, textures, aliases, and provenance
3. `noisemaker::graph`
   - immutable `ExecutionPlan`
   - `GraphExecutor` over owned CPU resources
4. `noisemaker::Renderer`
   - `render(dsl, RenderOptions)` returning `RenderResult`
   - default dimensions 512 by 512, time 0, frame 0, seed 1, and one-shot mode
     `ready`, matching CPU JS
   - owned-by-value seed surfaces and external textures; the executor copies
     them into stable render-owned resources before binding
5. `noisemaker-cpp`
   - `render`, `inspect`, `catalog`, and `benchmark-driver` subcommands

The pure compiler may produce a plan containing unavailable effects when
`CompileOptions::require_executable` is false, which supports catalog and
porting tools. `Renderer` and the CLI always require executable plans.

## Typed model

The catalog uses explicit ordered structures rather than a runtime JSON tree.
The core value type supports null, boolean, JavaScript Number-compatible
double, string, and recursively ordered arrays. Objects with a schema are
represented by named fields or ordered key/value vectors.

Required model types include:

- `SourceLocation`, `Token`, and typed AST nodes;
- `Value`, `SurfaceReference`, and parameter values;
- `ParameterDefinition` with type, default, choices, enum, min/max, zero,
  `define`, `uniform`, `texture`, `colorModeUniform`, and `cpuOnly`;
- `DimensionExpression` for input size, screen size, literal, parameter,
  parameter default, power, and screen division;
- `TextureDefinition` with typed width/height expressions and canonical format;
- `PassDefinition` with name, program, ordered inputs/outputs/uniforms,
  conditions, count, repeat, viewport, draw mode, draw buffers, and blend;
- `EffectDefinition` with directory, namespace, function, domain, kind,
  parameters, aliases, passes, resources, external texture, image/volume/
  geometry/XYZ/velocity/RGBA outputs, iteration, and loop metadata;
- `ProgramCompatibility` with canonical factory, source and semantic hashes,
  typed binding sources/types, outputs, capabilities, and rejection reasons;
- `CompiledStep`, `CompiledChain`, and `ExecutionPlan`.

All catalog and plan order is observable and preserved with `std::vector`.
Hash maps may be used only as secondary indices whose iteration order is never
serialized or used for positional binding.

## DSL parity rules

The CPU implementation's `src/dsl` directory is the exact grammar authority.
Notable rules include:

- required `search` directive and ordered namespace resolution;
- context-sensitive acceptance of `render` as a search namespace;
- `o0` through `o7` surface references only;
- JavaScript Number evaluation for unary and binary arithmetic;
- left-to-right binding evaluation;
- callable partials with positional append and named overwrite semantics;
- no mixing named and positional arguments;
- enum member lookup using the final dotted path component;
- exact color expansion for `#RGB`, `#RRGGBB`, and `#RRGGBBAA`;
- generator, image, volume, and loop domain validation;
- render defaults to the last written surface.

Diagnostics include source name, one-based line and column, and a source index.
Index and column both advance in UTF-16 code units exactly like JavaScript;
newline resets column to one. UTF-8 byte offsets are tracked separately and
are never substituted for observable positions. Astral-character fixtures
cover tokens, strings, comments, EOF, and errors. Error classes and message
bodies are compared against the JS oracle; no generic parse failure replaces a
more specific reference error.

The authority lexer deliberately accepts malformed exponent lexemes such as
`1e`, `1e+`, and `1e-`, whose JavaScript Number value is `NaN`. The test
serializer uses tagged canonical values (`number:NaN`, positive/negative
infinity, and negative zero) rather than invalid JSON numbers. Parameter
normalization then rejects non-finite values exactly where the reference does.

## Catalog generation

Developer tooling imports the frozen CPU `effectRecords` with Node and emits
checked-in C++ source plus provenance and backend-compatibility manifests.
Generation is allowed only through explicit authority paths, validates both
the CPU behavioral lock and upstream source lock first, enumerates every raw
schema key, and rejects unknown fields. This prevents a new upstream pass,
parameter, output, or resource feature from being silently discarded.

`--check` regenerates into an external temporary directory and byte-compares
the checked-in catalog. The generator's authority census pins:

- 205 effect definitions;
- 305 ordered pass rows;
- 295 unique reference program keys;
- 213 fragment factory rows and 211 unique fragment keys;
- the two named legacy duplicate rows;
- one separately registered scatter key;
- 205 raw-exact program sources, six token/typed-IR-equivalent comment-only
  source updates, and one initially incompatible source (`filter/text:text`)
  against upstream commit `117a236...`;
- derived counts of source-compatible programs, ABI-compatible programs,
  executable definitions, incomplete definitions, and exact rejection reasons.

Counts are evidence, not the only gate: ordered IDs, normalized field values,
and the full generated output are hashed and compared.

## Graph execution

`GraphExecutor` owns every transient surface for the duration of a render.
`Bindings::set_texture` remains non-owning, so resources live in
`std::vector<std::unique_ptr<GraphResource>>`; vector reallocation never moves
the pointed-to resource. Named lookup stores non-owning pointers into that
stable arena. Seed surfaces and external textures are copied into the arena at
render start, preserving dimensions/filter while preventing caller lifetime or
mutation from invalidating a bound pass. A `GraphResource` wraps `Surface`
with format, extent, logical name, and lifetime metadata; `Surface` itself
remains a simple pixel buffer.

Every top-level and derived allocation enforces the reference maximum of
16,777,216 pixels before multiplication or allocation. The exact boundary is
accepted; one pixel above it is rejected with a deterministic error.

For each effect step the executor:

1. resolves defaulted and explicit parameters;
2. creates the effect resource table from current input, referenced surfaces,
   and declared textures;
3. evaluates pass conditions and repeat counts;
4. resolves typed dimension expressions and maps reference formats
   (`rgba16float`, `rgba8unorm`, `rgba32float`) to C++ formats, rejecting
   unknown names;
5. resolves input textures and a typed uniform-source ABI in reference order;
6. binds the exact canonical generated program key;
7. runs the pass at its declared extent;
8. quantizes into the declared texture format immediately after the pass;
9. replaces the named resource and releases resources only after last use;
10. publishes the effect output to the chain.

Uniform sources are explicit: effect parameter, pass literal, pass-derived
value, named resource, external texture, or reserved runtime value. Reserved
runtime state includes the exact generated ABI for resolution, full resolution,
render scale, tile offset, time, frame, seed, and delta time. If an effect has a
default `seed` and DSL did not explicitly supply it, the top-level render seed
overrides that default exactly as in CPU JS. Before binding, the executor proves
every required typed uniform/sampler is populated and no required output or
capability is unsupported.

The first vertical slice, only after its source and binding ABI pass the new
compatibility census, is `synth/solid -> filter/blur -> write(o0)`, because
blur proves defaults, two-pass routing, an `rgba8unorm` intermediate, dynamic
kernel binding, nearest/default sampling, and final exact pixels. A separate
corpus fixture explicitly marks a texture linear before claiming linear-filter
parity. The executor then
expands over the entire census-admitted definition set. Wormhole's point
deposit pass uses the existing explicit scatter registry; ordinary fragment
execution never pretends to implement scatter. `GraphExecutor` initializes the
built-in scatter catalog itself (or accepts an explicitly initialized registry)
so tests and callers cannot accidentally rely on hidden setup.

Duplicate legacy catalog aliases are resolved by generated source and ABI
metadata before graph lookup. Direct legacy factories remain public for
compatibility, but the graph uses one explicit canonical map. Function-pointer
equality is never used as a semantic test; an inequivalent duplicate is a
generation error.

Single-output fragment passes compare backend outputs by canonical slot and
cardinality: the graph retains the authority's logical output route name while
the physical C++ `Vec4` slot is index zero regardless of whether upstream calls
it `color`, `fragColor`, or another single name. MRT requires exact ordered
physical output names and is incompatible until a matching multi-output ABI
exists.

## Correctness corpus

Fixtures are data, not hand-coded C++ test cases. Each fixture records:

- exact DSL bytes and SHA-256;
- source name, dimensions, time, frame, seed, and optional seed surfaces;
- normalized compiler plan from the JS CPU authority;
- top-down raw RGBA8 bytes or a source-bound byte hash;
- CPU behavioral lock, upstream source lock, backend compatibility, and
  catalog hashes;
- whether execution is admitted or the exact expected diagnostic.

The suite has three levels:

1. frontend corpus: tokens, AST, compiled plan, and diagnostics;
2. vertical render corpus: focused programs proving each executor feature;
3. catalog render corpus: a deterministic default program for every executable
   definition plus adversarial explicit-parameter programs for polymorphism.

C++ versus JavaScript CPU is a hard exact gate: dimensions equal, raw byte
SHA-256 equal, mismatch count zero, maximum channel delta zero. The required
gate uses public final output because the reference exposes no pass trace;
optional diagnostic drivers may expose source-bound intermediate resources but
cannot replace final exactness or modify the authority. Fixtures
are regenerated only from a validated frozen authority root; comparison code
cannot rewrite expected output.

## Cross-platform reproducibility harness

One manifest drives all platforms. For each program the harness validates the
DSL hash and source pins, then invokes:

- the installed or just-built `noisemaker-cpp benchmark-driver`;
- a Node driver calling `CpuRenderer.render` in `noisemaker-for-cpu`;
- a browser driver compiling the same source with upstream `CanvasRenderer`
  and reading the physical output surface directly from WebGL2 or WebGPU.

Before pixels, normalized CPU and shader plans must agree on effect IDs,
explicit/default parameters, program keys, pass order, resource names/routes,
dimensions, formats, repeat/condition behavior, and final surface. If the two
runtime graph schemas cannot establish those relations, the record is labeled
only `same-dsl-bytes`, not semantic or same-source parity.

Canvas screenshots and PNG byte hashes are prohibited. All correctness hashes
cover raw top-down RGBA8 bytes. Dynamic fields such as `compiledAt` are removed
from normalized graph serialization before hashing.

The initial corpus is stateless and uses the common executable intersection,
256 by 256 pixels, normalized time 0.25, frame 0, and explicit deterministic
seeds. Correctness capture uses a fresh compiled renderer and captures its first
documented frame before benchmark warmups. Stateful fixtures, after their
kernels exist, specify their entire frame protocol, including renderer reset,
settle-frame count, time progression, and captured frame.

Each GPU result records requested and actual formats, float renderability and
filtering extensions/features, adapter capabilities, and any substitution. A
missing capability or format fallback rejects the parity run before output
comparison.

The harness always computes exact CPU-to-C++ and GPU-to-authority differences.
GPU arithmetic differences are reported, never normalized away or accepted as
CPU parity. A program with a GPU mismatch remains benchmarkable but is clearly
marked correctness-failing and cannot support a cross-platform parity claim.

## Benchmark protocol

Performance is reproducible evidence in v1, not a fixed release threshold.
Correctness remains blocking. Stable host/browser baselines can later promote
explicit regressions to gates without redesigning the record format.

The common CPU comparison mode is `compile_and_render`: both C++ and JS call
their public top-level render API for every sample, because JS
`CpuRenderer.render` recompiles DSL and includes result cloning and pool cleanup
in its elapsed time. It uses five warmups, at least 30 samples, and reports
median, p95, total pixels, megapixels per second, pass count, and output hash.
Process startup, PNG encoding, and correctness hashing remain outside timing.
A separate C++ `render_only` record is allowed but is never compared to a JS
render-only number until the reference exposes an execute-plan API.

GPU uses a recorded five warmups and at least 30 samples, with a separate fresh
renderer from correctness capture. It reports two separate modes:

- fenced per-frame latency;
- batched submission throughput with one final fence.

Readback-inclusive timing is a third separate measurement. RAF frame rate is
not used. The record includes OS, CPU architecture, compiler and flags, Node,
browser, Playwright, WebGL vendor/renderer, WebGPU adapter/device, dimensions,
all source/DSL/graph/output hashes, warmup/sample counts, and raw samples.

## Safety and repository hygiene

- Builds, unpacked reference snapshots, browser profiles, screenshots, raw
  frames, and temporary generated trees live outside the repository and are
  removed after bounded runs.
- Only small, intentional, source-bound fixtures are committed.
- No worktrees, feature branches, or pull requests are used.
- Every implementation commit stages exact owned files on local `main`.
- Public release waits for full exact-pixel verification, formal code review,
  addressed findings, publication cleanup, MIT metadata, and the separately
  authorized repository push.

## Acceptance

The DSL frontier is complete when:

1. CPU behavioral lock, upstream source lock, per-program source closure, and
   backend ABI/capability admission are deterministic and verified;
2. the full frontend/compiler oracle corpus is exact;
3. all admitted C++ DSL programs render byte-identically to JS CPU;
4. every unsupported effect fails before execution with exact missing keys;
5. installed-package consumers can compile and render DSL;
6. same-source C++, JS CPU, WebGL2, and WebGPU runs emit reproducible correctness
   and benchmark manifests;
7. the full strict build/test/parity matrix is green;
8. independent review finds no unaddressed important findings.
