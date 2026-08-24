# Task 28 review-fix report

Date: 2026-08-11

Review authority: `docs/port-engineering/task-28-implementation-review.md`,
SHA-256 `c740a5b9f3e4094a4f5cfaf6e2f1d0a40d531b35c922ea0871ff4a5694ebc898`.

## Result

All three Important findings were repaired with focused RED/GREEN tests.  No
generated output, runtime, parser, semantic analyzer, IR schema, corpus,
`glsl_types.hpp`, or CMake file changed.

## I1: independently fail-closed emitter

RED reproduced both reviewed bypasses: a re-keyed exact Rotate tree and a
separately parsed/analyzed foreign-key Rotate source each emitted a matrix
return with an absent carrier.  The exact and foreign carrier variants already
rejected.

The emitter now first detects whether a program has any matrix-return function.
In such a program it rejects every matrix-return declaration/definition and
every matrix constructor, matrix-valued call, and matrix-containing binary
expression unless the visited object is the corresponding exact object from
the emitter's independent Rotate authentication.  Historical programs with
non-returning, non-escaping matrix arithmetic retain their existing behavior;
no generic matrix capability was added.

GREEN covers two foreign trees crossed with absent, exact, and foreign carriers
(six emitter rejections), plus the validator's unchanged foreign absent-carrier
rejection and exact Rotate acceptance/emission.

## I2: complete negative, carrier, and identity proof

The exact single-axis set now contains 83 named candidates and 83 matching
preconditions.  Sorted-name SHA-256:
`5f6d408f883906d19fdd2c8de10c19ba57291f1821d00cbdfb4a9486de70ecb8`.
For every candidate the test proves the selected coordinate changed and every
disjoint protected coordinate remains equal, then separately requires profile,
validator, and emitter rejection.

The set covers source/key/status, declaration and function order/cardinality,
resources, loop/call graph proof, declaration/builtin interface identity,
function/signature/return/parameter, local symbol/type/storage/initializer,
return shape, constructor type/kind/arity/order/children, call
callee/signature/arity/argument, and matrix-parent type/operator/order/role.

Additional matrices cover:

- all 60 combinations of five define states, three carrier states, two caller
  hashes, and two numeric modes; exactly one combination accepts;
- coexistence with each of the seven other per-program carrier categories,
  rejected independently by validator and emitter;
- seven separately analyzed source alternatives: constructor order,
  helper-local return, second call, stored result, vector-matrix, row-major
  custom lowering, and generic matrix helper; each is distinct and rejects at
  all three boundaries;
- a recursively rebuilt equal tree authenticating its own four new objects,
  followed by patched authenticators returning the original tree's objects;
  both validator and emitter reject identity-based completion.

Focused closure: 1 test in 0.787 seconds, OK.  Complete Task28 class after all
repairs: 7 tests in 182.896 seconds, OK.

## I3: executable table and witness authentication

The Python representation now authenticates:

- all six matrix-mode enum names and numeric IDs;
- both return-shape enum names and numeric IDs;
- mode-name strings and per-mode return-shape association;
- the exact by-value `task28_local` helper body;
- each switch arm's exact constructor, multiplication, and helper form;
- the default `invalid_argument` throw;
- mode/name/shape return fields, four exact matrix-lane extractions, and two
  product-lane extractions.

The reviewed `helper_local` substitution from `task28_local(c,s)` to a direct
constructor was first observed as RED (`parser_equal=True`) and now changes the
authenticated representation while leaving oracle bytes and numeric values
unchanged.  An additional 618-token executable-region mutation pass tampers
each independently tokenized switch/helper/witness field and requires parse
rejection or an unequal authenticated representation.  The original >300
constant-table mutation pass remains.  Native execution remains all six modes
across all six rows (36 executions) plus invalid-enum rejection.

## Verification

- Strict Task15-28 oracle-generator chain: `TASK15_28_ORACLES_OK`.
- Strict canonical generator and corpus chain: typed slice OK (128 programs),
  corpus OK, `GENERATOR_CORPUS_OK`.
- Fresh warnings-as-errors Debug build/CTest: 1/1 passed, 6.69 seconds.
- Fresh warnings-as-errors Release build/CTest: 1/1 passed, 0.64 seconds.
- Fresh ASan+UBSan Debug build/CTest with leak detection disabled on Apple and
  halt-on-error enabled: 1/1 passed, 15.35 seconds.
- Python compilation of both changed Python files: `PY_COMPILE_OK`.
- Fresh full Python discovery: 179 tests in 1986.945 seconds, OK.

The first full-discovery attempt was intentionally interrupted and discarded.
An earlier combined oracle/corpus command used the wrong corpus filename and
lacked `set -e`; its corpus portion was discarded.  Both were rerun cleanly as
the strict evidence above.

Generated C++ is byte-identical, so the accepted Task28 stack and AArch64 ABI/
disassembly results remain applicable and were not rerun.

## Final SHA-256

```
904ac0df016a6128cb5dcce8bc28fbee2ca8a78eb40faba9fa91601effd29b02  tools/glslcpp/emit_typed_cpp.py
ee5778035f3002b4d05096b13850a79c2e81ba3ccdc9b1fcece0dc40aa3a50c1  tests/test_typed_generator.py
5a8c0ac8447391478d204480bf2999a8d8077e5e3c8af6775b57f5ee91be2d55  tests/test_generated_kernels.cpp
b53e020b990a88d17de7fcaaa29965c1304cad510e2888cdd4e54ca98900763e  src/typed_generated/typed_slice.cpp
612d35229abf0580932cfaf11785311359afe29f20f1ebef5fb925cc91de044e  src/typed_generated/typed_manifest.json
372d1f69e1e7db772ddebc05945a714527b22b35f87ca3160bbb8eb85135a4ac  include/noisemaker/generated/catalog.hpp
55fee138f1477d183cc1e007e89b104cb4b4d126de9b1688844879e73be121d6  tests/test_typed_slice.cpp
37e71f566d5b8d5e1abf68fee1b27338898e4afacb116764824274dfda6780d8  include/noisemaker/glsl_types.hpp
bca6b4ab77d26c72449ef8d7a66d5832fdc939ebb35a85211b7684dde62216d5  CMakeLists.txt
```

No Git action was performed.  After the full suite exits green, this report and
its SHA-256 sidecar are the handoff for independent re-review.
