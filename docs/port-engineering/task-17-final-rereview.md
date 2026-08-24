# Task 17 final remediation re-review

## Decision

**APPROVED for the requested Task 17 P1/P2 remediation scope.** I found no
P0, P1, P2, or P3 issue in the current whole-program proof, array/index
authorization, generated Task 17 output, or amended catalog-header ownership
contract.

This review was repository-read-only. I invoked no Git command and changed no
repository file. This report is the only file written.

## P1 adversarial reproduction

I independently reconstructed the three attacks from the rejected review for
both `filter/sharpen:sharpen` and `filter/sobel:sobel`:

1. append a cloned `amount` declaration as the fresh required uniform
   `forgedExtra` and append it to `ResourceRequirements.uniforms`;
2. append only `forgedExtra` to `ResourceRequirements.uniforms`;
3. append a fresh output declaration `forgedGlobalArray` using the canonical
   local `float[9]` type and append it to `ResourceRequirements.outputs`.

For each forged program I tested three proof states independently at both
boundaries: the retained authentic proof, a cleared proof, and an
attacker-updated proof whose `whole_program_sha256` was recomputed from the
forged program. The result was **36/36 rejected, 0 accepted**. Every validator
case raised `GeneratorError: malformed fixed-nine whole-program profile`; every
emitter case raised `TypedEmissionError` with the same reason.

The attacker-updated variant does not establish authority because
`fixed_nine_table_proof.py:39-42` pins an independent digest for each exact
program. Reconstruction hashes the complete immutable semantic program profile
at lines 55-64, then compares it to that pin at lines 87-92. A dataclass-field
census confirmed that the fingerprint contains every current `TypedProgram`
field except `fixed_nine_table_proof`, which is deliberately cleared and
reconstructed. It includes key, raw and normalized source, declarations,
functions, resources, body status, local types, structs, UBOs, interfaces,
builtins, counted-loop program proof, and define provenance. Raw/normalized
source, empty defines, and the caller source hash are also independently pinned
at lines 67-76.

Both boundaries rebuild counted-loop/counter evidence, clear the stored
fixed-nine proof, and independently reconstruct it before accepting the stored
proof (`generate_typed_slice.py:748-796`, `emit_typed_cpp.py:202-217`). Thus a
retained, absent, or self-recomputed proof cannot rescue a noncanonical program.

## Exact array authorization

The prior blanket array admission is gone.

- Validator declaration admission requires an exact proved symbol ID, span,
  and displayed type (`generate_typed_slice.py:733-746`).
- Validator store/read admission requires the exact proved tuple
  `(array symbol ID, literal/index symbol ID, index-expression span)`
  (`generate_typed_slice.py:785-794,979-996`).
- Emitter index admission independently requires a proved array identity and
  type, then the exact literal/index symbol and span (`emit_typed_cpp.py:490-512`).
- Emitter array declaration lowering additionally checks proof presence,
  no initializer, exact declaration span/type, exact symbol ID, and exact name
  (`emit_typed_cpp.py:827-838`).

The function-body pin plus the whole-program pin also prevent additional,
relocated, renamed, retyped, or globally stored arrays from reaching those
site-specific authorization maps.

## P2 generator ownership

The design is now explicitly amended rather than silently violating the
earlier frozen file map. `task-17-implementation-design.md:49-53` lists
`include/noisemaker/generated/catalog.hpp` as generator-owned, and lines 60-66
record the amendment and its rationale. The current design SHA-256 is
`538a6ca49b0dc729d3b287dd091cf01ada6e80f0f5473a0dc6b247f638bbb8cf`,
matching the implementation report.

The ownership claim is implemented and tested:

- `render_catalog_header` renders the full sorted factory surface and the file
  carries a generated/do-not-edit marker (`generate_typed_slice.py:150-175`).
- `--check` byte-compares the header to that render
  (`generate_typed_slice.py:1155-1169`).
- `--write` writes the rendered bytes through a same-directory temporary and
  atomic replacement (`generate_typed_slice.py:1202-1216`).
- The regression test byte-compares the checked-in header with the canonical
  render and requires both Task 17 declarations
  (`tests/test_typed_generator.py:372-380`).

Fresh ownership/drift verification passed, and both the direct public factory
declarations and generic `generated::bind(key, bindings)` paths are covered by
native tests.

## Generated output, counts, and oracles

Independent inspection found:

- **110 typed entries**, unique and sorted; **110 generated manifest entries**,
  unique; **112 public factory declarations**, unique; **100 public-unported
  corpus programs**.
- Each Task 17 key appears exactly once in the generated manifest.
- Sharpen emits one `std::array<double, 9>{}` and one
  `std::array<glsl::Vec2, 9>{}`, 18 literal-index stores, and two `[i]` reads.
- Sobel emits two `std::array<double, 9>{}` and one
  `std::array<glsl::Vec2, 9>{}`, 27 literal-index stores, and three `[i]` reads.
- Both pixels remain `noexcept`; their generated namespace slices contain no
  `.at(`, `std::vector`, `new`, or `malloc`.
- `node task-17-oracle-generator.mjs --check` returned
  `ok task-17-oracles.json`.

Frozen oracle hashes still match:

- generator: `ab607be447bf86457267e8b76298e24961065407db54039c206d21a6b85dfb9e`
- JSON: `6a68386e0244a2c5ec0b183e4e5e4e3e59f01c30414f8854a041d871637c907a`
- report: `4f7848798975d6025a138cbb9eb77080987a64188e3867dc7f90bc13d1bdec95`

All 14 repository-file hashes listed in the amended implementation report
match the current files. The current implementation report SHA-256 is
`b6ccdd66a4b518e9c37de78711190b81bc7c03bfea503227d15375efcb49232b`.

## Fresh verification evidence

- Independent adversarial matrix: **36 rejected / 0 accepted**.
- Focused semantic/generator/proof/ownership suite: **6/6 passed** in 0.371 s.
- `python3 tools/glslcpp/generate_typed_slice.py --check`:
  `typed slice ok (110 programs)`.
- Frozen Task 17 oracle regeneration check: passed.
- Existing instrumented Debug native binary: **101 PASS**, exit 0, no failure
  marker.
- Existing instrumented Release native binary: **101 PASS**, exit 0, no
  failure marker.
- Reported repository hashes: **14/14 matched**.

The native binaries were not rebuilt in this read-only re-review; their
generated-source and header inputs are byte-identical to the hashes in the
amended implementation report, and both complete binaries were executed fresh.

## Findings

No P0-P3 findings.
