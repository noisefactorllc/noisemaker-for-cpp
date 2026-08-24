# Task 28 independent implementation re-review

Date: 2026-08-12

## Verdict

- **Production/spec PASS: YES**
- **Original Important findings addressed: 3/3**
- **New Critical findings: 0**
- **New Important findings: 0**
- **New Minor findings: 0**
- **Blockers: none**

The review-fix report authenticates exactly as
`6b47ee5fed7d431342fbd4455d5b7949808be6a06f72839c4089d0aae2535e67`.
The repair is confined to `tools/glslcpp/emit_typed_cpp.py` and
`tests/test_typed_generator.py`. Generated C++, manifest, catalog, native test
source, runtime, IR, corpus, CMake, and isolation files retain the submitted
hashes. No Git action was performed.

## Original finding dispositions

### I1 — unauthenticated foreign-key matrix return: ADDRESSED

`emit_typed_cpp.py:985-1008` now identifies matrix-return programs and rejects
every matrix constructor, matrix-valued call, and matrix-containing binary
expression unless the visited object is the exact independently authenticated
Rotate constructor/call/parent. `function()` and `function_declaration()` at
`1507-1536` independently reject any matrix-return function other than the
authenticated helper. Existing non-returning/non-escaping matrix arithmetic is
not widened or disabled.

The new test crosses both a re-keyed exact tree and an independently analyzed
foreign tree with absent, exact, and foreign carriers; all six emitter calls
reject. The validator still rejects the independently analyzed foreign tree
without a carrier as `unsupported matrix return type`. An independent direct
probe reproduced all six rejections, the validator rejection, and exact Rotate
acceptance with the exact carrier (`I1_DIRECT_PROBE_OK`).

### I2 — incomplete negative/carrier/identity matrix: ADDRESSED

The single-axis dictionary is now exactly 83 candidates and 83 matching
preconditions, with sorted-name SHA-256 `5f6d408f...`. For each candidate the
test asserts inequality, the selected replacement, and equality of every
disjoint protected coordinate before separately requiring profile, validator,
and emitter rejection. Independent AST inspection confirmed 83 axes.

The separate exhaustive matrix executes all 60 define/carrier/caller-hash/
numeric-mode combinations and permits exactly the one exact combination. It
rejects coexistence with all seven other carrier categories in validator and
emitter. Seven distinct analyzer-produced alternatives cover constructor
order, helper-local return, second call, stored result, vector-matrix,
row-major custom lowering, and a generic matrix helper. A recursively rebuilt
equal tree authenticates its own four objects; patched validator and emitter
authenticators returning the original objects both fail identity completion.

### I3 — executable switch/witness semantics unauthenticated: ADDRESSED

The parser now authenticates numeric IDs/names for both enums, mode strings,
per-mode return-shape association, exact by-value local helper body, witness
signature/prefix, all six complete switch-arm bodies, the default throw, and
the complete witness epilogue with mode/name/shape, four lane extractions, and
two product extractions.

The reviewed local-helper-to-direct-constructor substitution now changes the
authenticated representation. Independent token census found 618 executable
tokens; every token is mutated and must either fail parsing or produce an
unequal representation. The original constant-table tamper pass remains.
Native all-36 execution, wrong-mode divergence, local/direct value identity
with distinct shape, and invalid-enum rejection remain unchanged.

## Independent verification

- Five focused repair tests: **5 passed in 4.629 seconds**.
- Direct foreign-emitter/validator probe: **passed**.
- Canonical generator check: **typed slice OK, 128 programs**.
- Current generated artifact hashes remain exactly:
  - typed C++ `b53e020b990a88d17de7fcaaa29965c1304cad510e2888cdd4e54ca98900763e`
  - manifest `612d35229abf0580932cfaf11785311359afe29f20f1ebef5fb925cc91de044e`
  - catalog `372d1f69e1e7db772ddebc05945a714527b22b35f87ca3160bbb8eb85135a4ac`
- The fix report's fresh full verification is credible and internally
  consistent: 179 Python tests passed; strict Task15-28 oracle and canonical
  generator/corpus chains passed; fresh warnings-as-errors Debug and Release
  CTest passed; fresh ASan+UBSan CTest passed with the documented Apple leak
  setting and halt-on-error.
- Because generated C++ bytes are identical, the previously accepted stack,
  by-value AArch64 ABI, and disassembly evidence remains applicable.

Task 28 is accepted for the continuing port sequence.
