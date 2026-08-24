# Task 20 final acceptance review

## Decision

**APPROVED.** The completed Task 20 Sacred Geometry implementation has no
P0, P1, P2, or P3 correctness, least-privilege, verification, or scope
finding.

This was a read-only audit. I used no Git command, changed no repository file,
and wrote only this requested review artifact outside the repository.

## Reviewed implementation identities

- `tools/glslcpp/frontend/sacred_geometry_compatibility.py`:
  `96987d7418216113a712ab70e7180cf919e5c2942528cf00264f8777bc1ab0d4`
- `tools/glslcpp/frontend/fixed_affine_centers13_proof.py`:
  `ac82d95f7a79dacb9749a2241d15e92e533299c61bf97fbcf3e2c128226499bd`
- `tools/glslcpp/frontend/typed_ir.py`:
  `7e16d088d7ffe90b7b6cc11dfff27d9df413ff4ffcdd13f9648fc4c35c91272c`
- `tools/glslcpp/generate_typed_slice.py`:
  `ff9cc618c98255ed71714c0384e5f64b613a09f5540457cca4e38b133ad62594`
- `tools/glslcpp/emit_typed_cpp.py`:
  `f8c9c21a8bc0590e2af78b892dc7504a55aafd8987a41e367a73f66a8de4ea11`
- `tools/glslcpp/typed_slice.json`:
  `bf86b4e7e5e26a89a27f23009eb5a7589618ec54b469b79ffa4cad343f66ccb0`
- `src/typed_generated/typed_slice.cpp`:
  `3b56d4f69b4477c7306ac659ec6a59c64f0a929d72a56921c28eb9961e82eef8`
- `src/typed_generated/typed_manifest.json`:
  `8840aedc26a73c2af8e871cac4a2a41ffb8f107dbaea870902e9b22340614f41`
- `include/noisemaker/generated/catalog.hpp`:
  `292c212ffb77e2bc597749899c7211a8134027f556c6b6f5eb03412a037aef6a`
- `tests/test_typed_generator.py`:
  `ece8739c40e37e7e9ac42054d4c647a1f4cdb2543bbd92ed0c2ec0dec275fb27`
- `tests/test_typed_slice.cpp`:
  `acfe7fe5483188b3936eb3d02b15f1187f185c2474f341996ce4d764f07b31a0`
- `tests/test_generated_kernels.cpp`:
  `fba30769e2ac4e66a173a9fc1c61c2ec920483c6b3b347e9377242d5c6b3035d`

## Transform and proof contract

The compatibility transform is confined to the exact Sacred key, raw and
normalized source identities, interface identity, and frozen pre-transform
function and whole-program trees. It changes only the five authenticated Star
arithmetic nodes, requires empty Task 17-20 carriers before transformation,
and rejects duplicate, partial, already-transformed, source-drifted, or
proof-bearing inputs. Its nonmutating authenticator requires the exact frozen
post-transform function and whole-program trees.

The Task 20 proof is a dedicated optional `TypedProgram` carrier rather than a
general array feature. It independently derives the exact `centers@73`
ownership, three store regions, seven index sites, loop and guard ownership,
13 dynamic stores, 26 circle reads, 156 line-endpoint reads, 182 maximum reads,
complete disjoint initialization, dominance, no later writes, and no
copy/alias/escape. Derived facts are compared with frozen source, interface,
canonical factory/runtime, function, body, routing, RHS, enclosing-expression,
and post-transform hashes.

## Validator and emitter least privilege

Both boundaries require the exact Sacred compatibility and `glsl-f32`
metadata carriers, authenticate the post-transform tree without reapplying the
transform, clear all four top-level proof carriers, reconstruct counted and
discarded-counter facts, rebuild Task 17 -> Task 18 -> Task 19 -> Task 20, and
compare the caller-carried complete proof chain.

The validator admits Task 20 array operations only by the authenticated symbol,
exact span, and lvalue/rvalue role. The emitter additionally scopes admission
to `fruitMask` signature 40. Declaration lowering is limited to the one proved
`centers` declaration. Foreign keys, wrong or missing metadata, cleared/stale/
forged Task 20 proofs, forged predecessor proofs, alternate types, and
unproved indices remain closed.

## Generated output, catalog, and parity

The committed generated Sacred namespace contains exactly one
`std::array<glsl::Vec2, 13>` alias, exact 8-byte `Vec2` and 104-byte table
assertions, one `Centers13 centers{}` declaration, and seven scoped subscripts.
The Star `j` expression uses double arithmetic with no `%`, `integer_mod`, or
integral cast-back. Sacred has one sorted slice entry, one manifest entry, one
public declaration, one factory definition, and one catalog entry. Inventory
is 114 typed programs, 116 public factories, 96 unported programs, and 212
corpus programs.

The ten native case names and F32/RGBA8 hashes match the independently checked
Task 20 oracle exactly. The separate Star test covers every `starPoints` value
from 5 through 12 and requires canonical `0x7fc00000` qNaN RGB with exact-one
alpha for all 851 pixels.

## Verification evidence

Independently rerun during this review:

- all seven focused Task 20 transform, proof, boundary, tamper, and exclusion
  tests: 7/7 passed;
- committed typed generation check: passed;
- direct Task 20 oracle generator check and ten-case identity comparison:
  passed;
- generated/source/catalog count and code-shape assertions: passed.

Accepted completion evidence supplied with the final audit request:

- full Python discovery: 113/113 passed;
- canonical corpus, semantics, kernels, and typed checks: passed;
- Task 15-20 proof oracles: passed;
- Debug and Release CTest: passed;
- ASan and UBSan CTest: passed; Apple ASan leak detection alone was disabled
  because that runtime rejects `detect_leaks`;
- Release stack frames are fixed at 320/64/176/96 bytes for the four Sacred hot
  functions, and scoped relocations contain no indirect or allocation target;
- reconstructed pre-Task20 output has zero normalized byte drift across all
  113 prior typed programs.

No acceptance residual remains.
