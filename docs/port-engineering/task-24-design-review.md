# Task 24 amended-brief and implementation-design review

## Verdict

**APPROVED.** The amended brief and final design are internally consistent and
coherent with the accepted Task 23 tree. The design's exact site/parent-owned
clamp-helper emission, negative matrices, native oracles, generated isolation,
loop/resource accounting, and verification gates satisfy the frozen scope.

Reviewed inputs:

- amended brief SHA-256
  `a5184121126d75b32372440aae13ef9cde06006c5f4189607327e323e7d16e53`;
- implementation design SHA-256
  `8a93fe7818ddd6b20d3ce034d8bcd0ae13216e7794d9a1aef56b189de260376c`;
- amended brief review SHA-256
  `2adfde8d084e310bcd00089f26d70ad813f94aef713d708f82a08306356261a0`.

## Prior preflight finding resolved

The final design replaces the superseded initial-review hash with the amended
approving review SHA-256
`2adfde8d084e310bcd00089f26d70ad813f94aef713d708f82a08306356261a0`,
labels it precisely as the amended Task 24 brief review, and omits the old
hash. The immutable preflight now resolves every artifact at its current
frozen path and can pass without historical ambiguity.

## Substantive checks passed

### Exact profile and emission ownership

- The loader carries exactly `gather-sorted-round-to-int-v1` on Gather and
  does not infer authority from key membership or add a typed-IR field.
- The pure authenticator resolves the exact frozen path and independently
  locks source/key/defines, round child, immediate int parent, declaration,
  function/whole/interface hashes, loop proof, resources, and sole-round
  census. Identity application returns the same immutable program object.
- Validator admission is exact-object-only and does not add `round` to
  `APPROVED_CAPABILITIES` or `_BUILTINS`.
- Emitter admission is exact-parent and exact-child object identity. It emits
  only
  `glsl::detail::float_to_int32(glsl::round(authenticated_argument))` as one
  parent-owned expression. `_BUILTIN_NAMES` and the generic scalar
  `int(float)` fallback remain unchanged, preventing sibling or future round
  exposure.
- The current Task 23 RED projection is correctly the direct
  `std::int32_t(glsl::round(...))` route. The design requires that spelling to
  disappear only at the authenticated Gather site and requires all prior
  generic conversions to remain byte-identical.

### Loader, validator, emitter, and forgery matrices

- All four exact/forged tree by absent/exact carrier modes are exercised at
  loader/driver, direct validator, and direct emitter boundaries.
- Wrong/foreign/duplicate carriers, caller-hash variants, key/source/define/
  normalized/function/whole/interface drift, every round child/parent/
  declaration mutation, wrong nested-helper spelling, loop/proof/control-flow
  mutation, resource/interface/function additions, and unrestricted `round`
  capability injection are explicit negatives.
- Each boundary re-authenticates independently; no earlier accepted object or
  caller-supplied digest becomes proof authority.

### Oracle and native execution

- The frozen oracle package is unchanged and `node
  task-24-oracle-generator.mjs --check` passes on accepted Task 23.
- The design transcribes all four normative cases, all four normative
  mutations, both exclusions, and all three exclusion controls field-for-field
  into a hermetic native fixture, including all input/output hashes and probes,
  signed F32 row bits, finite counts, repeat identity, and three-input
  immutability.
- Floor, ceil, and loop-8 temporary variants must first be rejected by both
  production boundaries, remain outside repository outputs, and reproduce the
  frozen mutation metrics. The production identity row exercises the exact
  nested helper.
- Negative-half equality and huge-positive clamp/wrap divergence are run
  through the production helper with the frozen candidate hashes and metrics,
  while remaining explicitly non-normative and outside generic parity.

### Counts, isolation, resources, and stack

- Accepted/projected counts, list digests, and insertion remain exactly
  122/124/88/212 to 123/125/87/212 and typed position 51.
- All accepted Task 23 owned-file hashes in the design reproduce; the new
  helper is absent as required. Artifact/source/tree/profile/loop identities
  and the 88-key emitter-aware frontier census remain unchanged.
- Isolation protects raw blocks 0-50 and all 122 prior normalized-ordinal
  blocks; only one namespace, manifest record, catalog row, and header
  declaration are added. Prior manifest records may change only their existing
  monolithic `output_sha256`, and prior scalar-int emission remains identical.
- The exact three sampler bindings, one output, one texture-size site, three
  static fetch sites, and 66 dynamic fetches are locked at typed, generated,
  and native levels. The 64-trip loop proof and hashes are unchanged.
- The generated namespace bans dynamic allocation, containers, callbacks,
  exceptions, recursion, VLA/`alloca`, indirect calls, and dynamic stack. Fresh
  Debug/Release/sanitizer builds, `.su`, Release disassembly, the ordered
  `round -> glsl_round -> floor -> float_to_int32` route, and the 16 KiB static
  frame gate are required on final bytes.

No repository file or Git state was changed.
