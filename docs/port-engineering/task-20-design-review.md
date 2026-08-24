# Task 20 implementation-design review

## Decision

**APPROVED.** No P0-P3 ambiguity, missing proof boundary, or omitted literal
matrix row remains in the second-amended Task 20 implementation design.

This was a read-only review of the design and current repository seams. I used
no Git command, changed no repository file, and wrote only this requested
review artifact.

Reviewed design SHA-256:
`4e015d511d6054f324c2084c15aaf7460c33bae49ea515b620d1418237141f7d`.

## Frozen inputs and baseline

The design points to the accepted binding artifacts with their exact current
identities:

- brief `65dcd5a522234a8c024edaafe7b942e678c5c0f2c643a260543547380c545ab5`;
- risk audit `6798f1459cd6ae512a8bd70ac730684d2b2b2b5389e2d367099d6fad07b85149`;
- oracle generator `4e9bead18c312cbf0aa5b3239bb575cfaec3ddd40cb246f3d47e8f3ccd49f75e`;
- oracle JSON `1f71fc6fb2f91f0c3b660decda30d533ecca20070bb318cc9757242be3499d03`;
- oracle report `02db6d234953dd23b2bea50b02e1c5d25449aefbdd7117e0959be003395b3f30`;
- approved scope/proof review
  `4c2f2fd8e5eb50bf483538fbc7bb8aa7adae9ef64f891d368e2ba9927a503297`.

The direct canonical generator independently passes `--check` with
`ok task-20-oracles.json`. Every repository baseline digest listed in the
design also matches the current post-Task-19 checkout, including the final
Task 19 generator, emitter, typed-IR, schema, tests, and three generated
outputs. The implementation therefore has a precise drift boundary and no
unexplained preexisting overlap.

## Compatibility-transform design

The design preserves the brief's exact five-node remedy. It authenticates the
raw and normalized source, empty proof-carrier input, interface, pre-function,
and pre-whole-program profiles before changing only the `/`, multiplication,
subtraction, `j@107` declaration/symbol, and sole later `j@107` read/symbol
types from `int` to `float`. It then requires both frozen post hashes and exact
dataclass equality everywhere else. `%`, `integer_mod`, early F32 arithmetic,
integral casts, geometry shortcuts, NaN tests, and hard-coded NaN output remain
closed.

The corrected validator/emitter seam is implementable against the current
pipeline: the pre-to-post transform runs exactly once after analysis and
rejects any pre-carried Task 17-20 proof. Validator and emitter receive the
post-transform tree and use a nonmutating post-tree authenticator rather than
trying to transform it again. Both boundaries now receive and authenticate
explicit `compatibility_transform` and `numeric_literal_contract` carriers,
so a direct caller cannot omit or forge the schema decision. The proposed
keyword-only emitter extension also explicitly requires the existing generator
call to move its literal-contract argument to a named carrier.

The resulting typed `float` chain composes with the current emitter: scalar
float arithmetic emits binary64 operations and `double j`, while the authored
`float(j)` constructor remains the F32 consumption boundary. The retained
`-ffp-contract=off` verification requirement protects the separately rounded
divide/multiply/subtract sequence.

## Affine-table proof and lowering

The proof remains closed to the one `fruitMask` `centers:vec2[13]@73` object.
It authenticates the declaration; the center, inner-ring, and outer-ring write
regions; exact affine/RHS profiles; all four read contexts/seven index sites;
direct call routing; `drawLines` control; loop summary; initialization
dominance; and all no-copy/no-alias/no-escape facts.

The revised design separates static syntax from dynamic work precisely:
one declaration, eight array-typed expressions, seven base identifiers, seven
indices, three static store sites / thirteen dynamic stores, and four static
read sites / 182 maximum Metatron reads, decomposed into 26 circle and 156
accepted-line endpoint reads. The mutation matrix explicitly rejects either a
correct static census with incorrect dynamic totals or the converse.

Validator and emitter both reattach counted-loop/discarded-counter facts,
clear all four top-level Task 17-20 proof fields together, rebuild Task 17,
Task 18, Task 19, then Task 20 in order, compare every original carrier with
its independent reconstruction, and reject nonapplicable foreign proofs. The
four required modes are explicit: authentic acceptance, cleared rejection,
stale rejection, and attacker-updated rejection.

Lowering is exact and local: `Centers13` is
`std::array<glsl::Vec2,13>`, the 8-byte Vec2 and 104-byte table assertions are
mandatory, `centers{}` preserves positive-zero F32 initialization, and only
the seven registered sites receive direct `operator[]` with explicit
`std::size_t` conversion. No ambient type, generic affine-index, runtime ABI,
or generic array permission is introduced.

## Literal matrix and completion gates

The second amendment now carries the brief's literal negatives through the
design, including:

- source/factory/runtime/interface/function-count and metadata-carrier drift;
- missing, duplicate, foreign, extra, already-applied, or twice-applied
  transform registration;
- every five-node identity/operator/span/ancestry and forbidden arithmetic
  variant;
- exact `2+k`, `6+k`, `8+k`, `k+1`, and `k+7` affine near misses;
- initializer control insertion, overlap/gap, precision/materialization, and
  symmetry-related RHS changes;
- early, literal, affine, unproved, out-of-range, moved, missing, duplicated,
  and control-shifted reads;
- whole-array, pointer/span, static/global/thread-local, parameter/return,
  multidimensional/nested/struct-array, resource/stage, and foreign-capability
  exclusions;
- all predecessor-proof clearing, staleness, substitution, reconstruction
  order, nested-copy, and fully attacker-updated forgery cases; and
- `.at()`, missing static assertions, dynamic stack, allocation/dispatch,
  finite-Star, RGBA8-only, catalog/count, and unrelated-generated-body failures.

All typed mutations are required at both validation and direct-emission
boundaries in the four proof modes. Generated-only properties are correctly
handled as code/native inspection cases.

The generated-source inspection is now scoped to the exact Sacred namespace,
with brace-balanced per-function inspection required for `fruitMask`,
`starPolygonMask`, `lineSegmentSDF`, `main`, and `pixel`. This avoids false
positives from unrelated authenticated factories and bind-time code while
retaining separate non-Sacred body-drift comparison. Debug, Release,
ASan/UBSan, ten full F32/RGBA8 cases, all eight Star qNaN variants, prior
oracles, stack `.su` classification, and Release disassembly remain mandatory
completion evidence.

## Residual

No design residual remains. Approval is for implementation readiness only; it
does not waive any review gate, native parity, sanitizer, stack, generated
shape, or final independent implementation review required by the brief and
design.
