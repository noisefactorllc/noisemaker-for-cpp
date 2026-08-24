# Task 20: Sacred Geometry typed CPU port

## Outcome

Task 20 ports `synth/sacredGeometry:sacredGeometry` into the generated C++ CPU
slice without changing any previously ported program. The typed slice now has
exactly 114 generated programs, the public runtime catalog has exactly 116
factories including the two handcrafted factories, 96 of the 212 pinned corpus
programs remain unported, and Sacred Geometry appears exactly once in the
generated manifest and catalog.

No Task 21 work, Git operation, branch, worktree, pull request, publish, or
deployment was performed.

## Fidelity contracts

- Added the source-locked `sacred-star-number-division-v1` compatibility
  transform. It changes exactly the five typed-expression sites required to
  preserve canonical JavaScript Number division in `starPolygonMask`: the
  division, multiply, subtract, declaration of `j`, and the later read of `j`.
  It rejects partial application, duplicate application, source/interface
  drift, and every Task 17-20 proof carrier.
- Added the source- and interface-locked `fixed-affine-centers13-v1` proof.
  The proof reconstructs the one 13-element `Centers13` declaration, three
  static and thirteen dynamic stores, four read sites, 26 circle reads, 156
  line-endpoint reads, and the full 182-read maximum. It derives the nested
  loop facts and proves coverage, disjointness, dominance, no post-write, and
  no escape from typed IR rather than accepting metadata constants.
- Both validator and emitter independently clear and rebuild the Task 17 -> 18
  -> 19 -> 20 carrier chain and compare the exact predecessor/proof records.
  Authorization is limited to the exact `(symbol_id, span, lvalue/rvalue)`
  sites. Foreign arrays, proof reuse, mutated snapshots, malformed carriers,
  partial transforms, and interface/source drift fail closed.
- Emission is scoped to Sacred Geometry's exact `fruitMask` signature. It emits
  `using Centers13 = std::array<glsl::Vec2, 13>`, exact 8-byte/104-byte static
  assertions, one local `Centers13`, and exactly seven proved `std::size_t`
  subscripts. `starPolygonMask` emits `double j` and double arithmetic; it does
  not emit modulo or an integral cast for the repaired expression.

## Oracle and native parity

The frozen Task 20 oracle was authenticated before edits and its canonical
generator continues to pass `--check`. Native tests freeze ten 37x23 Sacred
Geometry cases, including full F32 and RGBA8 SHA-256 values, nine probes per
case, metrics, alpha, and repeatability. The exact 17 required bindings have a
missing/wrong-type rejection matrix. Star-point cases 5 through 12 verify every
one of 851 pixels: RGB is the canonical quiet NaN bit pattern `0x7fc00000` and
alpha is `0x3f800000`. A test-only discriminator separately proves canonical
Number division rather than the tempting integer-remainder translation.

The public catalog test locks all 116 sorted keys and keeps CRT/Degauss adapter
effects excluded.

## Generated isolation and resource evidence

A pre-Task20 113-program typed specification was reconstructed in memory and
run through the current generator. After normalizing only namespace ordinal
renumbering, all 113 prior generated program blocks are byte-identical:
`non_sacred_normalized_byte_drift=0`.

Fresh Release stack-usage and disassembly evidence for the Sacred hot path:

| Function | Release frame | Stack classification |
| --- | ---: | --- |
| `fruitMask` | 320 bytes | static |
| `lineSegmentSDF` | 64 bytes | static |
| `starPolygonMask` | 176 bytes | static |
| `pixel` | 96 bytes | static |

The largest known non-inlined hot chain is `pixel -> fruitMask ->
lineSegmentSDF`, 480 bytes total. The four prologues use fixed frame adjustments
(`0x140`, `0x40`, `0xb0`, and `0x60`). Scoped Release object relocations contain
239 direct branch relocations, all to known generated helpers, `noisemaker::f32`,
or math functions; the four disassembly blocks contain no `blr`, allocation
target, VLA, or `alloca`. Sanitizer `.su` files classify their instrumented
frames as dynamic because of sanitizer instrumentation; non-sanitized Debug and
Release builds classify the corresponding functions as static.

## Red/green and final verification

- Transform RED: import failed before the compatibility module existed. GREEN:
  both exact-shape and rejection tests passed.
- Proof RED: import failed before the affine proof module existed. GREEN: both
  exact proof and structural-drift rejection tests passed.
- Boundary RED: the new capability and explicit metadata contracts were absent,
  producing one failure and 21 errors. GREEN: validator/emitter boundary tests
  passed after exact carrier reconstruction and site authorization.
- Focused final Task 20 generator tests: 5/5 passed in 0.671 seconds.
- Full Python suite: 113/113 passed in 247.295 seconds.
- `check_corpus.py --check`: passed, 212 corpus programs.
- `check_semantics.py --check`: passed, 212 program bodies.
- `generate_kernels.py --check`: passed.
- `generate_typed_slice.py --check`: passed, 114 typed programs.
- Task 15, 16, 17, 18, 19, and 20 oracle generators: every `--check` passed.
- Fresh Debug Unix Makefiles configure/build: passed; CTest 1/1 passed in
  1.03 seconds.
- Fresh Release Unix Makefiles configure/build: passed; CTest 1/1 passed in
  0.26 seconds.
- Fresh ASan+UBSan configure/build: passed; CTest 1/1 passed in 2.60 seconds
  with `ASAN_OPTIONS=detect_leaks=0` and UBSan halt/stacktrace enabled. Apple's
  ASan runtime rejects `detect_leaks=1` as unsupported and aborts before test
  execution, so leak detection could not run on this platform; the sanitizers
  themselves otherwise completed cleanly.
- Three staged read-only implementation review gates returned APPROVED with no
  P0-P3 findings after their requested regression-strengthening fixes.

## Exact Task 20 file inventory

Exactly these 12 repository files changed:

| File | SHA-256 |
| --- | --- |
| `tools/glslcpp/frontend/sacred_geometry_compatibility.py` | `96987d7418216113a712ab70e7180cf919e5c2942528cf00264f8777bc1ab0d4` |
| `tools/glslcpp/frontend/fixed_affine_centers13_proof.py` | `ac82d95f7a79dacb9749a2241d15e92e533299c61bf97fbcf3e2c128226499bd` |
| `tools/glslcpp/frontend/typed_ir.py` | `7e16d088d7ffe90b7b6cc11dfff27d9df413ff4ffcdd13f9648fc4c35c91272c` |
| `tools/glslcpp/generate_typed_slice.py` | `ff9cc618c98255ed71714c0384e5f64b613a09f5540457cca4e38b133ad62594` |
| `tools/glslcpp/emit_typed_cpp.py` | `f8c9c21a8bc0590e2af78b892dc7504a55aafd8987a41e367a73f66a8de4ea11` |
| `tools/glslcpp/typed_slice.json` | `bf86b4e7e5e26a89a27f23009eb5a7589618ec54b469b79ffa4cad343f66ccb0` |
| `src/typed_generated/typed_slice.cpp` | `3b56d4f69b4477c7306ac659ec6a59c64f0a929d72a56921c28eb9961e82eef8` |
| `src/typed_generated/typed_manifest.json` | `8840aedc26a73c2af8e871cac4a2a41ffb8f107dbaea870902e9b22340614f41` |
| `include/noisemaker/generated/catalog.hpp` | `292c212ffb77e2bc597749899c7211a8134027f556c6b6f5eb03412a037aef6a` |
| `tests/test_typed_generator.py` | `ece8739c40e37e7e9ac42054d4c647a1f4cdb2543bbd92ed0c2ec0dec275fb27` |
| `tests/test_typed_slice.cpp` | `acfe7fe5483188b3936eb3d02b15f1187f185c2474f341996ce4d764f07b31a0` |
| `tests/test_generated_kernels.cpp` | `fba30769e2ac4e66a173a9fc1c61c2ec920483c6b3b347e9377242d5c6b3035d` |

