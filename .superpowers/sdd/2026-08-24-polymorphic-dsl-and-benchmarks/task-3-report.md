# Task 3 report: exact Polymorphic DSL lexer

Status: implemented on the current `main` checkout. No worktree, branch, PR,
push, live CPU checkout mutation, or repository cache was used.

## Scope

The C++20 lexer ports the frozen CPU authority
`src/dsl/tokenize.js` in ordered rule order. It retains ASCII-only identifier,
number, color, escape, punctuation, and operator grammar; keeps `render` as a
keyword; accepts `1e`, `1e+`, and `1e-` as NaN-valued number tokens; and tracks
UTF-8 byte offsets separately from JavaScript-compatible UTF-16 index/column
locations. `DslError` exposes deterministic structured source, line, column,
UTF-16 index, and UTF-8 byte-index fields. Invalid UTF-8 bytes are consumed
without undefined behavior.

## Fixtures and hashes

- 16 fixture cases: 9 token streams and 7 error streams.
- 75 canonical tokens including EOF records.
- `tests/fixtures/dsl/frontend-cases.json`:
  `40684189849bbebb477848be185a8c2c42625d8ce9d0671ceb24b396ecb3533e`
- `tests/oracles/dsl_frontend_expected.txt`:
  `9e5cf4ba6b7f70939d62b92b37626ccc575bfce21cbb4b69a578edb0a69d0b50`

The corpus covers whitespace, line/block comments, EOF, valid and malformed
exponents, overflow values, strings and escapes, all color lengths, keywords,
surface forms, every punctuation/operator, unexpected characters,
unterminated strings/comments, astral characters before tokens/EOF/errors and
malformed UTF-8 through native regression coverage.

## Red evidence

At base `35247b0`, the requested lexer headers, sources, fixtures, oracle, and
tests were absent (`git cat-file -e
35247b0:include/noisemaker/dsl/lexer.hpp` and the corresponding test path both
returned missing-object errors). The first focused test invocation therefore
had no lexer API/target to build. The implementation then made those tests
green under strict warnings.

## Verification

Commands run from the repository root:

```text
cmake -S . -B /private/tmp/noisemaker-cpp-task3-build -DCMAKE_BUILD_TYPE=Release
cmake --build /private/tmp/noisemaker-cpp-task3-build --parallel 4       PASS
/private/tmp/noisemaker-cpp-task3-build/noisemaker-cpu-tests             PASS for all Task 3 tests
NOISEMAKER_CPU_ROOT=/private/tmp/noisemaker-cpp-continuation.e033lt/oracle/noisemaker-for-cpu \
NOISEMAKER_DSL_CPP_ORACLE=/private/tmp/noisemaker-cpp-task3-build/noisemaker-dsl-frontend-oracle \
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_dsl_frontend_oracle   PASS
node --check tools/dsl/js_frontend_oracle.mjs                          PASS
PYTHONDONTWRITEBYTECODE=1 python3 -B -m py_compile tests/test_dsl_frontend_oracle.py PASS
git diff --check                                                        PASS
```

The full native executable returned status 1 only for the two pre-existing,
unrelated baseline oracle failures:

- `typed_glitch_matches_all_eight_authoritative_js_oracles`
- `typed_shape_mixer_matches_all_forty_two_independent_js_oracles`

All six Task 3 native lexer tests passed in that run. The Python oracle test
regenerates to an external temporary file, checks byte identity with the
checked expected stream, then diffs every canonical C++ record exactly;
missing or non-absolute `NOISEMAKER_CPU_ROOT` is a hard failure.

## Files

Created `include/noisemaker/dsl/{error,token,lexer}.hpp`,
`src/dsl/{error,lexer}.cpp`, the fixture and checked oracle, native and Python
tests, and `tools/dsl/js_frontend_oracle.mjs`. Modified only `CMakeLists.txt`
to add the library sources, native tests, and the standalone C++ oracle mode.

Concern for follow-up: the authority lexer emits string decoded content as the
token `lexeme` (without quotes), which is intentionally preserved even though
other token lexemes are source slices. Parser work should consume that exact
contract.
