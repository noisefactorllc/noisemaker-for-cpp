# Task 28 independent implementation review

Date: 2026-08-11

## Verdict

- **Production/spec PASS: NO**
- **Critical findings: 0**
- **Important findings: 3**
- **Minor findings: 0**
- **Blockers:** the three Important proof/authorization defects below must be
  corrected and independently re-reviewed before Task 28 is accepted.

The submitted implementation report authenticates exactly as
`a78042ed7b50ca406e87531d23bc1bcec9cd0a0c957044902528fa98abbfaea3`.
All frozen Task 28 artifact sidecars authenticate. Current owned-file and
isolation hashes match the report. The exact canonical state is 128 typed
programs, 130 unique public mappings, Rotate ordinal 67, typed ordered hash
`30f0333c...`, and public ordered hash `102f5436...`. The generated Rotate block,
six public fixtures, binding checks, and six-by-six native matrix computations
are numerically consistent with the frozen oracle. The profile itself is
strongly source/tree/interface locked, and the validator independently
authenticates and traverses the exact objects.

## Important findings

### I1. The emitter still admits an unauthenticated foreign-key matrix return

**Evidence:** `tools/glslcpp/emit_typed_cpp.py:155-177` requires the Rotate
carrier only when `program.key == ROTATE_KEY`. Its pre-existing generic paths at
`tools/glslcpp/emit_typed_cpp.py:1013-1018`, `1104-1107`, and `1491-1520` still
emit `mat2`, `mat2 * vec2`, and a by-value matrix-return function without
checking that those exact objects were authenticated. A direct read-only probe
rebuilt the exact Rotate tree with only its key changed to
`filter/rotate:foreign`: `validate_capabilities(..., carrier=None)` correctly
rejected `unsupported matrix return type`, but
`render_typed_cpp(..., carrier=None)` accepted it and emitted
`return glsl::Mat2(...)`. This violates the frozen carrier matrix's
`foreign + absent -> never gain matrix return` rule and the required
independent fail-closed emitter boundary.

**Fix contract:** make matrix emission fail closed independently of the program
key. A matrix-return function, matrix constructor, matrix-valued call, or
matrix binary expression must be emitted only when the visited objects are the
exact independently authenticated Rotate helper/constructor/call/parent.
Retain the existing final exact visitation counts. Add synthetic emitter tests
for the re-keyed exact tree and an independently analyzed foreign matrix-return
program with absent/exact/foreign carriers; all must reject. Confirm the
validator continues rejecting the same foreign absent-carrier case.

### I2. The claimed 59-candidate negative/carrier/identity matrix is incomplete

**Evidence:** the only Task 28 negative dictionary at
`tests/test_typed_generator.py:12577-12636` contains **58**, not 59, axes
(independent AST count). The loop at `12637-12656` checks only that the selected
coordinate has its replacement value; it does not prove protected-coordinate
equality. It omits the frozen matrix's separate exact/absent/foreign carrier
cross-product, wrong caller hash, numeric mode, define mutations, coexistence
with every other carrier, analyzer-produced code-shape alternatives, and forged
old-object validator/emitter authorization on an equal reconstructed tree.
The equal-tree check at `12544-12548` reaches only the profile and proves only
that new objects authenticate. In contrast, the submitted report claims
"59 distinct one-axis mutations" at all three boundaries.

**Fix contract:** implement the complete named Task 28 candidate and
precondition set promised by the frozen brief/design. Require an exact
candidate/precondition key set, verify the selected coordinate changes and all
protected coordinates remain equal, and run every tree mutation separately
through profile, validator, and emitter. Add the full carrier/caller-hash/
numeric/define cross matrix and every existing carrier coexistence case. Add
analyzer-produced alternate constructor/local-return/second-call/stored-result/
vector-matrix/row-major/generic-matrix candidates. Authenticate a recursively
rebuilt equal tree's own objects, then patch validator and emitter
authenticators to return the original tree's objects and prove identity-based
completion rejects. Correct the report's candidate count to measured evidence.

### I3. The executable-table authenticator does not authenticate switch or witness semantics

**Evidence:** `_task28_parse_executable_tables` at
`tests/test_typed_generator.py:130-159` parses only three constant initializers
and the six `case` labels. It does not parse enum numeric IDs, return-shape
associations, witness fields, switch-arm expressions, or the returned witness.
The `>300` tamper loop at `12736-12750` is bounded by
`TASK28_NATIVE_ORACLE_TABLE_END`, which occurs at
`tests/test_generated_kernels.cpp:8097`; the executable switch begins later at
`8118`. Therefore none of the executable arm/witness tokens is tampered or
authenticated. A concrete read-only mutation replaced the
`helper_local` arm's `matrix=task28_local(c,s)` with the exact direct
constructor while retaining the fabricated `local_return` shape; the Python
parser returned an identical authenticated structure (`parser_equal=True`).
The native expected bits would also remain identical, so the required
genuinely distinct by-value local-return witness is presently defeatable.

**Fix contract:** extend the authenticated representation to include exact
enum IDs/names, return-shape enum and per-mode association, every switch arm's
actual constructor/multiply/helper form, default throw, lane/product extraction,
and returned witness fields. Tamper each executable token/field independently,
including replacing `task28_local` with a direct constructor, and require the
authenticator to reject while oracle JSON bytes remain unchanged. Keep the
native all-36 execution and invalid-enum checks, and add a structural witness
that cannot be satisfied by merely setting the shape enum.

## Verified clean areas

- `rotate_mat2_return_profile.py` authenticates raw/normalized source,
  declarations/resources/interface, exact helper/constructor/call/parent,
  matrix cardinality, and returns exact object identities.
- `generate_typed_slice.py` admits only the exact carrier in the canonical row,
  applies it without mutation, independently authenticates in the validator,
  bypasses only the exact helper return, and records exact traversal.
- Canonical generated spelling remains column-major `Mat2(Vec2(c,-s),
  Vec2(s,c))`, by value, with one direct matrix-vector use; no runtime,
  `glsl_types.hpp`, CMake, or corpus widening was found.
- Real post-Task28 removal of Rotate regenerates the exact three Task 27
  artifacts (`aa15e469...`, `f25401d4...`, `b82abfa0...`). Current generated
  artifacts and catalog counts/hashes match the frozen projection.
- The native six-mode implementation has explicit arms, actual `Mat2`/`Vec2`
  calculations, incorrect-mode numeric divergence, exact/local value identity,
  and invalid-enum rejection. The defect is that its structural distinctions
  are not independently authenticated.
- The submitted full 176-test, Debug/Release CTest, sanitizer, stack, and AArch64
  disassembly evidence is internally consistent with current bytes; this review
  found no contrary runtime/ABI evidence. A focused Task 28 suite was started
  but intentionally interrupted during its expensive full-corpus reconstruction
  after the source-level defects above were independently reproduced.

## Re-review gates

After fixes, rerun the focused Task 28 profile/carrier/reconstruction/table
tests, canonical generator/oracle checks, native Task 28 tests, fresh
Debug/Release CTest, sanitizer, and any full-suite gates affected by test or
emitter changes. Re-run stack/disassembly if production emitter output changes.
No Git action was performed.
