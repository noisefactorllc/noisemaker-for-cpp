# Task 27 independent implementation review

## Verdict

- **Code/production implementation: PASS**
- **Frozen implementation/test specification: FAIL**
- **Critical findings: 0**
- **Important findings: 3**
- **Minor findings: 0**
- **Blockers: the three Important verification gaps below must be fixed and re-reviewed before Task 27 acceptance**

This review was read-only with respect to the repository and Git state. The
implementation-report SHA-256 was independently authenticated as
`945f837aeaf55c8413b602b4bcfecd948e34be5b661c7ed41392a832a77dc4c7`.

## Confirmed implementation evidence

The production implementation is narrowly scoped and source-locked:

- `tools/glslcpp/frontend/perlin_scalar_uint_xor_profile.py:109-209`
  authenticates the exact profile/key/caller digest, raw and normalized bytes,
  exact `DIMENSIONS=2` define, whole program/interface/function fingerprints,
  exact outer and inner expression objects, ordered operands, scalar-XOR
  cardinality, loop proof, and reachability partition. It returns the exact
  outer/inner objects; `apply` at lines 212-217 is an identity operation.
- `tools/glslcpp/generate_typed_slice.py:1327-1348,1779-1791,1962-1966`
  independently authenticates the validator carrier, admits only object-
  identical `uint/uint -> uint` sites, preserves the existing vector-XOR path,
  and requires exact traversal of both sites.
- `tools/glslcpp/emit_typed_cpp.py:154-176,1043-1057,1570-1574`
  independently authenticates the emitter carrier, emits direct binary `^`
  only for the two exact objects, preserves vector `glsl::bitwise_xor`, and
  requires exact emission of both sites.
- Generated `hash3` at
  `src/typed_generated/typed_slice.cpp:12043-12055` contains the exact direct
  left-nested three-word reduction, unchanged float-constructor boundary and
  denominator, one distinct vector helper XOR, and no scalar helper.
- The executable mode dispatcher at
  `tests/test_generated_kernels.cpp:7967-7982` has six explicit, genuinely
  distinct switch arms and a throwing default. The native test at lines
  8011-8030 executes every arm, validates frozen result words, requires OR/AND
  divergence, distinguishes right association through the witness, and tests
  fail-closed invalid-enum handling. This does not repeat Task 26's vacuous
  mode failure.
- Current owned-file and sentinel hashes exactly match the implementation
  report. The manifest contains 127 programs with Perlin at ordinal 123 and
  ordered-key SHA-256
  `ed2b5d24ac3fb80520b2036acfc13c18df294c1583f76fe2957d00a6282fdd72`;
  the generated catalog has 129 entries. The public binder declaration and
  catalog mapping each occur exactly once.
- Fresh review execution passed the Task 27 oracle check, corpus check,
  canonical generator check, and all 7 `Task27PerlinTests` (35.715 seconds).
  The attempted review CTest path did not exist, so this review does not claim
  an independent native rerun; the preserved final native log records all
  three Task 27 native tests passing.

## Important findings

### I1. The required unsigned-vs-signed-JavaScript discriminator is not executable

**Evidence:** `Task27WordCase` stores only `numerator_bits` at
`tests/test_generated_kernels.cpp:7947-7950`. The direct-word test checks only
that the unsigned result converts to that value at lines 8014-8019. It never
stores or compares the frozen
`canonical_js_signed_numerator_f32_bits_le`, and never counts or requires the
high-bit rows where the two conversions differ. The Python transcription at
`tests/test_typed_generator.py:11876-11888` likewise transcribes only
`source_unsigned_numerator_f32_bits_le` and omits the signed-JS field.

The frozen brief requires the high-bit rows to distinguish source-unsigned
conversion from canonical-JS signed conversion. The current test proves the
selected unsigned value, but not that discriminator; a frozen semantic choice
can silently lose its explicit negative witness.

**Fix contract:** extend the C++ word row with the signed-JS numerator bits,
transcribe that field one-to-one from the frozen JSON, compute the signed
comparison through a defined two's-complement word-to-`int32_t` interpretation
without implementation-defined out-of-range unsigned casts, assert each
signed bit pattern, and require a positive exact count (the frozen eight rows)
where signed and unsigned numerator bits differ. Extend the Python parser and
tamper proof so changing either numerator column fails while the oracle JSON
is unchanged.

### I2. Task 27's mandated exhaustive profile/validator/emitter negative closure was not implemented

**Evidence:** the only Task 27 structural candidates are four mutations at
`tests/test_typed_generator.py:11920-11941` (outer operator, inner operator,
right association, and swapped operands), passed through the three boundaries
at lines 11943-11959. The basic profile test at lines 11766-11773 adds only a
wrong digest/profile and foreign key. There is no Task 27 test for the frozen
single-axis closure covering define name/value/order/count and `DIMENSIONS=3`,
raw/normalized source, declaration/interface/resource mutations,
function/signature/body/owner/path/span/category/parent-role mutations,
reachability/call-graph/loop-proof mutations, signed/mixed/vector/third-site or
equal-looking-object cases, mandatory/foreign/combined carriers, or independent
emitter-carrier history. The much broader exhaustive test immediately before
this class is explicitly Task 26 Smooth coverage and exercises the Smooth
profile, not Perlin (`tests/test_typed_generator.py:11007` onward).

The production authenticator appears to reject many of these through exact
fingerprints, but the accepted design expressly required analyzer-produced or
`dataclasses.replace` candidates, asserted single-axis preconditions, and
separate profile/validator/emitter rejection. Seven focused tests are not the
specified closure for this new authorization boundary.

**Fix contract:** add the frozen Task 27 exhaustive candidate matrix with an
explicit precondition for every candidate and pass every applicable candidate
separately through profile, validator, and emitter. Include the mandatory
carrier matrix and every combined-carrier coordinate, exact/foreign/mutated
trees, a value-equal reconstructed authorized site that is not one of the
authenticated objects where applicable, `DIMENSIONS=3`, and distinct signed,
mixed, vector/scalar, third-site, reassociated, parent/owner/path, call-graph,
loop-proof, interface/resource, and source mutation witnesses. Tests must
reach their named structural precondition before asserting rejection.

### I3. Task 27 generated isolation and Task 26 artifact reconstruction are report-only, not regression tests

**Evidence:** the Task 27 generation test at
`tests/test_typed_generator.py:11826-11841` checks only one Perlin block,
binder, manifest field, and header declaration. It does not remove Perlin,
regenerate the accepted Task 26 state, compare the three frozen Task 26
artifact hashes, compare all 126 historical blocks after ordinal
canonicalization, compare all historical manifest rows, or prove the carrier
is absent from every historical row/block. No Task 27 test contains the frozen
Task 26 hashes `df4aa212...`, `e7f7acd5...`, or `557ccdbe...`.

The existing isolation test at `tests/test_typed_generator.py:10920-11005` is
a Task 26 Smooth test: it removes Smooth while leaving the newly added Perlin
row in the supposed prior state (`10930-10936`). It therefore cannot establish
the Task 27 delta or reconstruct accepted Task 26, despite the implementation
report claiming both checks.

**Fix contract:** add a Task 27 isolation test that removes only Perlin from
the current spec, regenerates via the real pipeline, authenticates the exact
accepted Task 26 C++/manifest/header hashes, canonicalizes only namespace
ordinals and the common monolithic output hash, and proves all 126 historical
blocks, rows, binders, and catalog mappings unchanged. Prove exactly one new
Perlin carrier owner, no direct scalar XOR in historical blocks, exactly one
new declaration/mapping, and exact 127/129 counts and ordered hashes. Repair
the stale Task 26 phase reconstruction so its historical phase explicitly
excludes later Perlin rather than treating the live Task 27 tree as Task 26's
baseline.

## Scope and hardening assessment

No evidence of generic scalar-bitwise widening, runtime/parser/IR/CMake/corpus
change, `DIMENSIONS=3` admission, adapter addition, or public ABI drift was
found. The exact nine owned files and three frozen sentinels have the hashes
reported. The report's stack, release-disassembly, sanitizer, full Python, and
full native results are internally coherent, but acceptance remains blocked
because the frozen proof suite is materially incomplete at the three points
above.

No repository edit and no Git operation was performed by this review.
