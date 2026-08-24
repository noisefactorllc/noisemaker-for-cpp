# Task 6: freeze and parse-validate the stateless corpus

## Objective

Make the exact 167-effect stateless sibling target self-contained and offline before widening C++ emission. Vendor a pinned, hash-locked corpus and reduced metadata snapshot, add a full fail-closed GLSL frontend adapted from the sibling Python port, and prove every admitted program normalizes/parses locally.

This task does **not** emit or compile the other 206 generated C++ kernels, add runtime builtins, implement the render graph, or add the four adapters. Preserve the Task-5 two-program generated outputs and normal CMake behavior.

## Scope truth and gates

Pinned revision: `a024dc3a960cc44af454abc7aebce50456c194e6`.

The admitted stateless milestone must be count-gated as:

- 167 effects;
- 212 passes total;
- 208 coverage records with status `generated`;
- 4 coverage records with status `adapter`:
  - `classicNoisedeck/fractal`
  - `filter/historicPalette`
  - `filter/palette`
  - `synth/julia`
- 212 canonical coverage source files total. `filter/wormhole:deposit` has a pinned canonical `deposit.frag` coverage source but the sibling runtime intentionally overrides that pass as a CPU `drawMode: points` operation, so reduced runtime metadata gives it no kernel key;
- 211 keyed runtime kernels/passes plus that one draw-op override.

Do not admit the 21 current iterated/stateful effects or the five later scatter adapters in this task.

## Constraints

- Work only in `.`.
- Never invoke Git or any indirect Git operation. No branches/worktrees/commits/PRs.
- TDD for corpus validator/frontend behavior; report to `docs/port-engineering/task-6-report.md`, not the repo.
- Apply code/test/manifest edits with `apply_patch`. Exact byte-for-byte copying of the large admitted source corpus and reduced metadata is a permitted bulk mechanical operation after paths and hashes are resolved; do not use shell redirection tricks to author code.
- Never modify sibling repositories.
- Normal CMake must remain Python/Node/network/sibling-independent and continue compiling only committed C++.
- Developer tools use Python 3 standard library only.
- Preserve the hardened Task-5 generated-directory transaction/path rules.
- Add Python cache patterns to `.gitignore` (`__pycache__/`, `*.py[cod]`) as a directly related hygiene change; do not remove unrelated files.

## Authoritative local extraction inputs

Read-only extraction inputs:

- current coverage records: `../noisemaker-for-cpu/src/effects/generated/glsl-coverage.js`;
- pinned revision evidence: `../noisemaker-for-cpu/src/effects/generated/upstream-snapshot.js` and `scripts/upstream/source-lock.js` (read the constants only; do not execute the Git-based lock check);
- target effect/pass metadata: `../noisemaker-python/src/noisemaker_cpu/bundle/metadata.json`;
- canonical raw sources: `../noisemaker/shaders/effects/<effectId>/glsl/<coverage.file>`.

Extract only effect IDs present in the 167-effect metadata snapshot. Verify every resolved canonical source exists and remains inside the canonical `shaders/effects` root. Do not access CDN/network. Do not assert sibling working-tree cleanliness/HEAD.

## Vendored layout

Suggested:

```text
tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/
  manifest.json
  metadata.json
  sources/<effect-id path>/<program-file>.glsl
```

The corpus manifest is schema-versioned and sorted. Each source-backed record includes:

- `effect_id`, `program`, stable `program_key`, `status` (`generated`/`adapter`);
- safe relative source path;
- source byte size and raw SHA-256;
- normalized byte size and normalized SHA-256;
- normalized outputs/varyings needed by the future emitter;
- pass index/name if needed to disambiguate metadata.

Retain the real canonical `filter/wormhole:deposit` coverage source and also mark its reduced-metadata pass as a CPU draw-op override with no kernel key. Never generate or register that GLSL as the runtime implementation in this milestone.

The reduced `metadata.json` must be deterministic JSON derived from the sibling snapshot, contain exactly the 167 admitted effects, preserve effect/pass/param/texture data required by the later renderer, and contain no absolute paths or URLs needed at runtime. It may retain immutable provenance strings.

## Full frontend

Add a private full frontend under `tools/glslcpp/frontend/`:

- `__init__.py`
- `lexer.py`
- `preprocess.py`
- `parser.py`
- optionally `ast.py` for typed dataclasses/helpers

Adapt the sibling Python port's standard-library lexer/preprocessor/parser semantics rather than extending the Task-5 proof parser with special cases. Preserve the Task-5 `tools/glslcpp/parser.py` API/output for its two generated kernels; a compatibility wrapper may call the full frontend only if it keeps Task-5 output byte-identical.

Frontend requirements:

- no network, eval/exec, Node, sibling imports, or mutable global state;
- deterministic token positions and `FrontendError(program_key,line,column,message)` for invalid/unsupported input;
- do not mutate caller ASTs during later compatibility conversion;
- support every syntax family present in the admitted corpus: top-level variables/functions/prototypes, uniform blocks, structs, qualifiers, scalar/vector/matrix/sampler types, arrays/indexing, constructors/swizzles, unary/binary/ternary/assignment expressions, overload declarations/calls, out/inout params, blocks, if/else, for/while/do, return/break/continue/discard;
- preprocessing must deterministically handle the corpus's `#version`, `GL_ES`, object-like macros, conditional defines lowered from runtime parameter defines, interface blocks, helper lowerings, and canonical normalization rules already proven by the sibling port;
- reject unconsumed tokens and malformed directives fail-closed.

This task's completion gate is normalization + full parse for all admitted source-backed programs. A standalone semantic/type checker is the next task; do not claim type-check coverage here.

## Corpus tool

Create `tools/glslcpp/check_corpus.py` with explicit modes:

```sh
python3 tools/glslcpp/check_corpus.py --check
python3 tools/glslcpp/check_corpus.py --report
```

- Paths resolve relative to the repository/tool, never CWD/home.
- `--check` validates schema, revision, exact count gates, program/effect uniqueness, safe relative paths (including POSIX/Windows traversal/device/ADS rules), no symlinks, exact recursive file set, raw/normalized hashes and sizes, reduced metadata count/pass relationships, adapter allowlist, wormhole draw-op override identity, and parses all 212 coverage sources.
- Re-normalize/parse in stable program-key order; do not trust recorded normalized fields.
- `--report` is read-only and prints deterministic JSON summary with counts and syntax-feature incidence; no timestamps/absolute paths.
- The tool must not offer a mode that mutates the vendored corpus in normal use. One-time extraction belongs to this implementation task/report, not an ongoing sibling-dependent command.

## Required tests

Add `tests/test_corpus.py` using stdlib `unittest`. Direct tests must cover:

1. current committed corpus passes and exact gates are 167 effects / 212 passes / 212 canonical sources / 208 generated statuses / 4 adapter statuses / 211 keyed runtime kernels / 1 wormhole draw-op override;
2. two existing Task-5 fixtures byte-match their corresponding corpus sources or hashes;
3. corpus manifest ordering does not affect deterministic validation/report ordering (or unsorted input is rejected explicitly—prefer normalization to stable order);
4. raw-source tamper, normalized-hash tamper, metadata effect/pass deletion, adapter-set drift, duplicate program/output key, path traversal/absolute/backslash/colon/Windows-device paths, symlink, nested extra, and missing source all fail with program-aware errors;
5. `--report` is byte-stable over two runs and contains no absolute path/timestamp;
6. focused frontend fixtures cover each syntax family listed above, malformed/unconsumed tokens, directive errors, and source locations;
7. all 212 admitted coverage programs normalize and parse; failures list every failing program deterministically rather than stopping at the first during the coverage test;
8. importing/running the tool from `/tmp` succeeds without changing CWD-sensitive behavior;
9. Task-5 generator test/check remain byte-identical and green;
10. normal CMake remains unaware of Python/corpus sources.

Avoid one assertion per corpus file; aggregate deterministic diagnostics while retaining exact failing keys.

## Verification

Run and record:

```sh
python3 tests/test_corpus.py
python3 tools/glslcpp/check_corpus.py --check
python3 tools/glslcpp/check_corpus.py --report
python3 tests/test_generator.py
python3 tools/glslcpp/generate_kernels.py --check
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build --parallel
build/noisemaker-cpu-tests
ctest --test-dir build --output-on-failure
```

## Report

Write `docs/port-engineering/task-6-report.md` with:

- exact extraction mapping/count/hash evidence and any reconciled count ambiguity;
- red/green commands;
- files/asset counts and total bytes;
- frontend subset/full-coverage truth;
- exact `--report` summary;
- final Python/generator/C++/CTest results;
- explicit statement that no sibling Git/HEAD/clean check was performed;
- remaining blocker before semantic typing and broad C++ emission.
