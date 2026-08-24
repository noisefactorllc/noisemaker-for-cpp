# Task 7B body semantic frontier report

## Scope and result

Implemented the remaining immutable body semantic/type frontier only in
`.`.  All 212 pinned programs now
produce typed function bodies.  The checker reports `body_success: 212` for
revision `a024dc3a960cc44af454abc7aebce50456c194e6`.

No Git command, sibling mutation, dependency download, CMake-input change,
C++ runtime/emitter change, generated-kernel change, branch, worktree, or PR
was performed.

## Red/green evidence

The first body contracts failed as expected: four failures exposed the former
`body_status: not analyzed` boundary and missing conversion/condition checks.
After implementation and review repairs, the focused semantic suite is green (21 tests), and the
corpus checker has zero semantic failures: 212 / 212.

## Semantic API

- `frontend/body_semantic.py` performs lexical scope, local shadowing,
  strict scalar/vector/matrix/array/struct construction, lvalues and writes,
  operators, indexing/swizzles, user calls and ABI directions, control flow,
  and observed builtin/resource checks.
- `TypedExpression` now retains immutable literal lexemes/booleans, operators,
  callee/signature identity (positive user signature IDs and stable negative
  builtin IDs), member/swizzle name, constructor target, child
  operands, exact type, span and value category.  A later emitter can consume
  typed IR without consulting the parser AST.
- The normalizer preserves declared varying types independently of its legacy
  varying-name output.  These are source interface declarations, not inferred
  runtime bindings.
- Metadata compile-time define defaults are selected statically during corpus
  analysis.  This preserves valid selected GLSL scopes rather than lowering
  mutually exclusive source branches into invalid runtime scopes.
- `check_semantics.py` validates Task 6 first, walks all programs in stable
  manifest order, aggregates deterministic diagnostics, and emits stable JSON.

Locations are normalized-source offsets and line/columns.  The JSON readiness
artifact is `docs/port-engineering/task-7b-readiness.json`; it has no
absolute paths or timestamps.

## Measured readiness

```json
{
  "revision": "a024dc3a960cc44af454abc7aebce50456c194e6",
  "body_success": 212,
  "effects": 167,
  "passes": 212,
  "generated": 208,
  "adapter": 4,
  "keyed_runtime": 211,
  "draw_op_overrides": 1,
  "builtin_names": 47,
  "resolved_call_names": 558,
  "texture_programs": 185,
  "derivative_programs": 18,
  "emission": "not attempted",
  "compile": "not attempted"
}
```

## Verification

All required gates are green:

```text
python3 tests/test_corpus.py                         # 9 passed
python3 tools/glslcpp/check_corpus.py --check       # ok
python3 tests/test_semantic.py                       # 21 passed
python3 tools/glslcpp/check_semantics.py --check    # bodies ok (212 programs)
python3 tools/glslcpp/check_semantics.py --report   # deterministic JSON
python3 tests/test_generator.py                      # 7 passed
python3 tools/glslcpp/generate_kernels.py --check   # passed
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug         # passed
cmake --build build --parallel                       # passed
build/noisemaker-cpu-tests                           # 55 passed
ctest --test-dir build --output-on-failure           # 1/1 passed
```

## Remaining boundary

The semantic front end is now a strict typed input for future emission.  Broad
C++ code generation, runtime builtin implementations, pass graph/metadata
registration, CLI/DSL work, and stateful/particle effects remain unattempted.

## Review repair addendum

Independent review identified declaration-initializer, variant, strict-builtin,
and emitter-identity gaps.  They are now closed test-first:

- 215 source global initializers across 73 programs are typed and retained in
  `TypedDeclaration.initializer`, checked in source order with GLSL constant
  initializer rules.
- Typed literals retain both original lexeme and semantic value; 32-bit
  unsuffixed hexadecimal literals are signed `int` bit patterns, while an
  explicit `uint(...)` constructor establishes the unsigned target type.
- `TypedProgram` retains declared varying symbols and injected
  `gl_FragCoord`; typed identifier/declaration nodes retain their exact Symbol.
- Builtin families are strict and table-driven, including vector boolean
  `mix` selectors and `degrees`; constant out-of-bounds indexing is rejected.
- Semantic JSON reports exact operator lexemes, not merely AST expression
  categories.
- The semantic gate now validates static one-define-at-a-time metadata
  variants: exactly 622 candidate values and 646 pass-variant checks, all
  successful.  This includes the previously missed hatch/strokes `degrees`
  paths and both curl `RIDGES` choices.

The resolver is now declarative: every observed builtin name maps to a
reusable signature family and a family matcher, rather than a name-specific
conditional chain.  The repair added direct valid/invalid checks for GLSL's
directional `min`/`max`, `mod`, `pow`, and `step` overloads.  In particular,
vector-first scalar forms are accepted only where GLSL specifies them.

Constructor/operator review repair added GLSL ES matrix/vector conversion
rules: narrowing vector conversion, exact matrix-component vector construction,
and matrix-to-matrix conversion. Ordered relational operators now accept only
same-type scalar numeric operands; vector relational operations remain the
explicit relational builtins.

The final constant-expression repair centralizes signed-int constant evaluation
for global declarations, lexical local declarations, extents, and static
index-bounds checks. It supports the admitted arithmetic, bitwise, shift and
unary forms with 32-bit behavior and rejects uint/bool/nonconstant/divide-zero
or nonpositive extents. Local `const int` values are scoped and shadowed with
their block lifetime.

The repaired readiness JSON measures `body_success: 212`,
`global_initializer_success: 215`, `variant_candidates: 622`, and
`variant_success: 646`.
