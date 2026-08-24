# Shapes183 source-authenticated design and implementation checklist

Status: read-only design. No repository edit, build, generation, or Git action was performed while preparing this document.

## 1. Outcome and authority

Port exactly `classicNoisedeck/shapes:shapes` as the next typed program after Shape Mixer.

- Corpus revision: `a024dc3a960cc44af454abc7aebce50456c194e6`.
- Corpus zero-based order: `classicNoisedeck/shapeMixer:shapeMixer` 15, Shapes 16, `classicNoisedeck/splat:splat` 17.
- Current typed order: Shape Mixer 7, Splat 8. Insert Shapes at typed ordinal 8; Splat becomes 9. Projected ordinals 7-10 must be exactly `classicNoisedeck/shapeMixer:shapeMixer`, `classicNoisedeck/shapes:shapes`, `classicNoisedeck/splat:splat`, and `filter/adjust:adjust`.
- Current state, re-audited from the live slice/catalog: 182 typed/public unique keys, 30 unported, 212 corpus programs, 184 catalog entries because the two legacy entries are dual-registered; 2 scalar-XOR carriers, 3 linear-sRGB carriers, and 25 rows with non-empty `defines` maps.
- Projected state, asserted literally in schema/generator tests: 183 typed/public unique keys, 29 unported, 212 corpus programs, 185 catalog entries, 3 `scalar_uint_xor_profile` carriers, 4 `linear_srgb_lane_index_profile` carriers, 1 `shapes_float_bits_ingress_profile` carrier, and 26 rows with non-empty `defines` maps.
- Projected sorted 183-key-list SHA-256: `b10e0d7eb918c60dae3fa24d0a09b1a9578a334c39ab5a9561db54176eca539b`.
- Program/effect/runtime key: `classicNoisedeck/shapes:shapes` / `classicNoisedeck/shapes` / `classicNoisedeck/shapes:shapes`.
- Canonical source: `tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/classicNoisedeck/shapes/shapes.glsl`.
- Raw authority: 21,289 bytes, SHA-256 `60bc6e76ac9d9f5bc83638fa934b279499559f7733806e462cea16a4cbe85eb0`.
- Normalized authority: 18,713 bytes, SHA-256 `347d19f46adb59129ec2f5eb58910b1ea981be9ec03788a068ff6e884bb848e6`.
- Typed functions SHA-256 already frozen by the scalar-XOR profile: `dfd7220ab36ed03702afbc5e69e7e3a7346c60d488d9b3a2087d31214219943a`.
- Typed whole-program SHA-256: `e072ec89fef6122ed3d581ea5efb6cec953d9b7492294ca9d8b0f011af5411f0`.
- Typed interface SHA-256: `e27ca4581c14991de7a17e296353b1993e8f9c6e5a4ec48b170dde8f8d1b1b6c`.
- Exact default defines: `LOOP_A_OFFSET=40`, `LOOP_B_OFFSET=30`. This remains a default-only typed factory; no alternate define variants are admitted.
- Resources: 18 uniforms (`time`, `seed`, `wrap`, `resolution`, `tileOffset`, `fullResolution`, `loopAScale`, `loopBScale`, `speedA`, `speedB`, `paletteMode`, `paletteOffset`, `paletteAmp`, `paletteFreq`, `palettePhase`, `cyclePalette`, `rotatePalette`, `repeatPalette`), no samplers, one `fragColor` output, no texture reads, no derivatives.
- Canonical JavaScript oracle factory: `canonicalFactory16`, frozen factory-text SHA-256 `a4e1aeaf8cbc3d748517369e054b7ec4a2fd5f70962cbafef61d5e473527c2c3` in the existing matrix precompute.
- The current upstream Noisemaker checkout's GLSL differs from the corpus source only in one comment URL. Do not refresh the pinned corpus during this task.

Existing pre-change generated artifacts to reconstruct exactly after implementation:

- `src/typed_generated/typed_slice.cpp`: `7e3b659ff007b08acda39d8f67f931e61742befe8959c4fa212ffa8f051fc6c7` (1,757,260 bytes).
- `src/typed_generated/typed_manifest.json`: `242c49a756b541a6fbbf94a984039a6ab4db41437d21770e43c302692f57e50d` (290,280 bytes).
- `include/noisemaker/generated/catalog.hpp`: `6f89a6b51bf8b6eba2c4c1f16a1852cce3e293d514be8d57efaaca96827b77c4` (16,831 bytes).
- `tools/glslcpp/typed_slice.json`: `8d58736afa431f2d2c3fa992c22301d9775e4bed7d122d43c85218ccfada315c` (22,305 bytes). This is the prechange input lock, not a reconstruction output.
- Current sorted typed-list SHA-256: `33cc895dbee2e0b0451081f5e940d3ee101442a5e3ae90b49dec34d84f5b124b`.

## 2. Chosen architecture

Use three composable, fail-closed authorities on the one Shapes row:

1. Reuse the existing `scalar-uint-xor-v1` carrier. `scalar_uint_xor_profile.py` already contains complete Shapes source/interface/function/loop/reachability locks, all three scalar `uint ^ uint` sites, and the full `float(uint)` census. Do not add another XOR implementation or duplicate those proofs.
2. Extend the existing shared `linear_srgb_lane_index_profile.py` with one exact Shapes lock and profile name such as `linear-srgb-shapes-lane-index-v1`. This is the identical `linearToSrgb` induction closure already supported for Adjust, Colorspace, and Cell Noise. Change its hardcoded empty-define check to a per-key exact define tuple so the three old keys remain `{}` and Shapes requires exactly `40/30`.
3. Add one small Shapes-only profile, suggested name `shapes-float-bits-ingress-v1`, authenticating only the reachable-call-graph `floatBitsToUint(seedFrac)` node. Keep it separate from scalar XOR so each mechanism retains one responsibility and independent traversal accounting.

The Shapes slice row should therefore have exactly:

```json
{
  "defines": {"LOOP_A_OFFSET": 40, "LOOP_B_OFFSET": 30},
  "linear_srgb_lane_index_profile": "linear-srgb-shapes-lane-index-v1",
  "program_key": "classicNoisedeck/shapes:shapes",
  "scalar_uint_xor_profile": "scalar-uint-xor-v1",
  "shapes_float_bits_ingress_profile": "shapes-float-bits-ingress-v1"
}
```

Require all three carriers together at both validator and emitter boundaries. Missing, wrong, foreign, or partially composed carriers fail closed.

Rejected alternatives:

- A monolithic copied `shapes_builtin_profile`: duplicates the existing linear-index and XOR mechanisms and makes future review harder.
- Generic `vec3[i]` or `floatBitsToUint` admission: widens unrelated programs and violates the frozen 44-capability vocabulary and node-identity policy.
- Reusing the Shape Mixer closure wholesale: it authenticates unrelated blend/reflect/refract/mod control flow and cannot safely describe Shapes.

No runtime primitive should change. Current support already supplies literal const `mat3` globals, column-major 9-float construction, `mat3 * vec3` with final f32 lane narrowing, loop proof, `float_bits_to_uint`, scalar XOR lowering, safe mangling of the local named `state`, and default define binding.

## 3. Exact new closures

### 3.1 Five `linearToSrgb` indexes

Authenticate a whole-program census of exactly these normalized sites:

- `576:13-576:22`: read `linear[i]` in the condition.
- `577:13-577:20`: write `srgb[i]` on the true branch.
- `577:23-577:32`: read `linear[i]` on the true branch.
- `579:13-579:20`: write `srgb[i]` on the false branch.
- `579:35-579:44`: read `linear[i]` under `pow` on the false branch.

The raw source sites are lines 590, 591, and 593. Prove one `for (int i=0; i<3; ++i)` loop, trip count three, a `vec3` input parameter named `linear`, a local `vec3` named `srgb`, the exact read/write roles above, and all three result lanes definitely initialized before return. Authenticate source, normalized source, functions, interface, whole program, resources, exact defines, call graph, owner, parents, spans, node hashes, base/induction symbol identities, and the complete index-node census. Reject a sixth index anywhere.

The validator and emitter must independently re-authenticate and independently consume all five objects exactly once. Admission is by object identity and must skip `used.add(...)`; do not add a capability token.

### 3.2 One float-bit ingress

Authenticate only normalized `119:21-119:46` (raw line 133):

```glsl
uint fracBits = floatBitsToUint(seedFrac);
```

Bind it to the exact `randomFromLatticeWithOffset` owner and declaration parent, the exact scalar `float -> uint` signature, the local `seedFrac` source initialized to positive `0.0`, and the downstream ancestry feeding the three already-authenticated scalar XORs. Census the whole program and require exactly one `floatBitsToUint` node. Reject vector overloads, inverse conversions, numeric casts, another ingress, a moved call, a different operand, another parent, foreign key, source/define drift, or a dead/unreachable owner substitution.

Important claim boundary: with defines `40/30`, the noise/hash branch is not taken by a normal full render even though the owner is reachable in the conservative function call graph. Full-surface cases cannot prove these bit sites executed. Claim structural/emission authentication for this closure, not render execution. The runtime bit-pattern test as extended in section 5, plus profile mutation tests, carries its semantic proof.

### 3.3 Existing scalar XOR reuse

Require `scalar-uint-xor-v1`; do not edit its Shapes lock unless the final exact parsed tree proves current constants stale. Its three normalized sites are `122:10-122:46`, `123:10-123:46`, and `124:10-124:47` in `randomFromLatticeWithOffset`. Preserve its exact source hashes, call-graph SHA `cdecf94aab2a041d245737ed5be8a3d8db26bb945682f4720ac6ea01c1f6b8b3`, three-site census SHA `8f37784de5b36230e1535ad67dcf6c4054e9825f3c3f681e2589bbab4f22de63`, and current JavaScript materialization contract. Do not introduce a Shapes-specific scalar XOR helper.

## 4. Oracle, provenance, coordinates, and exact comparer

The oracle/native owner creates one deterministic package with no alternative locations:

- `docs/port-engineering/shapes-parity/shapes183_oracle_generator.mjs`;
- `docs/port-engineering/shapes-parity/shapes183-oracles.json` as canonical full-array authority;
- `docs/port-engineering/shapes-parity/shapes183-oracle-report.md`;
- `tools/glslcpp/generate_shapes_native_oracle_include.py` as the sole JSON-to-C++ materializer;
- `tests/oracles/shapes183_expected.inc` as its generated native fixture.

Commit a sibling `<artifact>.sha256` for every one of those five new files. Each sidecar contains the full lowercase SHA-256 and basename; each generator/checker verifies all applicable sidecars byte-for-byte. The JSON-to-C++ materializer must also have negative tests for missing/extra fields, duplicate case names, malformed dimensions/counts/hex words/byte values, wrong hashes/sidecars, and truncated/extra arrays. Do not create another Shapes oracle or repair unrelated historical sidecar debt.

The JSON locks schema/version, corpus revision, key, exact defines, source path/bytes/SHA, factory name/text SHA, generator provenance, comparer self-test ledger, unique case/coverage labels, and exact full arrays. For every case it stores dimensions; all 18 runtime bindings; external pass time/seed; every float/Vec lane as a hexadecimal f32 word; expected full-surface f32 words and RGBA8 bytes; finite/nonfinite counts; and SHA-256 over each array. The 18 bindings are runtime data and the two compile-time defines are recorded separately, never counted as 20 bindings.

Use exactly the six authenticated compact matrix-precompute cases as the initial fixture set: `oklab-palette-a`, `oklab-palette-tiled`, `oklab-palette-extreme`, `oklab-palette-negative-speed`, `diagnostic-palette-hsv`, and `diagnostic-palette-rgb`. Together they cover OKLab/HSV/RGB, landscape/portrait/square, tiled/untiled, wrap true/false, positive/negative/zero speeds, cycle -1/0/1, repeat/rotate, and varying bound seed/time. The four OKLab cases must each discriminate both `shapes-fwdB-column-swap` and `shapes-cube-unnarrowed`; the HSV/RGB cases are non-reaching controls. Do not add cases unless a proved live branch lacks a witness.

### 4.1 Independent JavaScript authority

Define `CPP_ROOT=/Users/aayars/platform/noisemaker-for-cpp` and create one immutable `CPU_ROOT=$RUN_ROOT/oracle/noisemaker-for-cpu` snapshot of `/Users/aayars/platform/noisemaker-for-cpu`. Generate through the public path in that frozen snapshot via the C++-repository script's required `--cpu-root "$CPU_ROOT"` argument. Pin these exact CPU-relative paths and current full hashes in fixture metadata:

- `src/effects/generated/canonical-kernels.js`: `66adc01c7df07298b40eaf74fddb7226fdf87bb18dea75b527640c88d0f40ebe`;
- `src/effects/catalog.js`: `d8cf312294ccd915892a4a668432ca2533ab255fb24664d89dee8456331e4ea4`;
- `src/csl/glsl-kernel.js`: `a684b1bc16f095c550e488d1db35b9cea9c69b761db6ad3af175110e6a2e2baa`;
- `src/csl/glsl-runtime.js`: `a20421c56aa3274746f6887555445b8c7f7bb8318921fe6f75f6aa8ffe71c072`;
- `src/runtime/pass-runner.js`: `fbfd53470735a07dca317c384b9985bb55383961199815e67aee9adda7e881aa`;
- `src/runtime/surface.js`: `0cd69c920a710f636a5208e05b49633fc2747cdc2f5fc61113433ceb9ec8ba59`.

Before execution, require `kernelFactories.get(key) === canonicalKernelFactories[key]`, require that function to be the expected `canonicalFactory16`, require name plus `Function.prototype.toString` SHA `a4e1aeaf8cbc3d748517369e054b7ec4a2fd5f70962cbafef61d5e473527c2c3`, and require `canonicalAdapterFactories` not to own the key. Resolve every CPU import by real path, require it is beneath `CPU_ROOT`, and reject imports/cache hits from the live CPU checkout or any other root. A replaced file, adapter override, alternate factory, monkey-patched/substituted runtime, or identity mismatch is a hard failure. Execute the unmodified public factory with the pinned `bindCanonicalKernel`/runtime and `runPass`; a locally reimplemented formula is not an oracle.

> **Superseded in part — see §11.** The bound-`seed` requirement in this
> paragraph is retracted: `seed` is not consumed on any live path at defines
> 40/30, so it is recorded and proven *invariant*, not required to differ. The
> bound-`time` and external-pass-invariance requirements below stand as written.
> This paragraph is left unedited so the GO review remains auditable against it.

Attach a one-axis control group to `oklab-palette-a`. Render identical bindings/dimensions with external `runPass` time/seed words `(0x00000000,0x3f800000)` and `(0x4f000000,0xcf000000)` and require identical full f32/RGBA8 arrays. Holding the first external pair and every other binding fixed, separately change only bound `time` from `0x3f000000` (0.5) to `0x41200000` (10.0), then only bound `seed` from int32 3 to 123; each controlled render must differ from baseline. **[The `seed` half of that clause is RETRACTED — see §11. `seed` is dead at 40/30; it is recorded and proven invariant. The `time` half stands.]** Store each control's exact full arrays/hashes and a pass/fail ledger. This kills accidental external-control consumption while proving the shader-owned uniforms dominate. These nested controls do not expand the six top-level coverage cases.

### 4.2 Top-down crop normalization

Both runners store top-down while GLSL fragment coordinates are bottom-left. The canonical JSON/include always stores native top-down row order. For a top-down crop at `(crop_x,crop_y)` of size `(tile_width,tile_height)` from full size `(full_width,full_height)`, the full route binds `resolution=fullResolution=(full_width,full_height)` and `tileOffset=(0,0)`; the tile route binds `resolution=(tile_width,tile_height)`, the same `fullResolution`, and `tileOffset=(crop_x,full_height-crop_y-tile_height)`. Hold the other 15 runtime bindings identical. The oracle generator must prove tile output equals the corresponding top-down crop of full output after this translation; it must not copy raw top-down `crop_y` into `tileOffset.y`.

### 4.3 Custom exact comparer

Write the Shapes-specific comparer in `tests/test_generated_kernels.cpp`. It must validate width and height before lane count (so equal-lane-count dimensions fail); require both arrays to contain exactly `width*height*4` elements; compare every float by exact 32-bit word including signed zero and NaN payload; compare every RGBA8 byte; and report the first mismatch with top-down x/y, channel, expected/actual float words, and expected/actual bytes. Self-tests cover dimension mismatch, +0/-0, differing NaN payloads, word-only and byte-only mismatch, and short/long word and byte arrays.

Every output alpha word must be exactly `0x3f800000`, and every RGBA8 alpha byte exactly `255`, in every case and route. Do not replace full-array comparison with tolerance, hashes, probes, or RGBA8-only checks; hashes and probes are secondary integrity/diagnostic data.

## 5. Test and mutation matrix

### Python/frontend RED then GREEN

1. Freeze a preflight asserting Shapes is absent, is corpus ordinal 16, has exact source/define/resources, and currently rejects first at normalized `576:13` as `unsupported typed expression index`.
2. Add failing exact tests for the five index roles and the one ingress before production wiring.
3. Prove the linear-index profile authenticates all five sites only with the exact Shapes source/defines and coexists with the scalar-XOR and ingress carriers.
4. Prove the ingress profile authenticates one site, its owner/parent/operand/ancestry, and the complete float-bit census.
5. At both validator and emitter, test missing, wrong, foreign, and partial carrier combinations.
6. Add single-axis structural mutations: source/path/hash, each define value/name/order, loop start/bound/update/trip count, base symbol, induction symbol, read/write role, each index node, added/removed/reordered index, ingress callee/signature/operand/parent/owner/path/reachability, extra ingress, downstream XOR ancestry, foreign key, resource/type drift, matrix constant/order drift, and an unrelated proof carrier. Include the focused initializer mutant `float seedFrac = 0.0;` -> `float seedFrac = -0.0;`, preserving declaration parent, storage, and symbol; it must fail the positive-zero initializer lock rather than a coarse hash.
7. For every mutation whose purpose is local structural logic, patch/refreeze the coarse source/function/whole/interface hashes to the mutated candidate, assert the coarse mismatch message did not fire, and assert the intended local failure message. This prevents vacuous mutation coverage.
8. Assert validator and emitter re-authenticate independently and consume all six new profile nodes exactly once. Sabotage each visitation check in a negative test to prove the ledger is load-bearing.
9. Assert the approved capability tuple remains exactly 44 and the type tuple remains unchanged.

### Generated artifacts and historical reconstruction

1. Insert only the one sorted Shapes row. Update exact schema/profile censuses and expected defines.
2. Generate only through `PYTHONDONTWRITEBYTECODE=1 python3 -B tools/glslcpp/generate_typed_slice.py --write`; never hand-edit generated C++/manifest/header.
3. Require the projected sorted 183-key SHA `b10e0d7eb918c60dae3fa24d0a09b1a9578a334c39ab5a9561db54176eca539b`, the exact Shape Mixer / Shapes / Splat / Adjust neighborhood, 183 unique rows, 185 catalog entries, 29 unported, carrier censuses 3/4/1, and 26 rows with non-empty `defines` maps. Then freeze final hashes/sizes for `typed_slice.cpp`, `typed_manifest.json`, `catalog.hpp`, and `typed_slice.json`.
4. Assert the manifest row contains both new profile names plus `scalar_uint_xor_profile`, exact defines, factory `bind_classicNoisedeck_shapes_shapes`, source hash, and default-only define contract.
5. Assert public catalog size 185, Shapes occurs exactly once between Shape Mixer and Splat, and named/catalog binders point to the same factory.
6. Historical 183 -> 182 reconstruction: deep-copy the live spec, remove only the Shapes row, generate in memory, and require the exact three pre-change hashes in section 1. Compare every surviving emitted program block after replacing only `typed_N` ordinals with a sentinel. The block set difference must be exactly Shapes. Do not mechanically rewrite older historical tests; classify each count/hash assertion by its enclosing milestone.

### Native parity, direct/public, repeatability, immutability, and ABI

1. Run every oracle through both `generated::bind("classicNoisedeck/shapes:shapes", bindings)` and `bind_classicNoisedeck_shapes_shapes(bindings)` plus a second public repeat render from independent bindings.
2. Compare all three outputs to the full exact oracle and to each other. Assert independent output storage, deterministic repetition, finite-lane counts, alpha behavior, and expected RGBA8.
3. Because Shapes has no input texture, immutability is executable binding-state proof: before bind/run, snapshot all 18 getter-visible values using their production getter/type (`int32`, bool, number, `Vec2`, or `Vec3`) and separately snapshot the raw f32 words of each caller-owned `Vec2`/`Vec3` lane array. After public/direct/repeat passes, compare all getter-visible snapshots and all original caller-vector words exactly. Also require unchanged fixture arrays and independent output backing storage. Do not claim input-surface immutability for a generator with no sampler.
4. ABI-test all 18 uniforms through both binders. For each binding, omit it once and supply the wrong variant type once; require `KernelBindingError` naming the binding. Lock `seed`, `paletteMode`, and `cyclePalette` as `int32`, `wrap` as bool, four palette fields as `Vec3`, `resolution/tileOffset/fullResolution` as `Vec2`, and all other scalar uniforms through `get_number`. Confirm compile-time defines are not runtime bindings. Confirm unrelated extra uniform/texture entries are ignored and behavior-neutral.
5. Extend `tests/test_numeric.cpp` with the exact controlled-payload assertion `float_bits_to_uint(uint_bits_to_float(0x7fc12345U)) == 0x7fc12345U`, alongside exact +0, -0, finite, infinity, and high-bit scalar-XOR cases. Do not say the default Shapes render executes the dead hash branch.
6. Mutation evidence is generated, not asserted abstractly: `shapes183_oracle_generator.mjs` independently computes `shapes-fwdB-column-swap` and `shapes-cube-unnarrowed`, records per-case f32/RGBA8 hashes and a case-by-mutant discrimination ledger, and `--check` validates that all four reaching OKLab cases differ for each mutant while the two non-reaching controls do not. The native implementation must match only the unmutated full oracle. Do not commit hand-mutated generated C++; if a native mutant is additionally compiled, create it only beneath `$RUN_ROOT/assembly` and delete it with that owned root.

## 6. Likely owned file scope

Production/profile owner:

- Modify `tools/glslcpp/frontend/linear_srgb_lane_index_profile.py`.
- Create `tools/glslcpp/frontend/shapes_float_bits_ingress_profile.py`.
- Modify `tools/glslcpp/generate_typed_slice.py`.
- Modify `tools/glslcpp/emit_typed_cpp.py`.
- Modify `tools/glslcpp/typed_slice.json`.
- Generated only: `src/typed_generated/typed_slice.cpp`, `src/typed_generated/typed_manifest.json`, `include/noisemaker/generated/catalog.hpp`.

Python-test owner:

- Modify `tests/test_typed_generator.py` for integration, counts, hashes, reconstruction, and cross-profile composition.
- Prefer a focused new `tests/test_shapes_float_bits_ingress.py` for the ingress proof/mutations; extend an existing linear-profile focused test if one exists rather than duplicating its harness.

Oracle/native owner:

- Solely own the exact package in section 4: the three `docs/port-engineering/shapes-parity/` artifacts and sidecars, `tools/glslcpp/generate_shapes_native_oracle_include.py` and sidecar, and `tests/oracles/shapes183_expected.inc` and sidecar.
- Modify `tests/test_generated_kernels.cpp` for comparer, public/direct/repeat parity, ABI, binding immutability, alpha, and mutation-ledger checks.
- Modify `tests/test_numeric.cpp` only for the exact controlled NaN-payload round trip.

Do not edit the corpus, runtime math/types, Surface/sampler, CMake, README, unrelated profiles, existing expected fixtures, or generated files by hand. Do not create a second oracle/native owner. Expand scope only on a reproduced blocker and update the design first.

## 7. Parallel ownership and merge order

Use four bounded workers without concurrent edits to the same file:

1. Integration owner: profile interfaces, generator/emitter wiring, slice row, generated artifacts. Sole owner of `generate_typed_slice.py`, `emit_typed_cpp.py`, and `typed_slice.json`.
2. Python owner: focused RED tests, local mutation barriers, 183->182 reconstruction. Coordinate any `tests/test_typed_generator.py` overlap before editing.
3. Oracle/native owner: canonical JS fixture, exact comparer, parity/ABI tests. Does not touch generator/emitter.
4. Independent verifier: read-only source/profile/oracle review first; after integration, fresh full suites, sanitizer and assembly audit. Does not repair code; returns exact findings to the integration owner.

Merge order: test contract -> profile implementation -> generator/emitter wiring -> generated output -> oracle/native integration -> historical reconstruction -> full verification -> independent review. If two owners need the same file, serialize that file; do not resolve by wholesale replacement.

## 8. Verification and native-code gates

Run only after the environment/storage controls in section 10 are active. Every Python command uses both `PYTHONDONTWRITEBYTECODE=1` and `python3 -B`:

1. Schema checks must assert 183 unique rows, 185 catalog entries, 29 unported, carrier counts 3/4/1, 26 rows with non-empty `defines` maps, projected key-list SHA `b10e0d7eb918c60dae3fa24d0a09b1a9578a334c39ab5a9561db54176eca539b`, and the exact four-key neighborhood.
2. `PYTHONDONTWRITEBYTECODE=1 python3 -B tools/glslcpp/check_corpus.py --check`.
3. `PYTHONDONTWRITEBYTECODE=1 python3 -B tools/glslcpp/check_semantics.py --check` (212 programs).
4. Run `node "$CPP_ROOT/docs/port-engineering/shapes-parity/shapes183_oracle_generator.mjs" --check --cpu-root "$CPU_ROOT"`, then `PYTHONDONTWRITEBYTECODE=1 python3 -B "$CPP_ROOT/tools/glslcpp/generate_shapes_native_oracle_include.py" --check`; require imports confined beneath the immutable snapshot, all sidecars, public identity, external controls, full arrays, alpha, crop, and mutant ledger.
5. `PYTHONDONTWRITEBYTECODE=1 python3 -B tools/glslcpp/generate_kernels.py --check`.
6. `PYTHONDONTWRITEBYTECODE=1 python3 -B tools/glslcpp/generate_typed_slice.py --check` (183 programs).
7. Focused profile/oracle/reconstruction tests, then `PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p 'test_*.py' -q`.
8. Fresh `$RUN_ROOT/Debug` configure/build, direct test binary, and CTest 1/1.
9. Fresh `$RUN_ROOT/Release` configure/build, direct test binary, and CTest 1/1.
10. Fresh `$RUN_ROOT/sanitizer` ASan+UBSan configure/build, direct test binary, and CTest 1/1 with `UBSAN_OPTIONS=print_stacktrace=1:halt_on_error=1`. On Apple, use `ASAN_OPTIONS=detect_leaks=0`; report zero ASan/UBSan diagnostics but make no LSan claim.
11. Confirm warnings as errors and `-ffp-contract=off` in all three builds; preserve exact commands, exits, and bounded logs under their lane directories.

Assembly audit both native ARM64 and x86_64 cross-compile for the final exact source:

- Inspect `typed_8::pixel`, `linearToSrgb`, `linear_srgb_from_oklab`, `oklab_from_linear_srgb`, `randomFromLatticeWithOffset`, and the binder. Resolve symbols after generation rather than assuming spelling.
- Pixel/helper scope: no indirect `br`/`blr` or indirect `jmp`/`call`, no fused FP (`fmadd`/`fmsub`/`vfmadd`), heap allocation, exception/unwind path, virtual/callback dispatch, string/container work, or dynamic stack allocation.
- Direct helper calls are allowed. Binder-only `shared_ptr` allocation/cleanup and exception paths must remain construction-only and outside the pixel scope.
- Record exact instruction counts, frame/stack sizes, direct callees, and any architecture difference. If a compiler jump table or other indirect branch appears, repair with a source-authenticated bounded dispatch shape and repeat all parity/full-suite gates; do not waive it.

## 9. Failure boundaries and stop conditions

Stop and redesign rather than widening if any of these occurs:

- the current source hashes/defines no longer match the authority above;
- Shapes needs a capability outside the two new closures plus existing scalar XOR/matrix/runtime support;
- the oracle factory/source provenance cannot be authenticated;
- a full render is used to claim execution of the default-dead hash branch;
- exact f32 parity fails and a tolerance is proposed;
- a profile mutation reaches only the coarse hash gate;
- historical 182 reconstruction changes any surviving normalized emitted block;
- sanitizer or assembly gates reveal a pixel-path allocation, indirect dispatch, fused FP, UB, or unbounded/dynamic stack behavior.

## 10. Storage and cleanup gate

- Allocate exactly one external root: `RUN_ROOT="$(mktemp -d /private/tmp/noisemaker-shapes183.XXXXXX)"`. Immediately require it is a directory and its resolved path matches `/private/tmp/noisemaker-shapes183.*`; never use another build/scratch root. Create explicit `$RUN_ROOT/Debug`, `$RUN_ROOT/Release`, `$RUN_ROOT/sanitizer`, `$RUN_ROOT/reconstruction`, `$RUN_ROOT/assembly`, and `$RUN_ROOT/oracle` lane directories. The frozen CPU copy, Node scratch, logs, probes, object/assembly files, and generated comparisons live only in the matching lane.
- Before any Python/Node/build command, create `$RUN_ROOT/oracle/tmp`, `$RUN_ROOT/oracle/xdg-cache`, and `$RUN_ROOT/oracle/pycache`, then export `TMPDIR=$RUN_ROOT/oracle/tmp`, `TMP=$RUN_ROOT/oracle/tmp`, `TEMP=$RUN_ROOT/oracle/tmp`, `XDG_CACHE_HOME=$RUN_ROOT/oracle/xdg-cache`, `PYTHONPYCACHEPREFIX=$RUN_ROOT/oracle/pycache`, and `PYTHONDONTWRITEBYTECODE=1`. Every Python invocation is spelled `python3 -B` (including modules, generators, tests, and helper probes).
- Define the exact retained-product allowlist before execution as only the owned source/test/doc files in section 6, their named sidecars, the one slice-row change, and the three generator-produced C++/manifest/catalog outputs. Before work, write `$RUN_ROOT/repository-full.before.tsv` for every repository entry outside that allowlist: repo-relative path, kind, byte size, full SHA-256 for regular files, and exact link target for symlinks. Include dotfiles and pre-existing artifacts; do not omit a path merely because it is under `.git`, `build*`, a cache, or a scratch-looking directory. Sort bytewise for deterministic comparison.
- Also write `$RUN_ROOT/repository-transients.before.tsv` with the same fields for exact transient patterns: top-level/recursive `build*`, `cmake-build*`, `CMakeFiles`, `CMakeCache.txt`, `Testing`, `_deps`, `compile_commands.json`, `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`, `.cache`, `.coverage*`, `*.pyc`, `*.pyo`, `*.o`, `*.obj`, `*.a`, `*.so`, `*.dylib`, `*.dll`, `*.exe`, `*.s`, `*.su`, `*.tmp`, `*.log`, and `shapes183-scratch*`.
- After oracle, reconstruction, Debug, Release, sanitizer, assembly, and final verification lanes, regenerate both manifests. Require the full manifest outside the allowlist to be byte-for-byte identical to `repository-full.before.tsv`; separately require zero new transient paths and unchanged bytes/link targets for every pre-existing transient entry. Thus an existing non-transient file cannot change undetected. A failure stops the run; it does not authorize cleanup of pre-existing content.
- Keep every canonical/control full output array only once in `shapes183-oracles.json`; the generated include is the one necessary native materialization, not another scratch copy. Repository fixtures/sidecars are retained product assets; build products and ad-hoc dumps are not.
- After evidence has been summarized into the retained report/sidecars, record a final owned-root manifest and `du -sk` in the handoff, validate `RUN_ROOT` again against the exact prefix, and delete only `"$RUN_ROOT"`. Require the path no longer exists. Never scan, glob-delete, or modify unrelated `/private/tmp`, and never delete or alter any pre-existing repository artifact.

Completion means the 183-key generated state, exact full-surface parity, two profile closures plus reused scalar XOR, historical reconstruction, full Python/Debug/Release/sanitizer gates, native assembly GO, independent review with Critical/Important feedback addressed, and a final clean storage audit all agree.

---

## 11. Amendment 1 — the bound-`seed` control is unsatisfiable at 40/30

Added 2026-08-15 by the integration owner, after the oracle implementer reported
it and the claim was independently verified from the corpus source. Sections 1-10
above are the originally reviewed text and are left unedited; this section
overrides §4.1 only where stated.

**§4.1 as written requires an impossible control.** It says that, holding
everything else fixed, changing only bound `seed` from int32 `3` to `123` must
change the output. At the default defines `LOOP_A_OFFSET=40` /
`LOOP_B_OFFSET=30`, `seed` is not consumed on any live path:

- `main()` reaches `seed` only through two `offset(...)` calls
  (`shapes.glsl:669,671,683,685`). `offset()`'s sole use of its `seed`
  parameter is `shapes.glsl:519`, inside the `loopOffset >= 300 && loopOffset <= 380`
  arm. At `40` the taken arm is lines 508-510 and at `30` it is lines 506-507;
  neither reads `seed`.
- `value()` — which holds the other two `float(seed)` uses at
  `shapes.glsl:446,450` — has exactly **one** caller in the whole program, that
  same dead line 519.
- The remaining uses (`seedInt` at line 114, `seedBits` at line 132) are inside
  `randomFromLatticeWithOffset`, the hash branch §3.2 already documents as
  call-graph reachable but dynamically dead at these defines.

The corpus source says so itself, at `shapes.glsl:12-19`:

> The default (40 = square, 30 = diamond) doesn't reach the noise variants, so
> the entire 9-way `value()` dispatch and the variant function bodies get
> dead-code-eliminated by the GLSL→HLSL translator before ANGLE drives the D3D
> backend.

**Amended requirement.** The bound-`seed` axis is **recorded and proven
invariant**, not required to differ. The oracle stores the measured result
verbatim together with a `seed_liveness_census` identifying every `seed`
consumer and why each is unreachable at 40/30, and both the generator and the
materializer surface the discrepancy against the original §4.1 text on every
run rather than silently accommodating it.

**What is unchanged.** `seed` remains a **required int32 ABI binding**: phase 2
must still omit it once and supply a wrong variant once, requiring
`KernelBindingError` to name it. The bound-`time` axis and the
external-pass-invariance axis are untouched and still carry §4.1's original
purpose — proving the shader-owned uniforms dominate and that no external
`runPass` state is accidentally consumed.

**The invariance is itself a parity assertion, not a waived test.** A C++ port
that wrongly made `seed` live at 40/30 would differ from an oracle that is
invariant, and the full-surface comparison would catch it. Manufacturing a
difference, dropping the binding, or deleting the axis would each have been
worse than recording the truth.

---

## 12. Amendment 2 — a third closure: the rvalue compound assignment at 42:19

Added 2026-08-15 by the integration owner, after the integration worker
reproduced a §9 stop condition and correctly refused to widen it. This adds one
closure to §2's list of three; it does not change anything else.

**The blocker.** Normalized `42:19` (raw `shapes.glsl:56`):

```glsl
vec2 rotate2D(vec2 st, float rot) {
    float angle = rot *= PI;
```

A compound assignment used as an **rvalue**. The validator accepts the program;
the **emitter** lowers assignment only at statement level and has no `assign`
arm in its expression dispatcher. This is a genuine capability gap that §§1-10
did not anticipate.

**It is the only gap.** A whole-tree census finds exactly one rvalue assignment,
zero unapproved operators, and `floatBitsToUint` as the only builtin outside the
emitter table. An in-memory probe lowering only that node runs the real
generator to completion at 183 manifest rows, with the Shapes manifest row
already correct.

**The lowering is settled by the shipped JavaScript, not by GLSL reading.**
`canonicalFactory16` does **not** dead-code-eliminate `rotate2D`; it materializes
the line as:

```js
function rotate2D (st, rot) {
	st = $runtime.copy(st);
	var angle = rot *= 3.1415927410125732;
```

So the reference keeps the compound assignment as an rvalue, with `PI`
materialized as the f32 value widened to double. `float angle = (rot *= <f32 pi>);`
is directly expressible in C++ with identical semantics. This is the usual rule
of this project applying again: the parity target is the transpiler's
materialization, and here it can simply be read off.

**Chosen mechanism.** A narrow Shapes-only identity closure, suggested name
`shapes-rvalue-assign-v1`, admitting exactly that one node by identity, skipping
`used.add(...)`, adding **no** token to the frozen 44-entry vocabulary, and
arming a new rejection at the widened boundary. The emitter gains an `assign`
arm in its expression dispatcher gated on the admitted node's identity.

Rejected alternatives:

- *A general rvalue-assignment capability.* Grows the frozen vocabulary and
  admits the construct program-wide. Banned by §2's node-identity policy.
- *A whole-function dead-code exemption.* Exemption is a weakening where every
  other mechanism in this project is an admission; it would also suppress a
  function the reference actually emits. The design already reserves that
  mechanism for `moodscape` as separate work.

**Claim boundary.** `rotate2D` has zero callers and `rot` is read nowhere after
the assignment, so the construct is dead and **no oracle case can discriminate
the lowering**. Do not cite full-surface parity as proof it is correct.
Structural authentication, mutation coverage, and the JS materialization quoted
above carry that proof — exactly as §3.2 already requires for the float-bit
ingress.

---

## 13. Amendment 3 — assembly gate result, and what its cleanliness depends on

Added 2026-08-16 by the integration owner from the independent verifier's report
(`$RUN_ROOT/verification/verifier-report.md`). Records the §8 outcome and one
forward-looking constraint that is not obvious from a green gate.

**Result.** ASan+UBSan: 242 PASS / 0 FAIL, **zero ASan and zero UBSan
diagnostics**, ctest 1/1. On Apple `detect_leaks=0`, so **no LeakSanitizer claim
is made either way**. Assembly, ARM64 native and x86_64 cross: all six required
symbols resolved from the emitted listings, all emitted out-of-line, none
inlined away. `typed_8::pixel`, `linearToSrgb`, `linear_srgb_from_oklab`,
`oklab_from_linear_srgb`, and `randomFromLatticeWithOffset` each have zero
indirect branches, zero fused FP, no heap, no exception path, no string or
container work, no dynamic stack, and no jump table, identically on both
architectures. Frames 48-176 B, 67-253 instructions, all calls direct. Fused FP
is zero across **all 53/54 functions of the Shapes namespace** on both arches,
which is what verifies `-ffp-contract=off` actually reached the compile lines.

The binder's two indirect calls were authenticated rather than assumed:
`ldaddal` refcount decrement → vtable slot 16 → `blr x8` (`callq *16(%rax)` on
x86_64) is libc++ `shared_ptr` control-block teardown, binder-only and outside
the pixel path — the carve-out §8 permits.

**The constraint worth carrying.** `typed_8::value` *does* compile to a real
jump table (`LJTI196_0` → `jmpq *%rax`; `br x10` on ARM64). It is outside pixel
scope **only because the defines are frozen at 40/30**: `pixel` reaches `value`
solely through `offset`'s `300..380` arm, and at 40/30 clang inlines `offset`
and constant-folds the dispatch away entirely. The assembly therefore
independently corroborates §3.2's dead-branch claim boundary — a second,
compiler-level witness for something the oracle cannot discriminate.

But the containment is a consequence of the frozen defines, not a property of
the code. **If a define variant is ever admitted for Shapes, that jump table
lands in the pixel path and §8's bounded-dispatch clause fires.** This is not
waived; it is recorded as a precondition. Any future work admitting alternate
`LOOP_A_OFFSET`/`LOOP_B_OFFSET` values must re-run the assembly gate and expect
to need a source-authenticated bounded dispatch shape.

**Two pre-existing conditions observed, neither Shapes' and neither fixed here.**
`typed_8::hsv2rgb` carries an LSDA and `___clang_call_terminate` landing pad
inside the pixel closure — the mandatory `noexcept` terminate handler,
unreachable on normal flow, caused by `glsl::Vec<N,T>::Vec(const FloatExpr<N>&)`
at `glsl_types.hpp:164` lacking `noexcept`. It affects 51 functions in the
translation unit, including other programs' `pixel`. And the known
`synth/bitwise` signed-overflow UBSan diagnostic (`DEFECTS-FOUND.md` item 4)
**did not reproduce** in this lane; both bitwise tests ran and passed. Since no
diagnostic appeared there was nothing to confirm as the same one, so it is
**not** claimed fixed and item 4 keeps no resolution marker.

Non-finding, recorded so it is not later misread as a Shapes regression:
`pow`/`atan2` route to platform libm while `sin`/`cos` route to the repository's
`fdlibm`. That asymmetry is generator-wide, matches `glsl_runtime.hpp:42,61`, is
permitted by the gate, and the oracle tests are bit-exact under it.
