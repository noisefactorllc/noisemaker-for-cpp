# Task 8: typed native-emission slice

## Red/green evidence

- RED: `python3 tests/test_typed_generator.py` initially failed because the
  typed generator, emitter, committed typed TU, and manifest did not exist.
- RED: adding the seven-factory CMake target failed because
  `src/generated/typed_slice.cpp` did not yet exist.
- RED: the external 8x8 BC oracle exposed a source conversion mismatch:
  `Surface::from_rgba8` multiplied by a pre-rounded float reciprocal, unlike
  JavaScript's double divide followed by Float32 storage. The focused byte-7
  test failed before the conversion was corrected.
- RED: the scalar smoothstep test failed before the double-intermediate,
  single-f32-boundary overload was added.
- GREEN: the typed TU is emitted from immutable `TypedProgram` records only;
  it compiles under AppleClang strict warnings and all five external 8x8
  parity fixtures pass after the focused fidelity repairs.

## Capability truth

The locked `typed-ir-v1` slice emits five corpus programs:

- `filter/wormhole:clear`
- `filter/bc:bc`
- `filter/threshold:thresh`
- `filter/smoothstep:smoothstep`
- `mixer/channelCombine:channelCombine`

It covers typed functions, scalar/vector constructors and arithmetic,
read/write swizzles, texture/textureSize, dot, smoothstep, and typed bound
samplers/uniforms. The catalog is exactly seven sorted factories with the two
Task-5 factories; `filter/wormhole:deposit` is intentionally absent.

Still excluded before the next emission slice: loops, arrays, uint, matrices,
derivatives, structs, UBOs, adapters/render graph/CLI, the remaining stateless
programs, and all stateful/point-draw work.

The typed slice consumes 5 of the 212 frozen corpus programs, so 207 corpus
programs remain outside this emitter slice. The separate seven-key runtime
catalog additionally retains the two Task-5 proof factories; it does not make
a native factory for the `filter/wormhole:deposit` point draw-op.

## Generated artifact hashes

| File | SHA-256 |
| --- | --- |
| `src/typed_generated/typed_slice.cpp` | `3fe9d7c3764f0d98a0ac590434d1bbe8aff6d958268aeedde6ed48f81f950d9d` |
| `src/typed_generated/typed_manifest.json` | `2f4974fd75994aa2de3c7f9ca5ea3bded58805dffbf00978d1e4041b3721448a` |
| Task-5 `src/generated/synth_solid.cpp` | `4a88533b90ce71268461f2d6fc2ad71025deb830e403c878b424b7b0ef822363` |
| Task-5 `src/generated/filter_invert.cpp` | `06dd8cf0dacb86fb4ae11ebc822fd8103f648bc98d8272bc526c4507b2d4f1b7` |

The typed generator owns an exact separate `src/typed_generated` directory and
uses a whole-directory stage/backup swap. It rejects unexpected entries,
symlinks, and non-directory targets; injected backup/install failures restore
the original tree and leave no typed temporary directory. This leaves
Task-5's `src/generated` exact ownership intact: its generator check/write
coexists without admitting arbitrary foreign files. The old generator is not
called by the typed generator and its committed outputs remain byte-identical.
The two known unused items in immutable Task-5 solid TU have only exact
source-specific suppressions for AppleClang, Clang, and GNU; typed code remains
under `-Wall -Wextra -Wpedantic -Werror -ffp-contract=off`.

## Oracle provenance and frozen parity

Oracle source revision: `a024dc3a960cc44af454abc7aebce50456c194e6`.
Inputs are deterministic top-down RGBA8 surfaces using
`[(31x+17y+13t)%256, (11x+47y+29t)%256, (67x+19y+7t)%256,
(255-23x-37y-5t)&255]`; `A=5x3,t=1`, `R=5x3,t=11`, `G=3x5,t=23`,
`B=7x2,t=37`, nearest/bottom-left sampling, 8x8 output, fragcoord
`(x+.5,8-y-.5)`, time `.125`, seed `7`.

The implementation-time oracle ran under Node v24.7.0 from
`../noisemaker-for-cpu` using
`node tools/glslcpp/oracle_typed_slice.mjs`.
The persisted development-only script imported only
`node:crypto`, `canonicalKernelFactories`, `bindCanonicalKernel`, `runPass`,
and `Surface` from the sibling source modules (no npm dependency). For each
key it constructed the listed `Surface.fromRgba8` sources; explicitly applied
`Math.fround` to every declared float uniform; bound
`canonicalKernelFactories[key]` with 8x8, f32 time/seed and full resolution;
ran `runPass`; and SHA-256 hashed both the exact `destination.data` byte view
and `destination.toRgba8()`. It is never called by CMake, normal runtime, or
tests; the construction formula, parameters, source hashes, and results are
frozen below.

Float32 hashes are SHA-256 of exact little-endian Float32 bytes; RGBA8 hashes
are SHA-256 of output bytes. The C++ test includes standard SHA-256 known
vectors, selected float-bit probes per factory, alpha/orientation checks, and
actual rerenders (not clone-only comparisons).

| Key | Float32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- |
| `filter/wormhole:clear` | `5f70bf18a086007016e948b04aed3b82103a36bea41755b6cddfaf10ace3c6ef` | `5341e6b2646979a70e57653007a1f310169421ec9bdd9f1a5648f75ade005af1` |
| `filter/bc:bc` | `17e28b5ca13d1a21234aaaf6d3a2fc2f605f29413ad1baa1db1b6343010878e3` | `a10774e92b60d5558b372d349fcac02f3424fd92cd880f2701d1d00f3154767e` |
| `filter/threshold:thresh` | `61f2a88622e0a75332fb6994f5ae82a21c6889df4296e9c64b58f2de9d41d45e` | `63d3dc8653662baff87afd576ae73ecfc61d65c688cebfde7406153e6484ac65` |
| `filter/smoothstep:smoothstep` | `200eb65fed133e0640ed0165c4be24923e6fda1c236c3ea8b5d07f8747566b45` | `340558b647177c7f72bbd4b2fcbecef4facfd780a5e6fbfaf7231961895058a7` |
| `mixer/channelCombine:channelCombine` | `8bd32d6a3e760ed40d064c8671aec9e9ce7e491d666083c5cf2785224fb4a290` | `a5ac13cccc6fdb4d53bd7fefc545b7fedcbf5cca1ec93b7ab51fe746438c342f` |

The frozen oracle uses explicitly f32-bound uniform inputs. The older
canonical JavaScript path leaves some supplied scalar uniforms as raw Numbers;
that quirk is excluded because this port's typed binding ABI stores declared
`float` values at its f32 boundary.

## Focused post-review verification

- `python3 tools/glslcpp/generate_kernels.py --check` passed with the typed
  directory present.
- Typed rollback tests passed for injected first/second swap failures and a
  symlink owned target, while preserving an unrelated Task-5 generated file.
- Typed generator adversarial tests passed for direct traversal/reserved-device
  output names, unexpected directory and FIFO owned entries, committed-output
  tamper detection, and a deliberately failed rollback restoration. The latter
  raises a specific `GeneratorError` and retains the recoverable backup rather
  than deleting it.
- Debug configure/build and `build/noisemaker-cpu-tests` passed with 63 tests,
  including all five parity fixtures and direct missing/wrong binding tests for
  BC, threshold, smoothstep, and channel-combine.

## Final build verification

- `cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug`
- `cmake --build build --parallel`
- `build/noisemaker-cpu-tests` (63/63 passed)
- `ctest --test-dir build --output-on-failure` (1/1 passed)
- `cmake -S . -B build-release -DCMAKE_BUILD_TYPE=Release`
- `cmake --build build-release --parallel`
- `build-release/noisemaker-cpu-tests` (63/63 passed)
- `ctest --test-dir build-release --output-on-failure` (1/1 passed)
- `cd ../noisemaker-for-cpu && node tools/glslcpp/oracle_typed_slice.mjs` (all five frozen oracle rows passed)
