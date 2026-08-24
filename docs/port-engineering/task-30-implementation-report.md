# Task 30 implementation report: Extrude bvec2 relational/reduction closure

Date: 2026-08-12
Author: integration owner (continuation agent)

## Result

`filter/extrude:extrude` is ported under identity profile
`extrude-bvec2-relational-reduction-v1`, with full-surface bit-exact parity
against the JavaScript reference.

| Quantity | Before | After |
|---|---:|---:|
| Typed programs | 129 | **130** |
| Public programs | 131 | **132** |
| Publicly unported | 81 | **80** |
| Corpus programs | 212 | 212 |

- typed-list SHA-256 `d31014f538686245f09fefe57ffccf9f2b8d36bdcaf65b0ae423be7476ab5904`
- public-list SHA-256 `4fe573b21a782a784b7fcacacaa276a03a395a1b8c92e83149971b8a19831056`
- Extrude zero-based typed ordinal **25**, between
  `filter/directionalBlur:directionalBlur` and `filter/fibers:fibersBlend`

The frozen precompute's projected counts were **stale** — they described the
post-Focus-Blur state rather than the post-Extrude state. The corrected
projection above was derived independently three times (design agent's two
methods plus the integration owner's own recomputation) and all agreed.

## The closure

Exactly four AST nodes, all in `main` (function id 36), inside the one counted
`for` at 143:5-173:6:

```glsl
bool topHit  = all(lessThanEqual(abs(P - faceCenter), faceHalf));           // 159
bool sideHit = (!topHit) && all(lessThanEqual(abs(P - cellC), halfCell));   // 160
```

| Site | Span | Type |
|---|---|---|
| top `all` | 159:23-159:72 | `bvec2 -> bool` |
| top `lessThanEqual` | 159:27-159:71 | `vec2,vec2 -> bvec2` |
| side `all` | 160:37-160:81 | `bvec2 -> bool` |
| side `lessThanEqual` | 160:41-160:80 | `vec2,vec2 -> bvec2` |

The profile proves every `bvec`-typed node in the whole program is one of the
two relational results, which is what structurally forbids declaration,
storage, return, subscripting, aggregation, and escape.

## Generated lowering

```cpp
[[maybe_unused]] bool topHit =
    glsl::all(glsl::lessThanEqual(glsl::abs((P - faceCenter)), faceHalf));
[[maybe_unused]] bool sideHit =
    ((!topHit) && glsl::all(glsl::lessThanEqual(glsl::abs((P - cellC)), halfCell)));
```

## Pixel parity — full-surface, bit-exact

Rendered through the real public binder and compared against the frozen
JavaScript oracle. **Eligibility matters**: the oracle carries six cases, but
only the three whose define map equals the slice's authorized default
`{EXTRUDE_TYPE: 0, DEPTH_SOURCE: 0}` are valid for the native port. The other
three use `EXTRUDE_TYPE: 1` and/or `DEPTH_SOURCE: 1`; binding them natively
would silently render a different program. They remain public-source
sensitivity evidence only.

| Case | F32 SHA-256 | Result |
|---|---|---|
| `blocks-default-luminance-solid` (13×9) | `47dee1b5c5d290f510a1c43f81f41bb19782b6f9f7d389e7be6701d0c8a01ac5` | MATCH |
| `blocks-depth-zero-window` (11×7) | `f8b901fde60223c9a3068ad5320295eed1098070d882978be5e5d6e3d4693106` | MATCH |
| `blocks-max-depth-luminance-window` (15×10) | `04ea7d2c0abee1daed54b97dcf1b1efb3c05cd828d23b8d2ac7c65d04d19ef73` | MATCH |

Whole-surface equality, plus all fifteen probes and input immutability.

## Design constraint discovered during implementation

`typed_manifest.json` records the **full global** capability vocabulary in
every program row — all 130 rows carry an identical 44-entry list. Adding a
45th capability would therefore have changed every row and invalidated the
frozen Task 27/28 historical-reconstruction hashes.

The existing `round` gate already solved this: admit by node identity, then
skip the capability bookkeeping. Extrude follows it exactly:

```python
if value.callee not in {"round", "all", "lessThanEqual"}:
    used.add(value.callee)
```

Post-implementation the vocabulary is still **44**, and neither `all` nor
`lessThanEqual` appears in any program's capability list. This was not
anticipated by the design brief and is the main non-obvious constraint a
future relational/reduction task must respect.

## Boundary verification

| Property | Result |
|---|---|
| `bvec2` in `APPROVED_TYPES` / `emit._TYPES` | absent from both |
| `all` / `lessThanEqual` in `_BUILTIN_NAMES` | absent |
| capability vocabulary length | 44, unchanged |
| 3-lane reduction | **compile error** — `constraints not satisfied [with N = 3]` |
| leak check: `filter/waves:waves` | still fails `41:9: unsupported builtin any` |

The C++ runtime functions are deliberately `requires(N == 2)`, so wider
boolean-vector relational reduction is structurally impossible rather than
merely untested.

### Independent authentication at both authorities

| Attack | Validator | Emitter |
|---|---|---|
| no profile carrier | rejected | rejected |
| wrong profile string | rejected | rejected |
| foreign program (`filter/waves`) | rejected | rejected |
| top/side `lessThanEqual` → `lessThan` | rejected | rejected |
| top/side `all` → `any` | rejected | rejected |

The emitter was invoked directly, bypassing the validator entirely, and still
failed closed. Neither authority trusts the other.

## Regeneration is surgical

```text
before blocks: 129   after blocks: 130
added:   ['filter/extrude:extrude']
removed: []
existing blocks CHANGED (modulo ordinal renumbering): NONE
```

Inserting at ordinal 25 renumbers later namespaces (Focus Blur 110→111,
`gatherSorted` `typed_52`→`typed_53`); no block's content changed.

## Verification (all fresh)

```text
Full Python discovery     Ran 193 tests in 2221.809s   OK   EXIT=0
Native (Debug, -Werror)   148/148 PASS, exit 0
check_corpus --check      exit=0 PASS
check_semantics --check   exit=0 PASS   (212 programs)
generate_typed_slice --check exit=0 PASS (130 programs)
generate_kernels --check  exit=0 PASS
oracle task-15 … task-30  exit=0 PASS   (16 of 16)
failures=0
```

Python grew 186 → 193 (7 new Task 30 tests); native grew 144 → 148 (4 new).
The full Python discovery result was reproduced independently by the
integration owner, not accepted from the test owner's report.

## Test coverage added

**Python** (`Task30ExtrudeBvec2RelationalReductionTests`, 7 tests): exact
authentication plus independent reconstruction with distinct objects; 47
single-axis structural mutations each asserting its own precondition before
rejection at all three authorities; validator/emitter independence including
forged-proof rejection; identity-scoping proven behaviorally rather than by
static list check; 9-item coexistence matrix; byte-for-byte Task 29
reconstruction; and native-table transcription with a 3,791-token tamper
sweep.

**Native** (4 tests): the three eligible oracle fixtures with exact F32/RGBA8
hashes, lane counts and probes; full binding-ABI fail-closed coverage; a
five-mode relational switch with no default arm; and direct truth tables for
the new runtime functions including inclusive equality, signed zero, and NaN.

### Anti-vacuity, verified not assumed

Task 26 shipped 3 of 11 native mutation modes that silently shared the
baseline code path, making 24 of 88 claimed rows meaningless. That class of
defect was explicitly guarded here, and the integration owner verified the
guard rather than trusting it: the 28-wide semantic signature payload is
derived only from observed behavior (reduced results, per-lane results, call
counters) and **excludes** mode id, mode name, and the one-hot dispatch array,
so pairwise uniqueness is genuine evidence of five distinct code paths. The
modes really do differ — mode 0 calls `all<2>()` while mode 1 runs an explicit
OR-reduce loop with its own counter — and the mirrored mode is proven to
diverge from the exact mode on specific rows rather than aliasing it.

## Note on the native test owner's compile-time proof

The `static_assert` proving `lessThanEqual<3>`/`all<3>` are hard errors
initially failed to compile: a `requires`-expression evaluated directly in a
non-template context is non-dependent, so Clang diagnoses the constraint
failure eagerly instead of treating it as substitution failure. The fix was to
keep the width dependent via file-scope template variables. Recorded because
the naive form looks correct and silently does not test what it claims.

## File hashes

| File | SHA-256 |
|---|---|
| `tools/glslcpp/frontend/extrude_bvec2_relational_reduction_profile.py` | `8954c974acacbd09012af554c0b3640259241f71a75a0d2a869cb7b8071cf8f9` |
| `tools/glslcpp/generate_typed_slice.py` | `56de25ca89aede60bb425c9884921a0e744b58ff8206c1b91d12f36681701c8d` |
| `tools/glslcpp/emit_typed_cpp.py` | `d4bab0bf7f57233b0b136375fda6061e716d43cba6d989d33088a233e0678236` |
| `tools/glslcpp/typed_slice.json` | `fcd63d5587e8c7f43dad2748c28e6a01c3e8812a2a470808dc4630e2883339b1` |
| `include/noisemaker/glsl_types.hpp` | `b9a6014483c22871e618a8557389174a5f73b2e59cf45e62d0ae1a2dfa0d4014` |
| `src/typed_generated/typed_slice.cpp` | `5765f8637fd08711cb665c295b7f1488f76fc2c19515b22d72c476e51808b5f3` |
| `src/typed_generated/typed_manifest.json` | `3a6b52895f4a4f4e25a3bafb67d84a40e194e11d157508fc1dc9763cb304c87e` |
| `include/noisemaker/generated/catalog.hpp` | `16ebd7b1c7908fcad87e4a0c1890b2eabc87a0ce09fa6ded961ce68162315b42` |
| `tests/test_typed_generator.py` | `0a8fc2b051ec7e6bfc40be588e47bc72c4d360cb370aba781f8dd234081c7030` |
| `tests/test_generated_kernels.cpp` | `a6167ead19169e095fb3daeb9c17c05de0e36c520be13ee6acba763fc06ed0a9` |
| `tests/test_glsl_types.cpp` | `4de6d7140a52ee874d0937108a2632bac4761234b9e24b6955bebcb29a20bc11` |
| `tests/oracles/task-30-oracles.json` | `bf8c4c165846eb116d2afb4f78b7c1de78f70f104ac714e09395ceffbe51c758` |

## Native lanes (fresh, this session)

```text
debug configure/build/ctest       exit=0 PASS
release configure/build/ctest     exit=0 PASS
sanitize configure/build          exit=0 PASS
sanitize run                      exit=0 PASS
failures=0
```

Sanitizer procedure preserved: attempt 1 ran with `detect_leaks=1` and aborted
with exit 134 and the platform message `AddressSanitizer: detect_leaks is not
supported on this platform`. The prescribed leak-disabled retry then passed
with exit 0. The first attempt was not skipped.

## Outstanding before acceptance

Independent adversarial implementation rereview.

---

## Addendum: independent rereview and response

The independent adversarial rereview
(`task-30-implementation-rereview.md`, SHA-256
`61e03afa2d39fa4db5b2f29bcb4aebe319a0eaa172a006fc342e026ea53cbfa0`) returned
**ACCEPT** with 0 Critical, 1 Important, 1 Minor, 2 Nits. Both substantive
findings were fixed rather than deferred.

### Important — the mutation test never reached the novel logic. FIXED.

The claim that "47 single-axis structural mutations reject at all three
authorities" was true but far weaker than it read. The reviewer ran all 47
axes directly against the profile and found **46 of 47** absorbed by the
single coarse gate

```text
source, define, function, whole-program, or interface mismatch
```

with the 47th caught by an equally coarse key check. **Zero** axes reached the
module's node-walk, reduction/relational pairing, ancestry, or bvec2-escape
checks — precisely the novel logic this task introduced. Any tree edit
perturbs the whole-program hash, so the coarse gate always fires first.

Fix: added
`test_task30_node_level_closure_logic_rejects_past_the_coarse_hash_gate`,
which re-freezes the coarse hashes to match each mutated tree (via
`mock.patch.multiple`, auto-restored) so the node-level logic actually runs.
Six mutations now reach it and are each rejected by a **specific** node-level
message, with an explicit assertion that the coarse message did **not** fire:

| Mutation | Node-level rejection |
|---|---|
| reduction `all` → `any` | `closure site cardinality mismatch` |
| relational `lessThanEqual` → `lessThan` | `closure site cardinality mismatch` |
| reduction loses its only child | `closure site cardinality mismatch` |
| reduction consumes the other relational | `closure node identity mismatch` |
| relational gains a third argument | `closure node identity mismatch` |
| relational result retyped to `bool` | `closure node identity mismatch` |

Each case asserts the mutation genuinely changed the tree before checking
rejection, and the test restores the real profile and re-authenticates the
exact program at the end so later tests cannot inherit a mis-frozen module.

The new test was itself proven non-vacuous: sabotaging the
`closure node identity mismatch` check (`if actual != _NODES` → `if False`)
makes three subtests fail. The sabotage also surfaced genuine defense in
depth — `consumed object cardinality mismatch` and `relational arity mismatch`
independently catch some of the same mutations.

### Minor — loosely scoped `bvec2` type admission. FIXED BY REMOVAL.

`emit_typed_cpp.py` admitted `bvec2` lowering scoped to "an Extrude proof
exists for this program" rather than to the two exact node identities, unlike
every other admission gate.

Investigation showed the branch was **dead code**: the `bvec2` value is
produced and consumed inline inside `glsl::all(glsl::lessThanEqual(...))` and
never needs a spelled type. Removing it entirely is strictly stronger than
tightening its scope — `bvec2` as a type name is now rejected
unconditionally, and generation is byte-identical
(`typed_slice.cpp` still `5765f863…`).

### Nits — recorded, no code change

1. GLSL `&&`/`||` do not short-circuit whereas the emitted C++ does. No
   observable difference here because the right-hand side is side-effect-free,
   but any future closure with effectful operands must revisit this.
2. `filter/edge:edge` is rejected at an earlier unrelated gate, before its
   `bvec3`/`greaterThanEqual` code is reached — a clarification of the leak
   control, not a defect.

### Post-fix verification

```text
check_corpus --check          exit=0 PASS
check_semantics --check       exit=0 PASS   (212 programs)
generate_typed_slice --check  exit=0 PASS   (130 programs)
generate_kernels --check      exit=0 PASS
native (Debug, -Werror)       148/148 PASS, exit 0
```

### Updated hashes after review fixes

| File | SHA-256 |
|---|---|
| `tools/glslcpp/emit_typed_cpp.py` | `7fd56b115692bea17651653011589197a762583bf4bf32d853a8fa1a3fd02ccf` |
| `tests/test_typed_generator.py` | `f64b7c1a71d0db9035efc65fe90341f25fbaa88d1c861e282920954bf34790eb` |

`src/typed_generated/typed_slice.cpp` is unchanged at
`5765f8637fd08711cb665c295b7f1488f76fc2c19515b22d72c476e51808b5f3`, confirming
the emitter fix altered no generated output.

### Final full Python discovery after review fixes

```text
Ran 194 tests in 1342.735s
OK
EXIT=0
```

193 → 194 (the new node-level closure test). **Task 30 is accepted.**
