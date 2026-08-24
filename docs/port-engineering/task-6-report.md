# Task 6 report: pinned stateless GLSL corpus

## Extraction and provenance

- Read-only inputs only: `noisemaker-for-cpu` coverage/snapshot constants,
  `noisemaker-for-python` bundle metadata, and canonical files below
  `noisemaker/shaders/effects`.  No network, sibling Git/HEAD, cleanliness, or
  lock command was invoked.
- Pinned revision: `a024dc3a960cc44af454abc7aebce50456c194e6`.
- The resulting self-contained corpus is 212 canonical source files / 1,056,829
  source bytes.  `manifest.json` is 133,010 bytes and SHA-256
  `d9abd402d2baee5c4fb4a4150aa889768f812892f2641d6d6da2b56e624c5d0f`;
  reduced `metadata.json` is 449,976 bytes and SHA-256
  `258ea5aa64edf7499c4872babf574743b09a12b51e658f01dd74d020392f2c29`.
- Count reconciliation: coverage has exactly 212 records for the metadata's 167
  stateless effects: 208 generated, 4 adapter.  There are 211 non-null runtime
  keys because `filter/wormhole:deposit` retains its canonical `deposit.frag`
  coverage source but deliberately has `key: null, drawMode: points` in reduced
  metadata.
- Each sorted manifest record locks raw and normalized byte sizes/SHA-256,
  interfaces, pass relation, status, and runtime key.  The manifest additionally
  locks the complete reduced metadata hash; this prevents silent param/pass drift.
- `filter/text:text` is explicitly provenance-tested because the local sibling's
  current shader had drifted.  The corrected pinned raw is 1,327 bytes, SHA-256
  `be62b513c1fb56f34d23ace109b76a525454f5a5dbac64239949d6faf16e7462`;
  the displaced 2,058-byte local raw SHA-256 was
  `dbc53485dd4e410ee305044ef5bde2241ea58f33460e3cc8f8264a3cc2e43daf`.

## TDD evidence

RED, before the frontend/validator existed:

```text
$ python3 tests/test_corpus.py
ImportError: cannot import name 'check_corpus'
ModuleNotFoundError: No module named 'tools.glslcpp.frontend'
```

GREEN after the implementation:

```text
$ python3 tests/test_corpus.py
.........
Ran 9 tests
OK
```

The final source-location assertion also followed a red/green cycle: before
the diagnostic-position fix it reported `location:1:1`; after the minimal
fix it reports the expected `location:2:15` and the same nine-test suite is
green.

The tests exercise exact gates, fixture byte identity, report CWD/stability,
syntax and directive diagnostics, raw/normalized tampering, metadata effect and
pass deletion, adapter drift, duplicate program/runtime/interface records,
unsafe POSIX/Windows/ADS paths, ordinary `COM10` acceptance, missing/nested and
symlinked sources, and deterministic aggregate diagnostics.

## Frontend truth

`tools/glslcpp/frontend/` is a local adaptation of the sibling's standard
library tokenizer, preprocessor and recursive-descent parser, wrapped in a
program-keyed `FrontendError`.  The preprocessor has no `eval`/`exec`; it uses a
small integer conditional parser.  It is a full syntax/normalization frontier,
not a semantic/type checker.  All 212 admitted coverage programs normalized and
parsed successfully.

Deterministic `--report`:

```json
{
  "counts": {"adapter": 4, "draw_op_overrides": 1, "effects": 167, "generated": 208, "keyed_runtime": 211, "passes": 212, "sources": 212},
  "features": {"for": 103, "out_param": 7, "struct": 4, "ternary": 104, "uniform_block": 1, "while": 1},
  "revision": "a024dc3a960cc44af454abc7aebce50456c194e6",
  "schema": 1
}
```

## Final verification

```text
$ python3 tests/test_corpus.py
......... OK
$ python3 tools/glslcpp/check_corpus.py --check
check_corpus: ok
$ python3 tools/glslcpp/check_corpus.py --report
deterministic JSON above
$ python3 tests/test_generator.py
....... OK
$ python3 tools/glslcpp/generate_kernels.py --check
exit 0
$ cmake -S ... -B .../build -DCMAKE_BUILD_TYPE=Debug
$ cmake --build .../build --parallel
$ build/noisemaker-cpu-tests
55 PASS
$ ctest --test-dir build --output-on-failure
1/1 passed
```

Normal CMake remains unaware of Python/frontend/corpus sources and Task-5's two
generated outputs remain checked byte-for-byte by its unchanged generator test.

## Remaining boundary

The next task still needs semantic/type checking and broad C++ emission.  This
task intentionally did not register the other 206 generated kernels, add
runtime builtins/render graph, or implement adapters.
