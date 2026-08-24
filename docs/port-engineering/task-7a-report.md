# Task 7A declaration frontier report

## Scope and boundary

Implemented the declaration/signature/interface frontier only in
`.`.  The resulting immutable
`TypedProgram` explicitly records `body_status: "not analyzed"`; expression
typing, overload-call selection, lvalue checking, control flow, C++ emission,
runtime builtin support, render-graph work, and CLI work were not attempted.

No Git command, sibling-repository mutation, CMake input change, generated C++
output change, network access, or dependency download was performed.

## Red/green evidence

The first semantic contract was written before implementation and failed as
expected with `ModuleNotFoundError: tools.glslcpp.frontend.semantic`.  The
current focused suite is green (11 tests). A subsequent review found the
span/retained-structure P1 gaps; each was fixed test-first with exact
parser-produced spans, retained declaration records, and shared signature
identities now passing.

## API/files

- `tools/glslcpp/frontend/span.py`: frozen normalized-source `SourceSpan`.
- `tools/glslcpp/frontend/parser.py`: parser-private `Node` mappings retain
  token-derived start/end offsets for every declaration, control header,
  declarator, field/member, and expression mapping.
- `tools/glslcpp/frontend/ast_spans.py`: strips those private attributes into
  the unchanged legacy plain mapping AST and emits its exact, non-mutating
  AST-path span table.
- `tools/glslcpp/frontend/semantic_types.py`: immutable structural scalar,
  vector, matrix, sampler, array, and named-struct types.
- `tools/glslcpp/frontend/diagnostics.py`: stable program/line/column semantic
  diagnostics.
- `tools/glslcpp/frontend/typed_ir.py`: immutable symbols, declarations,
  struct fields/declarations, uniform blocks, function signatures/functions,
  resources, and typed-program boundary state.
- `tools/glslcpp/frontend/semantic.py`: two-pass declaration/signature
  collection with strict unknown/duplicate/incompatible/main checks.  It
  decodes local declaration types without analyzing bodies.
- `tools/glslcpp/check_semantics.py`: validates Task 6 first and reports a
  deterministic 212-program declaration frontier from any working directory.
- `tests/test_semantic.py`: focused immutable/span/type/signature/interface,
  negative-diagnostic, report-stability, and retained-record tests.

## Readiness JSON

`check_semantics --report` is deterministic and has no absolute paths or
timestamps.  Its exact readiness gate is:

```json
{
  "revision": "a024dc3a960cc44af454abc7aebce50456c194e6",
  "declaration_success": 212,
  "body_analysis": "not attempted",
  "emission": "not attempted",
  "compile": "not attempted"
}
```

The report measures 1,390 prototype/definition occurrences, 2,236 retained
global/interface declarations, and 6,654 decoded local declaration types.
It reports 2,450 `in`, 20 `out`, and 2 `inout` parameter occurrences.  The
full byte-stable JSON is at `docs/port-engineering/task-7a-readiness.json`.

Locations use normalized corpus source (post Task-6 preprocessing), not raw
source locations. `SourceSpan` offsets and line/columns are therefore
deterministic for the actual parser/emitter input. The corpus-wide invariant
measured all 212 programs: 0 missing mapping spans, 0 non-root whole-program
fallback spans, and 0 invalid ranges.

## Verification

Green commands recorded in this task:

```text
python3 tests/test_corpus.py                         # 9 tests passed
python3 tools/glslcpp/check_corpus.py --check       # ok
python3 tests/test_semantic.py                       # 11 tests passed
python3 tools/glslcpp/check_semantics.py --check    # declarations ok; body analysis not attempted
python3 tools/glslcpp/check_semantics.py --report   # declaration_success 212
python3 tests/test_generator.py                      # 7 tests passed
python3 tools/glslcpp/generate_kernels.py --check   # passed
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug         # passed
cmake --build build --parallel                        # passed
build/noisemaker-cpu-tests                            # 55 passed
ctest --test-dir build --output-on-failure            # 1/1 passed
```

## Exact remaining boundary

Task 7A supplies immutable, span-bearing declaration data only.  The next
phase must convert every function body into typed statements/expressions and
apply strict literals, operators, constructors, lvalues, function overloads,
uniform mutability, builtins, loop/control-flow, and resource-use analysis
before any broad C++ emitter may consume the corpus.
