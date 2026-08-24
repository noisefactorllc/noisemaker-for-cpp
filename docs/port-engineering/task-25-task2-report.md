# Task 25 Task 2 report

## Scope

Implemented only the requested literal-vec3-lane carrier plumbing in:

- `tools/glslcpp/frontend/literal_vec3_lane_index_profile.py`
- `tools/glslcpp/generate_typed_slice.py`
- `tools/glslcpp/emit_typed_cpp.py`
- focused Task 25 coverage in `tests/test_typed_generator.py`

The helper received one fix-round private source-provenance function;
no slice, generated, native, registry, typed-IR, capability-vocabulary, or
numeric-contract files were changed.

Fix-round helper SHA-256:
`62920c523ab4a73e4a6c75fe912459bdf7ccde86196871eda2eeab16c69ca216`.

## RED

Before implementation, this focused command failed as intended:

```text
python3 -m unittest \
  tests.test_typed_generator.TypedGeneratorTests.test_task25_loader_schema_admits_only_the_two_later_lane_carriers \
  tests.test_typed_generator.TypedGeneratorTests.test_task25_four_modes_and_value_forgery_reject_at_each_boundary \
  tests.test_typed_generator.TypedGeneratorTests.test_task25_profiled_emission_uses_only_fixed_hsv_lanes
```

Observed failures:

- loader exact 125-entry planned spec: `typed slice programs are invalid`
- validator: `validate_capabilities() got an unexpected keyword argument 'literal_vec3_lane_index_profile'`
- emitter: `render_typed_cpp() got an unexpected keyword argument 'literal_vec3_lane_index_profile'`

## GREEN

The same focused command passed after the implementation:

```text
Ran 3 tests in 0.605s
OK
```

Focused coverage verifies:

- the exact future 125-entry loader form admits exactly the two selected
  profile carriers, and missing/wrong/duplicate/foreign/compatibility variants
  reject;
- pre/post four modes at loader, validator, and emitter boundaries;
  independent validator/emitter acceptance of an exact structural post clone;
  and rejection of a value-forged post tree for absent/wrong/exact carriers
  and exact/missing/wrong/recomputed caller hashes;
- six fixed `set_swizzle<I>(hsv, rhs)` writes and five fixed
  `swizzle<I>(hsv)` reads in emitted pixel bodies, preserving the line-260
  scalar-to-vec3 splat; and empty lane authorization for ordinary and
  `object.__new__` emitter instances.

The existing Task 24 loader/generator, ordinary emitter, loader-negative, and
Task 25 helper tests were also invoked together with `py_compile` as a
compatibility check.

## Concern / Task 3 hard requirement

Because Task 2 is explicitly prohibited from editing `typed_slice.json`, the
current 123-program no-carrier form remains accepted only when its sorted key
list hashes exactly to the accepted Task 24 digest
`df7750a48a77733e50f0e20072e291c2404e761932f6df8ddbcf8793d58fb6ac`.
This is not a generic legacy mode. Task 3 must add RED coverage requiring this
transitional branch to be removed when the live slice becomes the exact
125-entry, two-carrier form.

## Fix round 1 RED/GREEN

Review expansion first added literal 3-carrier by 4-caller-hash matrices for
each selected program at the application boundary and independently at the
validator and emitter boundaries.  The matrix uses one-axis site/member,
kind, children, type, category, span, write-role-context, raw/normalized
source, key, defines, function tuple, and interface mutations, plus every
exact-raw post mutation combined with a foreign outer key.

The first expanded run was RED.  A foreign-key plus exact-post-member mutation
with no carrier was accepted by both direct layers; the old key detector only
recognized an otherwise exact post tree.  The failure also covered equivalent
site/context combinations.

The repair adds only the private profile helper `_selected_source_key`.  It
recognizes the two frozen raw-and-normalized source identities independently
of program key and tree contents; both validator and emitter use it to require
the carrier before generic handling.  It adds no public profile function,
IR/schema/proof/carrier field, or runtime capability.

GREEN evidence after the repair:

```text
python3 -m unittest \
  tests.test_typed_generator.TypedGeneratorTests.test_task25_pre_and_exact_raw_post_forgery_cartesians_are_closed

Ran 1 test in 3.247s
OK
```

The exact pre/post controls are also exercised across all 3 carrier modes and
4 caller-hash labels, with explicit application/validator/emitter subtests.
The patched `generate_outputs` driver disagreement test was invoked with both
a forged post returned by the profile application and a patched analyzer that
returns a post tree into the pre application boundary; it performs the real
corpus semantic preflight and stops before generated-byte writes on rejection.

The same Cartesian now additionally covers independent base name/ID/type/
storage/writability and index non-int/nonliteral/negative/lane-3/effectful
fixtures.  Fresh focused evidence after that expansion:

```text
Ran 1 test in 3.119s
OK
```

Later review hardening added a 125-key digest lock
`9b8f94754fc40e8f8701bb539d403d44343dbfc9c351809a6ca6dbbd468cdbd4`
to the future-carrier loader form and direct exact capability-vocabulary
enforcement.  The loader test now includes a valid-corpus key substitution;
the four-mode test includes missing/duplicate/unknown capability cases.
Fresh focused verification:

```text
Ran 4 tests in 6.547s
OK
```

The private selected-source check was also hardened to retain provenance when
either frozen raw or normalized source identity remains exact, so a one-field
source drift plus a foreign key cannot erase carrier enforcement.  The Task 1
profile tests and the extended Cartesian were rerun together and passed:

```text
Ran 3 tests in 13.962s
OK
```

The next exploratory Section 7 chunk added structural main-body and assignment
operator mutations at both application and post-boundary Cartesian paths.
These are not yet a substitute for the required exact site-census mutations
or real prefix/postfix AST fixtures, so they are explicitly not claimed as
complete coverage.  Fresh result:

```text
Ran 1 test in 5.195s
OK
```

## Fix round 2: complete Section 7 binding

This round replaced the exploratory Task 25 site-count/update labels with
independently targeted, real parser/semantic fixtures and exact typed-tree
mutations.  Production behavior did not require another fix.  The only
repository file changed in this round was `tests/test_typed_generator.py`;
the three previously implemented Task 2 production files retain their exact
behavior and final hashes listed below.

### Exact site and Cartesian coverage

`test_task25_exact_site_shape_origin_and_context_cartesians_are_closed`
now resolves every frozen path directly, asserts the literal span and exact
8/3 per-program census, and freezes the aggregate 11-site control plus literal
10- and 12-site boundary counts.  The application matrix runs every forged
pre value across three carriers by four caller-hash labels.  Validator and
emitter each independently run every forged post value across the same literal
3 by 4 matrix.

The exact-source mutations independently cover zero, partial, one additional
dataclass-equal site, one shared-identity duplicate, move, order reversal,
already transformed input, and an acyclic nested/twice-transformed post value.
The post move is built only from `post_main.body`, and identity census proves
each authenticated post swizzle remains present exactly once.

Real parsed and analyzed index values supply alternate local, parameter,
global, uniform, vec2, vec4, integer-vector, array, matrix, uniform-index,
induction-index, effectful-index, nested-index, alias, delayed indexed lvalue,
and runtime-subscript origins.  Real parsed expression parents supply direct
write, compound assignment, unary prefix update, postfix update, `out` and
`inout` escape, RHS, and scalar-splat contexts.  In particular, the test uses
an authenticated read as a plain-`=` LHS and an authenticated write in an
rvalue splat, rather than changing an assignment operator to pretend that it
is a prefix/postfix expression.  Reversed RHS order and the Lens line-260
three-argument nonsplat are separate exact mutations.

The same Cartesian includes actual typed global, array, matrix, struct, UBO,
loop, derivative, sampler, fetch, output, function, early-return, and recursive
insertions, plus independent main/function/order/signature/body, resource,
proof, and body-status changes.

### Real language-boundary and metadata coverage

`test_task25_real_parser_semantic_resource_and_control_exclusions_are_closed`
uses nearby accepted controls and actual source text.  Valid typed constructs
reach capability validation; non-int, negative, out-of-range, struct, sampler,
and pointer index/pointer-like forms reach semantic rejection; a VLA reaches
`E_ARRAY_SIZE`; and allocation, callback, exception, and indirect-call syntax
rejects in the parser.  The pointer spelling is explicitly asserted to parse
as binary `float * ptr` before semantic `E_UNKNOWN_SYMBOL` rejection.

`test_task25_selected_corpus_identity_drift_rejects_at_real_preflight` runs
the real corpus preflight against both selected entries and independently
mutates corpus revision, effect/program/program-key/runtime-key identity,
source path, raw and normalized sizes/hashes, generated/adapter status, pass
identity, outputs, and varyings.

The future 125-entry loader fixture now additionally covers sorted count/key
drift, Grade LUT carrier borrowing, extra selected fields, nonempty selected
defines, program order, and missing/duplicate/unknown/index/runtime-subscript/
reordered capability vocabularies.  Numeric contracts cover missing,
selected-key, unknown, and extra-key variants.  Compatibility contracts cover
missing, selected-key, and unknown/foreign variants.  The valid loader control
still requires the exact newline-terminated 125-key digest and exact two
carrier records.

### Driver non-laundering and mutation sensitivity

The driver test now exercises both selected keys independently with:

- a forged pre value returned by the analyzer;
- an exact already-post value returned into the pre application boundary;
- a forged post value returned by the application helper.

Each case snapshots the generated C++, manifest, and catalog header before and
after rejection.  One iteration performs the real corpus and semantic
preflight (including semantic report's own second corpus validation); the five
remaining literal cases reuse only those expensive preflight results so the
test stays bounded.  Fresh standalone evidence was:

```text
Ran 1 test in 34.040s
OK
DRIVER_STATUS=0
```

Mutation sensitivity was proved by temporarily removing only the validator's
raw-or-normalized selected-source provenance arm.  The exact-source Cartesian
went RED with 180 validator failures, including foreign-key exact/raw/member,
context, interface, and source variants.  The guard was immediately restored
with `apply_patch`; the same focused test then returned GREEN:

```text
Ran 1 test in 2.921s
OK
```

No temporary production mutation remains.

### Final verification

All ten Task 25 Task 1 plus Task 2 Python methods were run together:

```text
Ran 10 tests in 88.469s
OK
TASK25_FOCUSED_STATUS=0
```

The four owned Python files compiled cleanly:

```text
PY_COMPILE_STATUS=0
```

The real transitional 123-program generator check completed with explicit
status:

```text
generate_typed_slice: typed slice ok (123 programs)
GENERATOR_CHECK_STATUS=0
```

Final SHA-256 values:

| File | SHA-256 |
| --- | --- |
| `tools/glslcpp/frontend/literal_vec3_lane_index_profile.py` | `62920c523ab4a73e4a6c75fe912459bdf7ccde86196871eda2eeab16c69ca216` |
| `tools/glslcpp/generate_typed_slice.py` | `8c453c5526dee235232df1d25ada88294d120e2023632fbfa89da1b425ff7df1` |
| `tools/glslcpp/emit_typed_cpp.py` | `18659e9b2e76e14d2da69ce198b21ce653d325525a67b290b856ee7af61dbd1c` |
| `tests/test_typed_generator.py` | `0e89165df7f7c40652075e6a83d68e3aee7ffa3a4a89844c49fd6e57aeb99bc2` |

No slice, generated, native, registry, parser, semantic, typed-IR, capability,
numeric-contract, proof, runtime, or CMake file was edited.  No Git, branch,
worktree, commit, push, pull request, workflow, deployment, or external write
was performed.
