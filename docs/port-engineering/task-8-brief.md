# Task 8: typed native-emission slice

## Objective

Consume the independently approved immutable typed IR and widen the native C++
catalog from the two Task-5 proof kernels to a small, real capability slice.
Add five pinned corpus kernels:

- `filter/wormhole:clear`
- `filter/bc:bc`
- `filter/threshold:thresh`
- `filter/smoothstep:smoothstep`
- `mixer/channelCombine:channelCombine`

Together with existing `synth/solid:solid` and `filter/invert:inv`, the compiled
catalog gate becomes exactly seven keyed factories. This task establishes the
typed-IR emitter/runtime architecture for scalar/vector code, functions,
swizzles, constructors, texture sampling, and a focused builtin subset. It does
not attempt loops/arrays/uint/matrices/derivatives/structs/UBOs, the 14-shard
full catalog, adapters, render graphs, CLI/DSL, or wormhole deposit.

## Constraints

- Work only in `.`.
- Never invoke Git or indirect Git. No branch/worktree/commit/PR.
- TDD; use `apply_patch`; no repo process docs. Report to
  `docs/port-engineering/task-8-report.md`.
- Preserve Task-5 generator output and its two committed generated files
  byte-for-byte. Add a separate typed generator path.
- Normal runtime/build: C++20 + stdlib + zlib only. No Python/JS/Node/network/
  sibling/file parsing at runtime. Normal CMake compiles only committed C++.
- Generator: Python stdlib only, consumes only the pinned local corpus,
  metadata, manifest, and approved semantic frontend. No AST guessing: emission
  must consume `TypedProgram`/typed nodes and stable symbol/signature identities.
- Never add map/string/variant lookup, virtual calls, `std::function`, or heap
  allocation inside the per-pixel hot path. Binding-time lookup/state allocation
  is allowed.
- Keep `-ffp-contract=off`, no fast-math. Preserve current FloatExpr/f32 storage
  boundary semantics.

## Typed generator

Add a separate deterministic tool, suggested:

```text
tools/glslcpp/emit_typed_cpp.py
tools/glslcpp/generate_typed_slice.py
tools/glslcpp/typed_slice.json
tests/test_typed_generator.py
```

`typed_slice.json` is schema/revision-locked, sorted, and allowlists exactly the
five new program keys. The generator must:

- run Task-6 corpus validation and Task-7 semantic analysis first;
- use metadata static defaults for define variants exactly as
  `check_semantics.py` does;
- reject a program outside the allowlist/capability set before writing;
- emit transactionally with the hardened Task-5 path/symlink/device/rollback
  rules (share helpers instead of weakening/copying them inconsistently);
- support `--check` and an explicit implementation-only write mode; stable
  output contains revision/program/source hash and no absolute paths;
- emit a generated manifest with exact factory/key/source/output hashes and
  capability flags;
- prove output is byte-stable from any CWD and a failed generation leaves the
  committed tree unchanged.

Do not silently fall back to the old Task-5 AST emitter or raw AST strings.

## Emitter/runtime surface

The typed emitter must generate statically typed C++ for all constructs used by
the five selected kernels:

- retained global constants/initializers where present;
- `void` and typed helper functions, exact parameters/returns/calls;
- local declarations, assignments and compound assignments;
- literals, identifiers, constructors/casts, unary/binary operators;
- read/write swizzles with alias-safe simultaneous writes;
- scalar/vector arithmetic, comparisons and `if` where admitted;
- builtins used here: `dot`, `smoothstep`, `texture`, `textureSize`;
- samplers and source uniforms bound once into an immutable typed state;
- `gl_FragCoord` from `PixelContext` and output assignment to the pixel result.

Map standard source uniforms deliberately:

- `resolution`, `time`, `seed`, `frame`, `deltaTime` may come from
  `PixelContext` only when their exact source type/name contract matches;
- `tileOffset`, `fullResolution`, parameters, and samplers are typed bound state
  for this slice. Do not silently invent missing bindings.

Generated locals that the pinned source makes unused (for example
`globalCoord`) must compile under the existing `-Werror`; preserve source
semantics with `[[maybe_unused]]` or a deterministic equivalent rather than
deleting AST nodes opportunistically.

Extend the C++ GLSL runtime only where the selected typed programs require it.
Do not add untested broad builtin stubs. Every new helper needs scalar/vector
fidelity tests, NaN/signed-zero behavior where relevant, and exact type
availability. Internal texture sampling remains nearest/bottom-left and
`textureSize` uses the sampled texture's own dimensions.

## Generated/catalog layout

Add one deterministic committed typed slice translation unit or a very small
fixed set; do not create the future 14 shards yet. Update generated public
declarations/catalog lookup so exactly seven keyed factories are available,
sorted by full runtime key. Lookup may use a static array/binary search at bind
time; pixel dispatch remains the existing raw function pointer/state path.

No factory may be registered for `filter/wormhole:deposit`; `clear` is the
ordinary fullscreen kernel, while `deposit` remains the later native point
draw-op boundary.

## Oracle and parity fixtures

Use `noisemaker-for-cpu` and/or the already parity-proven Python port only as a
read-only implementation-time oracle. Never invoke Git. Freeze small local
fixtures/results into this repository through `apply_patch`; normal tests cannot
call siblings or Node/Python generators.

For each of the five new factories:

- direct bind test (required uniforms/samplers; wrong/missing type rejects at
  bind time);
- deterministic render at 8x8 with nontrivial typed parameters and nonuniform
  source texture(s);
- frozen expected top-down RGBA8 hash/bytes plus selected float32 pixel-bit
  probes before quantization;
- exact output dimension/orientation and alpha checks;
- repeat render byte identity.

Oracle extraction must record exact command/API, source revision/hash, inputs,
and result hashes in the temporary report. If an oracle cannot exercise a
kernel reliably, build an independent scalar reference in the C++ test and say
so; never label a hand-derived expected value as an external oracle.

## Required tests

1. Typed emitter rejects untyped/raw AST and unsupported typed constructs with
   program/span diagnostics.
2. Synthetic typed fixtures cover scalar/vector expressions, constructors,
   helper calls/returns, swizzle writes, texture calls, and output assignment.
3. Generator allowlist/schema/path/transaction/determinism/CWD/tamper checks.
4. The five selected corpus programs generate byte-stably and committed output
   passes `--check`; Task-5 outputs remain byte-identical.
5. C++ runtime tests for any new helpers and exact Bindings ABI.
6. Catalog exact-key gate: seven factories, no duplicate/unknown/deposit entry.
7. Five direct factory/parity tests described above.
8. Debug and Release compilation; no generated warning suppression broader than
   the exact unused-local mechanism.

## Verification

Run and record:

```sh
python3 tests/test_corpus.py
python3 tools/glslcpp/check_corpus.py --check
python3 tests/test_semantic.py
python3 tools/glslcpp/check_semantics.py --check
python3 tests/test_generator.py
python3 tools/glslcpp/generate_kernels.py --check
python3 tests/test_typed_generator.py
python3 tools/glslcpp/generate_typed_slice.py --check
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build --parallel
build/noisemaker-cpu-tests
ctest --test-dir build --output-on-failure
cmake -S . -B build-release -DCMAKE_BUILD_TYPE=Release
cmake --build build-release --parallel
build-release/noisemaker-cpu-tests
ctest --test-dir build-release --output-on-failure
```

## Report

Write `docs/port-engineering/task-8-report.md` with red/green evidence,
selected capability truth, exact generated files/hashes, oracle provenance and
frozen parity results, seven-key catalog evidence, Debug/Release results, and
the exact remaining constructs/program count before the next emission slice.
