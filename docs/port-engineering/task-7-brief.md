# Task 7: complete semantic/type analysis for the pinned GLSL corpus

## Objective

Build a deterministic, fail-closed semantic/type frontier over the exact pinned
167-effect / 212-program corpus. Every admitted GLSL program must produce an
immutable typed IR with resolved symbols, overloads, lvalues, control flow, and
resource requirements. This is the only input the later broad C++ emitter may
consume.

This task does **not** widen C++ emission, add runtime builtins, modify CMake,
register effects, build the render graph/CLI/DSL, or claim that the corpus can
compile as C++. Preserve Task 5's two generated kernels byte-for-byte and Task
6's independently approved corpus.

## Fixed gates and provenance

- Revision `a024dc3a960cc44af454abc7aebce50456c194e6`.
- 167 effects, 212 passes/sources, 208 generated + 4 adapters, 211 keyed
  runtime programs + one `filter/wormhole:deposit` points override.
- Task 6's exact pinned-source audit is authoritative, including the 1,327-byte
  pinned `filter/text:text` source. Do not re-extract or mutate the corpus.
- Corpus parser facts measured before this task: 26 AST node kinds; 8,834
  declarations; 1,388 functions; 14,777 binary expressions; 3,863
  assignments; 1,743 `if`s; 186 `for`s; 4 `while`s; 262 ternaries; 59
  `break`s; 18 `continue`s. Recompute/report final counts from the committed
  corpus rather than trusting this note.
- Relevant families: 21 array programs, 13 matrix, 44 unsigned, 41 bitwise, 18
  derivative, 103 loop, 7 out/inout, 4 struct, one anonymous uniform block,
  60 overloaded user-function names, and 47 observed builtin names.

## Constraints

- Work only in `.`.
- Never invoke Git or any indirect Git operation. No branches/worktrees/PRs.
- TDD. Write the implementation report to
  `docs/port-engineering/task-7-report.md`, never add process docs to the
  repository.
- Use `apply_patch` for source/test edits.
- Do not modify sibling repos or download/build dependencies.
- Python 3 standard library only. No Node, network, sibling imports, `eval`, or
  `exec` in normal tools/tests.
- Normal CMake remains wholly unaware of Python/corpus sources.
- Do not mutate caller ASTs. Do not use variant/map/string lookup as a future
  per-pixel execution model; the typed IR exists to make later C++ statically
  bound.
- Stable, program-aware diagnostics. No first-overload, unknown-field,
  unknown-symbol, or unknown-type fallback.

## Useful read-only references

- Current sibling corpus-oriented discovery code under
  `../noisemaker-python/src/noisemaker_cpu` (locate the
  actual transpiler/codegen file; do not assume an outdated path). It is useful
  for inventory only: its heuristic type guesses/fallbacks are not semantic
  authority.
- Qt diagnostics and validator boundaries under
  `/tmp/noisemaker-cpp-research.5XGC2U/noisemaker-for-qt-main/qt/noisemaker/compiler`.
  The Qt Polymorphic DSL compiler is useful for stable diagnostics and
  fail-loud design, but it is separate from canonical GLSL semantics.
- Khronos GLSL ES 3.x type rules where corpus behavior needs confirmation.

## Parser and source spans

Retain Task 6's external `parse_program()` result compatibility while making
source positions first-class:

- Add a frozen `SourceSpan` carrying program key, start/end normalized offsets,
  and start/end line/column.
- Attach a span to every AST declaration, statement, and expression (or create
  a lossless immutable parsed-AST wrapper carrying those spans). Do not replace
  locations with token indices.
- Preserve the normalized source/interface in the parsed-program result so
  semantic diagnostics and future emission can be traced deterministically.
- Existing Task 6 source-location and all-212 parse gates must remain green.
- Diagnostics may initially use normalized-source coordinates; state this
  precisely in the report.

## Immutable semantic model

Suggested private modules under `tools/glslcpp/frontend/`:

- `span.py`: frozen `SourceSpan`.
- `diagnostics.py`: frozen `SemanticDiagnostic(code, span, message)` plus an
  aggregate/program-aware `SemanticError`.
- `semantic_types.py`: internable structural types: void; scalar bool/int/uint/
  float; vector(base,width); matrix(columns,rows); sampler kind; array(element,
  constant size); struct with stable symbol identity.
- `typed_ir.py`: frozen typed program/declaration/function/statement/expression,
  symbol, signature, interface, and resource-requirement records.
- `semantic.py`: two-pass analysis: collect structs/functions/globals first,
  then analyze initializers and bodies without AST mutation.

Every typed expression must carry its exact type, span, and value category
(`rvalue`, writable lvalue, readonly lvalue). Every identifier/member/function
reference resolves to a stable ID/signature, not an unresolved string.

## Required semantic rules

### Types, literals, and conversions

- Cover the actual corpus types: `void`, `bool`, `int`, `uint`, `float`,
  `vec2/3/4`, `ivec2/3`, `uvec2/3`, `bvec3`, `mat2/3/4`, `sampler2D`, arrays,
  and named/anonymous structs/uniform blocks. Reject unknown types.
- Strict GLSL ES behavior: no implicit numeric conversions and no contextual
  literal typing. Decimal integer literals are `int`; `u`/`U` literals are
  `uint`; decimal/exponent float forms are `float`; booleans are `bool`.
- Initializers, assignment, returns, function arguments, ternary arms, and
  overload selection require exact types. Numeric conversion happens only via
  constructors/casts.
- Narrow pinned-corpus rule: accept unsuffixed hexadecimal values through 32
  bits as signed `int` bit patterns (`0xFFFFFFFF` is `-1`), enabling explicit
  `uint(0xffffffff)` to produce `UINT_MAX`. Reject broader out-of-range values.
- Validate scalar/vector/matrix/array/struct constructor arity and component
  counts exactly. Matrices are float-only and column-major.

### Names, scopes, and mutability

- Persistent lexical scopes for globals, overload sets, function parameters,
  blocks, and `for` initializers. Diagnose duplicates deterministically.
- Analyze a declaration initializer before inserting the new local binding, to
  preserve shadowing behavior.
- Symbol records distinguish uniform, const, global, local, parameter, output,
  builtin, struct, and function storage/namespace as applicable.
- Inject only the corpus fragment builtin `gl_FragCoord: vec4`; declared outputs
  and uniforms come from the source/manifest. Do not invent runtime bindings.
- Reject writes to uniforms, consts, readonly parameters, or rvalues.

### Expressions and lvalues

- Table-drive unary/binary/assignment/ternary signatures. Include same-base
  scalar/vector arithmetic, vector-scalar float operators, comparison/logical
  forms, signed/unsigned integer bit/shift forms, and legal matrix/vector/
  matrix/scalar multiplication dimensions.
- Resolve struct fields exactly. Vector swizzles must use one naming family
  (`xyzw`, `rgba`, or `stpq`), stay within vector width, and reject repeated
  destinations for writes. No fallback field index.
- Array/vector/matrix indexing requires `int`/allowed integral index per GLSL
  rule and produces the correct element/column lvalue category. Validate
  constant bounds where statically known.
- Array dimensions are positive scalar constant `int` expressions.
  `__array_length` accepts arrays only and returns `int`.

### Functions, calls, builtins, and control flow

- Collect prototypes/definitions before bodies; detect duplicate definitions
  and incompatible declarations. Mangle/identify overloads by full signature,
  including parameter directions.
- Exact overload resolution only. `out`/`inout` arguments require writable,
  exact-type lvalues; `in` arguments are rvalues. Never select the first
  overload as fallback.
- Table-drive all observed builtins and constructor forms. Expected observed
  builtin names include: `abs`, `all`, `any`, `atan`, `ceil`, `clamp`, `cos`,
  `dFdx`, `dFdy`, `distance`, `dot`, `equal`, `exp`, `floor`,
  `floatBitsToUint`, `fract`, `fwidth`, `greaterThanEqual`, `inversesqrt`,
  `length`, `lessThan`, `lessThanEqual`, `log`, `log2`, `max`, `min`, `mix`,
  `mod`, `normalize`, `notEqual`, `packHalf2x16`, `pow`, `radians`, `reflect`,
  `refract`, `round`, `sign`, `sin`, `smoothstep`, `sqrt`, `step`, `tanh`,
  `texelFetch`, `texture`, `textureLod`, `textureSize`, and
  `unpackHalf2x16`. Recompute the actual set and fail/report any unregistered
  call.
- Conditions are scalar `bool`. Validate loop nesting for break/continue,
  return type/value, and fragment-only discard. Require exactly compatible
  `void main()`.

## Corpus semantic tool

Add `tools/glslcpp/check_semantics.py`:

```sh
python3 tools/glslcpp/check_semantics.py --check
python3 tools/glslcpp/check_semantics.py --report
```

- It first invokes/reuses Task 6 validation, then parses/analyzes all 212
  programs in stable program-key order and aggregates all diagnostics rather
  than stopping at the first program.
- `--check` succeeds only for exactly 212 typed programs and exact corpus gates.
- `--report` emits byte-stable JSON with revision/counts, semantic success 212,
  type/operator/builtin/overload incidence, per-program feature/resource flags,
  and explicit `"emission": "not attempted"` / `"compile": "not attempted"`.
  No timestamps or absolute paths.
- Tool import/run works from `/tmp` and cannot mutate corpus/generated files.

## Required tests

Add `tests/test_semantic.py` with focused tests for:

1. frozen/span-bearing typed IR; input parsed AST remains byte/deep equal after
   analysis;
2. literal types/ranges, explicit casts, and rejection of implicit conversion;
3. unknown/duplicate types, symbols, fields, signatures, and definitions;
4. exact overload choice plus ambiguous/no-match errors;
5. operator families, vector/matrix constructor/component rules, and ternaries;
6. valid/invalid swizzle read/write, index types, array dimensions, struct and
   uniform-block access;
7. const/uniform/readonly writes and `out`/`inout` writable-lvalue checks;
8. bool conditions, loop-control misuse, return/discard/main validation;
9. builtin coverage including texture, derivative, relational-vector,
   bit-cast/packing, and matrix/geometric families;
10. deterministic multi-program aggregate diagnostics with program/line/column;
11. all 212 pinned sources analyze successfully with no unresolved names/types/
    calls and stable resource requirements;
12. `--report` stability/CWD independence/no absolute path or timestamp;
13. Task 6 and Task 5 regression gates remain byte-identical/green.

Tests must prove error codes/messages and typed results, not just object
existence. Avoid one test per corpus file; aggregate failures deterministically.

## Verification

Run and record:

```sh
python3 tests/test_corpus.py
python3 tools/glslcpp/check_corpus.py --check
python3 tests/test_semantic.py
python3 tools/glslcpp/check_semantics.py --check
python3 tools/glslcpp/check_semantics.py --report
python3 tests/test_generator.py
python3 tools/glslcpp/generate_kernels.py --check
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build --parallel
build/noisemaker-cpu-tests
ctest --test-dir build --output-on-failure
```

## Report

Write `docs/port-engineering/task-7-report.md` with red/green evidence,
files/API summary, exact semantic incidence/readiness JSON, diagnostics/location
truth, full verification results, confirmation of no Git/sibling mutation, and
the exact remaining boundary before broad C++ emission/runtime expansion.
